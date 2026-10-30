import math

from qkdsim.config import G1_OTP, G2_QKD_SYM, G4_PQC
from qkdsim.sim import Results, Session, Outcome
from revision.metrics import summarize, paired_interval


def test_arrival_and_payload_denominators_remain_explicit():
    r = Results(cfg_summary={})
    for sid, payload, outcome, grade in [(0, 100, Outcome.SERVED, G1_OTP),
                                        (1, 900, Outcome.SERVED, G4_PQC),
                                        (2, 1000, Outcome.BLOCKED, None)]:
        s = Session(sid, 'ISR', 1, payload, 'a', 'b', G1_OTP, 10, 2)
        s.outcome, s.grade = outcome, grade
        s.served_t = 2 if outcome == Outcome.SERVED else None
        s.floor_violation = outcome == Outcome.SERVED and grade == G4_PQC
        r.sessions.append(s)
    out = summarize(r)
    assert out['availability'] == 2 / 3
    assert out['qualified_availability'] == 1 / 3
    assert out['degraded_arrival_fraction'] == 1 / 3
    assert out['blocked_arrival_fraction'] == 1 / 3
    assert out['forced_entitled_fraction'] == 1 / 3
    assert out['forced_payload_fraction'] == 900 / 2000
    assert out['conditional_forced_fraction'] == 1 / 2


def test_paired_interval_differences_use_matching_seed_pairs():
    result = paired_interval([1., 4., 9.], [0., 3., 8.], resamples=100)
    assert result == (1., 1., 1.)
    try:
        paired_interval([1., 4.], [0.], resamples=100)
    except ValueError:
        pass
    else:
        assert False, 'Unmatched comparison must fail'
