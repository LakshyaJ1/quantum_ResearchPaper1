"""Parameters for the contested multi-hop QKD key-supply simulator.

"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Tuple
import json


G1_OTP = "G1"        # information-theoretic payload; key bits == payload bits
G2_QKD_SYM = "G2"    # ITS-delivered 256-bit symmetric key, computational payload
G3_HYBRID = "G3"     # QKD (partial) (+) ML-KEM-768 via approved combiner
G4_PQC = "G4"        # ML-KEM-768 only; computational

GRADE_ORDER: Tuple[str, ...] = (G1_OTP, G2_QKD_SYM, G3_HYBRID, G4_PQC)
"""Operator assurance ordering, not a universal cryptographic security order.
Index in this tuple is the contractual rank: lower == stronger in this model.
G1 and G2 differ in payload protection; hybrid guarantees depend on the combiner.
"""


def grade_rank(grade: str) -> int:
    return GRADE_ORDER.index(grade)


def is_at_least(grade: str, floor: str) -> bool:
    """True if `grade` is at least as strong as `floor`."""
    return grade_rank(grade) <= grade_rank(floor)


# ML-KEM-768 wire artefacts, FIPS 203. Encapsulation key 1184 B + ciphertext
# 1088 B = 2272 B on the wire; shared secret 32 B.
MLKEM768_EK_BYTES = 1184
MLKEM768_CT_BYTES = 1088
MLKEM768_SS_BYTES = 32
MLKEM768_WIRE_BYTES = MLKEM768_EK_BYTES + MLKEM768_CT_BYTES  # 2272


@dataclass(frozen=True)
class PhysicsConfig:
    """Link secret-key-rate model. Dossier section 2.1."""

    e0: float = 0.03
    """Nominal QBER. Tokyo QKD Network measured 2.7% (NEC 45 km) and ~3.8%
    (Toshiba 1 GHz, afterpulse-dominated). Sasaki et al., Opt. Express 19(11)."""

    f_ec: float = 1.16
    """Error-correction inefficiency f in the BB84 rate expression. Ma, Qi,
    Zhao, Lo, PRA 72:012326, Eq. (1); f=1 is the Shannon limit."""

    e_abort: float = 0.075
    """Engineering security-abort threshold. Tokyo's deployed NEC key-
    distillation engine has LDPC coding rates ONLY for QBER <3.5/5.5/7.5% --
    there is no rung above 7.5%. Sensitivity value 0.11 = asymptotic one-way
    BB84 threshold (Rath arXiv:2603.27278; Shor-Preskill PRL 85:441)."""

    gamma: float = 1.0
    """Degradation sharpness exponent.
    gamma=1.0 : reduced asymptotic BB84 shape. Gives rho(0.06)~0.50;
                the entropy expression reaches zero near 0.098 for f=1.16,
                below the f=1 Shannon-limit threshold near 0.110.
    gamma=3.4 : calibrated to the ONLY measured degraded-link datapoint --
                Tokyo All-Vienna BBM92 at QBER 5-7% delivered 0.25 kbps vs
                2-3 kbps nominal, i.e. 8-12% of nominal. 0.50^3.4 ~ 0.098.
    BOTH are reported. The 50%-vs-10% gap at QBER 6% is a real uncertainty
    (finite-key effects, system specifics) and is published as a sensitivity
    row rather than hidden inside a point assumption."""


@dataclass(frozen=True)
class AccountingConfig:
    """Per-hop key debit. Dossier section 2.3, 2.8."""

    metadata_bits: int = 240
    """30 bytes. ITU-T Y.3803 Note 2: key relay is performed in units of a
    *key file* (metadata + key data); metadata is "typically a few 10s of
    bytes" and is normally OTP-encrypted too."""

    tag_bits: int = 127
    """Wegman-Carter/Toeplitz authentication tag. Walenta et al.
    arXiv:1309.2583 used a 127-bit tag per 2^20 bits of classical traffic
    (eps_AUT ~ 1e-33). Cost is k bits per authenticated message and only
    LOGARITHMIC in message length: eps_au = n*2^(-k+1), Fung/Ma/Chau
    arXiv:0910.0312 Eq. (9)."""

    n_auth: int = 2
    """Optimistic modelling assumption of two tags per relay transaction.
    Retained for historical API compatibility; this is not an independently
    validated count. Revised experiments explicitly sweep 2, 7 and 40.
    """

    auth_on: bool = True
    """False reproduces the literature's bare D*n cost law. This ablation is a
    headline experiment (E5), not a footnote: SECOQC measured ~91% of a live
    AES-VPN's key consumption as ITS authentication rather than cipher key
    (728 B per 20 s round; only 2x256 bit are cipher key). Peev et al.,
    New J. Phys. 11:075001, section 5.1.1, footnote 27."""

    def cost_per_hop(self, demand_bits: int) -> int:
        """Link key consumed on ONE hop to relay `demand_bits` of key.

        Invariant: charged on EVERY hop of the path (total h * this), once per
        link per relay -- not once end-to-end, and not once per endpoint.
        SECOQC arXiv:quant-ph/0610202; ITU-T Y.3803 cl. 8.2.3 (XOR with the
        neighbouring pair's key "in an OTP manner", Req_KM 6 of Y.3801);
        Salvail et al., J. Computer Security 19:61-106, arXiv:0904.4072.
        """
        if demand_bits <= 0:
            return 0
        if not self.auth_on:
            return demand_bits
        return demand_bits + self.metadata_bits + self.n_auth * self.tag_bits

    def overhead_factor(self, demand_bits: int) -> float:
        """Ratio of true cost to the naive D. At D=256 this is 2.93x; Cambridge
        measured 3.6x (1440 bit of link key per ~400-bit relayed global key,
        Dynes et al. npj Quantum Inf. 5:101). Same order -- both reported."""
        if demand_bits <= 0:
            return 1.0
        return self.cost_per_hop(demand_bits) / demand_bits


@dataclass(frozen=True)
class ReservoirConfig:
    """Key reservoir. QKDNetSim QKDBuffer semantics, adopted verbatim for
    citability. UNITS ARE BITS (qkd-buffer.h documents FetchKeyOfSize as
    "keySize in bits!").
    The 64 kbit of the original paper draft is ~3 orders of magnitude below
    every published link-level reservoir and has been dropped.
    """

    m_min: int = 1_048_576          # 1 Mibit
    m_thr: int = 11_324_620         # ~10.8 Mibit
    m_max: int = 52_428_800         # 50 Mibit
    m_initial_frac: float = 1.0

    # m_min doubles as the AUTHENTICATION RESERVE. SECOQC held a 2 MiB floor
    # "to ensure that ... enough key remains in the store to authenticate the
    # future communication on the classical channel" (Peev et al. 2009).
    # This is a published, NON-QoS floor rationale -- a different argument from
    # Mehic et al.'s per-class QoS floor (IEEE/ACM ToN 28, 2020), and one no

    # SWEEP: capacity over 1 Mbit - 1 Gbit (QKDNetSim's own code-default
    # range), reported against the dimensionless C/(R*T) so conclusions are
    # scale-free. No vendor publishes a key-storage capacity: across ~15
    # datasheets (IDQ, Toshiba, QuantumCTek, Quantum Xchange, LuxQuanta,
    # ThinkQuantum, QTI, KEEQuant, Qubitekk) it appears only as an
    # unquantified feature word. Zero exceptions. Corroborated by the KMS
    # survey arXiv:2408.04580.


@dataclass(frozen=True)
class TrafficClass:
    name: str
    arrival_rate: float
    payload_bits: int
    authorised_floor: str
    """Lowest grade policy permits for this class. FAIL_CLOSED blocks below it;
    FAIL_DEGRADED serves below it and records an auditable floor violation."""
    deadline_s: float
    priority: int  # 1 = highest


# Demands are grounded in measured deployments. The original draft's 32768-bit
# "OTP-grade imagery" was incoherent -- 4 kB is not an imagery product, and
# true OTP requires key bits == payload bits.
TRAFFIC_CLASSES: Tuple[TrafficClass, ...] = (
    TrafficClass(
        name="C2",
        arrival_rate=0.05,
        payload_bits=2_048,
        authorised_floor=G2_QKD_SYM,
        deadline_s=5.0,
        priority=1,
    ),
    # 256-bit AES rekey per 60 s is the modal industry consumption unit
    # (SwissQuantum arXiv:1203.4940; IDQ Geneva 60 keys/h; ADVA 400G channel).
    TrafficClass(
        name="ISR",
        arrival_rate=0.02,
        payload_bits=144_000,
        authorised_floor=G1_OTP,
        deadline_s=30.0,
        priority=2,
    ),
    # Hefei 46-node QMAN ran real OTP voice at 2.4 kbps for 31 months;
    # 2400 bit/s * 60 s session = 144 kbit. arXiv:2109.04736.
    TrafficClass(
        name="LOG",
        arrival_rate=0.03,
        payload_bits=320_000,
        authorised_floor=G3_HYBRID,
        deadline_s=120.0,
        priority=3,
    ),
    # Hefei measured OTP file transfer at 320 kbps.
)


def quantum_key_demand(grade: str, payload_bits: int) -> int:
    """Quantum key bits an end-to-end session needs at a given grade.

    G1: key bits == payload bits (Shannon 1949, "Communication Theory of
        Secrecy Systems", BSTJ 28(4):656-715, section 10 "Perfect Secrecy",
        pp. 679-682; rate inequality R_M*L_M <= R_K*L_K on p. 682, and "a bit
        of key completely conceals a bit of message information ... this is the
        best that can be done").
        Nuance: Shannon's bound is on message ENTROPY, reduced by redundancy
        removal. Charging one key bit per payload bit is the WORST case,
        exactly correct only for incompressible or already-encrypted payloads.
    G2: one 256-bit symmetric key, ITS-delivered.
    G3: 128 bit of quantum key combined with an ML-KEM-768 shared secret via an
        approved, domain-separated combiner (NIST SP 800-227 section 4.6 --
        a bare XOR or naive concatenation invites an objection).
    G4: no quantum key at all.
    """
    if grade == G1_OTP:
        return payload_bits
    if grade == G2_QKD_SYM:
        return 256
    if grade == G3_HYBRID:
        return 128
    if grade == G4_PQC:
        return 0
    raise ValueError(f"unknown grade {grade!r}")


def pqc_wire_bytes(grade: str) -> int:
    """ML-KEM-768 bytes on the wire for grades that use it."""
    return MLKEM768_WIRE_BYTES if grade in (G3_HYBRID, G4_PQC) else 0


@dataclass(frozen=True)
class LinkClass:
    name: str
    rate_bps: float
    provenance: str


LINK_CLASSES: Dict[str, LinkClass] = {
    "FIBRE": LinkClass(
        "FIBRE", 300_000.0,
        "Toshiba LD/MU datasheet: 300 kb/s secure key rate at 10 dB channel "
        "loss, 30 dB budget. NOTE the LE product page is self-inconsistent "
        "(300 kb/s + 30 dB in the spec table vs 150 kb/s + 24 dB in prose).",
    ),
    "FSO_NOMINAL": LinkClass(
        "FSO_NOMINAL", 240.0,
        "DRDO-IIT Delhi free-space entanglement demonstration, >1 km, ~240 "
        "bit/s secure key rate at QBER <7%, June 2025. SECONDARY SOURCE -- "
        "retrieve PIB PRID 2136702 and confirm the wavelength before citing.",
    ),
    "FSO_SHORT": LinkClass(
        "FSO_SHORT", 400.0,
        "IDQ SARG04 short commercial link measured 300-420 bps at 13 km in the "
        "Tokyo QKD Network (400-420 bps after adding a crosstalk filter).",
    ),
    "FSO_LATERAL": LinkClass(
        "FSO_LATERAL", 200.0,
        "Rossi et al. arXiv:2602.16680: 200 bit/s over 18 km free space at "
        "telecom wavelength with adaptive optics, 40 cm-class telescope.",
    ),
}


@dataclass(frozen=True)
class OutageConfig:
    """Hard outage process. R = 0 regardless of QBER.

    Covers fibre cut / LOS loss / terrain masking (Alleaume et al.
    quant-ph/0701168) AND denial of the classical post-processing channel
    (Mehic et al. arXiv:1810.03857: blocking routing or post-processing
    packets "would disable the link"). The latter leaves the quantum channel
    pristine, so it is invisible to any QBER-driven model -- which is exactly
    why it is a separate state here.
    """

    mean_uptime_s: float = 3600.0     # SWEEP: no published FSO hard-outage
    mean_outage_s: float = 120.0      # frequency or duration distribution was
    #                                   found. Both must be swept, not asserted.

    grace_s: float = 60.0
    """Spooren et al. arXiv:2604.05599 measured 60 s grace per component before
    failure, with disruption propagating over 240-720 s."""


@dataclass(frozen=True)
class AdversaryConfig:
    """The adversary cannot break QKD, so it attacks AVAILABILITY to force a
    grade downgrade -- the incentive Schartner & Rass identified in 2010
    (IEEE doc 5685533) and which nobody has since measured.

    Pressure is expressed in ABSOLUTE QBER units so that it is physically
    interpretable and can be checked against a measured error rate. A
    dimensionless "attack pressure multiplier" cannot.
    """

    budget_links: int = 0
    """k: number of links the adversary suppresses. Primary cost axis."""

    targeting: str = "betweenness"
    """How the adversary spends its budget.

    "betweenness" -- greedy by edge betweenness centrality. Plausible for an
        adversary with topology knowledge but no path-aware planning. MEASURED
        CONSEQUENCE: on a relay chain of depth d with one alternate path, this
        adversary exhausts the (already severed) primary path before touching
        the alternate, so it needs d+1 links to sever quantum supply entirely.

    "mincut" -- concatenate minimum source-to-terminal cuts, cheapest first.
        This is exact for disconnecting the one-terminal two-path chain, whose
        cut size is two. It is not an optimal traffic-weighted interdiction
        algorithm for an arbitrary multi-terminal formation.
    """

    delta_e: float = 0.05
    """Excess QBER injected on each attacked link. With e0=0.03, delta_e=0.045
    reaches e_abort=0.075."""

    deny_classical: bool = False
    """If True the adversary denies the classical channel instead of raising
    QBER: rate -> 0 with the quantum channel pristine."""


@dataclass(frozen=True)
class SimConfig:
    horizon_s: float = 86_400.0   # 24 h
    """Arrival horizon. Defaults reproduce the historical 24-hour study setup.
    A fixed horizon does not certify steady state: depletion time depends on
    policy, workload, initial inventory, topology and disturbance history.
    Pending requests are allowed to reach service or their own deadline after
    new arrivals stop at this horizon.
    """

    warmup_s: float = 43_200.0    # 12 h
    """Sessions arriving before this are excluded from all metrics. The
    transient is not discarded silently -- it is reported as a finding in its
    own right: a formation that deploys with topped-up reservoirs can run for
    hours before the free-space key economy binds at all. This is the same
    drain-from-full dynamic SECOQC measured in Fig. 22 of Peev et al. (2009)."""

    tick_s: float = 1.0
    seed: int = 0

    physics: PhysicsConfig = field(default_factory=PhysicsConfig)
    accounting: AccountingConfig = field(default_factory=AccountingConfig)
    reservoir: ReservoirConfig = field(default_factory=ReservoirConfig)
    outage: OutageConfig = field(default_factory=OutageConfig)
    adversary: AdversaryConfig = field(default_factory=AdversaryConfig)

    routing: str = "KAR"          # SP | KAR
    reservation_floors: bool = False
    fail_mode: str = "FAIL_DEGRADED"   # FAIL_CLOSED | FAIL_DEGRADED

    pqc_setup_s: float = 0.35

    hop_penalty: float = 0.5
    """KAR tie-breaker. Every extra hop costs key on EVERY link, so path length
    is a key-budget decision, not merely a latency one."""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)
