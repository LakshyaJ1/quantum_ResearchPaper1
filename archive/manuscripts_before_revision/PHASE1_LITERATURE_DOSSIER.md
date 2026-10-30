# PHASE 1 — Literature Dossier & Novelty Adjudication
## Key-Rate-Aware Routing and Hybrid QKD/PQC Fallback for Multi-Hop Tactical Quantum Networks

**Date:** 3 August 2026
**Method:** five parallel adversarial prior-art agents, each instructed to kill rather than confirm the claims. ~250 tool-invocations, ~980k subagent tokens.
**Verification legend used throughout:** `[V]` full text read · `[P]` partially verified (abstract/publisher page) · `[C]` citation lifted verbatim from a fetched reference list, paper itself unread · `[S]` search snippet only — **do not cite without retrieval**

---

## 0. Adjudication summary — the original claim set

| # | Claim as drafted | Status | Killed by |
|---|---|---|---|
| C1 | "We formulate a key-economy model for multi-hop tactical QKD and make the trusted-relay hop multiplier explicit" | **DEAD** | van Duijn ONDM 2024; Mehic ToN 2020; Hao 2025; Cao KoD 2017 |
| C2a | Shortest-path vs key-rate-aware routing comparison | **DEAD** | van Duijn 2024; Johann JOCN 2024 (5 algorithms); Hao 2025; Yang 2018 |
| C2b | Class-aware admission with per-class reservation floors | **DEAD** | Mehic ToN 2020 (`M_min` floor + 3 DSCP classes); Cheng/Sun/Ji 2011 (QKRA) |
| C3a | Three named security grades incl. a true-hybrid middle tier | **DEAD** | Sanz et al. QuLore 2025 (L1–L4, KDF-combined L3, same ETSI+FIPS anchoring) |
| C3b | "Key starvation becomes a labelled downgrade, not an outage" | **DEAD** | Schartner & Rass **2010**; Makris ECOC 2024 (field); James ARES 2023; **ITU-T Y.3803 Req_KM 7** |
| C3c | Fraction of traffic served per security grade, as a metric | **DEAD** | Zhu arXiv:2510.15248 (ρ_k,t, fallback occupancy, SLA framing) |
| C4 | "The tactical/contested setting is unstudied" | **FALSE** | NATO RTG IST-218; MuQuaNet; NATO STO drone-FSO-QKD routing; EDF-2026-RA-CYBER-QSTN; Hafeez *Sci. Rep.* 2026 |
| C5 | Derived per-hop key-rate requirement | **WEAK** | Rate and demand are linearly interchangeable in the model → restates an assumption |
| AI | RL for key-aware QKD routing | **SATURATED** | Johann *Photonics* 2026 (GAT-DRL); Hao 2025; Xie 2025; Sharma 2023; Seok 2025; Zuo 2020 |

**Nothing in the original contribution list survives as stated.** The idea is salvageable, but only by moving the research question. See §4.

---

## 1. Must-cite prior art

### 1.1 The routing/key-allocation core (kills C1, C2)

1. **van Duijn, T.; Verschoor, S.; Rommel, S.; Tafur Monroy, I.** "Routing Strategies for Quantum Key Distribution Networks based on Trusted Relay Nodes." *ONDM 2024*, IFIP. https://dl.ifip.org/db/conf/ondm2024/ondm2024/1570993422.pdf `[V]`
   Containernet + ETSI 014 emulation. Compares SPF, SPF+, ADA-KGR, ADA-KEYS, OSKAR, CUSTOM. States our C1 verbatim: OTP + ITS MAC require consumption of **two link keys per hop** per relay message. Per-link KMS buffers, max M=1000 keys. Headline **+13.4 pp** for resource-aware over SPF.
   **⚠ THE NULL RESULT:** differences *among* resource-aware strategies are **statistically insignificant** (Welch's t-test); recommends cheap SPF+. A reviewer will ask why our policies should separate at all.

2. **Mehic, M.; Fazio, P.; Rass, S.; Maurhart, O.; Peev, M.; Poppe, A.; Rozhon, J.; Niemiec, M.; Voznak, M.** "A Novel Approach to Quality of Service Provisioning in Trusted Relay Quantum Key Distribution Networks." *IEEE/ACM Trans. Networking* 28, 2020. DOI 10.1109/TNET.2019.2956079; arXiv:1810.03857 `[V]`
   **The single most dangerous citation for C2b.** Three DSCP traffic classes (best-effort / real-time / premium); per-node admission controller; per-link key storage as token bucket with `M_max, M_cur, M_min, M_thr`; **hard per-class floor** — only premium may draw when `M_cur ≤ M_min`. Also the canonical citation for classical-post-processing-channel jamming.
   *Volume discrepancy between arXiv (28(1), Feb 2020) and secondary cites (28(2):168–181, Apr 2020) — resolve before citing.*

3. **Cheng, X.; Sun, Y.; Ji, Y.** "A QoS-supported scheme for quantum key distribution." *AIAI 2011*, IET, pp. 220–224. `[C]`
   Three service classes (key-guaranteed / key-prioritized / key-best-effort). **Quantum Key Reservation Approach (QKRA) reserves key on intermediate relay nodes** for the guaranteed class. Our third policy, from 2011. **Retrieve this — if it reports class-level blocking, C2b is unrecoverable.**

4. **Johann, T.; Wenning, M.; Giemsa, D.; Dochhan, A.; Gunkel, M.; Fehenberger, T.; Pachnicke, S.** "Comparison and optimization of different routing methods for meshed QKD networks using trusted nodes." *J. Opt. Commun. Netw.* 16(3):382–391, 2024. `[S]` — **direct C2a competitor, retrieve.**

5. **Hao, Y.; Xie, Y.; Gao, W.; Tang, J.** "Q-Learning for Resource-Aware and Adaptive Routing in Trusted-Relay QKD Network." *Photonics* 12(10):969, 2025. DOI 10.3390/photonics12100969 `[V-abs]`
   Per-link key-pool state model; baselines SPF and max-residual-key. ~100 s vs 170–590 s distribution time; 61 vs 32–55 keys/s.
   *Do not cite the "45.8 vs 118.5" figure seen in a snippet — inconsistent with the abstract's units.*

6. **Yang, C.; Zhang, H.; Su, J.** "QKD network: Optimal secret-key-aware routing method for trust relaying." *China Communications* 15(2):33–45, 2018. DOI 10.1109/CC.2018.8300270 `[C]` — "OSKAR"; residual-local-key forecast + depletion index.

7. **Cao, Y.; Zhao, Y.; Colman-Meixner, C.; Yu, X.; Zhang, J.** "Key on demand (KoD) for software-defined optical networks secured by QKD." *Optics Express* 25(22):26453, 2017. `[C]` — founding key-pool + RWKA work; MAX/MIN/WARN pool thresholds.

8. **Chen, L.; Zhang, Z.; Zhao, M.; Yu, K.; Liu, S.** "APR-QKDN: A QKD Network Routing Scheme Based on Application Priority Ranking." *Entropy* 24(11):1519, 2022. `[V]` — priority = importance(1–5) × key volume × utilisation; soft deadline `R_delay` with 5 retries.

9. **Cicconetti, C.; Conti, M.; Passarella, A.** "Qkd@Edge: Online Admission Control of Edge Applications with QKD-secured Communications." *IEEE SMARTCOMP 2023*; arXiv:2305.02015 `[V]` — explicit online admission control, LP/ILP, three policies.

10. **Cvitić, I.; Peraković, D.; Pinto, A. N.** "Overview of Routing Approaches in Quantum Key Distribution Networks." arXiv:2511.15465, Nov 2025 `[V]`
    26 routing strategies 2013–2024. **Field-level headlines we must not appear to rediscover: key-aware dynamic routing reduces service rejection 25–40% vs static shortest path; multipath increases key consumption 30–60%.** Names "AI-driven predictive routing" as open.
    **Also the smoking gun on C4:** its acknowledgment states the work is part of **NATO RTG IST-218, "Multi-Domain QKD for Military Usage."**
    *arXiv-only, not peer-reviewed; two of its citations conflict with primary sources. Re-verify any number at source.*

11. **Dervisevic, E.; Tankovic, A.; Fazel, E.; Kompella, R.; Fazio, P.; Voznak, M.; Mehic, M.** "QKD Networks – Key Management: A Survey." arXiv:2408.04580; *ACM Comput. Surv.* DOI 10.1145/3730575 `[V]`
    Already tabulates 16 KMSs against **Priorities** and **Fallback method** columns. States plainly that with HKDF fallback the network "will be unable to serve true ITS keys."

### 1.2 The hybrid/graded-security core (kills C3)

12. **Sanz, A.; Salegi, E.; Atutxa, A.; Franco, D.; Astorga, J.; Jacob, E.** "QuLore / Extending Quantum-Safe Communications to Real-World Networks: An Adaptive Security Framework." arXiv:2511.22416, Nov 2025 `[V]`
    **Kills C3a outright.** Four named security levels assigned by a central controller: L1 direct QKD; L2 multi-hop OTP trusted relay; L3 "hardened KDF from at least one QKD-derived segment and one PQC KEM shared secret"; L4 purely PQC. Preference L1>L2>L3>L4. Anchors ETSI GS QKD 014/015/020 + FIPS 203.
    **Residual gap (verified absent):** selection is *node-capability-driven, not runtime-exhaustion-driven*; no starvation model; **no operator reporting of the assigned level**; no per-level traffic statistics.

13. **Zhu, Z.** "Techno-Economic Feasibility Analysis of Quantum Key Distribution for Power-System Communications." arXiv:2510.15248, Oct 2025 `[V]`
    **Kills C3c.** Out-of-key event `B_i,t < b_i^min`; fallback indicator `χ_i,t`; fraction `φ_i` shifting to PQC-only; **`ρ_k,t` = fraction of time/traffic for which class k benefits from QKD keys**; fallback occupancy `Pr(χ=1)`; per-class availability targets, SLA compliance, "observable, auditable, measurable."

14. **Schartner, P.; Rass, S.** "Quantum key distribution and Denial-of-Service: Using strengthened classical cryptography as a fallback option." IEEE, 2010, doc 5685533 `[S]`
    **Kills C3b priority, from 2010.** Premise: adversaries who cannot steal keys will DoS the QKD network to *force* classical cryptography; proposes OTP-strengthened classical crypto for emergency operation. **Must cite; cannot be positioned around.**

15. **Spooren, P.; Neuhold, A.; Ramacher, S.; Hühn, T.** "PQC-Enhanced QKD Networks: A Layered Approach." *IEEE QCNC 2026*, Kobe; arXiv:2604.05599 `[V]`
    **Our strongest adversarial reviewer.** Explicitly frames our Grade A→C transition as a **downgrade attack** and chooses **fail-closed**: "a fail-safe mechanism prevents downgrade attacks, where the data tunnel is interrupted after a defined time." Timing envelope: disruption propagates 240–720 s, 60 s grace per component, 11.6 s provisioning over a degraded control path.

16. **Makris, A. et al.** (GRNET/NKUA/Nokia/evolutionQ/IDQ) "Field demonstration of a fully managed, L1 encrypted 3-node network with hybrid relayed-QKD and centralized symmetric classical key management." *ECOC 2024*; arXiv:2403.08526 `[V]`
    Field-demonstrated fail-degraded behaviour: on attack or failure, transitions to classically-generated quantum-safe keys. **1 key/min for a 300 Gbps circuit**; intervals 1/5/15/60 min; buffer 1000 keys; 4 h expiry; 98% rotation success.

17. **Barral, D. et al.** "Interconnecting Regional QKD Networks: Hybrid Key Delivery Across Quantum Domains." arXiv:2604.20376, Apr 2026 `[V]`
    Galicia–Basque testbed where **some relay hops are QKD-secured and others PQC-secured**; hybridised OTP (XOR of QKD and PQC secrets); ETSI 014/020. Reports keyrate/delay/jitter — **no security-composition metric.**

18. **Garms, L. et al.** (Toshiba/QUB) "Experimental Integration of QKD and PQC in a Hybrid Quantum-Safe Cryptosystem." *Adv. Quantum Technol.* 7(4):2300304, 2024 `[S]` — hardware-demonstrated true combiner. **Grade B itself is not claimable.**

19. **Tysowski, P. K.; Ling, X.; Lütkenhaus, N.; Mosca, M.** "The engineering of a scalable multi-site communications system utilizing QKD." *Quantum Sci. Technol.* 3(2):024001, 2018 `[V]` — **VERIFIED, full text.** States the fall-back-OR-block fork under policy control; substitute cryptosystem keeps the same KMS interface. Contains NO simulation or measurement. Does NOT define five client security categories (that was a survey characterisation) — its categories are three raw-key buffers. See item 3 in §6.

20. **Doering, R.; Geitz, M.; Braun, R.-P.** ICCNT/Springer 2022, pp. 148–158 `[C]` — QKD and PQC keys coexist in one key store, **distinguishable by applications via metadata**. The label our metric would aggregate already exists.

### 1.3 Tactical / contested (kills C4)

21. **Hafeez, M. et al.** "Quantum-secured routing in drone communication for 6G-enabled smart mobility." *Scientific Reports*, 2026. DOI 10.1038/s41598-026-36297-5 `[V]`
    **The closest existing work to our whole design.** 500-UAV SAGIN; **RIS-assisted FSO** BB84 links; multi-hop relaying; three parameterised attack classes with Poisson inter-arrivals (jamming, topology poisoning, side-channel); **hard QBER < 11% feasibility cut with PQC failover**; key-pool update rule, min pool 10 kbit, min lifetime 100 s. Reports 96.2% key-establishment success, 23.7 ms latency, >88% detection TPR.

22. **Li, M.; Zhang, Q. et al.; Boutaba, R.; Tornatore, M.** "Routing and Wavelength Assignment with Minimal Attack Radius for QKD Networks." arXiv:2508.10613 `[P]`; extended version at https://rboutaba.cs.uwaterloo.ca/Papers/2026/li-qe26.pdf `[V]`
    High-power jamming; **maxNAR** metric; Quantum Key Pools as attack-immune caches; DRL/PPO. −23.5% / −56.6% maxNAR. **Single worst-case attack placement, not a swept intensity** — that is our remaining wedge, and it is narrow.

23. **Ghorab, A.; Azab, M.; Grañani, ...** "A QKD Routing Scheme for a Zero-Trust QKD Network System: A Moving Target Defense Approach." *Big Data Cogn. Comput.* 9(4):76, 2025 `[V]`
    **Sweeps attacker pervasiveness** (20% benchmark) against attack success and key-distribution success. Nearly doubles key-distribution success rate.

24. **NATO / programme evidence that C4 is false:** RTG **IST-218** "Multi-Domain QKD for Military Usage" (confirmed in ref 10's acknowledgment); **"QKD Key Management for Military Applications: A Study in the MuQuaNet Testbed,"** NATO STO 2023/24 `[S]` (Bundeswehr University Munich; 13 nodes, dark fibre **plus free-space**, multi-vendor, R&S KMS); **"Implementation Model of Free-Space QKD Routing Protocols for Ground-to-satellite Links Using Drones,"** NATO STO `[S]`; **EDF-2026-RA-CYBER-QSTN "Quantum secured tactical networks"** funding call `[S]`.
    **All three NATO documents 403 to automated fetch. Retrieve manually — priority order: drone-FSO-routing, then MuQuaNet.**

### 1.4 AI/ML (saturates the RL angle)

25. **Johann, T.; Kühl, ...; Pachnicke, S.** "Adaptive Routing for Meshed QKD Networks of Flexible Size Using Deep Reinforcement Learning." *Photonics* 13(2):198, 2026. DOI 10.3390/photonics13020198 `[V-abs]`
    **Kills option (a).** DRL + **Graph Attention Networks** → generalises to unseen topologies without retraining. Reward = **entropy of key-store filling levels**. Trained on random 10–20-node graphs, evaluated on 14-node NSFNET. **+18.7% mean key-store level, zero depletion.** Beats hop-count *and weighted* shortest path.
26. **Xie, Y. et al.** "Efficient routing algorithm for trusted relay QKD networks via quantum reinforcement learning." *Optics Express* 2025, DOI 10.1364/OE.570196 `[V-abs]` — HQ-DDPG; >91.35% key delivery ratio; 45× fewer parameters.
27. **Seok, ... Lee** "Deep RL-Driven Optimization of End-to-End Key Provision in QKD Systems." *J. Netw. Syst. Manage.* 33:30, 2025, DOI 10.1007/s10922-025-09902-7 `[P]` — **GAT + LSTM** for key provisioning. Kills the "learned forecasting" option.
28. **Sharma, ... Prakash** "Deep RL-based routing and resource assignment in QKD-secured optical networks." *IET Quantum Commun.* 4(3):136–145, 2023 `[V]` — blocking ↓ 7.19/10.11/33.50%.
29. **Zuo, Zhao, Yu, Nag, Zhang** "RL-based Resource Allocation in QKD Networks." *ACP/IPOC 2020* T3C.6 `[S]` — "weights key quantity against **security requirement**." Nearest published gesture at our grade axis. **Retrieve.**
30. **ITU-T Y.Sup70** "Y.3800-series: QKD Networks — Applications of Machine Learning," approved 2021-07 `[V]` — standards-level catalogue of ML across QKDN layers. **Cite it: legitimises ML to a standards reviewer, but means "we apply ML to QKDN control" is not itself a contribution.**
31. **Premakumari, ... Pérez Guzmán** "Reinforcement Q-Learning-Based Adaptive Encryption Model for Cyberthreat Mitigation in WSNs." *Sensors* 25(7):2056, 2025 `[V]`
    **Closest prior art to a learned security-grade policy.** MDP whose **action is the encryption level**, driven by a threat classifier. Constrains but does not kill: driver is *threat level*, not *ITS-key-reservoir exhaustion*; no QKD, no relay, no traffic classes.
32. **Zhu, Z.** "Dynamic-Key-Aware Co-Simulation Framework for Next-Gen SCADA Encrypted by QKD." arXiv:2510.14838, Oct 2025 `[V-abs]` — key-inventory prediction + key-aware reconfiguration by task security demand. **+25% task success, +83% key utilisation. Uncomfortably close to our thesis in another vertical. Read in full.**
33. Classical learned admission control is **fully saturated** — there is an entire survey (Khani et al., *Int. J. Commun. Syst.* 2024, DOI 10.1002/dac.5857) plus *Sensors* 22(8):3031 (2022), IEEE 9779742, arXiv:2406.17334. Useful ally: **digital-twin-assisted DRL admission control** (arXiv:2310.09299; IEEE 10711852) — the reviewer-legible framing for "the simulator is the training environment."
34. Policy distillation: **VIPER**, Bastani et al., NeurIPS 2018, arXiv:1805.08328. No QKD-network paper distils a learned control policy into operator-auditable rules.

---

## 2. Physics and modelling ground truth

### 2.1 RULING — the degraded-link model

**"Bad state = 5% of nominal rate" is indefensible for the jammed/attacked state.** Evidence:

- **Alléaume et al.**, quant-ph/0701168; *Theor. Comput. Sci.* 560:62–81 (2014) `[V]`: DoS is mounted "by acting on the quantum channel in order to increase the noise above the security threshold"; "Any strong enough perturbation … inducing noise above the security threshold … will in practice disrupt the key generation." **An adversary applying pressure is by definition pushing across the threshold. Modelling that as 5% throughput models an adversary who fails.**
- **Hard cliff ≈ 11% asymptotic:** Rath, Panth, Bhaskar, arXiv:2603.27278 `[V]` — above ≈11% "secret key extraction becomes impossible." Shor–Preskill ~11.4% via Ranade & Alber, quant-ph/0510041 `[V]`. **Do NOT use 18.9%/20%** (Gottesman–Lo/Chau) — those need two-way advantage distillation no deployed system runs.
- **Practical abort is far lower — 7.5%:** Tokyo QKD Network's deployed NEC distillation engine has LDPC coding rates only for QBER <3.5% / <5.5% / <7.5%. **There is no rung above 7.5%.** (Sasaki et al., *Opt. Express* 19(11):10387, 2011 `[V]`)
- **Below the cliff, decay is continuous:** Ma, Qi, Zhao, Lo, *PRA* 72:012326 (2005), quant-ph/0503005, Eq. (1): `R ≥ q{−Q_μ f(E_μ) H₂(E_μ) + Q₁[1 − H₂(e₁)]}` `[V]`.
- **The gift:** Tokyo's All-Vienna BBM92 link with a deliberately misaligned source at **QBER 5–7%** delivered **~0.25 kbps against 2–3 kbps nominal** for the same hardware in SECOQC — i.e. **8–12% of nominal at QBER 5–7%** `[V]`. So "≈5–10% of nominal" *is* defensible for a degraded-but-sub-threshold link, and it becomes an **output** of the model rather than an assumption.

**Model to implement — four states, not two:**

| State | Rate | Trigger | Citation |
|---|---|---|---|
| NOMINAL | `R₀(link type, length)` | — | field-trial table §2.2 |
| DEGRADED | `R₀ · [1 − f·H₂(e) − H₂(e)] / [1 − f·H₂(e₀) − H₂(e₀)]`, `f ≈ 1.16–1.22` | `e₀ < e < e_abort` | Ma et al. Eq. (1); calibrated by Tokyo All-Vienna |
| ABORT | **0** | `e ≥ e_abort`; **e_abort = 0.075** engineering, sensitivity run at 0.11 | Tokyo LDPC ladder; Rath; Shor–Preskill |
| HARD OUTAGE | **0** | fibre cut, LOS loss, terrain masking, **classical-channel denial** | Alléaume (cut); Mehic (classical-channel jamming) |

Two failure modes **bypass QBER entirely** and must be separate states — say so explicitly, it reads as rigour: (a) classical post-processing channel jamming (quantum channel pristine, rate zero — Mehic et al. `[V]`: blocking routing or post-processing packets "would disable the link"); (b) **detector blinding** (Lydersen et al., *Nature Photonics* 4, 2010 `[S]`) extracts the full key **without increasing QBER** — QBER-driven models are blind to it by construction.
Newest availability attack worth one sentence: **Kuniyil et al.**, "Recovery-Induced Erasure Attack on QKD Systems," arXiv:2603.03217 `[P]` — pushes observed QBER *below* the abort threshold while raising erasure probability.

### 2.2 Parameter provenance

Only rows marked `[V]`/`[P]` are safe to cite.

| Parameter | Value | Conditions | Source | Conf |
|---|---|---|---|---|
| Fibre SKR, metro | **81.7 kbps** secure | 45 km installed fibre, 14.5 dB, QBER 2.7%, decoy BB84 | Sasaki 2011 `[V]` | high |
| Fibre SKR, GHz | **304 kbps** | same link, Toshiba 1 GHz, QBER ~3.8% | Sasaki 2011 `[V]` | high |
| Fibre SKR, long hop | **~2.1 kbps** | 90 km loopback, 27 dB, QBER 2.2–2.3% | Sasaki 2011 `[V]` | high |
| Fibre SKR, short commercial | **300–420 bps** | 13 km, IDQ Cerberis, SARG04, QBER 4%→2% | Sasaki 2011 `[V]` | high |
| Entanglement, degraded | **0.25 kbps** vs 2–3 kbps nominal | ~1 km BBM92, QBER 5–7%, misaligned source | Sasaki 2011 `[V]` | high |
| FSO, long mountaintop | **12.8 bit/s** | 144 km La Palma→Tenerife, ~35 dB, decoy BB84 | Schmitt-Manderbach, *PRL* 98:010504 (2007) `[P]` | med-high — **QBER not found, do not quote one** |
| FSO, short high-rate | **164.8 kbps**, QBER ≈3.3% | 2 km outdoor, 100 MHz, active beam-wander correction | Park et al., arXiv:2607.24118 `[P]` | med-high |
| FSO, medium + AO | **200 bit/s** | 18 km, telecom λ, 40 cm telescope, adaptive optics | Rossi et al., arXiv:2602.16680 `[P]` | med |
| **FSO, entanglement, DRDO** | **~240 bit/s**, QBER <7% | >1 km, IIT Delhi campus, DRDO DIA-CoE, Jun 2025 | PIB PRID 2136702 via secondary `[S]` | med — **get the PIB text** |
| FSO, mobile platforms | drone↔drone **8.5 kbps** / QBER 2.45%; vehicle 70 mph **2.5 kbps** / 3.08%; tabletop 41.5 kbps / 2.87% | **night only**, ~100 m, polarization decoy | Conrad et al., arXiv:2505.17587 `[P]` | high — mobility costs ~5×, speed ~8× |
| QBER threshold, asymptotic | **≈11%** | one-way postprocessing, BB84 | Rath, arXiv:2603.27278 `[V]` | high |
| QBER, practical abort | **7.5%** | deployed LDPC ladder | Sasaki 2011 `[V]` | high |
| Key pool, field | **1000 keys** (~256 kbit at 256 b), 4 h expiry | evolutionQ BasejumpQDN, 3-node field net | Makris arXiv:2403.08526 `[V]` | high |
| Key pool, spec example | `stored_key_count` 25000, `max_key_count` **100000**, `key_size` 352 b → 8.8 / 35.2 Mbit | **illustrative example only — NOT normative.** 352 appears exactly once in the whole document, inside a worked Status example. ETSI specifies **no** default/recommended/mandatory key size; `key_size` is KME-declared at runtime | ETSI GS QKD 014 **V1.1.1 final, read** `[V]` cl. 6.1 Table 9 | high |
| Block granularity | "order of Mbits" then resized | quantum layer output | Dervisevic survey fn.1 `[V]` | med |
| **Reservoir capacity** | **default `C = 52,428,800 bit (50 Mibit)`, `Mmin = 1,048,576 bit`, `Mthr = 11,324,620 bit`; sweep `C` over 1 Mbit–1 Gbit** | the actual published values in QKDNetSim's shipped SECOQC script; sweep interval = its own code defaults | QKDNetSim `qkd-buffer.cc` + `scratch/secoqc_p2p_qkd_system.cc` `[V-source]` — see §2.7 | high (citable) |
| Auth cost per message | **k bits**; `ε_au = n·2^(−k+1)`; `k=127` → `ε≈10⁻³³` | Toeplitz/LFSR; tag OTP-encrypted so the 2k-bit hash key is reusable | Fung/Ma/Chau arXiv:0910.0312 Eq. 9 `[V]`; Walenta arXiv:1309.2583 `[V]` | high |
| Auth, distillation overhead | **2.7%** @1 km, **5.0%** @25 km, ~20% for 6-bit sift blocks | 625 MHz COW, ε=4×10⁻⁹, 10⁶-bit blocks | Walenta `[V]` | high — **already inside R, do not double-count** |
| Relay auth overhead | ~**50%** at D=256 bit; **0.013%** at D=1 Mbit | 127-bit tag per relay message | *derived arithmetic* | **block size must be a parameter** |
| Bulk key demand | **256 bit / 60 s** per 300 Gbps; or 256 bit / 17.3 s at 180 Gbit/s ⇒ **~15 bit/s** | AES-256 L1/OTN encryptors | Makris `[V]`; DemoQuanDT arXiv:2503.21186 `[V]` | high |
| Data-per-key ceiling | ≤2³² invocations/key; ~64 GB/invocation; 389 GB per 256-bit key | GCM limits | NIST SP 800-38D cl. 8, 8.3 `[V]`; 389 GB attributed to ePrint 2024/051, **unverified at source** | high / med |
| C2 circuit demand | 128 kbit of key per second (contract example); or 100 kbps charging / 7 s period | SECOQC guaranteed-key-rate service class; Mehic simulation | `[V]` | **weakly grounded — sweep** |
| OTP | key bits = payload bits | Shannon, via Y.3803 cl. 8.2.3 | `[V]` | high — **stress regime only, never a baseline** |
| Multi-path cost | **+30–60%** key consumption; key-aware routing **−25–40%** rejection | synthesis over 26 strategies | Cvitić arXiv:2511.15465 `[V]` | high |
| Outage timing | disruption propagates **240–720 s**, 60 s grace/component, 11.6 s provisioning under 300 ms/100 ms/1% loss | layered QKD+PQC stack | Spooren arXiv:2604.05599 `[V]` | high |
| Attack→reroute (field) | QBER spike detected "in a few seconds"; KMS stopped link, switched route **before the buffer emptied** | live eavesdropping demo, 90 km link, 128 kbps OTP video | Sasaki 2011 `[V]` | high — **this transient is the phenomenon to model** |

**Refused for lack of provenance — do NOT invent:** QBER for the 144 km link; QBER for the 18 km AO link; any FSO hard-outage duration or frequency distribution; any mountainous-terrain QKD link budget; the "turbulence dominates within 20 km" split; "AO gives 100 km clear / 50 km overcast at 0.7 m aperture."

### 2.3 Key relay accounting — CONFIRMED with four refinements

**`D` bits on each of `n` links, total `D·n`. Efficiency 1/n.** Confirmed by SECOQC (arXiv:quant-ph/0610202 `[V]`) and **ITU-T Y.3803 (12/2020) cl. 8.2.3** `[V]`: key data **and metadata** of the KMA-key are XOR-encrypted with the neighbouring pair's key "in an OTP manner" per Req_KM 6 of Y.3801.

1. **Invariant across all four ITU-T relay schemes** (Y.3803 cl. 9: hop-by-hop OTP of `K_AB`; locally-generated `KeyRN`; XORs uniformly processed at destination, Fig. 7; XORs collected at one centralised node, Fig. 8). They differ in trust model and message routing, **not bit accounting**. Model one rule.
2. **The source consumes no QKD key for the payload** — Y.3803 permits a local non-deterministic RNG (ISO/IEC 18031 or QRNG). The `D·n` is pads only.
3. **Metadata rides along** — relay is performed in units of a *key file* (metadata + key data), metadata "typically a few 10s of bytes." At `D=256` bit a 30-byte metadata block is **~94% overhead**. Not ignorable at small block sizes.
4. **Contention** — each link's generated key is **divided among all relay paths crossing it**; end-to-end rate is the min over links of the *allocated* contribution ⇒ a multicommodity-flow problem. Real KMSs keep **two pooling levels**: link-fed pools, then per-SAE-pair Quantum Key Pools (Selentis et al., arXiv:2509.24440 `[V]`).

### 2.4 Standards — what actually exists

**ETSI GS QKD 014 (REST key delivery).** Three methods; `Status` exposes `stored_key_count`, `max_key_count`, `max_key_per_request`, `max/min_key_size`. **Only three error codes: 400, 401, 503.** Grepping the spec for "insufficient", "not enough", "unavailable", "exhaust" returns **nothing** — *a KME with an empty pool has no standard way to say so and returns a generic 503.* **No priority field.** QoS is a vendor extension; the spec's own example defines `abc_route_type ∈ {direct, indirect}` — i.e. *whether a key was relayed through intermediate trusted nodes* — as a mandatory extension. `[V]` on draft V0.0.5; **V1.1.1 final not read (etsi.org 403) — re-verify field values before publication.**

**ETSI GS QKD 020 (Interoperable KMS API, V1.1.1, 2026-06).** Governs KMS-to-KMS relay and **has real denial semantics** — verbatim error identifiers read from the OpenAPI: `insufficient_key_material`, `no_known_route`, `no_route_multiple_targets`, `invalid_routing` ("requires directly passing it back to the calling KME, which is invalid"). `ack_status` enum: **relayed, failed, voided, failed to void, key not present.** Status codes include **408**. `[V]`

**ETSI GS QKD 015 (SDN control, V2.1.1).** Where priority actually lives: **`app_priority`** (uint32), `max/min/virt_bandwidth`, `jitter`, plus `skr`, `eskr`, `consumed_bits`, `expected_consumption`, `ttl`. Link types **VIRT / PHYS** — *a multi-hop relayed path is modelled as a **virtual** link.* Notifications include **`sdqkdn_link_overloaded`**. No RPCs. `[V]`

**ETSI GS QKD 004** (session interface, OPEN_CONNECT / GET_KEY / CLOSE, KSID) — QoS reportedly includes `Key_chunk_size, Max_bps, Min_bps, Jitter, Priority, TTL, Timeout`. **Spec not read; corroborated only second-hand. Medium confidence.**

**⚠ ITU-T Y.3803 cl. 8.2.3 / Req_KM 7 of Y.3801 — the most consequential finding in this dossier:**
> "If the necessary number of keys for OTP-encrypted key relay is not available, a **backup method with symmetric key cipher such as AES can be used** for key relay."
KMAs **record the encryption method in metadata**, and when an application requests QKD-grade security the KMA should select OTP-relayed keys. `[V]`
**Fallback to weaker crypto on key insufficiency is already standardised, and the grade is already recorded in metadata.** This kills C3b as novelty *and* hands us the standards anchor for the reframed paper.

**Y.3803 cl. 8.2.5:** rerouting should occur when relay-node key count "falls below a **threshold**", or on high QBER. The controller acquires "key consumption rates, shared number of keys in the KMAs and KMA link status" — **this defines exactly what state a routing policy may legitimately read.** `[V]`

**Also relevant, unread:** Y.3801, Y.3804, **Y.3815 (09/2023) resilience**, **Y.3821 (04/2024) resilience requirements** (reported to define *key service recovery ratio*), **Y.3831 (12/2025) "Integration of QKD network and user networks supporting end-to-end modern cryptography services"** — *highest-risk unread item; "modern cryptography services" may already cover PQC and graded key-supply modes.* ISO/IEC 23837-1/2:2023 (QKD module security requirements). ITU-T **Y.Sup70** (ML in QKDN).

### 2.5 Domain errors to avoid — a reviewer will catch these

1. Charging `D` bits only on the first hop, or once end-to-end. It is `D` on **every** link.
2. Double-debiting a link because both endpoints "use" the key. One shared pad, **one debit per link per relay**.
3. Modelling the four ITU-T relay schemes as having different key costs. They don't.
4. Assuming the source spends QKD key to *create* the end-to-end key. Y.3803 permits a local RNG.
5. Calling authentication negligible without stating the block size. Negligibility is a consequence of **batching**, not a property of Wegman–Carter.
6. Double-counting the 2.7–5% figure — that is *distillation* authentication, already inside the link rate. Relay authentication is separate.
7. Making authentication scale linearly with message length. It scales **logarithmically**.
8. Forgetting metadata (a few tens of bytes per relayed key file, normally OTP-encrypted too).
9. Returning a bespoke "insufficient key" error from an ETSI **014** interface. That vocabulary is in **020**.
10. Inventing a priority field in 014. Priority lives in 004 and 015.
11. Treating key-unavailable as necessarily blocking. **Y.3803 Req_KM 7 standardises AES fallback.**
12. Ignoring key wasted by a failed relay — a relay failing at hop *k* has already spent pads on hops 1…*k*−1. ETSI 020 `ack_status` has `failed` and `key not present`.
13. Allowing a route that passes a key back to the calling KMS — ETSI 020 `invalid_routing`.
14. One flat pool per link serving all destinations. Real KMSs keep **two levels**.
15. Setting e2e rate = min link SKR while ignoring contention across paths.
16. Treating key as a continuous fluid. Delivery is quantised `number` × `size`, bounded by min/max key size and `max_key_per_request`.
17. Omitting key TTL (4 h measured).
18. Assuming OTP for bulk traffic. Real encryptors are AES-256 rekeyed per minute or per 389 GB; OTP at 180 Gbit/s is ~10¹⁰× more key.
19. Ignoring **detector saturation** — SKR is *flat* below ~25 km, not monotonically rising as distance shrinks.
20. Giving the routing policy state the control plane cannot see (Y.3803 8.2.5 + ETSI 015 define what is exposed).
21. Calling a relayed multi-hop path a physical link — ETSI 015 types it **VIRT**.
22. Reporting a 64 kbit reservoir as justified. Nothing supports it.
23. A smooth 5% degradation under attack. See §2.1.

### 2.7 Reservoir sizing — resolved with citable values

**The 64 kbit reservoir is ~3 orders of magnitude below every published link-level reservoir.** At Toshiba's 300 kb/s it is 0.21 s of key generation — 250 AES-256 keys. Defensible only if reframed as a *per-application key-block quota*, never as a *per-link reservoir*.

**QKDNetSim `QKDBuffer` — read directly from source, units are bits** (`FetchKeyOfSize` is documented `"keySize in bits!"`):

| Field | Code default | Shipped SECOQC script value |
|---|---|---|
| `m_Mmin` | 1,000,000 (`//1Mb`) | **1,048,576** (1 Mibit) |
| `m_Mthr` | 2,000,000 (`//2Mb`) | **11,324,620** (≈10.8 Mibit) |
| `m_Mmax` | 1,000,000,000 (`//1Gb`) | **52,428,800** (50 Mibit) |
| `m_Mcurrent` | 5,000,000 (`//5Mb`) | 52,428,800 / 10,485,760 |

`CheckState()`: READY when `Mcurrent ≥ Mthr`; CHARGING when below threshold, above minimum, rising; WARNING when below threshold, above minimum, otherwise; **EMPTY when `Mcurrent ≤ Mmin`**. `AddNewContent()` **hard-rejects on overflow** — generated key is *discarded*, not queued, when full. Adopt these semantics verbatim for citability.
*Caveat: the example files label the arguments only `//min //thr //max //current` with no unit; the bits reading comes from `qkd-buffer.cc/.h`, not the examples.*

**Only empirically verified water-mark ratio:** Cambridge metro (Dynes et al., *npj Quantum Inf.* 5:101, 2019 `[V]`) — pool of **1000 global keys**, ~180 kbytes of QKD key to initialise, **refresh triggered at 800 keys = an 80% low-water-mark**; replenishment ~100 bps, limited by REST API speed.

**Three-tier threshold structure worth adopting** (arXiv:2510.14838 `[V]`): `Ksafe = αmax·Lmax·λmax·τcrit` (minimum reserve for the top-priority class over a critical window) < `Kth` (reconfiguration trigger) < `Kcap` (hardware buffer capacity, surplus discarded for freshness). **Assigns no numeric value to `Kcap`** — hence the sweep.

**⚠ CLEAN GAP CLAIM, well evidenced:** across ~15 fetched datasheets/brochures (IDQ, Toshiba, QuantumCTek, Quantum Xchange, LuxQuanta, ThinkQuantum, QTI, KEEQuant, Qubitekk) **no vendor publishes a key-storage capacity** — it appears only as an unquantified feature word ("key buffering", "key storage management"). **Zero exceptions.** Corroborated by the KMS survey (arXiv:2408.04580), which reports no quantitative storage figures for Cisco, NEC, Toshiba, MagiQ, NIST or SECOQC. **This justifies sweeping rather than fixing, and is itself a citable observation.**

**Report results against the dimensionless `C / (R·T)`** (capacity ÷ generation rate × holding time) so conclusions are scale-free and survive future vendor disclosure.
*Correction to an earlier assumption: "KaaS-120" in the QuIKS paper means **120 requests/second, not 120 seconds of key**. The "N seconds of key at rate R" convention is **not** what this literature uses.*

**Additional vendor/field SKR anchors** (all read directly): Toshiba LD/MU/LE **300 kb/s @ 10 dB** (30 dB budget, 150 km+); IDQ Cerberis XG **2 kb/s @ 12 dB**; IDQ Clavis XGR **400 kb/s @ 12 dB** (ID281 SNSPD); IDQ Clavis XG quotes **keys/hour not bit/s** — 70,000/hr @ 18 dB, 14,000/hr @ 24 dB, 2,800/hr @ 30 dB; QuantumCTek QKD-PHA300 **50 kbps @ 10 dB, 1 kbps @ 22 dB**; ThinkQuantum QUKY 2.2–4.4 kb/s @ 13 dB (JRC independently measured 12 kbit/s @ ~3 dB → ~300 bit/s @ ~28 dB); QTI Quell-X 2 kb/s @ 14 dB.
Field: **Cambridge metro** 2.22–2.58 Mbps at 3.9–4.2 dB, 360 Tbit over ~580 days; **Hefei 46-node MAN** 6–60.5 kbps, PA triggered after **256 kbit** accumulated, 32 kbit initial authentication key, scheduling driven by "the amount of keys stored in the local memories"; **CN-QCN national** 145 backbone nodes incl. **104 trusted relays**, ~70 km / 18.61 dB average hop, Harbin→Shenzhen across 64 KM-Links min **9.75** / max **359.89 kbps**, per-segment end-to-end **9.75–20.85 kbps**, OTP key relay, controller "gathers real-time data on the key quantity of each KM-link"; **MadQCI Madrid** Toshiba DV up to 2857.1 kbps down to 37.2 kbps @ 33.1 km/11.8 dB, IDQ DV 1.4–2.04 kbps, Huawei CV 0.09–12 kbps, ETSI 014 delivery, and notably **relay nodes have no KMS functionality**; **SECOQC** acceptance criterion **>1 kbit/s at 25 km, key latency <60 s**.
Records for context: 421 km **4.9 kbps @ 42.7 dB → 0.25 bps @ 71.9 dB**; 605 km TF-QKD 0.778 bit/s @ 104.8 dB; 1002 km 0.0011 bps.

**⚠ BEST REALISTIC DEMAND ANCHOR FOUND — use this instead of invented demands:** SECOQC measured AES-VPN key consumption of **~36 bytes/s** (rekey every 20 s in 728-byte steps) `[V]`. Together with Makris (256 bit / 60 s for a 300 Gbps circuit) and DemoQuanDT (256 bit / 17.3 s at 180 Gbit/s ⇒ ~15 bit/s), this brackets real encryptor demand at **tens of bit/s**, not tens of kbit/s. Recommended pairing: `R` = 300 kb/s @ 10 dB (Toshiba, datasheet-grade) for a metro link, ~10–20 kbps for multi-hop national end-to-end (CN-QCN measured). At 300 kb/s a 50 Mibit reservoir is **~175 s of key** — a physically sensible minutes-scale buffer.

**Not established — sweep, never assert:** any vendor key-storage capacity; any standard or industry water-mark convention (the three instances above are implementation-specific); ETSI constraints on `stored_key_count` (etsi.org 403 on every attempt — **do not cite an ETSI clause number from this dossier that is not marked `[V]`**). **Do not cite** Mehic et al. 2017 *QIP* 16:253 figures (6400/2000/128 kBytes) — paywalled, snippet-only; note 6400 kiB and 128 kiB *exactly* match the script's max and min (corroborating the bits reading) but 2000 kiB ≠ 11,324,620. **Do not cite** "quantum key pool capacity 300 units / lower limit 50 / 80 units/s" or "Beijing MAN key pool 20–80 keys of 32 bits" — snippet-only. Chen et al., *Nature* 589 (2021) is paywalled; only the 47.8 kbit/s satellite-to-ground abstract figure is verified, and QuIKS's citation of 79.3 kbps to it could not be confirmed.

### 2.8 Key consumption — measured ground truth, and the error that would have broken the paper

**⚠⚠ THE SINGLE MOST IMPORTANT MODELLING FINDING IN THIS DOSSIER.**
SECOQC Vienna measured a live AES-IPsec VPN over a QKD link consuming **728 bytes every 20 s = 291.2 bit/s**, "and does not depend on the actual size of the plaintext message." Their footnote 27 breaks it down: the tunnel "needs **two portions of 256 bits on both sides in each exchange round. The remaining bits are OTP tunnel authentication overhead.**"
⇒ Of 5824 bits per round, only **512 bits (2×256) are actual cipher key**. **~91% of measured encryptor key consumption was ITS authentication, not key material.** (Peev et al., *New J. Phys.* 11:075001, 2009, §5.1.1, Fig. 20 right, ERD–GUD link `[V]`)
**A simulator that charges only 256 bits per rekey and ignores per-hop authentication will overstate how many encryptors a trusted-relay network can serve by roughly an order of magnitude.**

Corroborating relay overhead: **Cambridge** distributed 1000 global keys at a cost of **~180 kbytes of QKD key** ⇒ **1440 bits of link key per ~400-bit global key relayed ≈ 3.6× the naive figure** (Dynes et al. `[V]`; the 400-bit global key size is *derived* from 1 key/4 s ≈ 100 bps, not stated). **So a bare `D·n` model is optimistic — carry an explicit per-hop authentication term.**

Also citable: SECOQC's key stores held a **2 MiB minimum threshold "to ensure that… enough key remains in the store to authenticate the future communication on the classical channel"** `[V]`. **This is a published reservation-floor rationale that is not QoS — it is self-sustaining authentication.** Use it: it justifies a floor on grounds no reviewer can call arbitrary, and it is a *different* argument from Mehic's per-class QoS floor. Separately, SECOQC notes "even pure generation is accompanied by key consumption" — 96-byte portions authenticate sifting/EC/key-confirmation/PA.

**Measured / stated encryptor consumption — spans 3.5 orders of magnitude, so parameterise, never fix:**

| Source | Encryptor | Rekey | Key size | **bit/s** | Status |
|---|---|---|---|---|---|
| SECOQC *NJP* 2009 | AES IPsec VPN over Q3P | 20 s | 728 B/round | **291.2** | **measured** (91% auth) |
| Ciena + Toshiba + JPMorgan, *QST* 8:035015 (2023), arXiv:2202.07764 | Ciena Waveserver 5, 800 G | **1 s** | 256 b | **256** | stated design point; 258 DWDM channels = 66163÷256 |
| Cambridge *npj QI* 5:101 (2019) | ADVA 100G line-card pair | 4 s | ~400 b *(derived)* | **~100** | **measured — API-limited, not crypto-limited** |
| Bristol *JOCN* 14(1):A50 (2022) | FPGA 100G AES-256 | 1/27 s | 256 b | **6912** | measured **hardware ceiling**, 474 MB/key |
| Jouguet, *Opt. Express* 20:14030 (2012), arXiv:1201.3744 | Thales Mistral Gigabit | 10 s (**≥3 s HW floor**) | 128 b | **12.8** (max 42.7) | measured |
| SwissQuantum, arXiv:1203.4940 | IDQ Centauris 10G / FC / IPsec | 60 s | 256 b | **4.27** | measured |
| IDQ Geneva elections, 2007– | IDQ Cerberis L2 (dual-key ⊕ PKI) | 60 s (60 keys/h) | 256 b | **4.27**/dir | deployed since 2007 |
| IDQ + BT + Senetas CN9100 | 100 G L2 | 60 s | *not established* | 4.27 if 256 b | vendor claim |
| Adtran/ADVA blog 2023 | 400 G DWDM channel | 60 s | 256 b | **4.27**/ch/dir | **explicitly hypothetical** |
| JPMorgan + IDQ + Fortinet, arXiv:2405.04415 | FortiGate 4201F IPsec | 120 s | 256 b | **2.13**/tunnel | measured; 0.03% of 7.4 kbps SKR |

**Modal industry value: 256 bits per minute = 4.27 bit/s. Realistic operational cluster: 2–300 bit/s per encryptor.** The 6912 bit/s Bristol figure is a hardware capability, not a security requirement.

**Measured OTP anchors — use these, never invent an OTP demand:**
- **Tokyo QKD Network:** live OTP-encrypted video conference at a stated **128 kbit/s**, "stored key mode", relayed over 135 km (primary) and 69 km (secondary) — **switched routes on live eavesdropping detection without interrupting the call** `[V]`.
- **Tokyo OTP smartphone (Mitsubishi):** voice at **1 kB/s ⇒ 8 kbit/s per direction, 16 kbit/s bidirectional**; ~1.2 MB per 10-min bidirectional call; 2 GB SD card ⇒ 10 days of talk; key erased immediately after use `[V]`.
- **Hefei 46-node QMAN, 31 months continuous:** OTP voice **2.4 kbps**, file transfer **320 kbps**, FPGA XOR at 800 Mbps, delay <50 µs; supports **11 simultaneous user pairs**, demonstrated **22 users calling simultaneously for 6 minutes**. *Derived:* 11 pairs × 2.4 kbps × 2 ≈ 53 kbit/s, consistent with its 49.5–60.5 kbps link rates. **Best empirical anchor for "how many OTP voice users a QKD link supports."** `[V]`
- **⭐ SECOQC rerouting experiment (Fig. 22) — adopt this as the validation scenario:** an application consuming **≈1 KiB/s = 8192 bit/s** by OTP exhausted **3.5 MiB of a 5.5 MiB keystore in ~1 hour** (arithmetic checks: 3.5 MiB ÷ 1024 B/s = 3584 s ≈ 60 min ✓), then rerouted FOR–ERD–SIE–BRT for ~1.5 h, then FOR–ERD–GUD–BRT for ~0.5 h `[V]`. **A measured trusted-relay key-drain-then-reroute trace is exactly what our simulator must reproduce.**
- Framing quote (Tokyo 2011): typical field performance of a few kbps at tens of km "was only sufficient to encrypt voice data by real time OTP, or to feed the primary session key to a classical encryptor" `[V]`.
- Framing quote (Jouguet 2012): reported field rates below 1 Mbit/s make "**OTP incompatible with most of practical applications that require key rates above 1 Gbit/s**" `[V]`.

**Shannon, cited precisely** — C. E. Shannon, "Communication Theory of Secrecy Systems," *Bell Syst. Tech. J.* **28**(4):656–715, 1949, **§10 "Perfect Secrecy," pp. 679–682** `[V]`: Theorem 6 (p. 680); the key-count bound (p. 680); and the rate inequality **`R_M L_M ≤ R_K L_K`** (p. 682) with "a bit of key completely conceals a bit of message information… this is the best that can be done."
*Nuance worth one sentence:* Shannon's requirement is on message **entropy**, reduced by redundancy removal by the factor R/R_M. **Charging 1 key bit per payload bit is the worst case — correct only for incompressible or already-encrypted payloads.**

**Canonical cost-law citation, now confirmed** (was a `[[verify]]` placeholder in the original draft): **Salvail, Peev, Diamanti, Alléaume, Lütkenhaus, Länger, "Security of Trusted Repeater Quantum Key Distribution Networks," *J. Computer Security* 19:61–106, 2011; arXiv:0904.4072** `[V]` — hop-by-hop transport "ensured by **One Time Pad encryption and ITS authentication, both realized with a local QKD key**."

**Two ETSI corrections that must reach the paper:**
1. **Drop any claim that 352 bits is an ETSI default.** Correct wording: *"352 bits appears only as the illustrative `key_size` value in the example Status object of ETSI GS QKD 014 clause 6.1; the standard leaves key size KME-declared."* Cambridge's ~400-bit derived global key is the closest real number found — and it is not the ETSI value.
2. **No ETSI QKD deliverable states any numeric key rate or consumption rate.** Grepped across GS 002/003/004/014/015/018/020 and GR 003: zero numeric hits for any rate unit. ETSI supplies only the *variables* (`key_size`, `number`, `size`, `Key_chunk_size`, `Max_bps`/`Min_bps`, `expected_consumption`, `consumed_bits`, `skr`, `eskr`). **Every rate in our model must cite vendor or field-trial literature, never ETSI.**
   Interoperability wrinkle worth a sentence: **QKD 004 `Key_chunk_size` is in BYTES; QKD 014 `size` is in BITS.** Also QKD 014: a KME supporting only multiples of 8 **shall** return HTTP 400 `"size shall be a multiple of 8"`; `number` defaults to 1; `size` defaults to `key_size`. QKD 004 `Priority` handling is "left to the specific implementation."

**Contention effect to model:** IDQ Clavis XG **Hub&Spoke key rate per spoke falls ~4× going from 3 spokes (1170 keys/h) to 12 spokes (292 keys/h) at fixed 23 dB loss** `[V]` — a shared-generator contention effect, directly relevant to a relay chain sharing a QKD module.

### 2.6 Simulator decision

**Write a purpose-built discrete-event simulator; use QKDNetSim v2 as the semantic reference and cross-validate one configuration.**

Ruled out by source-tree inspection: **SeQUeNCe** (`sequence/qkd/` is point-to-point BB84 + cascade; no trusted relay, no key pools), **NetSquid** (no relay/pools; package *and* docs behind registration with no OSI licence — an artifact-availability problem for the paper), **QuISP** (no pools; inherits OMNeT++ Academic Public License, non-commercial; note `pip install quisp` installs an unrelated Jupyter widget).

**QKDNetSim v2** is the only on-target tool — its `QBuffer` (`Mmin/Mthr/Mmax/Mcurr`, states READY/WARNING/CHARGING/EMPTY) *is* our reservoir, and `Relay()` with `prev_hop_id`/`next_hop_id` *is* our trusted relay. But it is wrong for *this* study because the two things we compare are its weakest parts: routing is self-described as "an early version of routing table", `QCenController` implements exactly one policy (Dijkstra, recompute on EMPTY), and **admission control does not exist**. Plus a brittle toolchain (ns-3 3.46 source build + `git apply` patches), poor citability (repo renamed, history squashed 2025-12-25, 6 commits, no tags/releases), validation on 6 nodes / 3 user pairs, and GPL-2.0 inheritance.

**Mitigate the "why trust your simulator?" objection with four concrete moves:** anchor request semantics to ETSI 014/004/020 and note QKDNetSim does the same; **reuse QKDNetSim's published abstractions verbatim** (`Mmin/Mthr/Mmax`, the four buffer states, key-waste-on-failed-relay) for citability; reproduce its `examples_qkdnetsim_secoqc` 6-node configuration once and report agreement, as the QuISP–SeQUeNCe cross-validation paper does (arXiv:2504.01290); and draw the policy set from the 26-strategy survey so the comparison reads as comprehensive.

Also noted: **QKDNetSim+** (arXiv:2402.10822) found that nodes did not adequately process received key material and the crypto handler malfunctioned — **in exactly our layer.** Cite as motivation for an independent implementation. Other artifacts: `Open-QKD-Network/qkd-net` (MIT, real KMS), QNLab-USTC key-management framework (GPL-3.0), Quditto digital twin (*Appl. Sci.* 14:1018).

---

## 3. What survives — the openings

Consolidated across all five agents. Only these are defensible.

**O1 — Fail-degraded vs fail-closed is an unresolved contradiction in the literature.** ITU-T Y.3803 Req_KM 7 **standardises** AES fallback on key insufficiency; Makris et al. field-demonstrate it; Spooren et al. (QCNC 2026) **deliberately fail closed** and call the same transition a **downgrade attack**. Nobody has quantified the trade-off. *This is the strongest surviving research question and it is a genuine tension, not a manufactured gap.*

**O2 — The adversary's cost to force a downgrade.** Schartner & Rass (2010) observed that an adversary who cannot steal keys will DoS to *force* classical crypto. No work measures how cheaply that can be done. Li et al. have `maxNAR` (worst-case affected requests) but nothing grade-aware. A **downgrade-forcing cost** metric — adversary effort per unit of traffic pushed below ITS — is an *attack-economics* metric, not a service metric, and I found no equivalent.

**O3 — Grade as a delivered, per-request attribute.** No verified work carries the grade **back to the consuming application** as a first-class attribute. QuLore decides internally and never exposes it; Zhu's grade is a modelling variable; ETSI 014 has no provenance field (its own vendor-extension example is `route_type: direct|indirect`, which is *adjacent to exactly this*). Y.3803 records the method in **KMA metadata** — so the information exists at the KMS and is not surfaced. **Verify against final ETSI 014 V1.1.1 and 020 text before asserting the gap.**

**O4 — Terrain-correlated, bursty, spatially-correlated outage on FSO relay chains.** Every attack model found uses Poisson/i.i.d. arrivals. Real contested outage is bursty and correlated across hops sharing a valley or weather cell. No paper couples terrain-driven LOS/weather outage to trusted-relay key-pool dynamics. *Uniquely aligned to DEAL — founded as the Himalayan Radio Propagation Unit, currently fields a Compact Transhorizon Communication System.*

**O5 — Joint sweep of adversarial pressure × relay-chain depth.** Li sweeps nothing (single worst-case placement); Ghorab sweeps pervasiveness on multipath; Hafeez sweeps jamming on a mobile mesh. Nobody sweeps pressure against **hop count**, where each hop is simultaneously a key-rate bottleneck *and* a compromise surface — and the +30–60% multipath key penalty makes that trade quantitatively interesting.

**O6 — Reproduce and explain van Duijn's null result.** They found resource-aware routing variants statistically indistinguishable under centralised routing and recommended cheap SPF+. Reproducing that null and identifying what breaks it (contested conditions? a grade-aware objective?) is a strong, honest, reviewer-respected contribution. *A reviewer who knows this paper will ask why our policies separate at all — we must answer pre-emptively.*

**O7 — Learned grade-selection policy under a hard constraint.** Learned *routing* is saturated; learned *admission* is saturated; learned **cryptographic-grade selection driven by ITS-key-reservoir exhaustion, per traffic class, in a multi-hop relay** is not. Closest is Premakumari et al. (action = encryption level, driven by threat classifier, no QKD).

---

## 4. Reframed thesis

**Old (dead):** *"We propose a key-economy model, compare key-aware routing policies, and add a graded PQC fallback."* — every clause pre-empted.

**New (defensible):**

> Standards permit a QKD network to fall back to symmetric or post-quantum key supply when quantum key is insufficient (ITU-T Y.3803 Req_KM 7), and field deployments do exactly that. A parallel line of work rejects this, treating the same transition as a downgrade attack to be prevented by failing closed. We quantify this trade-off for contested multi-hop trusted-relay networks: we model terrain-correlated bursty outage on relay chains, sweep adversarial pressure jointly against chain depth, and measure both the availability gained by fail-degraded operation and **the adversary's cost to force a given fraction of traffic below information-theoretic security**. We show under which conditions labelled degradation dominates denial, and report the grade composition of served traffic as an operator-facing indicator absent from current QKD resilience standards.

Contribution list to write against:
1. **Threat-aware degradation model** with the four-state link (§2.1) including classical-channel denial and QBER-invisible attacks, calibrated to published field measurements.
2. **Downgrade-forcing cost** — a new adversary-effort metric (O2), reported against chain depth and pressure (O5).
3. **Fail-degraded vs fail-closed quantified** (O1), with the per-flow minimum-grade authorisation model that neither position currently specifies.
4. **Terrain-correlated correlated-outage model** for FSO relay chains (O4).
5. Reproduction of the van Duijn null and identification of the regime that breaks it (O6).
6. *(Conditional, gated)* policy-space audit of the heuristics (O7, §5).

**Title candidates:**
- *Forced Downgrade: The Adversarial Cost of Fail-Degraded Key Supply in Contested Multi-Hop QKD Networks*
- *Fail-Closed or Fail-Degraded? Quantifying Security-Grade Loss in Tactical Trusted-Relay QKD Networks*

**Terminology discipline (all verified):**
- **"Hybrid" means simultaneous combination via a key combiner, secure if at least one component is unbroken** — draft-ietf-tls-hybrid-design §1.2 (read verbatim `[V]`), NIST SP 800-227 §4.6. **A QKD→PQC substitution is NOT hybrid.** Call it *fallback substitution* or *labelled grade downgrade*. Our Grade B (combined) is legitimately hybrid — but use an **approved, domain-separated combiner** with an explicit delimiter, not a bare XOR.
- **Do not use "security level"** — it already means *key length/quantity* in QKD KMS work (DDKA-QKDN `Sec` 0–5) and *key-update period* in the RWTA literature (Sharma 2023). Use **"assurance grade"** or **"key-supply grade"** and define it on first use.
- Never write "novel metric" unqualified for grade composition — Zhu 2025 has `ρ_k,t`. Write: *"named as a design concern [Dervisevic], instantiated as per-class policy [Tysowski], observable at the key store [Doering], but not reported as a quantitative network indicator against swept adversarial pressure."*

---

## 5. AI strategy — decision

**Rejected:** (a) DRL routing/admission vs our heuristics — *actively harmful*, invites comparison with Johann 2026 (GAT-DRL, topology generalisation, +18.7%) which we lose. (c) learned reservoir forecasting — cheapest and weakest; in a simulator we wrote, reservoir dynamics are a deterministic function of our own arrival process, so **the circularity objection is not arguable, it is true**. (e) MORL Pareto front — the deliverable is obtainable by sweeping one heuristic threshold in an afternoon; anything a parameter sweep produces was never an ML contribution.

**Adopted (gated): policy-space audit — learned policy as heuristic *auditor*, not replacement.** One subsection, ~1.25 pages, one table, one figure. The claim is deliberately narrow and falsifiable:

> Within model M, the hand-designed heuristics attain X% of the best policy discoverable in M under a hard constraint on command traffic; where the learned policy exceeds them, we extract the responsible rule.

Design: joint action `(next_hop, admit ∈ {accept, defer, reject}, grade ∈ {G_ITS, G_QKD-AES, G_hybrid, G_PQC})` — **the grade action is the whole point; drop it and we collapse into option (a) and lose.** Hard **shield** (deterministic action mask: command traffic never below `G_QKD-AES`; no action may drive a reservoir below the reserve floor guaranteeing command continuity for horizon H) — concede up front that the guarantee comes from the shield, verifiable by inspection, and that learning only searches inside it. Tabular Q-learning or a 2-layer DQN over aggressively discretised state; **no GPU**. Distil via VIPER/DAGGER into a CART tree of depth ≤4 and **print the tree in the paper** — an operator-readable rule set is the artifact a DRDO reviewer will actually value. Evaluate **out-of-distribution, not nominal**: SKR ×{0.25, 0.5, 1, 2}, shifted demand/burstiness, single and dual link failure, one compromised node. **If the heuristic degrades more gracefully than the learned policy, publish that** — it is a stronger and more credible result than any win, and it directly answers circularity. Mandatory ablation: shielded vs unshielded learner ⇒ **the price of the command-traffic guarantee**, a systems number only the ML apparatus produces.

Baselines: primary is **our own tuned heuristics**; mandatory secondary is **key-aware weighted shortest path**, not plain Dijkstra — beating unweighted SPF in 2026 is a strawman and will be named as one. Position explicitly against Johann 2026 and Hao 2025 in related work, not defensively in rebuttal.

Circularity, addressed rather than dodged: **change the quantifier** (a claim about our design's headroom within M, not about the world — the same epistemic status as every other simulation result in the paper, and that parity is the argument); **make the model's fragility the experiment** (the OOD grid measures how much of the result is the simulator); use the accepted **digital-twin** vocabulary and cite arXiv:2310.09299 / IEEE 10711852; anchor every parameter to a standard or a measurement; and **never claim deployment readiness**.

**HARD GATE:** if the systems results are not complete with ≥1 week to spare, **cut the ML section entirely and ship the systems paper.** The ML must never sit on the critical path. Rationale: a thin fourth contribution reduces the perceived quality of the first three, and reviewers reject on the weakest section more often than they accept on the strongest.

---

## 6. Retrieval queue — before any submission

**Blocking (could still change the verdict):**
1. ~~**"Joint Routing and Relay Key Allocation in QKD Networks for Communication Security"**~~ — **ADJUDICATED, no longer blocking.** computer.org/csdl/journal/nw/…/11222830 (IEEE, in press). Its objective is **minimising attack success probability** via joint routing + relay key allocation — a *confidentiality / trusted-node-compromise exposure* metric, structurally like Li et al.'s `maxNAR`. Confirmed to cover: multi-hop trusted relay, OTP hop-by-hop relay, relay-key availability constraining routes, relay-key allocation across routes affecting security, per-pair service-key-rate demand, trusted nodes with insufficient relay key rate. **Does not** cover PQC fallback, grade downgrade, fail-degraded vs fail-closed, swept adversarial pressure, or per-class grade composition.
   ⇒ **Further kills C1/C2; does NOT touch the reframed thesis (O1/O2).**
   ⚠ **But it weakens O5:** it reports that "adding more trusted nodes … beyond the minimum requirement may not continue to reduce significantly the attack success probability" — a diminishing-returns result on **trusted-node count vs security**. That is not pressure × chain-depth, but it is adjacent enough that we must cite it and differentiate explicitly (our axis is *grade loss under swept pressure*, theirs is *compromise probability vs node count*). Full text still unfetched (csdl 403) — retrieve before writing related work.
2. **Cheng/Sun/Ji, AIAI 2011** — if QKRA reports class-level blocking with per-class floors, C2b is unrecoverable.
3. ~~**Tysowski et al., QST 3(2):024001, 2018**~~ — **RESOLVED. Full text read** (arXiv:1712.02617, 34 pp, doi:10.1088/2058-9565/aa9a5d). Three findings, one of which changed the paper:
   - **It states BOTH branches of our fork, under policy control:** *"When the quantum key pool is exhausted, it falls back to key derivation if allowed by the policy, **or blocks the host**"*; and *"if the performance of this process is deemed insufficient or is interrupted, then another crypto-system can be utilized as a **fall-back mechanism if allowed by the security policy** … quantum-safe, or even a classical, algorithm … while its implementation maintains the same interface to the KMS layer."* ⇒ **The architecture of the fail-degraded/fail-closed choice is 2018 prior art and must be credited.** The paper's introduction now does so explicitly and narrows our claim to the *measurement*.
   - **No empirical evaluation.** Full-text grep: `simulat` = 0, `measured` = 0. It is a design specification. ⇒ **C3c survives**; the FA column of the positioning table stays empty.
   - ⚠ **Do NOT attribute "five client security categories" to this paper.** That came from the Dervisevic survey's characterisation and is **not** in the text: the only categories present are **three raw-key-buffer categories** in the temporary key pool manager. Correct line 88 above accordingly before citing.
   - Bonus for §V-A: *"If the costs limit the key generation rate to a level that cannot meet the expected demand, the security policy may need to be sufficiently relaxed to allow the re-use of key material"* — supports the finding that an OTP authorisation floor is unfundable at current free-space rates.
3b. ~~**Lydersen et al., Nature Photonics 4, 2010**~~ — **RESOLVED** (arXiv:1008.4593; *Nature Photonics* 4(10):686–689; doi:10.1038/nphoton.2010.214). Full author list: Lydersen, Wiechers, Wittmann, Elser, Skaar, Makarov. ⚠ The abstract's exact claim is *"tracelessly acquire the full secret key"* — it does **not** say "without raising QBER". The paper now quotes "tracelessly" and marks the QBER-invisibility as **our inference** from the mechanism, not their wording.
4. **Johann, JOCN 16(3):382–391, 2024** — direct C2a competitor, abstract only.
5. **ITU-T Y.3831 (12/2025)** "Integration of QKD network and user networks supporting end-to-end modern cryptography services" — may already define graded/negotiated key-supply modes.
6. **ETSI GS QKD 014 V1.1.1 and GS QKD 020 final text** — O3 rests on the absence of a grade/provenance field. **Cite no clause number not personally read.**
7. **James et al., ARES 2023** full text (10.1145/3600160.3605050) — the policy-permitted-fallback passage is snippet-only.
8. **NATO STO:** drone-FSO-QKD-routing model; MuQuaNet military KMS study; Marchsreiter & Sepúlveda hybrid encryptor. All 403 to automated fetch.
9. **Zhu, arXiv:2510.14838** (SCADA key-aware reconfiguration) — read in full; closest systems analogue in another vertical.
10. **Patents:** US 11,930,101 (mitigating key exhaustion), US 11,652,620, US 11,652,619, US 12,375,266; evolutionQ July-2025 filing on end-to-end multi-hop QKD. Read independent claims via Google Patents.

**Non-blocking but wanted:** Yu et al., *JLT* 40(12):3530 (SKP-CR, +62%); Cao et al., *JSAC* 39(9):2701 (hybrid trusted/untrusted relay); Cao et al., *JOCN* 11(3):67 (protection against link failures); Zhang et al., *IEEE TNSM* 2023 (RCKA); Dervisevic et al., *JOCN* 16(4):449 (large-scale QKD network simulator — **likely the simulator baseline a reviewer demands**); Mehic et al., *ACM CSUR* 53(5) DOI 10.1145/3402192; Seok et al. JNSM 2025; Zuo et al. ACP 2020 T3C.6; PIB PRID 2136702; Schmitt-Manderbach's LMU dissertation (for the missing 144 km QBER); Luykx & Paterson ePrint 2024/051 (for the 389 GB figure).

**Unresolved discrepancies to settle:** Mehic ToN volume/issue; the 89% vs 98% key-rotation figure (WiN-Lab attributes 89% to Makris, who state 98% for "QKD **or classical**"); the Hao et al. "45.8 vs 118.5" snippet; whether arXiv:2405.04113's 14 kbit/s is secret or raw key rate; arXiv:2507.09288's year (fetch said July 2024, the ID says July 2025).
