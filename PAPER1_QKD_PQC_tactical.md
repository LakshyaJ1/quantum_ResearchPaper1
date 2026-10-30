# PAPER 1 — DRAFT
## Key-Rate-Aware Routing and Hybrid Post-Quantum Fallback for Multi-Hop Tactical Quantum Key Distribution Networks

**Target:** IEEE WiCOMM-2026, Track 2 (Computing Technologies and Applications — Quantum Communications and Computing; Cyber Security and Cryptography)
**Status:** complete draft. All numbers are from `qkd_tactical_sim.py` (8 seeds × 4 h simulated time). Convert to the IEEE two-column template, insert the five figures from `out_idea1/`, verify every reference.

> **Author note (delete before submission):** everything in `[[double brackets]]` is an instruction to you, not paper text.

---

## Abstract

Quantum key distribution is moving from laboratory demonstration to fielded defence infrastructure, and the next step for national deployments is the multi-hop trusted-node network. In such a network the secret key is not a property of a link but a *depletable, time-varying resource* produced at a few hundred bits per second on optical hops and consumed on every hop of a relayed path. We argue that this makes key provisioning a network-control problem rather than a physical-layer problem, and we study it as such. We model a nine-node mountain relay formation carrying three classes of traffic — command, imagery/ISR and logistics — with per-link key reservoirs, degraded-channel dynamics and hard link outages, and we compare three control policies: shortest-path routing, key-rate-aware routing that minimises expected time-to-key, and a class-aware policy that adds per-class reservation together with a fallback to ML-KEM key establishment when quantum key cannot be supplied within a session deadline. Over 4-hour simulated missions, key-rate-aware routing raises the overall session service ratio from 82.8% to 86.7% and command-traffic service from 93.1% to 97.3%, at the cost of 14.4% higher total key consumption because it selects longer paths. The class-aware policy with post-quantum fallback attains 100% session availability with zero blocking, but only 85.1% of sessions are keyed with quantum-derived material; the remainder are served at a lower, explicitly labelled security grade. Under a sixteen-fold increase in link-disruption pressure, command-traffic service falls to 44.0% (shortest path) and 56.3% (key-rate-aware) while the hybrid policy holds availability at 100% with 33.6% of command sessions falling back. Finally, we derive a capacity requirement: at the ~240 bit/s per-hop secret-key rate reported for recent free-space demonstrations, only 42–46% of one-time-pad-grade ISR sessions can be quantum-keyed, and roughly 960 bit/s per hop is needed to exceed 90%. We release the simulator to support reproducible study of tactical quantum-network control.

**Index Terms** — quantum key distribution, trusted-node networks, tactical networks, key management, post-quantum cryptography, crypto-agility, military communications.

---

## I. Introduction

`[[Open with the operational scene — this is what makes a systems-lab reviewer keep reading.]]`

A brigade-level formation in mountainous terrain is connected to its rear area by a chain of relay sites. Command traffic must be re-keyed at short intervals; imagery products from forward observation posts are, for the highest-grade circuits, keyed at or near one-time-pad rates; logistics traffic is bulk and delay-tolerant. Recent progress has made it realistic to supply keys for such a formation from quantum key distribution (QKD) rather than from public-key cryptography alone: fibre QKD systems have completed military field trials, and entanglement-based free-space links have been demonstrated over kilometre distances at secure key rates of order 10² bit/s.

The step from a link to a *network*, however, changes the nature of the engineering problem. Beyond the reach of a single quantum channel, keys are relayed through trusted nodes: node *A* and node *B* share a key, node *B* and node *C* share another, and an end-to-end key is delivered by hop-by-hop re-encryption. The immediate consequence is that **an *n*-hop path consumes *n* times the key material of a single hop**. Combined with per-hop rates measured in hundreds of bits per second, this means that in a realistic tactical formation the binding constraint is not whether a quantum link exists, but whether the network can *allocate* its key production to the sessions that matter, at the time they matter.

This is a scheduling and routing problem, and it has received little attention. The QKD literature has concentrated on maximising the secret-key rate of individual links and on the security of trusted-relay architectures; the networking literature optimises throughput and latency for resources that are not consumed by transmission in this way. Key management for QKD networks has begun to be surveyed, and standards now define interfaces through which an external controller may obtain keys and configure a QKD network. What is missing is an evaluation of *control policies* for key-scarce, mobile, contested topologies — and an honest account of what happens when the key runs out.

**Contributions.**
1. We formulate key provisioning in a multi-hop tactical QKD network as a constrained control problem with a per-link key economy, and make the trusted-relay hop multiplier explicit in the cost model (§III).
2. We define and compare three control policies, including a **class-aware policy with hybrid post-quantum fallback** that converts key starvation into an explicit, labelled security-grade downgrade instead of a service outage (§III-C).
3. We quantify the resulting trade-offs by simulation, including the finding that key-rate-aware routing improves service but *increases* total key consumption, and that protecting command traffic measurably reduces the quantum-keyed fraction of ISR traffic (§V).
4. We derive a **per-hop key-rate requirement** for high-grade traffic classes, giving system designers a target rather than an aspiration (§V-D).
5. We release the simulator and all configurations.

---

## II. Background and Related Work

`[[Replace this prose with a comparison TABLE in the final version — see the note at the end of this section.]]`

**Trusted-node QKD networks.** Where distance exceeds the reach of a quantum channel, keys are extended through intermediate nodes that are trusted with the key material. This is the architecture of deployed metropolitan and intercity QKD networks and the declared direction of current national programmes. Its cost structure — key consumption proportional to path length — is well understood in principle but rarely treated as an object of network optimisation.

**Key management and standardisation.** Key management for QKD networks has recently been surveyed, and the integration of QKD with classical networks has been analysed from an evolutionary standpoint. ETSI has specified a REST interface by which applications obtain keys from a key management system, and a control interface for software-defined networks. These give us a realistic abstraction for a control plane, which we adopt: a controller with visibility of per-link key reservoirs and the authority to select paths and admit sessions.

**Simulation tooling.** Several discrete-event simulators exist for quantum networks, differing in the level of physical detail: NetSquid, SeQUeNCe, QuISP, and an ns-3 QKD module. Our study deliberately sits *above* the physical layer: we treat per-link secret-key rate as a parameterised input, because our object of study is the control policy, not the photonics. This choice is the reason a single-CPU experiment suffices, and it is also the paper's principal limitation (§VI).

**Post-quantum cryptography as the fallback layer.** NIST standardised ML-KEM (FIPS 203), ML-DSA (FIPS 204) and SLH-DSA (FIPS 205) in August 2024, and selected HQC as an additional code-based key-encapsulation mechanism in March 2025. Post-quantum key establishment is therefore an available, standardised alternative when quantum key is unavailable — with a different security assumption (computational rather than information-theoretic). Treating the two as a graded pair, rather than as competitors, is the design position we adopt.

`[[Final version: build a 5-row table with columns {Work | Object of study | Multi-hop? | Key-scarcity modelled? | Contested conditions? | PQC fallback?} and make your row the only one with all four ticks. This is the single most effective way to make your novelty legible in a 6-page paper.]]`

---

## III. System Model

### A. Topology and key economy

We model a nine-node formation: a rear-area node (BASE), two mountain relay nodes (REL1, REL2), two brigade nodes (BDE1, BDE2) and three forward posts (FWD1–FWD3), connected by nine links (Fig. 1). One link is a fibre backbone segment; the remainder are free-space optical hops of three grades. Per-link secret-key rates are parameters:

| Link class | Secret-key rate | Rationale |
|---|---|---|
| Fibre backbone | 5000 bit/s | rear-area trusted-node fibre segment |
| FSO (nominal) | 240 bit/s | anchored to reported entanglement-based free-space performance (~240 bit/s, QBER < 7%) |
| FSO (short) | 400 bit/s | shorter, better-aligned hop |
| FSO (lateral) | 150 bit/s | longer lateral hop |

Each link *e* holds a key reservoir *R<sub>e</sub>(t)* capped at 64 kbit. Keys accumulate at the link rate and are consumed by sessions. For a session of demand *D* bits routed over path *p*, the trusted-relay mechanism consumes *D* bits **on every link of *p***; total consumption is therefore *D·|p|*.

### B. Channel dynamics and disruption

Optical hops follow a two-state Gilbert–Elliott process: in the *good* state the link produces at full rate; in the *bad* state (turbulence, obscuration, or disruption of the classical channel that stalls post-processing) it produces at 5% of full rate. Mean sojourn times are 900 s and 180 s. Independently, links suffer hard outages — no key production and no traffic — with mean duration 120 s. A scalar **attack-pressure multiplier** scales the transition rate into the bad state and the outage onset rate, letting us sweep from benign to heavily contested conditions.

### C. Traffic classes and control policies

Sessions arrive as Poisson processes:

| Class | Arrival | Key demand | Deadline | Priority |
|---|---|---|---|---|
| C2 (command) | 0.05 s⁻¹ | 1024 bit | 5 s | 1 |
| ISR (imagery) | 0.02 s⁻¹ | 32768 bit | 30 s | 2 |
| LOG (logistics) | 0.03 s⁻¹ | 4096 bit | 120 s | 3 |

Demands reflect high-grade keying practice: short-interval re-keying for command circuits and one-time-pad-grade keying for imagery products, which is where trusted-node key becomes genuinely scarce.

We compare three policies:

- **SP (baseline).** Fixed minimum-hop path. A session waits until every link on the path holds sufficient key, and is *blocked* if its deadline expires.
- **KAR (key-rate-aware routing).** At request time the controller evaluates candidate simple paths and selects the one minimising the bottleneck expected time-to-key, (*D* − *R<sub>e</sub>*)⁺ / *r<sub>e</sub>*, with a small penalty per hop. Sessions still block on deadline expiry.
- **KAR+CAF (class-aware admission and fallback).** KAR routing plus per-class reservation floors — a session of class *c* may draw only from reservoir above a floor *φ<sub>c</sub>* (φ = 0, 0.20, 0.40 of capacity for C2, ISR, LOG) — plus **fallback to ML-KEM-768 key establishment** on deadline expiry, recorded as a distinct, lower security grade. The fallback costs 2272 B on the wire (encapsulation key 1184 B plus ciphertext 1088 B, verified against a reference FIPS 203 implementation) and 0.35 s of setup latency.

Sessions are served in strict priority order.

---

## IV. Experimental Setup

Discrete-event simulation at 1 s resolution; 4 h (14 400 s) per run; 8 random seeds for the main comparison and 3–4 seeds per point for the sweeps. Each run generates ≈1470 sessions (≈743 C2, ≈292 ISR, ≈433 LOG). Metrics: fraction of sessions served, split by whether they were served with quantum key or by post-quantum fallback; blocked fraction; mean and 95th-percentile time-to-key; mean hop count and total key consumed. The simulator is single-threaded Python; a full experiment set completes in under a minute on one CPU core. All parameters above are the complete set of assumptions; no other tuning was performed.

`[[Report your Python/numpy versions and the random seeds. Reviewers notice.]]`

---

## V. Results

### A. Policy comparison under nominal conditions (Table I, Figs. 2–3)

**TABLE I — Session outcome by policy and traffic class (mean of 8 seeds, 4 h runs)**

| Policy | Class | Served | Quantum-keyed | PQC fallback | Blocked | Mean TTK (s) | p95 TTK (s) |
|---|---|---|---|---|---|---|---|
| SP | C2 | 0.931 | 0.931 | — | 0.069 | 0.03 | 0.00 |
| SP | ISR | 0.394 | 0.394 | — | 0.606 | 2.72 | 20.30 |
| SP | LOG | 0.946 | 0.946 | — | 0.054 | 4.16 | 31.18 |
| KAR | C2 | 0.973 | 0.973 | — | 0.027 | 0.01 | 0.00 |
| KAR | ISR | 0.437 | 0.437 | — | 0.563 | 3.77 | 22.83 |
| KAR | LOG | 0.977 | 0.977 | — | 0.023 | 2.05 | 7.40 |
| KAR+CAF | C2 | **1.000** | 0.981 | 0.019 | 0.000 | 0.11 | 0.00 |
| KAR+CAF | ISR | **1.000** | 0.385 | 0.615 | 0.000 | 20.23 | 30.35 |
| KAR+CAF | LOG | 0.999 | 0.944 | 0.055 | 0.001 | 16.17 | 108.39 |

Pooled over all classes: SP serves 82.8% ± 1.4% of sessions, KAR 86.7% ± 1.7%, KAR+CAF 100.0% ± 0.1%.

Three observations, in order of importance.

**1) Key-awareness in the control plane buys real availability.** Simply choosing paths by expected time-to-key rather than hop count raises command-traffic service from 93.1% to 97.3% and pooled service by 3.9 percentage points, with no change to the physical layer. The mechanism is path diversity: when a link's reservoir is depleted, an alternative route with accumulated key exists more often than not.

**2) That gain is not free, and we should say so.** KAR consumes 20.29 Mbit of key per run against 17.74 Mbit for SP — **14.4% more** — because avoiding depleted links means accepting longer paths, and the trusted-relay multiplier converts every extra hop directly into extra key expenditure (mean path length rises from 2.85 to 2.88–3.15 hops). In a key-scarce network, path length is a security-budget decision, not merely a latency decision. `[[This is your most quotable sentence. Keep it.]]`

**3) The hybrid policy converts outage into a graded downgrade — and the downgrade is not evenly distributed.** KAR+CAF eliminates blocking entirely, but 61.5% of ISR sessions and 5.5% of LOG sessions are served by post-quantum fallback rather than quantum key, and the pooled quantum-keyed fraction is 85.1%. Note also that ISR's *quantum-keyed* fraction falls slightly under KAR+CAF (0.385) relative to KAR (0.437): the reservation floors that protect command traffic necessarily withhold key from lower-priority classes. This is a genuine Pareto trade, not a free improvement, and a designer must choose where on it to sit.

The latency picture (Fig. 3) is consistent: C2 time-to-key remains sub-second in all policies, while the deliberate queueing introduced by reservation raises ISR and LOG mean time-to-key substantially (to 20.2 s and 16.2 s) — sessions that would previously have been dropped are now waiting and then falling back.

### B. Behaviour under increasing disruption (Fig. 4)

**TABLE II — C2 service ratio versus attack-pressure multiplier**

| Attack pressure | ×1 | ×2 | ×4 | ×8 | ×16 |
|---|---|---|---|---|---|
| SP | 0.947 | 0.877 | 0.777 | 0.665 | 0.440 |
| KAR | 0.982 | 0.936 | 0.874 | 0.774 | 0.563 |
| KAR+CAF | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

Under sixteen-fold disruption pressure, command-traffic availability collapses to 44.0% with shortest-path routing and 56.3% with key-rate-aware routing. The hybrid policy holds availability at 100% throughout — but the *composition* of that availability degrades in a measurable, monotone way: the C2 fallback fraction rises from 1.5% to 33.6%, ISR from 58.2% to 95.9%, and LOG from 3.5% to 55.1%. This is precisely the behaviour a commander should be given visibility of: the network does not fail, it silently changes the security grade of its traffic unless that change is surfaced. We regard the *reportability* of this degradation as a design requirement, not a diagnostic afterthought.

### C. Sensitivity to per-hop secret-key rate (Fig. 5)

**TABLE III — Service fraction versus free-space per-hop key rate**

| Per-hop rate (bit/s) | 60 | 120 | 240 | 480 | 960 |
|---|---|---|---|---|---|
| C2 served, SP | 0.820 | 0.916 | 0.943 | 0.955 | 0.955 |
| C2 served, KAR | 0.906 | 0.962 | 0.973 | 0.978 | 0.977 |
| ISR quantum-keyed, SP | 0.007 | 0.135 | 0.415 | 0.671 | 0.808 |
| ISR quantum-keyed, KAR | 0.003 | 0.150 | 0.460 | 0.780 | 0.908 |

### D. A derived capacity requirement

Table III supports a concrete engineering statement, which we consider the most directly useful output of this work:

> At the ~240 bit/s per-hop secret-key rate reported for recent free-space demonstrations, a formation of this size and traffic profile can quantum-key only **42–46%** of one-time-pad-grade ISR sessions, while command traffic is already well served (94–97%). Reaching **>90%** quantum-keyed ISR service requires approximately **960 bit/s per hop** — a factor of four — or an equivalent reduction in per-session key demand.

Two design levers therefore exist, and they are interchangeable in this model: raise per-hop key rate, or reduce high-grade key demand (for example by re-keying a symmetric cipher at longer intervals instead of approaching one-time-pad operation). Which lever is cheaper is a programme decision; our contribution is to quantify the exchange rate. Note also the diminishing return above 480 bit/s for command traffic, which is limited by disruption rather than by key supply.

---

## VI. Discussion and Limitations

`[[Do not cut this section. Volunteering limitations raises acceptance probability at a systems-lab venue.]]`

**What we have shown.** In a key-scarce multi-hop QKD network, control-plane decisions materially determine which traffic gets keyed; a key-aware controller improves availability without touching the physical layer; and a post-quantum fallback converts residual starvation into a quantified, deliberate security-grade downgrade. The trusted-relay hop multiplier makes path length a security-budget quantity.

**Limitations, stated plainly.**
1. **Above-the-physics abstraction.** Per-link secret-key rates are parameters, not simulated photonics. Finite-key effects, basis reconciliation, privacy amplification and detector behaviour are absorbed into a single rate. Our results are therefore conditional on those rates; §V-C is included precisely so that a reader can locate their own system on the curve.
2. **Parameter provenance.** Key rates are anchored to publicly reported figures and to plausible fibre performance; traffic demands and deadlines are our own construction, informed by high-grade keying practice rather than by measured operational traces. They are assumptions, and they are all listed in §III.
3. **Trust model.** We assume relay nodes are trusted and uncompromised. Node compromise, which changes the security analysis fundamentally, is modelled only as an availability event (outage), not as a confidentiality breach.
4. **Fallback security semantics.** We treat post-quantum fallback as a distinct, lower grade, but we do not formalise a policy language for which traffic may be downgraded under which conditions. That is necessary future work and, we suspect, the harder problem.
5. **Single formation, single traffic profile.** Generalisation across topologies and mission profiles is untested.

**Future work.** Hardware-in-the-loop coupling to a real QKD key management system through the ETSI interfaces; learned (reinforcement-learning) admission control benchmarked against the heuristics here; a formal downgrade policy with commander-visible reporting; and extension to mobile relay nodes where the topology itself is time-varying.

---

## VII. Conclusion

Multi-hop QKD turns secret key into a routed, depletable resource, and once that is true, the control plane — not the quantum channel — decides which sessions are protected. Making the controller key-aware raised command-traffic service from 93.1% to 97.3% in our simulated formation, at a 14.4% increase in key expenditure; adding class-aware reservation and a standardised post-quantum fallback achieved uninterrupted availability while keeping 85.1% of sessions on quantum-derived key, and degraded gracefully and measurably under sixteen-fold disruption pressure. We also derived the per-hop key rate required for high-grade traffic — roughly four times current free-space demonstration performance. As national quantum-network programmes move toward multi-hop deployment, we suggest that key-economy-aware control, and explicit reporting of security-grade downgrades, belong in the architecture from the outset rather than being retrofitted.

---

## Figures (in `out_idea1/`)

| File | Caption to use |
|---|---|
| `fig1_topology.png` | Fig. 1. Simulated tactical trusted-node QKD formation. Link labels give per-link secret-key rate in bit/s; line style indicates link class. |
| `fig2_service_by_class.png` | Fig. 2. Session service ratio by traffic class under the three control policies. Error bars: standard deviation over 8 seeds. |
| `fig3_c2_ttk_cdf.png` | Fig. 3. Distribution of key-establishment latency for command (C2) sessions. |
| `fig4_attack_pressure.png` | Fig. 4. Degradation under increasing disruption. Left: C2 service ratio. Right: post-quantum fallback fraction by class under KAR+CAF. |
| `fig5_rate_sensitivity.png` | Fig. 5. Sensitivity of C2 service ratio to per-hop secret-key rate; dotted line marks the rate reported for recent free-space demonstrations. |

---

## References — **VERIFY EVERY ONE BEFORE SUBMITTING**

`[[These are leads I believe to be correct. Open each, confirm authors/venue/year/volume/pages, and confirm it supports the claim you attach to it. Delete anything you cannot verify. Aim for 20–25 references; add 3–5 recent Indian-context citations, which reviewers at this venue appreciate.]]`

1. NIST, *FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard*, Aug. 2024.
2. NIST, *FIPS 204: Module-Lattice-Based Digital Signature Standard*, Aug. 2024.
3. NIST, *FIPS 205: Stateless Hash-Based Digital Signature Standard*, Aug. 2024.
4. NIST announcement on the selection of HQC as an additional post-quantum KEM, Mar. 2025.
5. E. Dervisevic *et al.*, "Quantum key distribution networks key management: A survey," *ACM Computing Surveys*, 2025.
6. J. Li *et al.*, "Integration of quantum key distribution networks and classical networks: An evolution perspective," *IEEE Network*, vol. 39, pp. 180–187, 2025.
7. ETSI GS QKD 014, *Quantum Key Distribution (QKD); Protocol and data format of REST-based key delivery API*.
8. ETSI GS QKD 015, *Quantum Key Distribution (QKD); Control interface for software defined networks*.
9. T. Coopmans *et al.*, "NetSquid, a NETwork Simulator for QUantum Information using Discrete events," *Communications Physics*, vol. 4, 2021.
10. X. Wu *et al.*, "SeQUeNCe: a customizable discrete-event simulator of quantum networks," *Quantum Science and Technology*, vol. 6, no. 4, 045027, 2021.
11. R. Satoh *et al.*, "QuISP: a quantum internet simulation package," *IEEE QCE*, 2022.
12. M. Mehic *et al.*, QKDNetSim: QKD network simulation module for ns-3. `[[verify exact title/venue/year]]`
13. Security-of-trusted-repeater-QKD-networks reference. `[[e.g. Salvail et al., J. Computer Security, 2010 — verify]]`
14. DRDO press release on completion of military field trials of an indigenous fibre-based QKD system, 2026. `[[cite the official release, not a news aggregator]]`
15. Ministry of Defence / DRDO–IIT Delhi release on free-space entanglement-based quantum secure communication (~240 bit/s, QBER < 7%), Jun. 2025.
16–25. `[[Add: one-time-pad/key-consumption analysis for trusted relays; a tactical/DDIL networking reference; a hybrid QKD+PQC key-delivery paper; two or three Indian conference/journal works on QKD or secure tactical communications; a reference for Gilbert–Elliott channel modelling.]]`

---

## Reproducibility statement

`[[Include this verbatim; it costs six lines and buys real credibility.]]`

The simulator, all parameters and the scripts that generate every figure and table are available at `[[your GitHub URL]]`. Results in Tables I–III were produced with 8 random seeds (main comparison) and 3–4 seeds per sweep point, 14 400 s simulated per run, on a single CPU core; the complete experiment set runs in under one minute. ML-KEM-768 artefact sizes were verified against a reference FIPS 203 implementation (encapsulation key 1184 B, ciphertext 1088 B, shared secret 32 B).
