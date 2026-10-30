"""Reduced link secret-key-rate model and inventory of accepted key material.

The model distinguishes reduced generation, generation abort, and classical
transport outage. An abort rejects fresh key from the affected generation
process; it does not retroactively invalidate stored key. This model does not
simulate photonics or establish composable cryptographic security.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Optional

from .config import PhysicsConfig, ReservoirConfig


def h2(x: float) -> float:
    """Binary entropy in bits. H2(0) = H2(1) = 0."""
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


@lru_cache(maxsize=256)
def rate_fraction(e: float, cfg: PhysicsConfig) -> float:
    """Fraction of nominal secret-key rate delivered at QBER `e`.

    Shape: smooth monotone decline, then a HARD ZERO at the security-abort
    threshold. Derived from the asymptotic BB84 rate expression
    R ~ 1 - f*H2(e) - H2(e), which is the structure of
    Ma/Qi/Zhao/Lo PRA 72:012326 Eq. (1) with the decoy single-photon terms
    collapsed into the nominal rate.

    Normalised so rate_fraction(e0) == 1.0 exactly.

    >>> cfg = PhysicsConfig()
    >>> abs(rate_fraction(cfg.e0, cfg) - 1.0) < 1e-12
    True
    >>> rate_fraction(0.075, cfg) == 0.0   # at/above abort -> hard zero
    True
    """
    if e >= cfg.e_abort:
        return 0.0
    if e <= 0.0:
        e = 0.0
    num = 1.0 - cfg.f_ec * h2(e) - h2(e)
    den = 1.0 - cfg.f_ec * h2(cfg.e0) - h2(cfg.e0)
    if den <= 0.0:
        raise ValueError(
            f"nominal QBER e0={cfg.e0} with f={cfg.f_ec} yields no key; "
            "check PhysicsConfig"
        )
    frac = max(0.0, num) / den
    frac = min(1.0, frac)
    return frac ** cfg.gamma


class LinkState(str, Enum):
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    ABORT = "ABORT"      # QBER >= e_abort: security abort, rate 0
    OUTAGE = "OUTAGE"    # hard: cut / LOS loss / classical-channel denial


@dataclass
class Link:
    """One QKD link with its own key reservoir.

    A relayed multi-hop path is NOT a link -- ETSI GS QKD 015 types it VIRT
    (virtual key-association link) as opposed to PHYS. We keep that distinction.
    """

    name: str
    endpoints: tuple
    nominal_rate_bps: float
    link_class: str

    # adversary / environment state
    excess_qber: float = 0.0
    outage: bool = False

    def qber(self, cfg: PhysicsConfig) -> float:
        return cfg.e0 + self.excess_qber

    def state(self, cfg: PhysicsConfig) -> LinkState:
        if self.outage:
            return LinkState.OUTAGE
        e = self.qber(cfg)
        if e >= cfg.e_abort:
            return LinkState.ABORT
        if self.excess_qber > 0.0:
            return LinkState.DEGRADED
        return LinkState.NOMINAL

    def current_rate_bps(self, cfg: PhysicsConfig) -> float:
        """Secret key rate right now, bit/s."""
        st = self.state(cfg)
        if st in (LinkState.OUTAGE, LinkState.ABORT):
            return 0.0
        return self.nominal_rate_bps * rate_fraction(self.qber(cfg), cfg)


class BufferState(str, Enum):
    READY = "READY"
    CHARGING = "CHARGING"
    WARNING = "WARNING"
    EMPTY = "EMPTY"


class KeyStore:
    """Per-link key reservoir with QKDNetSim QKDBuffer semantics.

    State machine transcribed from QKDNetSim `QKDBuffer::CheckState()`:
        READY    when m_cur >= m_thr
        CHARGING when below threshold, above minimum, and rising
        WARNING  when below threshold, above minimum, and not rising
        EMPTY    when m_cur <= m_min

    Overflow behaviour transcribed from `QKDBuffer::AddNewContent()`: generated
    key that would exceed m_max is DISCARDED, not queued. We account it so the
    discarded volume can be reported.

    m_min doubles as the authentication reserve (SECOQC held a 2 MiB floor
    purely to guarantee future classical-channel authentication).
    """

    __slots__ = ("m_min", "m_thr", "m_max", "_cur", "_prev",
                 "discarded_bits", "generated_bits", "consumed_bits")

    def __init__(self, cfg: ReservoirConfig):
        self.m_min = cfg.m_min
        self.m_thr = cfg.m_thr
        self.m_max = cfg.m_max
        self._cur = float(cfg.m_max) * cfg.m_initial_frac
        self._prev = self._cur
        self.discarded_bits = 0.0
        self.generated_bits = 0.0
        self.consumed_bits = 0.0

    @property
    def level(self) -> float:
        return self._cur

    def state(self) -> BufferState:
        if self._cur <= self.m_min:
            return BufferState.EMPTY
        if self._cur >= self.m_thr:
            return BufferState.READY
        return BufferState.CHARGING if self._cur > self._prev else BufferState.WARNING

    def accumulate(self, bits: float) -> float:
        """Add generated key. Returns bits discarded to overflow."""
        if bits <= 0.0:
            self._prev = self._cur
            return 0.0
        self._prev = self._cur
        self.generated_bits += bits
        room = self.m_max - self._cur
        if bits > room:
            discarded = bits - room
            self._cur = float(self.m_max)
            self.discarded_bits += discarded
            return discarded
        self._cur += bits
        return 0.0

    def available(self, floor: Optional[float] = None) -> float:
        """Key drawable above `floor` (defaults to m_min, the auth reserve)."""
        f = self.m_min if floor is None else max(floor, self.m_min)
        return max(0.0, self._cur - f)

    def can_take(self, bits: float, floor: Optional[float] = None) -> bool:
        return self.available(floor) >= bits

    def take(self, bits: float, floor: Optional[float] = None) -> bool:
        """Debit `bits`. Refuses to breach the floor. Returns success.

        Invariant: never negative, never above m_max.
        """
        if bits <= 0.0:
            return True
        if not self.can_take(bits, floor):
            return False
        self._prev = self._cur
        self._cur -= bits
        self.consumed_bits += bits
        assert self._cur >= 0.0, "reservoir went negative"
        return True

    def __repr__(self) -> str:  # pragma: no cover
        return (f"KeyStore(level={self._cur:.0f}, state={self.state().value}, "
                f"min={self.m_min}, thr={self.m_thr}, max={self.m_max})")
