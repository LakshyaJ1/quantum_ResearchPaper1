"""Short checks for a post-hoc persistence intervention, not outcome assertions."""
import importlib
import importlib.util
from pathlib import Path
from dataclasses import replace
import hashlib
import tempfile
import unittest

import networkx as nx
from qkdsim.sim import Session
from revision.scenarios import Case


def module():
    assert importlib.util.find_spec('experiments.revision_online_persistence') is not None
    return importlib.import_module('experiments.revision_online_persistence')


def case():
    return Case(horizon_s=120,outage_model='none')


class PersistenceTests(unittest.TestCase):
    def test_unused_slots_retain_previous_targets_when_paths_are_temporarily_unusable(self):
        m=module()
        persistent=m.make_simulator(2,m.PERSIST,2,3100,case())
        release=m.make_simulator(2,m.RELEASE,2,3100,case())
        for sim in (persistent,release):
            sim._tick_outages()
            for link in sim.topo.links.values():
                link.outage=True
        previous=set(persistent._chosen_attack)
        self.assertEqual(len(previous),2)
        self.assertEqual(set(persistent.select_online_targets()),previous)
        self.assertEqual(release.select_online_targets(),[])

    def test_initialization_without_previous_targets_uses_a_deterministic_covering_cut(self):
        m=module()
        choices=[]
        for _ in range(2):
            sim=m.make_simulator(4,m.PERSIST,2,3100,case())
            for link in sim.topo.links.values():
                link.outage=True
            selected=sim.select_online_targets()
            graph=sim.topo.graph.copy()
            graph.remove_edges_from(selected)
            self.assertFalse(nx.has_path(graph,'N0','N4'))
            self.assertEqual(sum(sim.attack_costs[e] for e in selected),2)
            choices.append(selected)
        self.assertEqual(choices[0],choices[1])

    def test_primary_route_feedback_choice_is_unchanged_when_it_fills_the_budget(self):
        m=module()
        choices=[]
        for variant in (m.RELEASE,m.PERSIST):
            sim=m.make_simulator(2,variant,1,3100,case())
            s=Session(0,'C2',0,2048,'N0','N2','G2',5,1)
            self.assertTrue(sim._try_grade(s,'G2',0))
            choices.append(sim.select_online_targets())
        self.assertEqual(choices[0],choices[1])

    def test_retention_never_exceeds_concurrent_budget(self):
        m=module()
        for budget in (1,2):
            sim=m.make_simulator(6,m.PERSIST,budget,3100,
                replace(case(),outage_model='independent',transport_uptime_s=3,transport_outage_s=5))
            for _ in range(120):
                sim._tick_outages()
                self.assertEqual(sum(sim.attack_costs[e] for e in sim._adv_links),budget)
            self.assertEqual(sim.relative_cost_link_seconds,120*budget)

    def test_exogenous_streams_and_arrivals_match_every_variant_and_control(self):
        m=module()
        config=replace(case(),outage_model='independent',mean_uptime_s=10,
                       mean_outage_s=3,transport_uptime_s=10,transport_outage_s=3)
        sims=[m.make_simulator(2,v,0 if v==m.CONTROL else 2,3101,config)
              for v in (*m.VARIANTS,m.CONTROL)]
        results=[s.run() for s in sims]
        hashes=[s.attack_audit()['environment_trace_sha256'] for s in sims]
        self.assertEqual(len(set(hashes)),1)
        traces=[[(s.sid,s.cls,s.arrival_t,s.src,s.dst) for s in sorted(r.sessions,key=lambda s:s.sid)]
                for r in results]
        self.assertTrue(all(t==traces[0] for t in traces))
        self.assertTrue(all(s.purged_bits==0 for s in sims))

    def test_diagnostic_does_not_change_completed_source_or_dataset(self):
        m=module()
        protected=[m.ROOT/'experiments/revision_online_adversary.py',
                   m.ROOT/'results/revision/online_adversary/manifest.json',
                   m.ROOT/'results/revision/online_adversary/analysis.json']
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        m.make_simulator(2,m.PERSIST,2,3100,case()).run()
        after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        self.assertEqual(before,after)
        self.assertNotEqual(m.OUT.resolve(),(m.ROOT/'results/revision/online_adversary').resolve())

    def test_confirmation_seeds_are_disjoint_from_exploratory_seeds(self):
        m=module()
        self.assertEqual(set(m.SEEDS),set(range(3100,3106)))
        self.assertFalse(set(m.SEEDS)&set(range(3000,3006)))
        self.assertEqual(m.protocol()['requested_runs'],126)

    def test_paired_difference_preserves_null_or_negative_confirmation(self):
        m=module()
        self.assertTrue(hasattr(m,'paired'))
        def rows(v):
            return [{'seed':s,'arrival_sha256':str(s),'attack':{'environment_trace_sha256':str(s)},
                     'summary':{'all':{'forced_entitled_fraction':v}}} for s in m.SEEDS]
        result=m.paired(rows(0.2),rows(0.4),'forced_entitled_fraction')
        self.assertAlmostEqual(result['mean'],-0.2)
        self.assertAlmostEqual(result['ci_low'],-0.2)


if __name__=='__main__':
    unittest.main(verbosity=2)
