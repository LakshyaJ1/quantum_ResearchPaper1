"""Explicit finite-reserve scenarios and paired environmental counterfactuals.

Scenario values are stress-test assumptions, not measured weather or attack costs.
Generation suppression does not invalidate pre-existing secret key material.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Optional

import networkx as nx
import numpy as np

from qkdsim.config import (AccountingConfig, AdversaryConfig, OutageConfig,
                          PhysicsConfig, ReservoirConfig, SimConfig,
                          TRAFFIC_CLASSES)
from qkdsim.network import Topology, _build, formation_9node
from qkdsim.sim import Simulator


@dataclass(frozen=True)
class Case:
    topology: str = 'formation'
    horizon_s: int = 86400
    warmup_s: int = 0
    isr_scale: float = 0.1
    rate_scale: float = 1.0
    initial_spendable_fraction: float = 0.02
    reservoir_scale: float = 1.0
    n_auth: int = 7
    attack_budget: float = 0.0
    attack_method: str = 'weighted_cut'
    attack_surface: str = 'generation'
    attack_start_s: float = 0.0
    attack_duration_s: float = 86400.0
    delta_e: float = 0.05
    e_abort: float = 0.075
    gamma: float = 1.0
    fibre_attack_cost: float = 10.0
    outage_model: str = 'independent'
    mean_uptime_s: float = 3600.0
    mean_outage_s: float = 120.0
    transport_uptime_s: float = 3600.0
    transport_outage_s: float = 120.0
    routing: str = 'KAR'
    fail_mode: str = 'FAIL_DEGRADED'
    fallback: str = 'online_kem'
    buffer_policy: str = 'retain'

    def to_dict(self):
        return asdict(self)


def build_topology(name: str, res: ReservoirConfig) -> Topology:
    if name == 'formation':
        return formation_9node(res)
    if name == 'ring':
        g = nx.cycle_graph(8)
        rear, terminal = 0, 4
    elif name == 'grid':
        g = nx.grid_2d_graph(3, 3)
        rear, terminal = (0, 0), (2, 2)
    elif name in ('parallel3', 'parallel4'):
        count = int(name[-1])
        g = nx.Graph()
        for branch in range(count):
            nx.add_path(g, ['source', f'b{branch}a', f'b{branch}b', 'sink'])
        rear, terminal = 'source', 'sink'
    else:
        raise ValueError(f'Unknown topology: {name}')
    names = {n: f'N{i}' for i, n in enumerate(g.nodes)}
    edges = [(names[u], names[v], 'FSO_NOMINAL') for u, v in g.edges]
    roles = {names[n]: 'relay' for n in g.nodes}
    roles[names[rear]], roles[names[terminal]] = 'rear', 'forward'
    return _build(edges, roles, res)


def attack_order(topo: Topology, method: str, fibre_cost: float):
    """Return a heuristic order, relative costs, and exact all-terminal cut.

    The cut minimizes *structural* isolation cost; it is not asserted to maximize
    finite-horizon assurance loss. Adaptive centrality recomputes the residual
    graph after every suppression, unlike the historical fixed ranking.
    """
    source = next(n for n, role in topo.node_roles.items() if role == 'rear')
    targets = sorted(n for n, role in topo.node_roles.items() if role == 'forward')
    costs = {k: fibre_cost if lk.link_class == 'FIBRE' else 1.0
             for k, lk in topo.links.items()}
    graph = topo.graph.copy()
    for u, v in graph.edges:
        graph[u][v]['capacity'] = costs[Topology.key(u, v)]
    sink = '__all_targets__'
    infinity = sum(costs.values()) + 1
    for t in targets:
        graph.add_edge(t, sink, capacity=infinity)
    _, partition = nx.minimum_cut(graph, source, sink, capacity='capacity')
    left, right = partition
    cut = sorted(Topology.key(u, v) for u in left for v in graph.neighbors(u)
                 if v in right and sink not in (u, v))
    if method == 'weighted_cut':
        order = cut + sorted((k for k in costs if k not in cut),
                             key=lambda k: (costs[k], k))
    elif method == 'static_betweenness':
        bc = nx.edge_betweenness_centrality(topo.graph, normalized=False)
        order = sorted(costs, key=lambda k: (-bc.get(k, bc.get(k[::-1], 0)) / costs[k], k))
    elif method == 'adaptive_betweenness':
        remaining = topo.graph.copy()
        order = []
        while remaining.number_of_edges():
            reachable = [t for t in targets if nx.has_path(remaining, source, t)]
            if not reachable:
                break
            bc = nx.edge_betweenness_centrality_subset(
                remaining, sources=[source], targets=reachable, normalized=False)
            useful = [(Topology.key(*k), v) for k, v in bc.items() if v > 0]
            if not useful:
                break
            edge = min(useful, key=lambda pair: (-pair[1] / costs[pair[0]], pair[0]))[0]
            order.append(edge)
            remaining.remove_edge(*edge)
        order += sorted(k for k in costs if k not in order)
    else:
        raise ValueError(f'Unknown attack method: {method}')
    return order, costs, cut


class RevisionSimulator(Simulator):
    def __init__(self, topo, cfg, case: Case, traffic, grade_policy=None):
        self.case = case
        self.now_s = -cfg.tick_s
        self.environment_transport = {k: False for k in topo.all_link_keys()}
        self.environment_generation = {k: False for k in topo.all_link_keys()}
        self._env_group = False
        self._previous_generation_failure = set()
        self.purged_bits = 0.0
        self._env_rng = np.random.default_rng(np.random.SeedSequence([cfg.seed, 731]))
        self._group_rng = np.random.default_rng(np.random.SeedSequence([cfg.seed, 947]))
        self._order, self.attack_costs, self.exact_cut = attack_order(
            topo, case.attack_method, case.fibre_attack_cost)
        self._chosen_attack = []
        remaining = case.attack_budget
        for edge in self._order:
            if self.attack_costs[edge] <= remaining + 1e-10:
                self._chosen_attack.append(edge)
                remaining -= self.attack_costs[edge]
        super().__init__(topo, cfg, traffic=traffic, grade_policy=grade_policy)

    def _apply_adversary(self):
        # Applied on an explicit clock in _tick_outages, including release.
        self._adv_links = set()

    def _tick_outages(self):
        self.now_s += self.cfg.tick_s
        c = self.case
        dt = self.cfg.tick_s
        if c.outage_model not in ('none', 'independent', 'correlated'):
            raise ValueError(c.outage_model)
        # Draw the same number of exogenous random values regardless of attacks
        # and policy actions, including during classical transport denial.
        draws = self._env_rng.random((len(self.environment_transport), 2))
        group_draw = self._group_rng.random()
        if c.outage_model != 'none':
            p = dt / (c.mean_outage_s if self._env_group else c.mean_uptime_s)
            if group_draw < p:
                self._env_group = not self._env_group
        active = c.attack_start_s <= self.now_s < c.attack_start_s + c.attack_duration_s
        self._adv_links = set(self._chosen_attack) if active else set()
        current_failures = set()
        for i, k in enumerate(self.topo.all_link_keys()):
            link = self.topo.links[k]
            if c.outage_model != 'none':
                old = self.environment_transport[k]
                if draws[i, 0] < dt / (c.transport_outage_s if old else c.transport_uptime_s):
                    self.environment_transport[k] = not old
                if link.link_class != 'FIBRE':
                    if c.outage_model == 'correlated':
                        self.environment_generation[k] = self._env_group
                    else:
                        old = self.environment_generation[k]
                        if draws[i, 1] < dt / (c.mean_outage_s if old else c.mean_uptime_s):
                            self.environment_generation[k] = not old
            transport = self.environment_transport[k]
            generation = self.environment_generation[k]
            attacked = k in self._adv_links
            link.outage = transport or (attacked and c.attack_surface == 'transport')
            link.excess_qber = max(c.delta_e if attacked and c.attack_surface == 'generation' else 0,
                                  1.0 if generation else 0)
            if link.current_rate_bps(self.cfg.physics) <= 0:
                current_failures.add(k)
                if c.buffer_policy == 'purge' and k not in self._previous_generation_failure:
                    store = self.topo.stores[k]
                    lost = store.available()
                    # Discard is separately reported as purge, never useful key
                    # consumption. Authentication reserve remains protected.
                    store._cur -= lost
                    store.discarded_bits += lost
                    self.purged_bits += lost
        self._previous_generation_failure = current_failures


def make_simulator(case: Case, seed: int, policy=None) -> RevisionSimulator:
    if not 0 <= case.initial_spendable_fraction <= 1:
        raise ValueError('Initial spendable fraction must be in [0,1]')
    if case.fallback not in ('online_kem', 'preplaced_symmetric'):
        raise ValueError(case.fallback)
    if case.buffer_policy not in ('retain', 'purge'):
        raise ValueError(case.buffer_policy)
    base = ReservoirConfig()
    scale = case.reservoir_scale
    minimum, maximum = round(base.m_min * scale), round(base.m_max * scale)
    initial = minimum + case.initial_spendable_fraction * (maximum - minimum)
    reservoir = replace(base, m_min=minimum, m_max=maximum,
                        m_thr=round(base.m_thr * scale), m_initial_frac=initial / maximum)
    cfg = SimConfig(horizon_s=case.horizon_s, warmup_s=case.warmup_s, seed=seed,
                    reservoir=reservoir, accounting=AccountingConfig(n_auth=case.n_auth),
                    physics=PhysicsConfig(e_abort=case.e_abort, gamma=case.gamma),
                    adversary=AdversaryConfig(budget_links=0),
                    outage=OutageConfig(), routing=case.routing,
                    fail_mode=case.fail_mode,
                    pqc_setup_s=0.35 if case.fallback == 'online_kem' else 0.0)
    topo = build_topology(case.topology, reservoir)
    for link in topo.links.values():
        link.nominal_rate_bps *= case.rate_scale
    traffic = tuple(replace(tc, arrival_rate=tc.arrival_rate * case.isr_scale)
                    if tc.name == 'ISR' else tc for tc in TRAFFIC_CLASSES)
    return RevisionSimulator(topo, cfg, case, traffic, grade_policy=policy)
