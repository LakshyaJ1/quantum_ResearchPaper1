"""Contested multi-hop QKD key-supply simulator.

Companion artifact for "Fail-Closed or Fail-Degraded? Quantifying Forced
Security-Grade Loss in Contested Multi-Hop QKD Networks".

Historical results were produced by version 0.1.0 at commit 0d1e2fa. Revised
semantics and measurement windows are documented in docs/revision/.
"""
__version__ = "0.2.0"

from .config import (GRADE_ORDER, G1_OTP, G2_QKD_SYM, G3_HYBRID, G4_PQC,
                     SimConfig, TRAFFIC_CLASSES, grade_rank, is_at_least,
                     quantum_key_demand)
from .network import chain_topology, formation_8node, formation_9node
from .physics import BufferState, KeyStore, Link, LinkState, h2, rate_fraction
from .sim import Outcome, Results, Session, Simulator, run_once

__all__ = [
    "GRADE_ORDER", "G1_OTP", "G2_QKD_SYM", "G3_HYBRID", "G4_PQC",
    "SimConfig", "TRAFFIC_CLASSES", "grade_rank", "is_at_least",
    "quantum_key_demand", "chain_topology", "formation_8node", "formation_9node",
    "BufferState", "KeyStore", "Link", "LinkState", "h2", "rate_fraction",
    "Outcome", "Results", "Session", "Simulator", "run_once",
]
