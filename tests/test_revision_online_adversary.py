"""Short genuine-simulation tests; never run the registered 126-run study."""
import importlib
import importlib.util
from dataclasses import asdict, replace
import unittest

from qkdsim.config import quantum_key_demand
from qkdsim.network import chain_topology
from qkdsim.sim import Outcome, Session
from revision.scenarios import Case, RevisionSimulator


def module():
    assert importlib.util.find_spec('experiments.revision_online_adversary') is not None
    return importlib.import_module('experiments.revision_online_adversary')


def request(sid=0, dst='N2', cls='C2', floor='G2', payload=2048):
    return Session(sid,cls,0,payload,'N0',dst,floor,10,1)


def short_case(**changes):
    return replace(Case(horizon_s=120,outage_model='none'),**changes)


class OnlineAdversaryTests(unittest.TestCase):
    def test_observer_records_real_committed_quantum_route(self):
        m=module()
        sim=m.make_chain_simulator(2,'online_route_feedback',1,3000,short_case())
        session=request()
        self.assertTrue(sim._try_grade(session,'G2',0))
        self.assertEqual(session.outcome,Outcome.SERVED)
        self.assertEqual(sim.quantum_route_observations,1)
        observed=next(iter(sim.recent_routes))
        self.assertEqual(set(observed),{('N0','N1'),('N1','N2')})
        self.assertEqual(session.key_bits,2770)

    def test_failed_attempt_and_classical_only_delivery_create_no_route_observation(self):
        m=module()
        sim=m.make_chain_simulator(2,'online_route_feedback',1,3000,short_case())
        self.assertFalse(sim._try_grade(request(cls='ISR',floor='G1',payload=10**9),'G1',0))
        self.assertEqual(sim.quantum_route_observations,0)
        self.assertTrue(sim._try_grade(request(1),'G4',0))
        self.assertEqual(sim.quantum_route_observations,0)
        self.assertFalse(sim.recent_routes)

    def test_online_target_changes_after_a_genuine_router_path_switch(self):
        m=module()
        sim=m.make_chain_simulator(2,'online_route_feedback',1,3000,short_case())
        sim._try_grade(request(),'G2',0)
        primary=set(sim.select_online_targets())
        self.assertTrue(primary & {('N0','N1'),('N1','N2')})
        sim.recent_routes.clear()
        sim.topo.link('N0','N1').outage=True
        self.assertTrue(sim._try_grade(request(1),'G2',0))
        sim.topo.link('N0','N1').outage=False
        alternative=set(sim.select_online_targets())
        self.assertNotEqual(primary,alternative)
        self.assertTrue(alternative & {('A1','N0'),('A1','A2'),('A2','N2')})

    def test_two_slots_cover_two_paths_and_never_exceed_concurrent_budget(self):
        m=module()
        sim=m.make_chain_simulator(6,'online_route_feedback',2,3000,short_case())
        chosen=sim.select_online_targets()
        self.assertEqual(len(chosen),2)
        primary={sim.topo.key(f'N{i}',f'N{i+1}') for i in range(6)}
        self.assertEqual(sum(edge in primary for edge in chosen),1)
        self.assertLessEqual(sum(sim.attack_costs[e] for e in chosen),2)
        sim._tick_outages()
        self.assertEqual(sum(sim.attack_costs[e] for e in sim._adv_links),2)

    def test_no_viable_route_means_no_pointless_active_suppression(self):
        m=module()
        sim=m.make_chain_simulator(2,'online_route_feedback',2,3000,short_case())
        for link in sim.topo.links.values():
            link.outage=True
        self.assertEqual(sim.select_online_targets(),[])

    def test_attack_methods_preserve_environment_and_arrival_realizations(self):
        m=module()
        case=short_case(outage_model='independent',mean_uptime_s=10,mean_outage_s=3,
                        transport_uptime_s=15,transport_outage_s=3)
        sims=[m.make_chain_simulator(2,method,2,3001,case) for method in m.METHODS]
        for tick in range(90):
            for sim in sims:
                sim._tick_outages()
                sim._tick_generate()
                sim._tick_arrivals(float(tick))
                sim._tick_serve(float(tick))
            self.assertTrue(all(s.environment_transport==sims[0].environment_transport for s in sims))
            self.assertTrue(all(s.environment_generation==sims[0].environment_generation for s in sims))
        def arrivals(sim):
            return sorted((s.sid,s.cls,s.arrival_t,s.src,s.dst)
                          for s in sim.results.sessions+sim.pending)
        self.assertTrue(all(arrivals(s)==arrivals(sims[0]) for s in sims))

    def test_route_observation_does_not_change_retention_or_key_accounting(self):
        m=module()
        monitor=m.make_chain_simulator(2,'weighted_cut',2,3002,short_case())
        plain=RevisionSimulator(chain_topology(2,monitor.cfg.reservoir),monitor.cfg,
                                monitor.case,monitor.traffic)
        a,b=monitor.run(),plain.run()
        self.assertEqual(asdict(a),asdict(b))
        self.assertEqual(a.initial_stored_bits+a.full_generated_bits-a.full_consumed_bits
                         -a.full_discarded_bits,a.final_stored_bits)
        self.assertEqual(monitor.purged_bits,0)

    def test_retention_is_visible_and_link_time_cost_is_a_distinct_quantity(self):
        m=module()
        sim=m.make_chain_simulator(2,'online_route_feedback',2,3002,short_case())
        initial={k:s.level for k,s in sim.topo.stores.items()}
        sim._tick_outages()
        self.assertEqual(initial,{k:s.level for k,s in sim.topo.stores.items()})
        self.assertEqual(sim.relative_cost_link_seconds,2)
        self.assertEqual(len(sim.distinct_links_touched),2)
        self.assertEqual(sim.retarget_count,0)
        self.assertTrue(all(sim.topo.links[k].current_rate_bps(sim.cfg.physics)==0 for k in sim._adv_links))

    def test_shared_no_attack_control_has_zero_cost_and_the_same_fixed_environment_trace(self):
        m=module()
        control=m.make_chain_simulator(2,'no_attack',0,3002,short_case())
        attacked=m.make_chain_simulator(2,'online_route_feedback',2,3002,short_case())
        a,b=control.run(),attacked.run()
        self.assertEqual(control.relative_cost_link_seconds,0)
        self.assertEqual(control.distinct_links_touched,set())
        self.assertEqual(control.attack_audit()['environment_trace_sha256'],
                         attacked.attack_audit()['environment_trace_sha256'])
        fixed_digest=attacked.attack_audit()['environment_trace_sha256']
        for _ in range(6):
            attacked._tick_outages()
        self.assertEqual(fixed_digest,attacked.attack_audit()['environment_trace_sha256'])
        self.assertEqual([(s.sid,s.arrival_t,s.cls) for s in sorted(a.sessions,key=lambda s:s.sid)],
                         [(s.sid,s.arrival_t,s.cls) for s in sorted(b.sessions,key=lambda s:s.sid)])

    def test_threshold_assessment_does_not_assert_a_universal_minimum(self):
        m=module()
        rows=[{'budget':1,'mean':0.2,'ci_low':0.1,'ci_high':0.3},
              {'budget':2,'mean':0.25,'ci_low':0.2,'ci_high':0.3}]
        crossing=m.threshold_assessment(rows,0.25)
        self.assertEqual(crossing['minimum_tested_budget_crossing_mean'],2)
        self.assertIsNone(crossing['minimum_tested_budget_with_lower_ci_crossing'])
        self.assertFalse(crossing['global_minimum_identified'])

    def test_six_seed_pairing_keeps_negative_excess_and_rejects_trace_mismatch(self):
        m=module()
        self.assertTrue(hasattr(m,'paired'))
        def records(value):
            return [{'seed':seed,'arrival_sha256':str(seed),
                     'attack':{'environment_trace_sha256':str(seed)},
                     'summary':{'all':{'forced_entitled_fraction':value}}} for seed in m.SEEDS]
        a,b=records(0.1),records(0.35)
        result=m.paired(a,b,'forced_entitled_fraction')
        self.assertAlmostEqual(result['mean'],-0.25)
        self.assertAlmostEqual(result['ci_low'],-0.25)
        b[0]['attack']['environment_trace_sha256']='different'
        with self.assertRaises(ValueError):
            m.paired(a,b,'forced_entitled_fraction')

    def test_incomplete_study_cannot_create_results_document(self):
        from pathlib import Path
        import tempfile
        m=module()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(FileNotFoundError):
                m.analyze_study(root,root/'results.md')
            self.assertFalse((root/'results.md').exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
