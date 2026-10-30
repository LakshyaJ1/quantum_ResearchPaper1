"""Small deterministic conservation and structural-ranking checks.

Run: python -c "from experiments.revision_theory_checks import main; main()"
This is separate from the Monte Carlo grid and does not modify its outputs.
"""
from __future__ import annotations

import os
for _thread_option in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_thread_option] = '1'

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qkdsim.config import AccountingConfig, ReservoirConfig, SimConfig
from qkdsim.network import Topology, _build, chain_topology
from qkdsim.sim import Outcome, Session
from revision.scenarios import Case, RevisionSimulator, attack_order


class RegularFixedGradeSimulator(RevisionSimulator):
    """Only the arrival process changes; production relay/purge code is used."""

    def __init__(self, topo, cfg, case, request_count, interval_s, initial_spendable):
        self.request_count = request_count
        self.interval_s = interval_s
        self.initial_spendable = initial_spendable
        self.cut_edges = [k for k in topo.all_link_keys() if 'S' in k]
        self.events = []
        self._recorded_results = 0
        super().__init__(topo, cfg, case, traffic=())

    def _tick_arrivals(self, t):
        if self._next_sid < self.request_count and int(t) % self.interval_s == 0:
            self.pending.append(Session(
                sid=self._next_sid, cls='C2', arrival_t=t, payload_bits=2048,
                src='S', dst='T', authorised_floor='G2', deadline_s=0.0, priority=1))
            self._next_sid += 1

    def _tick_serve(self, t):
        super()._tick_serve(t)
        if len(self.results.sessions) == self._recorded_results:
            return
        self._recorded_results = len(self.results.sessions)
        stores = [self.topo.stores[k] for k in self.cut_edges]
        consumed = sum(s.consumed_bits for s in stores)
        generated = sum(s.generated_bits for s in stores)
        discarded = sum(s.discarded_bits for s in stores)
        remaining = sum(s.available() for s in stores)
        initial = len(stores) * self.initial_spendable
        self.events.append(dict(
            time_s=float(t), arrivals=self._next_sid,
            served=sum(s.outcome is Outcome.SERVED for s in self.results.sessions),
            blocked=sum(s.outcome is Outcome.BLOCKED for s in self.results.sessions),
            cut_consumed_bits=consumed, cut_generated_bits=generated,
            cut_discarded_bits=discarded, cut_remaining_spendable_bits=remaining,
            cut_bound_holds=consumed <= initial + generated - discarded + 1e-9,
            cut_conservation_residual_bits=initial + generated - discarded - consumed - remaining,
        ))


def run_reservoir_case(branches=3, spendable_bits=1500, interval_s=5,
                       buffer_policy='retain'):
    """Exercise q=750-bit G2 delivery on m separate two-hop branches.

    Equal-length candidate paths are all enumerated for m<=4. KAR can choose
    another branch once one cannot afford a delivery. Requests have zero waiting
    allowance, so a failed request is resolved at its own arrival time.
    """
    if type(branches) is not int or not 1 <= branches <= 4:
        raise ValueError('The fixture requires one to four parallel branches')
    if type(spendable_bits) is not int or spendable_bits < 0:
        raise ValueError('Spendable stock must be a nonnegative integer')
    if type(interval_s) is not int or interval_s <= 0:
        raise ValueError('Arrival spacing must be a positive integer number of seconds')
    if buffer_policy not in ('retain', 'purge'):
        raise ValueError('Buffer policy must be retain or purge')

    accounting = AccountingConfig(metadata_bits=240, tag_bits=127, n_auth=2)
    debit = accounting.cost_per_hop(256)
    per_branch = spendable_bits // debit
    exact_capacity = branches * per_branch
    request_count = exact_capacity + 2
    horizon = (request_count - 1) * interval_s + 1
    reservoir = ReservoirConfig(m_min=10, m_thr=10 + spendable_bits,
                                m_max=10 + spendable_bits, m_initial_frac=1.0)
    edges = [(u, v, 'FSO_NOMINAL') for b in range(branches)
             for u, v in (('S', f'B{b}'), (f'B{b}', 'T'))]
    roles = {'S': 'rear', 'T': 'forward', **{f'B{b}': 'relay' for b in range(branches)}}
    topo = _build(edges, roles, reservoir)
    cfg = SimConfig(horizon_s=horizon, warmup_s=0, reservoir=reservoir,
                    accounting=accounting, routing='KAR', fail_mode='FAIL_CLOSED')
    # Attack every edge's generation so neither hop of any branch replenishes.
    # The production scenario code handles retention versus purge at t=0.
    case = Case(horizon_s=horizon, warmup_s=0, outage_model='none',
                attack_budget=float(2 * branches), attack_method='weighted_cut',
                attack_surface='generation', attack_duration_s=float(horizon + 1),
                buffer_policy=buffer_policy)
    sim = RegularFixedGradeSimulator(topo, cfg, case, request_count, interval_s,
                                    spendable_bits)
    result = sim.run()
    served = [s for s in result.sessions if s.outcome is Outcome.SERVED]
    blocked = [s for s in result.sessions if s.outcome is Outcome.BLOCKED]
    cut_stores = [topo.stores[k] for k in sim.cut_edges]
    cut_consumed = sum(s.consumed_bits for s in cut_stores)
    cut_generated = sum(s.generated_bits for s in cut_stores)
    cut_discarded = sum(s.discarded_bits for s in cut_stores)
    cut_remaining = sum(s.available() for s in cut_stores)
    expected_capacity = exact_capacity if buffer_policy == 'retain' else 0
    branch_counts = {f'B{b}': int(topo.store('S', f'B{b}').consumed_bits / debit)
                     for b in range(branches)}
    first_unserved = min((s.arrival_t for s in blocked), default=None)
    residual = (result.initial_stored_bits + result.full_generated_bits
                - result.full_consumed_bits - result.full_discarded_bits
                - result.final_stored_bits)
    checks = {
        'expected_session_count': len(served) == expected_capacity,
        'all_branches_reach_expected_count': all(
            count == (per_branch if buffer_policy == 'retain' else 0)
            for count in branch_counts.values()),
        'first_failure_at_expected_arrival': first_unserved == expected_capacity * interval_s,
        'all_cut_events_obey_bound': all(e['cut_bound_holds'] for e in sim.events),
        'all_cut_events_conserve_key': all(
            abs(e['cut_conservation_residual_bits']) < 1e-9 for e in sim.events),
        'full_conservation': abs(residual) < 1e-9,
        'one_cut_debit_per_served_request': cut_consumed == len(served) * debit,
        'two_hop_debits_per_served_request': result.full_consumed_bits == 2 * len(served) * debit,
        'no_new_key': result.full_generated_bits == 0,
        'classical_path_unchanged': all(not link.outage for link in topo.links.values()),
        'no_below_floor_service': all(s.grade == 'G2' and not s.floor_violation for s in served),
    }
    return dict(
        branches=branches, hops_per_branch=2, spendable_bits_per_edge=spendable_bits,
        protected_bits_per_edge=10, quantum_key_bits_per_session=256,
        relay_debit_bits_per_edge=debit, interval_s=interval_s,
        buffer_policy=buffer_policy, requests=request_count, served=len(served),
        blocked=len(blocked), branch_service_counts=branch_counts,
        retained_exact_branch_capacity=exact_capacity,
        pooled_cut_bound=math.floor(branches * spendable_bits / debit),
        post_discard_cut_bound=math.floor(
            (branches * spendable_bits + cut_generated - cut_discarded) / debit),
        cut_initial_spendable_bits=branches * spendable_bits,
        cut_consumed_bits=cut_consumed, cut_generated_bits=cut_generated,
        cut_discarded_bits=cut_discarded, cut_remaining_spendable_bits=cut_remaining,
        full_consumed_bits=result.full_consumed_bits,
        full_generated_bits=result.full_generated_bits,
        full_purged_bits=sim.purged_bits,
        full_conservation_residual_bits=residual,
        first_unserved_arrival_s=first_unserved,
        expected_first_unserved_arrival_s=expected_capacity * interval_s,
        retained_fluid_reference_s=branches * spendable_bits * interval_s / debit,
        fluid_scope='pooled continuous demand reference; not an exact discrete-store trajectory',
        transport_available=checks['classical_path_unchanged'],
        generation_stopped=checks['no_new_key'],
        checks=checks, all_checks_passed=all(checks.values()), events=sim.events,
    )


def _isolation_prefix(topo, order, costs):
    graph = topo.graph.copy()
    source = next(n for n, role in topo.node_roles.items() if role == 'rear')
    targets = [n for n, role in topo.node_roles.items() if role == 'forward']
    def connected():
        return any(nx.has_path(graph, source, target) for target in targets)
    prefix, cost = [], 0.0
    for edge in order:
        before = connected()
        graph.remove_edge(*edge)
        prefix.append(list(edge))
        cost += costs[Topology.key(*edge)]
        after = connected()
        if not after:
            return dict(isolation_edge_count=len(prefix), isolation_relative_cost=cost,
                        prefix_edges=prefix, connected_before_last_removal=before,
                        connected_after_prefix=after)
    raise AssertionError('Declared attack order failed to isolate its target')


def structural_depth_checks():
    """Offline graph removal, explicitly separate from finite-time FAL."""
    rows = []
    for depth in range(1, 7):
        topo = chain_topology(depth, ReservoirConfig())
        for method in ('static_betweenness', 'adaptive_betweenness', 'weighted_cut'):
            order, costs, cut = attack_order(topo, method, fibre_cost=10.0)
            rows.append(dict(depth=depth, method=method,
                             exact_structural_cut_cost=sum(costs[e] for e in cut),
                             tie_convention='canonical undirected edge names',
                             **_isolation_prefix(topo, order, costs)))
        # Reproduce the old code's static ranking exactly, including its raw
        # NetworkX edge-orientation tie-break, to expose naming sensitivity.
        centrality = nx.edge_betweenness_centrality(topo.graph)
        historical = [edge for edge, _ in sorted(
            centrality.items(), key=lambda kv: (-kv[1], kv[0]))]
        rows.append(dict(depth=depth, method='historical_static_betweenness',
                         exact_structural_cut_cost=sum(costs[e] for e in cut),
                         tie_convention='original NetworkX edge-orientation tuples',
                         **_isolation_prefix(topo, historical, costs)))
    return rows


def _source_hashes():
    paths = [Path(__file__), ROOT / 'revision/scenarios.py']
    paths += sorted((ROOT / 'qkdsim').glob('*.py'))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths}


def build_report():
    before = _source_hashes()
    reservoir_rows = [run_reservoir_case(branches=m, spendable_bits=b, buffer_policy=p)
                      for m, b, p in ((1, 1500, 'retain'), (2, 1500, 'retain'),
                                      (3, 1500, 'retain'), (4, 1500, 'retain'),
                                      (3, 1900, 'retain'), (3, 1900, 'purge'),
                                      (4, 749, 'retain'))]
    structural_rows = structural_depth_checks()
    structural_ok = all(r['connected_before_last_removal'] and
                        not r['connected_after_prefix'] and
                        (r['method'] not in ('adaptive_betweenness', 'weighted_cut')
                         or r['isolation_relative_cost'] == r['exact_structural_cut_cost'])
                        for r in structural_rows)
    unchanged = before == _source_hashes()
    return dict(
        schema_version=1, generated_utc=datetime.now(timezone.utc).isoformat(),
        python_version=platform.python_version(), networkx_version=nx.__version__,
        source_sha256=before, code_unchanged_during_run=unchanged,
        scope={
            'reservoir_test': 'deterministic fixed-grade requests; generation stopped; classical transport available',
            'structural_test': 'offline edge removal; no key inventory feedback',
            'evidence_type': 'implementation verification of conditional accounting and graph facts; not external validation',
            'fluid_reference': 'requires pooled or balanced continuous demand assumptions for equality',
        },
        reservoir_checks=reservoir_rows, structural_depth_checks=structural_rows,
        all_checks_passed=unchanged and structural_ok and all(
            row['all_checks_passed'] for row in reservoir_rows),
    )


def write_report(path=ROOT / 'results/revision/theory_checks.json'):
    report = build_report()
    if not report['all_checks_passed']:
        raise AssertionError('A deterministic theory check failed; refusing a passing artifact')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/revision/theory_checks.json')
    args = parser.parse_args(argv)
    report = write_report(args.output)
    print(json.dumps({'output': str(args.output), 'all_checks_passed': report['all_checks_passed'],
                      'reservoir_cases': len(report['reservoir_checks']),
                      'structural_cases': len(report['structural_depth_checks'])}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
