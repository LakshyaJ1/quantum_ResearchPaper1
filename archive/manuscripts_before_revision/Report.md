# WiCOMM-2026 — Research Topic Selection Study
### A multi-agent research assessment of Tracks 2, 4 and 5, optimised for a software / AI-ML researcher

**Prepared for:** Ayushmaan Singh Naruka (AI Engineer, HivePro; B.Tech AI&ML, NCU)
**Date:** 3 August 2026
**Target venue:** IEEE WiCOMM-2026, DEAL (DRDO), Dehradun — 30–31 October 2026
**Scope:** Not a paper. A decision document: which topic to write, why, and how to win with it.

---

## 0. Executive summary — read this first

### 0.1 The hard constraint that changes everything

The **extended submission deadline is 5 August 2026**. You have roughly **48 hours**, not 8 weeks. Every recommendation below is therefore split into two answers:

| Question | Answer |
|---|---|
| **What is the best research topic for you at WiCOMM (research merit)?** | Terrain-aware learned radio-map / propagation surrogate for Himalayan tactical links (Idea #23), Hybrid QKD+PQC key orchestration for multi-hop tactical networks (#1), Neural speech-over-HF for code-mixed Indian tactical voice (#15) |
| **What can you actually submit by 5 Aug and still be proud of?** | PQC-over-tactical-links measurement study (#2), Channel-degraded keyword spotting / priority-voice triage (#16), or Open-set cross-domain drone-RF identification (#21) — all three are dataset-ready, compute-light, and produce real numbers in a day |
| **What should you do with the "best" ideas if the deadline holds?** | Write #23 / #1 / #15 properly over 6–10 weeks for IEEE MILCOM, NCC 2027, IEEE CONECCT, or a Q2 journal. WiCOMM is one venue; these ideas are worth more than one deadline. |

**Before you commit anything:** check the conference site for (a) any further extension — a 5-day-old "extended deadline" notice is often extended again, (b) page limit and template, (c) whether review is single- or double-blind, (d) student registration fee and whether physical presentation in Dehradun on 30–31 Oct is mandatory for inclusion in IEEE Xplore. It is almost certainly IEEE 2-column format, ~6 pages, submitted via Microsoft CMT (the CMT acknowledgement text is visible in your own screenshot of the site).

### 0.2 The five overall recommendations (detail in Part VI)

1. **#23 — Terrain-aware learned propagation surrogate for mountainous tactical link planning.** The only idea in this study that is simultaneously novel, purely software, uniquely Indian, and sitting exactly on DEAL's founding competence (the lab began life as the Himalayan Radio Propagation Unit).
2. **#1 — Hybrid QKD + post-quantum key orchestration for multi-hop tactical networks.** DRDO announced completion of military field trials of an indigenous fibre QKD system weeks ago and explicitly framed the next step as large-scale multi-hop quantum networks. You can do the multi-hop key-management/scheduling study in simulation, today, with zero photonics.
3. **#15 — Neural speech transmission over HF/VHF tactical voice channels, extended to code-mixed Indian speech.** Track 4 literally lists "Speech, Audio and Language Processing" and almost nobody at an RF conference will submit into it. Your strongest skill-to-track arbitrage.
4. **#3 — Federated / continual spectrum-awareness learning over DDIL tactical MANETs.** The defence-native version of a very hot ML problem, with an explicit, freshly-published gap to attack.
5. **#2 — Post-quantum cryptography on constrained tactical links: a crypto-agility and overhead study.** Lowest-risk high-value paper in the set; also the one most likely to be finishable before 5 August.

### 0.3 The three things that will actually decide acceptance

1. **Track fit signalled in the title.** DEAL reviewers are radio and SATCOM systems engineers. A title that reads like a machine-learning paper gets triaged as off-topic; the same work titled around the *communications* problem gets read. Write "Learned propagation prediction for mountainous tactical links" not "A novel attention-based UNet for regression on elevation rasters."
2. **A defence-relevant evaluation, not a defence-relevant sentence.** Almost every AI-for-wireless submission bolts a "this is useful for the military" paragraph onto a civilian benchmark. Very few actually evaluate under the conditions the reviewer cares about: jamming, low SNR, mountainous terrain, intermittent links, narrow bandwidth, no cloud, no GPU at the edge. Make that your evaluation axis and you differentiate instantly.
3. **Reproducibility and honesty.** Complete, modest, verifiable results beat ambitious unverifiable claims at this class of venue. State clearly what is simulated. Reviewers from a systems lab punish overclaiming harder than they punish small scope.

---

# Part I — Conference intelligence dossier

## 1.1 What WiCOMM-2026 is

Confirmed facts from DRDO's announcement: IEEE International Conference on **Wireless Communication for Military Applications**, hosted by **Defence Electronics Applications Laboratory (DEAL), Dehradun**, Conference Record No. **69954**, **technically co-sponsored by IEEE Uttar Pradesh Section**, in collaboration with the Society of Wireless Communication Engineers, **30–31 October 2026**, **physical/offline**, extended submission deadline **5 August 2026**.

What that combination implies:

- **IEEE technical co-sponsorship + a conference record number** means accepted, presented papers are normally submitted to **IEEE Xplore** (subject to IEEE's quality checks). That is real, indexed, citable publication value — the main career payoff here.
- **A lab-hosted, two-day, single-venue conference with an extended deadline** implies a submission pool in the low hundreds at most, a programme committee drawn largely from DEAL scientists plus Indian academia (IITs, NITs, DIAT, private universities) and IEEE UP Section volunteers, and an acceptance rate that is generous by international standards. Extended deadlines are a demand signal: they need good submissions.
- **"For Military Applications" in the title is not decoration.** It is the primary novelty filter. Two papers of equal technical quality will be separated by which one is legible as a defence contribution.

## 1.2 Who reviews you — DEAL's actual mandate

This is the single most exploitable piece of intelligence in this study. DEAL's published technology charter is: <cite index="151-1">satellite communication and surveillance, software radios, data links, microwave and millimetre-wave communication, satellite image reception and processing, and troposcatter communication systems</cite>. The lab <cite index="154-1">began in 1965 as the Himalayan Radio Propagation Unit before being renamed DEAL in 1976, and its historic mandate includes jam-resistant data links for real-time transmission of battlefield information, control of airborne platforms, target tracking and acquisition, and reconnaissance/surveillance from remotely piloted vehicles</cite>.

Recent, verifiable DEAL/DRDO activity that tells you what is *live* in the building:

- <cite index="155-1">DEAL conducted successful field trials of a compact software defined radio (SDR) and a large-hop terrestrial backhaul communication system in the Joshimath area of Uttarakhand, coordinated with MHA and central armed police forces</cite>; <cite index="156-1">its Compact Transhorizon Communication System is a portable terminal that uses a troposcatter path for over-the-horizon, high-capacity links in narrow high-mountain terrain, aimed at connecting command and tactical levels where terrain and disasters break normal networks</cite>.
- <cite index="158-1">DEAL is leading development of a SATCOM-based datalink waveform for Tejas Mk2 and AMCA, with an EoI issued to Indian firms specialising in software-defined radios, waveform design and digital communication</cite>.
- <cite index="231-1">DRDO has completed military field trials of a scalable fibre-based QKD system with Taqbit Labs and describes the milestone as laying the foundation for large-scale, multi-hop, indigenously designed quantum networks</cite>, following <cite index="227-1">a DRDO–IIT Delhi free-space entanglement-based quantum secure communication demonstration over more than 1 km achieving roughly 240 bits/s secure key rate at under 7% quantum bit error rate</cite>.

**Translation into strategy.** Papers that touch *mountain/terrain propagation, SDR and waveform intelligence, jam resistance, SATCOM and data links, spectrum awareness, and quantum-safe key distribution* are speaking the host lab's native language. Papers about, say, RIS-assisted cell-free massive MIMO sum-rate maximisation in an urban microcell are technically fine and institutionally invisible.

## 1.3 Career value calculus (honest version)

| Dimension | Assessment |
|---|---|
| Indexing | Likely IEEE Xplore + Scopus/Google Scholar. Strong for a first-author conference paper as an intern/early-career researcher. |
| Prestige tier | Regional IEEE conference. Below MILCOM/ICC/GLOBECOM/INFOCOM; comfortably respectable; excellent as *first* publication. |
| Strategic value for you specifically | High and asymmetric: it builds a **defence-communications publication record inside India**, which is the single most useful credential if you ever want DRDO/DIA-CoE collaboration, defence-sector AI roles, or an Indian PhD/fellowship in this area. It also pairs unusually well with your cybersecurity employer context. |
| Citation expectation | Low (typical for regional conference). Optimise for credential + relationship-building + a follow-on journal version, not citations. |
| Best play | Treat the WiCOMM paper as **v1 of a two-step**: conference paper now, extended journal/MILCOM version later with hardware-in-the-loop or real measurements. Say so in your own plan, not in the paper. |

## 1.4 Open questions you must resolve on the site (do not guess)

1. Further extension of the 5 Aug deadline? 2. Page limit (assume 6, IEEE conference template). 3. Blind or non-blind review. 4. Student registration fee + mandatory in-person presentation. 5. Whether "Track" must be declared at submission (it usually is — and your track choice matters more than your abstract; see Part IV, Finding 7).

---

# Part II — Method: the multi-agent research team

I ran this as ten specialised analyst roles over authoritative sources (IEEE Xplore/ComSoc, ACM DL, ScienceDirect/Elsevier, Springer, Nature portfolio, arXiv, MDPI, NVIDIA Research, NIST, 3GPP-tracking literature, DRDO/DEAL public communications, and industry material from Boeing/Viasat/ZTE/Ericsson-adjacent publications).

| Agent | Role | Primary output |
|---|---|---|
| **A1 Venue & Reviewer Intelligence** | Reconstruct the venue, host-lab mandate, review pool, and implicit acceptance function | §1.1–1.4, Finding 7 |
| **A2 Track-2 Analyst** | ML for comms, military 5G/B5G/6G, SDN, quantum, cyber & crypto | §3.1 |
| **A3 Track-4 Analyst** | Cognitive radio, channel modelling/NGMA, adaptive SP, speech/audio/language, digital beamforming, anti-jamming & PLS, underwater | §3.2 |
| **A4 Track-5 Analyst** | Antennas, phased arrays, metasurfaces/RIS — isolating the software-tractable subspace | §3.3 |
| **A5 Saturation & Bibliometrics** | Publication volume, topic maturity, incremental-paper detection, benchmark critiques | Competition ratings |
| **A6 Defence Foresight** | DRDO/DEAL priorities, DDIL/EW trends, allied programme signals, 2026–2035 outlook | Defence-relevance ratings |
| **A7 Tooling & Feasibility** | Datasets, simulators, licences, compute cost, time-to-first-result | Complexity ratings, Appendix A |
| **A8 Career & Impact** | Follow-on potential, journal extensibility, employability signal | Career-impact ratings |
| **A9 Red Team (adversarial reviewer)** | Attack each idea as a hostile Reviewer 2 from a systems lab | Kill-risks in each card |
| **A10 Synthesis & Ranking** | Weighted scoring, leaderboards, execution plans | Parts V–VII |

### Scoring rubric

Each idea is scored 1–10 on six axes, then combined:

**WiCOMM Fit Score = 0.22·Defence-Relevance + 0.20·Feasibility(software, ≤10 weeks) + 0.18·Novelty + 0.15·AcceptanceProbability + 0.15·Skill-Alignment + 0.10·Future-Impact**, with **Competition** applied as a modifier (High = −0.5, Medium = 0, Low = +0.5).

Feasibility is scored *for you specifically*: Python/PyTorch, LangGraph/agentic systems, RAG, FastAPI, cybersecurity domain fluency, no RF lab, no anechoic chamber, no SDR hardware assumed, single GPU or Colab/Kaggle class compute.

Acceptance-probability figures throughout are **structured estimates**, not measured rates. Base assumption: a lab-hosted, IEEE-technically-co-sponsored, first-generation conference with an extended CFP typically accepts somewhere in the 50–70% range; strong track fit + defence-framed evaluation + complete results pushes a competent paper to the 75–90% band; hardware-mismatched, civilian-framed, or incomplete work falls to 25–45%.

---

# Part III — Landscape analysis: subtopic-by-subtopic

Legend — **Sat.** = topic saturation (H/M/L), **Comp.** = expected competition at WiCOMM, **Def.** = defence relevance to DEAL, **Feas.** = feasibility for a software/AI researcher, **Verdict**: ✅ target / ⚠️ conditional / ❌ avoid.

## 3.1 Track 2 — Computing Technologies and Applications

| Subtopic | State of the art & recent breakthroughs (3–5 yrs) | Open problems | Sat. | Comp. | Def. | Feas. | Verdict |
|---|---|---|---|---|---|---|---|
| **Machine Learning for Communications** | The centre of gravity of the whole field. Standardisation has caught up with research: <cite index="52-1">3GPP studied AI/ML for the NR air interface in Rel-18 covering CSI feedback, beam management and positioning, then in Rel-19 specified signalling and life-cycle-management mechanisms for AI/ML-based beam management and positioning for both UE-sided and network-sided models</cite>, and <cite index="53-1">Release 20 focuses on specification support for CSI compression with two-sided models, including model-pairing handshake and data collection, while addressing inter-vendor training collaboration</cite>. <cite index="50-1">Rel-20 also opens the formal 6G study phase, pushing toward a natively AI-hosting air interface aligned to ITU IMT-2030</cite>. Differentiable toolchains matured: <cite index="97-1">Sionna now ships as RT (standalone differentiable ray tracer), PHY (link-level) and SYS (system-level) modules, all modular and differentiable</cite>. | Generalisation across environments; data collection and labelling; complexity/energy at the edge; two-sided model interoperability; **sim-to-real gap** (the recurring reviewer question); life-cycle management and model drift; robustness under adversarial and contested conditions | H | H | H | H | ⚠️ Only with a defence-specific twist. Generic "DL beats classical estimator on a 3GPP TDL channel" is a rejection risk by saturation. |
| **Military usage of 5G/B5G/6G** | Defence integration of commercial stacks is now an industry programme, not a concept. <cite index="217-1">Viasat's April 2026 tactical offering treats SATCOM, 5G, MANET and legacy tactical radios as interchangeable pipes under software-defined orchestration for denied, degraded, intermittent and limited-bandwidth (DDIL) environments, with automated failover and connectivity maintained through EW and cyber attack</cite>. 3GPP work items increasingly carry public-safety/mission-critical relevance: <cite index="54-1">Rel-20 includes ProSe UE-to-UE multi-hop, NTN integration into the 5G architecture, AI/ML enhancements, ISAC and Ambient IoT, with a 6G system-architecture study underway</cite>. | Priority/preemption for C2 traffic under contention; slice assurance under jamming; multi-transport orchestration policy learning; offline/air-gapped operation; identity and zero-trust in disconnected states | M | M | **Very high** | H | ✅ Strong lane, under-served by academics who lack the defence framing |
| **Software Defined Networking** | Classic SDN is mature; the frontier moved to O-RAN RIC/xApps, intent-based networking and network digital twins. Digital-twin-assisted learning for space/tactical networks is active — e.g. digital-twin-assisted federated quantum DRL for inter-satellite-link routing under smart jamming. | Safety and verification of learned control loops; twin fidelity vs. cost; twin-to-reality transfer; policy conflict resolution between xApps; SDN for QKD control planes (ETSI GS QKD 015 defines an SDN control interface — barely explored in defence contexts) | M | L–M | H | H | ✅ Especially "learned control loop + safety/verification" or "digital twin fidelity quantified" |
| **Quantum Communications and Computing** | Two very different sub-lanes. (a) *Physics/photonics* — hardware, out of scope for you. (b) **Quantum networking as a systems/software problem** — this is wide open and India-timely. DRDO's own trajectory: 2022 intercity link, 100 km fibre QKD, <cite index="227-1">>1 km free-space entanglement-based link at ~240 bit/s and <7% QBER</cite>, and <cite index="231-1">completed military field trials of a scalable fibre QKD system with an explicit goal of large-scale multi-hop quantum networks</cite>. Mature open simulators exist (NetSquid, SeQUeNCe, QuISP, QKDNetSim/ns-3), and standards define integration points (ETSI GS QKD 014/015). | Multi-hop trusted-node key routing and scheduling; key-rate-aware QoS; hybrid QKD+PQC key delivery across domains; key management under link outage/jamming; SDN control of QKD networks; cost of trust assumptions | **L** | **Low** | **Very high** | H (pure simulation) | ✅✅ Best "blue ocean" in Track 2 |
| **Cyber Security and Cryptography** | PQC has moved from research to mandate. <cite index="121-1">NIST finalised FIPS 203 (ML-KEM), FIPS 204 (ML-DSA) and FIPS 205 (SLH-DSA) on 13 August 2024, with ML-KEM public keys of 800–1568 bytes, ML-DSA signatures of 2420–4595 bytes, and SLH-DSA signatures of 7856–49856 bytes</cite>. <cite index="119-1">HQC was selected as a fifth, code-based backup KEM in March 2025</cite>, <cite index="116-1">FIPS 206 (FN-DSA) is in progress and explicitly aimed at bandwidth-constrained applications, expected 2026–2027</cite>, and <cite index="123-1">in May 2026 NIST advanced nine additional signature algorithms to a two-year third-round evaluation, making crypto-agility rather than single-algorithm deployment the operational requirement</cite>. Separately, adversarial ML against wireless AI is an established threat class: <cite index="135-1">surveys document misclassification of AI-based channel estimation and signal classification via noise perturbation, plus new 6G threat vectors including malicious agents in federated learning and adversarial attacks on O-RAN near-real-time RIC xApps</cite>, and <cite index="137-1">experimental work on data poisoning of DRL-based xApps using an O-RAN dataset from the Colosseum emulator reports backdoor attack success rates up to 0.9 and demonstrates the attack on a live O-RAN-compliant near-RT RIC deployment</cite>. | PQC cost on narrowband/high-latency/lossy links (MTU fragmentation, handshake retries, rekeying under mobility); crypto-agility architectures; group/multicast rekeying for swarms; certification and attestation of AI models in the radio stack; realistic adversarial threat models with physical realisability; datasets | M (crypto) / M (adv-ML) | **Low–Medium** | **Very high** | **Very high** — your home turf | ✅✅ Highest strike-rate-per-effort area for you |

## 3.2 Track 4 — Communication and Signal Processing

| Subtopic | State of the art & recent breakthroughs | Open problems | Sat. | Comp. | Def. | Feas. | Verdict |
|---|---|---|---|---|---|---|---|
| **Cognitive Radios** (incl. spectrum sensing, AMC) | Extremely well-mined. Deep AMC has plateaued: dozens of architecture-tweak papers on the same benchmarks, and the field is now self-critical — <cite index="143-1">a 2026 review notes that public datasets frequently contain one modulation per capture with known centre frequency and simplified impairment models, which can overstate real-world readiness, and that many widely used datasets fail to report sampling rate, baud rate and other key signal characteristics</cite>; <cite index="146-1">others note the absence of a uniform dataset split, making cross-paper comparison unreliable</cite>. | **Realism and rigour, not accuracy**: co-channel/multi-signal captures, cross-dataset and cross-receiver generalisation, open-set (unknown emitter) rejection, calibrated uncertainty, honest benchmarking protocols, edge complexity budgets | **H (very)** | **H** | M | H | ❌ as "better AMC accuracy"; ✅ as "benchmark realism / open-set / generalisation" |
| **Channel Modelling & NGMA** | Learned propagation is a mature-but-still-open field. <cite index="159-1">RadioMapSeer is the foundational 2D path-loss benchmark (701 city maps × 80 transmitter positions = 56,080 maps at 5.9 GHz, 1 m resolution), and its main limitation is the absence of vertical information and multipath parameters</cite>; ICASSP ran dedicated outdoor (2023) and indoor (2025) path-loss radio-map challenges; recent work is explicit that <cite index="167-1">RT-supervised results should be understood as simulation-to-simulation surrogates rather than validation against real-world measurements</cite>. **The literature is overwhelmingly urban.** | **Terrain-dominated propagation** (mountains, diffraction over ridgelines, troposcatter), 3D/low-altitude airspace, cross-region transfer, physics-consistency, measurement validation, uncertainty bounds for link planning | M | **L** | **Very high** (DEAL's origin discipline) | H (open DEMs + Sionna RT / ITU-R models) | ✅✅ Best "blue ocean" in Track 4 |
| **Adaptive Signal Processing** | Model-based deep learning, neural receivers, learned equalisation; strongly served by differentiable simulators. | Robustness under mismatch; complexity; adaptation speed under fast fading and hostile interference | H | M | H | H | ⚠️ Good only if paired with a specific hostile-channel scenario |
| **Speech, Audio and Language Processing** | Two mature ecosystems now intersect, and almost no one has joined them for defence. (a) *Neural speech over radio*: <cite index="193-1">RADE is a neural codec for transmitting speech over HF radio channels, evaluated against Codec 2, using ITU-R F.1487 ionospheric channel simulator conventions and Whisper-based assessment, with an open RADAE repository</cite>; the low-resource codec push is formalised — <cite index="188-1">the 2025 Low-Resource Audio Codec Challenge targets neural/hybrid codecs under strict compute, latency and bitrate constraints with robustness to noise and reverberation, noting that codec performance under these constraints and integration with speech enhancement remain largely unaddressed</cite>. (b) *Indian-language speech resources are now world-class*: <cite index="198-1">IndicVoices provides 12,000 hours of natural/spontaneous speech from 22,563 speakers across 208 districts and 22 languages, of which 3,200 hours are transcribed</cite>; <cite index="205-1">IndicSUPERB provides a 6-task speech-understanding benchmark across 12 Indian languages including ASR, speaker verification, query-by-example and keyword spotting, built on the 1,684-hour Kathbath dataset</cite>; <cite index="200-1">Vistaar aggregates 59 benchmarks and >10,700 hours of training data across 12 Indian languages and provides IndicWhisper models</cite>; <cite index="201-1">VAANI adds 2,043 hours across 105 languages from 28 states, and streaming Indian-language ASR with code-mixed support now exists</cite>. | Intelligibility (not PESQ) as the objective; code-mixed Hindi-English tactical speech; very low bitrate + fading + jamming; ASR-in-the-loop evaluation; on-device complexity; keyword/priority-message triage on degraded voice; speaker ID under channel shift | **L (for the intersection)** | **Very low** | High (voice is *the* tactical service) | **Very high** — pure ML+audio | ✅✅✅ Your single biggest arbitrage |
| **Digital Beamforming Technology** | AI beam management is now standardised (Rel-19), and the software side is well tooled (Sionna, DeepMIMO). | Beam prediction for airborne/high-mobility platforms; sensing/position-aided beam selection; overhead reduction; robustness to blockage and hostile interference | H | M | H | H | ⚠️ Viable but crowded; needs an airborne/UAV-datalink framing to matter here |
| **Anti-Jamming and Physical Layer Security** | The core DRL formulation is old and heavily replicated: <cite index="70-1">the spectrum-waterfall DQN approach (2018) learns anti-jamming strategies directly from raw spectrum without estimating jamming patterns</cite>, and the pattern has since been extended in dozens of directions (dual-action networks, GAN-enhanced DRL, game-theoretic hybrids, fast-frequency-hopping variants, PSO-DNN hybrids). Covert/LPD communication is dominated by information-theoretic analysis (Bash's square-root law lineage) rather than software experimentation. | **Generalisation to unseen jammer policies** (almost everything is evaluated against the jammer families it trained on); offline/safe RL from logged spectrum; sim-to-real; standard benchmarks and reproducibility; **ML-based detection of LPI/covert waveforms** (dataset-scarce, ML-friendly, EW-relevant) | H (DRL anti-jam) / M (LPD detection) | M | **Very high** | H | ⚠️ Avoid "another DQN vs sweep jammer"; ✅ attack generalisation, benchmarking, or detection |
| **Underwater Communications** | Moderate volume, real tooling, low crowding. <cite index="112-1">DL-based OFDM receivers for underwater acoustic links are trained and tested on the measured-at-sea WATERMARK dataset</cite>; <cite index="109-1">complex-valued networks for UWA channel estimation evaluated on WATERMARK achieve near-optimal tracking while halving spatial resource use</cite>; <cite index="110-1">BELLHOP-based beam-tracing pipelines (with VirTEX and the World Ocean Simulation System) are the standard route to realistic UWA channel data for network simulation</cite>; semantic communication for underwater things is only now being framed (2026 surveys). | Extreme bandwidth scarcity → goal-oriented/semantic transmission; Doppler and rapid time-variation; dataset scarcity; energy limits; physics-informed learning and transfer | **L–M** | **Low** | High (naval/NPOL relevance) | M–H (WATERMARK + BELLHOP) | ✅ Genuinely under-contested |

## 3.3 Track 5 — Antenna, Phased Array & Meta Surfaces

**Strategic warning before the table.** Track 5 is where your risk profile inverts. Submission volume will be lower (good), but the reviewers will be electromagnetics and antenna specialists (bad, for a pure-ML paper). A learning paper here must be *EM-credible*: physically consistent channel/array models, correct terminology, and comparison against the classical method the reviewer already trusts. Submit here only with Idea #29 or #30, and only if you can show an EM-consistent setup.

| Subtopic | State of the art | Open problems | Sat. | Comp. | Def. | Feas. | Verdict |
|---|---|---|---|---|---|---|---|
| **Next-Generation Antenna Systems** | Hardware-dominated | — | — | — | H | **L** | ❌ Not your paper |
| **Flexible and Wearable Antenna** | Fabrication/materials | — | — | — | M | **L** | ❌ Not your paper |
| **Advanced Phased Array and Beamforming** | Mostly hardware + array signal processing. The software-tractable niche: **data-driven array health** — element-failure detection, calibration-error estimation and pattern recovery from measured/simulated patterns | Fault diagnosis with partial observations; graceful degradation; automated calibration; explainability for operators | M | L | **Very high** (AESA/AEW&C relevance) | M–H (simulate arrays in Python; no hardware needed) | ⚠️→✅ Viable, differentiated, and unusually well-matched to DEAL's radar/AEW&C world |
| **Meta Surfaces and Reconfigurable Intelligent Surfaces** | AI-for-RIS is heavily worked: <cite index="131-1">a 2026 survey reviews supervised, deep, reinforcement, federated, graph, transfer and meta learning across five RIS domains — channel estimation, sum-rate maximisation, energy efficiency, security enhancement and performance evaluation</cite>; <cite index="127-1">codebook-based frameworks were introduced specifically to cut the pilot-signalling overhead and model-dependency of channel-estimation-plus-passive-beamforming pipelines</cite>; foundation-model-aided DRL for RIS has appeared (2025). | Overhead-free control; low-bit and hardware-constrained phase control; **RIS for anti-jamming, covert and LPD links**; EM-consistent evaluation instead of idealised cascaded models; multi-RIS coordination | **H** | M | H | H (Sionna RT supports RIS) | ⚠️ Only with a defence objective (anti-jam/covert) *and* an EM-consistent channel; otherwise it reads as paper #4,001 |

---

# Part IV — Cross-cutting findings

**Finding 1 — The field's bottleneck has moved from accuracy to trust.** Across AMC, RF fingerprinting, radio maps and anti-jamming RL, the recurring critique in 2025–2026 literature is not "not accurate enough" but "not validated under realistic conditions, not reproducible, not generalising, and not honest about the simulation-to-reality gap." <cite index="143-1">Reviewers of AMC datasets flag oversimplified impairment models and missing signal parameters</cite>; <cite index="167-1">radio-map authors now explicitly label their work simulation-to-simulation rather than real-world-validated</cite>; <cite index="62-1">RF fingerprinting work documents that models achieving near-perfect same-day accuracy degrade substantially under day-to-day propagation drift</cite>. **Papers that make rigour their contribution are currently under-supplied and easy to defend in review.**

**Finding 2 — Domain shift is the universal open problem, and it is a software problem.** Cross-day, cross-receiver, cross-channel, cross-city, cross-environment: every single measurement-based wireless-ML task has an unsolved distribution-shift problem, and the toolkit (domain generalisation, self-supervision, test-time adaptation, physics-informed augmentation) is exactly your skillset. Nine of the Top 30 ideas exploit this.

**Finding 3 — Standardisation has created a two-year window on the "AI-native + security" seam.** AI is now *specified* inside the radio stack (Rel-19/Rel-20), which means attacks on and assurance of those AI components are no longer hypothetical. <cite index="137-1">Backdoored DRL xApps have already been demonstrated on a live O-RAN-compliant near-RT RIC with attack success rates up to 0.9</cite>. Very few researchers work at the intersection of *radio-stack AI* and *security engineering*. You work at a CTEM cybersecurity company. That is a defensible, rare positioning.

**Finding 4 — Post-quantum migration is now a compliance event, not a research curiosity — and nobody has properly measured it on tactical links.** <cite index="120-1">NIST's timeline runs from the FIPS 203/204/205 finalisations through HQC selection in March 2025 to the June 2026 executive order mandating accelerated, government-wide PQC migration for federal systems with binding deadlines</cite>, and <cite index="124-1">the operational bottleneck is identified as crypto-agility: protocols that hard-code algorithms or need firmware updates cannot pivot in relevant timescales</cite>. Tactical radio links — kilobit-per-second HF, high-latency SATCOM, lossy MANET multi-hop — are precisely the environments where kilobyte-scale keys and signatures hurt most, and precisely the environments nobody benchmarks.

**Finding 5 — The quantum lane is open in India specifically, right now.** DRDO has hardware momentum and has publicly declared multi-hop quantum networking as the next objective. The systems-level questions that come with multi-hop trusted-node networks (key routing, key-rate-aware admission control, hybrid QKD/PQC fallback, behaviour under link loss and jamming, SDN control planes) are answerable in open simulators by one person with a laptop. That mismatch between institutional priority and available software research is the definition of an opportunity.

**Finding 6 — Speech is the most mispriced asset in this CFP.** Track 4 explicitly invites speech, audio and language processing. The submitting population at a military-wireless conference is overwhelmingly RF/antenna/communications engineers. Meanwhile the tooling on your side is extraordinary: <cite index="198-1">12,000 hours of Indian-language speech</cite>, <cite index="205-1">a 12-language benchmark with keyword spotting and speaker verification tasks</cite>, <cite index="193-1">an open neural HF-radio speech codec with published channel-simulation methodology</cite>. You could be the only person in the room submitting there.

**Finding 7 — Track choice is a strategic decision, not a formality.** Same paper, different track, different outcome:

- **Track 2** — largest AI-literate reviewer pool, highest AI competition, most tolerant of a software-only contribution. *Default choice for ideas #1–#14.*
- **Track 4** — reviewers are DSP/comms engineers; they will demand a communications framing and correct signal-processing language, but the speech/underwater/PLS sub-lanes are thinly contested. *Choose for #15–#28; strongest expected-value per unit effort in the speech and underwater sub-lanes.*
- **Track 5** — smallest volume, highest reviewer mismatch risk for ML work. *Only #29–#30, only with EM-consistent modelling.*

**Finding 8 — What an accepted WiCOMM paper looks like (five archetypes).** Every one of the Top 30 is deliberately built as one of these:
1. *The measurement/benchmark study* — "we quantify X under conditions Y that nobody measured" (fast, safe, reviewer-friendly).
2. *The domain-shift fix* — "existing method collapses under realistic shift; here is a defensible remedy."
3. *The defence-scenario transplant* — "known technique, but formulated and evaluated for a contested/DDIL/terrain-limited military scenario."
4. *The systems-architecture + simulation study* — "here is an architecture for a capability the host lab is actively building, evaluated in open simulators."
5. *The threat-model paper* — "here is the attack surface of the AI we are now putting inside radios, plus a mitigation."

---

# Part V — The Top 30 ranked research ideas

Ranked by **WiCOMM Fit Score** (Part II rubric). Each card: problem → gap → contribution → method → tools → complexity → defence relevance → competition → acceptance estimate → career impact → future potential → the reviewer attack you must pre-empt.

Score notation: **N** novelty, **F** feasibility (software, for you), **D** defence relevance, **A** acceptance probability, **S** skill alignment, **I** future impact — each /10.

---

## 🥇 Idea 1 — Key-Rate-Aware Routing and Hybrid QKD/PQC Fallback for Multi-Hop Tactical Quantum Networks
**Track 2 (Quantum Communications) | Fit 9.3 | N 9 · F 8 · D 10 · A 8 · S 8 · I 9 | Competition: LOW**

- **Problem.** DRDO has a field-trialled fibre QKD system and has publicly named large-scale multi-hop quantum networks as the next objective. In a multi-hop trusted-node network, secret key is a *depletable, per-link, time-varying resource*. No one has treated "which flow gets key, over which path, when link key rates fluctuate or a hop goes down" as a schedulable network-control problem for tactical topologies.
- **Gap.** QKD literature optimises physical key rate per link; networking literature optimises throughput. The joint problem — key-rate-aware path selection, key-reservoir admission control, and graceful degradation to post-quantum key establishment when quantum key is exhausted or a trusted node is compromised — is barely studied, and essentially unstudied for mobile/contested topologies.
- **Novel contribution.** (1) A key-economy model for multi-hop tactical QKD (per-link key generation rate, reservoir state, per-flow security class). (2) Three control policies compared: greedy shortest-path, key-rate-aware weighted routing, and a learned (RL) scheduler. (3) A **hybrid fallback protocol** that degrades from QKD key to ML-KEM-based establishment with explicit security-class labelling, and a quantified availability/security trade-off curve. (4) Failure-mode analysis: node compromise, link outage, jamming of the classical channel.
- **Method.** Discrete-event simulation in **QKDNetSim (ns-3)** or **SeQUeNCe/NetSquid**; ETSI GS QKD 014/015 interfaces as the control-plane abstraction; **liboqs** for measured ML-KEM/ML-DSA cost; topologies modelled on realistic garrison-to-forward-post chains; metrics = key availability, secret-key-starved flow fraction, mean time-to-key, degradation events per hour, control overhead.
- **Tools/datasets.** QKDNetSim/ns-3, SeQUeNCe, NetSquid, liboqs/OQS-OpenSSL, Python. No physical hardware, no datasets required (parameterise link key rates from published DRDO/IIT-D figures: ~240 bit/s free-space at <7% QBER; fibre rates from literature).
- **Complexity.** Medium. 3–5 weeks for a strong paper; a 6-page version with two policies is achievable in ~10 days.
- **Defence relevance.** Maximal, and *timed*: it answers the question the host organisation has just publicly posed.
- **Competition.** Low. Very few groups combine quantum networking with tactical network constraints; almost none in India at conference level.
- **Acceptance estimate.** **85–90%** if the simulation is clean and the architecture diagram is legible to a systems engineer.
- **Career impact.** Very high. Positions you in India's highest-priority defence-tech lane with a credential no bootcamp can produce. Natural bridge to DRDO/DIA-CoE collaboration and to a journal extension.
- **Future potential.** 2026–2035 is exactly the QKD-network build-out decade; direct extension path to hardware-in-the-loop with a real QKD testbed.
- **Reviewer 2 attack to pre-empt.** "Your key rates are assumed." → State parameter provenance explicitly, run sensitivity sweeps, and frame the contribution as the *control policy*, not the physics.

---

## 🥈 Idea 2 — Post-Quantum Cryptography on Constrained Tactical Links: A Crypto-Agility and Overhead Study
**Track 2 (Cyber Security & Cryptography) | Fit 9.2 | N 7 · F 10 · D 10 · A 9 · S 10 · I 8 | Competition: LOW–MEDIUM**

- **Problem.** Tactical links are kilobits per second, high-latency, lossy and MTU-constrained. NIST's post-quantum standards ship keys and signatures one to two orders of magnitude larger than their classical counterparts, and federal migration is now mandated on binding deadlines. What that costs on an HF/VHF/SATCOM/MANET link — in handshake completion time, retransmissions, fragmentation, rekey cost under mobility, and battery — is undocumented.
- **Gap.** PQC benchmarking overwhelmingly targets TLS on the internet, browsers and CDNs. Nobody has systematically characterised PQC handshake behaviour across *tactical* link profiles, nor compared algorithm portfolios (ML-KEM vs HQC; ML-DSA vs SLH-DSA vs the forthcoming bandwidth-optimised FN-DSA) against a link-budget-driven cost model.
- **Novel contribution.** (1) A tactical link-profile taxonomy (HF 2.4 kbit/s, VHF combat net, SATCOM 500 ms RTT, multi-hop MANET with 5–20% loss). (2) End-to-end measured handshake cost per profile per algorithm suite, including hybrid X25519+ML-KEM. (3) A **crypto-agility cost model**: what an algorithm rotation costs operationally per profile. (4) Concrete design guidance: which suite for which link class, and where fragmentation/rekey policy must change.
- **Method.** `liboqs`/OQS-OpenSSL benchmarks on a laptop for compute cost; **ns-3 or Linux `tc`/netem emulation** for link profiles (rate, delay, loss, MTU); measure handshake completion CDFs, bytes-on-wire, failure rate under loss, rekey frequency under simulated mobility. Everything is reproducible on one machine.
- **Tools/datasets.** liboqs, OQS-OpenSSL/OpenSSL 3.x, ns-3 or netem, Python/pandas/matplotlib. **No dataset needed.** Zero acquisition risk.
- **Complexity.** **Low.** This is the one strong paper genuinely achievable in 36–48 hours by someone with your toolchain fluency.
- **Defence relevance.** Maximal and immediate — every Indian defence network faces this migration; harvest-now-decrypt-later makes it urgent for archived traffic.
- **Competition.** Low–medium. Crypto people don't model tactical links; radio people don't benchmark KEMs.
- **Acceptance estimate.** **85–92%.** Reviewers love a well-executed measurement paper with clean tables and actionable guidance, and there is no theory for them to dispute.
- **Career impact.** High and *directly monetisable* in your day job: PQC readiness is a live enterprise-security service line, and this is a publishable artefact you can point to.
- **Future potential.** Extends to group/multicast rekeying (Idea #12), to PQC-in-firmware constraints, and to a journal version with real SDR links.
- **Reviewer 2 attack.** "Emulation isn't a real radio." → Name it as emulation in the title/abstract, justify profiles from published waveform specs, and present the link-budget model so results transfer.

---

## 🥉 Idea 3 — Terrain-Aware Learned Propagation Surrogate for Mountainous Tactical Link Planning
**Track 4 (Channel Modelling) | Fit 9.2 | N 9 · F 8 · D 10 · A 8 · S 9 · I 9 | Competition: LOW**
*(Referred to as #23 in the executive summary's merit ordering; ranked here by composite fit.)*

- **Problem.** Tactical link planning in high mountains is dominated by terrain diffraction, ridgeline shadowing and troposcatter — the exact regime where fast statistical models are inaccurate and ray tracing is too slow for iterative planning across thousands of candidate site pairs. DEAL's own systems (compact SDR, transhorizon backhaul) are trialled in precisely this terrain.
- **Gap.** Learned radio-map/path-loss research is almost entirely urban and building-driven; the canonical benchmark is city-map based and lacks vertical/multipath information, and recent authors concede results are simulation-to-simulation surrogates. **Terrain-dominated, long-range, mountainous propagation with a defence link-planning objective is an open niche.**
- **Novel contribution.** (1) A terrain-conditioned neural surrogate that predicts path loss / link feasibility from public DEM tiles plus link geometry, trained against physics-based labels (ITU-R P.452/P.526 diffraction + ray tracing). (2) Evaluation on **cross-region generalisation** (train on one Himalayan sector, test on another) — the failure mode that matters operationally. (3) **Calibrated uncertainty** so a planner can ask "give me links with ≥95% confidence of closing," which is the actual military requirement. (4) 100–1000× planning-time speed-up quantified against the physics baseline.
- **Method.** SRTM/Copernicus 30 m DEM → terrain profile extraction → label generation via ITU-R diffraction models and/or Sionna RT on meshed terrain → CNN/UNet or transformer surrogate over profile+geometry features → deep-ensemble or quantile regression for uncertainty → cross-sector held-out evaluation → speed and accuracy tables vs. ITU-R baseline.
- **Tools/datasets.** SRTM/Copernicus DEM (open), GDAL/rasterio, ITU-R model implementations, Sionna RT (optional), PyTorch. All open, all free.
- **Complexity.** Medium-high (label generation is the long pole). 4–6 weeks for the full version; a reduced version (ITU-R labels only, single sector + cross-sector test) in ~2 weeks.
- **Defence relevance.** Maximal. This is the host lab's founding discipline, in the host lab's own terrain, for the host lab's current systems.
- **Competition.** Low. Almost nobody works terrain-dominated learned propagation, and nobody frames it for Indian mountain warfare logistics.
- **Acceptance estimate.** **85–90%.** Very high thematic resonance; low risk of a reviewer having a competing paper.
- **Career impact.** Very high. This is the idea most likely to start an actual research relationship with DEAL.
- **Future potential.** Extends to UAV/low-altitude 3D radio maps, troposcatter link prediction, drive-test/measurement validation, and an operationally deployable planning tool.
- **Reviewer 2 attack.** "You never validated against measurements." → Own it in the abstract, position as a *fast surrogate for a trusted physics model*, and add a measurement-validation section to the future-work roadmap.

---

## Idea 4 — Neural Speech Transmission over HF/VHF Tactical Voice Channels for Code-Mixed Indian Speech
**Track 4 (Speech/Audio/Language + Adaptive SP) | Fit 9.0 | N 8 · F 9 · D 9 · A 8 · S 10 · I 8 | Competition: VERY LOW**

- **Problem.** Voice is the primary tactical service and the hardest to carry: HF/VHF links give you a few kilobits per second through fading, noise and interference. Legacy vocoders sound robotic and degrade catastrophically at low SNR; neural codecs promise far better intelligibility per bit but are evaluated on clean English studio speech.
- **Gap.** The open neural-HF-radio codec line of work (RADE and relatives, evaluated against Codec 2 using standard ionospheric channel simulation) is English-centric and does not address (a) **code-mixed Hindi–English**, which is how Indian tactical voice traffic actually sounds, (b) intelligibility-first objectives, (c) hostile-channel robustness, or (d) edge compute budgets. The low-resource codec community itself states that codec behaviour under joint compute/latency/bitrate constraints and its integration with enhancement remain largely unaddressed.
- **Novel contribution.** (1) A joint source–channel neural speech pipeline evaluated on **Indian multilingual + code-mixed speech** at 1–3 kbit/s over simulated HF/VHF fading. (2) **ASR-in-the-loop intelligibility metric** (word error rate of a fixed recogniser on the received audio) as the primary objective instead of PESQ — much better aligned to mission utility. (3) Degradation curves under partial-band jamming and burst loss, versus a classical vocoder baseline. (4) Complexity/latency accounting for an edge radio.
- **Method.** Take an open neural codec / JSCC baseline; retrain or fine-tune on **IndicVoices/Kathbath/Vistaar** subsets (Hindi, Hindi-English code-mixed, plus 2–3 regional languages); channel simulation per ITU-R F.1487-style HF models plus AWGN/Rayleigh/partial-band jamming; evaluate WER with IndicWhisper + subjective MOS on a small panel; report MACs/latency.
- **Tools/datasets.** IndicVoices, Kathbath/IndicSUPERB, Vistaar benchmarks, IndicWhisper, RADAE/Codec 2 as baselines, PyTorch, GNU Radio optional.
- **Complexity.** Medium. 2–4 weeks; a keyword/intelligibility-only reduced version in ~1 week.
- **Defence relevance.** High: directly improves the service commanders actually use, on the links India actually fields, in the languages India actually speaks.
- **Competition.** **Very low.** You may be the only speech submission in the track.
- **Acceptance estimate.** **80–88%** — slight deduction only because DSP reviewers may want more channel-modelling rigour; fix by being scrupulous with the channel section.
- **Career impact.** Very high — a rare, defensible specialisation (defence speech comms for Indian languages) with obvious follow-on funding logic.
- **Future potential.** Enormous: semantic voice, on-device deployment, multi-speaker separation on a shared net, integration with SDR waveforms.
- **Reviewer 2 attack.** "Where's the communications contribution?" → Foreground the joint source–channel framing, bitrate/BER curves and link budget; keep the ML architecture in one subsection.

---

## Idea 5 — Federated and Continually-Learning Spectrum Awareness over DDIL Tactical MANETs
**Track 2 (ML for Communications) | Fit 8.9 | N 8 · F 8 · D 10 · A 8 · S 10 · I 9 | Competition: LOW–MEDIUM**

- **Problem.** Tactical nodes collectively observe a rich electromagnetic environment, but each node individually sees very little, cannot ship raw IQ to a server (no backhaul, and it leaks intelligence), and operates under denied/degraded/intermittent/limited (DDIL) conditions where standard federated learning assumptions break.
- **Gap.** Recent tactical-MANET learning work states the problem precisely: ML components in these systems are typically trained offline on curated datasets and deployed as fixed classifiers, with **no mechanism for nodes to collaboratively refine models against the evolving signal environment they jointly observe.** Meanwhile mainstream federated learning assumes a reliable parameter server and roughly synchronous rounds — neither exists here.
- **Novel contribution.** (1) A gossip/hierarchical federated protocol for spectrum-awareness models under intermittent connectivity and node churn, with **communication cost measured in bytes-on-a-tactical-link, not in rounds**. (2) Robustness to **non-IID observation** (each node sees a different local RF environment) and to a **malicious/poisoned participant** — the defence-critical case civilian FL papers skip. (3) Continual learning against distribution drift (new emitters appearing) with catastrophic-forgetting analysis. (4) An explicit accuracy-vs-overhead Pareto frontier a network designer can use.
- **Method.** Public IQ datasets (RadioML, RFUAV, DroneRF) partitioned non-IID across simulated nodes; mobility + link-availability traces from ns-3 (RWP/military mobility models); FL variants (FedAvg, gossip averaging, hierarchical) with Byzantine-robust aggregation; poisoning attack injected; metrics = accuracy, convergence time, bytes exchanged, degradation under 20–50% link availability, attack success rate.
- **Tools/datasets.** PyTorch + Flower or custom FL loop, ns-3 (mobility/link traces), RadioML 2018.01A, RFUAV/DroneRF.
- **Complexity.** Medium. 2–3 weeks.
- **Defence relevance.** Very high: distributed spectrum situational awareness without backhaul is a core JADC2-style requirement, and DDIL is the operative environment term in current industry practice.
- **Competition.** Low–medium (young, and the defence framing narrows it further).
- **Acceptance estimate.** **80–88%.**
- **Career impact.** High — combines federated learning, security and wireless: three hiring keywords in one paper.
- **Future potential.** Very high; extends to on-device continual learning, split learning over sidelink, and secure aggregation with PQC.
- **Reviewer 2 attack.** "This is FedAvg with a new story." → Make the *communication-cost accounting under real link constraints* and the *poisoned-node* result the headline contributions, not the aggregation rule.

---

## Idea 6 — Open-Set, Cross-Domain Drone RF Identification for Counter-UAS
**Track 4 (Cognitive Radio) / Track 2 | Fit 8.8 | N 7 · F 10 · D 10 · A 9 · S 10 · I 8 | Competition: MEDIUM**

- **Problem.** Counter-UAS is India's most acute near-term tactical problem. RF-based drone detection/classification reports 99%+ accuracy on public benchmarks — and then fails in the field on drone models it never saw, in the presence of Wi-Fi/Bluetooth clutter, on a different receiver, or with several drones transmitting at once.
- **Gap.** Benchmarks are saturated at ceiling accuracy under controlled single-emitter conditions; the documented failures are **cross-channel/cross-receiver domain shift** and **open-set rejection of unknown models**, with dataset diversity explicitly named as the limiting factor by the newest benchmark efforts.
- **Novel contribution.** (1) A **cross-dataset protocol** (train on DroneRF, test on DroneDetect/RFUAV and vice versa) that exposes the real generalisation gap — most papers never do this. (2) An open-set detector (energy/Mahalanobis/OOD scoring with calibrated thresholds) that rejects unseen platforms instead of confidently mislabelling them. (3) Interference-robust evaluation (Wi-Fi/Bluetooth present) and multi-emitter degradation curves. (4) Complexity budget for a deployable edge sensor.
- **Method.** Standard spectrogram/IQ front end; a modest backbone (deliberately not the contribution); domain-generalisation augmentations (receiver-gain, CFO, channel, SNR sweeps); open-set scoring with calibration; report closed-set vs cross-domain vs open-set metrics side by side, including AUROC for unknown rejection.
- **Tools/datasets.** DroneRF, DroneDetect(V2), RFUAV, optionally UAVSig; PyTorch; Kaggle/Colab GPU sufficient.
- **Complexity.** **Low.** Datasets are downloadable and small enough to train overnight. The most executable strong paper in the set alongside #2.
- **Defence relevance.** Maximal and topical.
- **Competition.** Medium (popular area) — but *the honest cross-domain/open-set framing* is what differentiates you from the accuracy-chasing crowd.
- **Acceptance estimate.** **80–88%.**
- **Career impact.** High; counter-UAS RF-ML is a hiring magnet in Indian defence-tech and in your own sector.
- **Future potential.** High: swarm separation, RF+acoustic+EO fusion, continual enrolment of new models.
- **Reviewer 2 attack.** "Accuracy is lower than published SOTA." → Pre-empt in the abstract: your point is precisely that published numbers do not survive domain shift; show the SOTA baseline collapsing under your protocol.

---

## Idea 7 — Doctrine-Grounded LLM Copilot for Spectrum Management and EW Planning (with a Benchmark)
**Track 2 (ML for Comms / Military 6G) | Fit 8.7 | N 9 · F 9 · D 9 · A 7 · S 10 · I 9 | Competition: LOW**

- **Problem.** Spectrum deconfliction, frequency assignment and EMCON planning at brigade scale are manual, expert-scarce, document-heavy tasks under time pressure — a natural fit for an agentic assistant, and a catastrophic fit for a hallucinating one.
- **Gap.** Telecom LLM research has exploded (domain-tuned models, RAG over standards, agentic network operations), but two things are missing: (a) **rigorous evidence that these agents can execute, not just talk** — a 2026 industrial benchmark reports that LLMs exceed 90% accuracy on linguistic interface tasks such as intent recognition and entity extraction while collapsing to roughly 30% on procedural execution tasks, i.e. competent diagnosticians but failing field engineers; and (b) **any defence-specific benchmark at all**.
- **Novel contribution.** (1) **SpectrumOpsBench** — a small, open, carefully-built benchmark of spectrum-management tasks (interpret an assignment table, detect a deconfliction conflict, compute a guard band, choose a hop set given a constraint list, refuse when data is missing). (2) A RAG + tool-calling agent architecture grounded in *open* regulatory/technical documents (ITU-R recommendations, published NFAP-style tables, open waveform specs), with a deterministic tool layer for the computational steps. (3) Quantified **hallucination and refusal behaviour** — the metric a military user actually needs. (4) An ablation showing which component (retrieval, tools, verification) buys the reliability.
- **Method.** LangGraph/agent framework you already use; open document corpus; 100–200 hand-built task items with gold answers; evaluate 2–4 models (including a small local model, since air-gapped operation matters); report exact-match, tool-invocation correctness, hallucination rate, appropriate-refusal rate.
- **Tools/datasets.** Your existing agentic stack, open documents only, small local model (e.g. 7–8B quantised) plus one API model for comparison.
- **Complexity.** Low–medium; benchmark construction is the honest work. ~2 weeks (or 3 days for a 60-item pilot).
- **Defence relevance.** High — spectrum management is a permanent operational bottleneck. **Critical framing rule: build a decision-support and verification tool, never an "AI that plans jamming."**
- **Competition.** Low at this venue; almost certainly zero competing submissions.
- **Acceptance estimate.** **72–82%** — the deduction is reviewer conservatism about LLMs; counter it by making *measurement of unreliability* the contribution rather than a demo.
- **Career impact.** Very high; it is exactly your professional profile (agentic systems + security + enablement) rendered as research.
- **Future potential.** High; benchmarks age well and get cited, and this generalises to any doctrine-constrained agentic decision support.
- **Reviewer 2 attack.** "LLMs are unreliable for military use." → Agree, in print. That is the finding. Report failure rates and a human-in-the-loop protocol.

---

## Idea 8 — Backdoor and Poisoning Resilience of AI Control Loops in the Radio Stack
**Track 2 (Cyber Security / SDN) | Fit 8.6 | N 8 · F 8 · D 10 · A 8 · S 10 · I 9 | Competition: LOW–MEDIUM**

- **Problem.** AI has been specified *into* the radio access network. Once a learned agent controls scheduling, beams or spectrum, its training data and model supply chain become attack surfaces for an adversary who never needs to jam anything.
- **Gap.** The threat is demonstrated but the defensive engineering is thin: published work shows data poisoning of DRL-based xApps achieving backdoor success rates up to 0.9, executed on a live O-RAN-compliant near-real-time RIC, and surveys identify adversarial attacks on RIC xApps and malicious agents in federated learning as distinctive 6G threat vectors. What is missing is a **deployable detection/attestation pipeline with measured cost**, especially under the assumption that the network is a military one where the model supply chain is not trusted.
- **Novel contribution.** (1) A threat model for learned radio-control agents in a military network (insider, supply-chain, tenant, external). (2) A layered defence: training-data provenance + model signing/attestation + behavioural anomaly detection on the agent's action distribution + a safe-fallback controller. (3) **Quantified defence overhead and detection latency**, i.e. can you catch a triggered backdoor before it damages the network. (4) Reproducible attack/defence harness released.
- **Method.** Lightweight RAN control simulator (or ns-3/open RIC-style loop) with a DRL scheduling/spectrum agent; implement trigger-based backdoor (SleeperNets/TrojDRL-style) and clean-label poisoning; implement action-distribution monitors, reward-anomaly detection and fallback; measure attack success, detection rate, false positives, latency, throughput cost.
- **Tools/datasets.** Python/PyTorch RL stack, ns-3 or a simplified RIC loop, optional public O-RAN/Colosseum-derived traces.
- **Complexity.** Medium. 2–4 weeks.
- **Defence relevance.** Very high, and unusually well-matched to your employer's CTEM worldview (exposure management applied to the radio stack).
- **Competition.** Low–medium.
- **Acceptance estimate.** **78–86%.**
- **Career impact.** Very high; "AI security for critical wireless infrastructure" is a scarce, well-paid specialisation and a natural HivePro-adjacent research identity (using only public data — see Part VIII).
- **Future potential.** Very high through 2035 as AI-native RAN ships.
- **Reviewer 2 attack.** "Your simulator isn't a real RIC." → Scope honestly, cite the published live-RIC demonstrations as motivation, and make the defence-cost measurement the contribution.

---

## Idea 9 — Generalisation-First Anti-Jamming RL: Beating Unseen Jammer Policies
**Track 4 (Anti-Jamming & PLS) | Fit 8.5 | N 8 · F 9 · D 10 · A 8 · S 9 · I 8 | Competition: MEDIUM–HIGH (but the angle is contested by almost nobody)**

- **Problem.** Learned anti-jamming agents are trained against a jammer family and evaluated against the same family. In the field, the jammer is adaptive, unseen and possibly also learning.
- **Gap.** The spectrum-waterfall DRL formulation has been replicated and decorated for eight years (dual-action networks, GAN augmentation, game-theoretic hybrids, fast-frequency-hopping variants). What is systematically missing: **held-out jammer generalisation**, standard benchmarks, and sample-efficiency/safety when learning online on a real radio.
- **Novel contribution.** (1) **JamGym** — a small open benchmark defining a training set and a *disjoint test set* of jammer policies (sweep, comb, reactive, pulsed, learning, cooperative multi-jammer). (2) Head-to-head evaluation showing standard DQN/PPO agents degrade sharply out-of-distribution. (3) A generalisation remedy: domain randomisation + jammer-population curriculum + meta-RL/context inference, with measured OOD gains. (4) **Offline-RL variant** trained purely from logged spectrum, since a deployed radio cannot afford exploratory failure — the operationally decisive point.
- **Method.** Gymnasium environment over a discretised time-frequency grid with configurable jammer policies; agents = DQN/PPO/recurrent PPO + CQL/IQL for offline; metrics = throughput/successful-transmission rate on held-out jammers, regret, adaptation time, catastrophic-failure count.
- **Tools/datasets.** Gymnasium, Stable-Baselines3/CleanRL, NumPy. Self-generated environment (no dataset risk).
- **Complexity.** Low–medium. 1.5–3 weeks; a 3-jammer pilot in ~4 days.
- **Defence relevance.** Maximal — jam resistance is DEAL's stated historical mandate.
- **Competition.** The *area* is crowded; the *generalisation-benchmark* framing is rare, and it converts crowding into an advantage (you have many baselines to beat honestly).
- **Acceptance estimate.** **78–86%.**
- **Career impact.** High; RL + EW is a distinctive combination, and a released benchmark accrues citations.
- **Future potential.** High; the benchmark becomes the reusable asset.
- **Reviewer 2 attack.** "Simplified spectrum model." → Justify the abstraction, keep it documented and reproducible, and show the *relative* ordering of methods is the claim.

---

## Idea 10 — Cross-Day and Cross-Receiver Domain Generalisation for Specific Emitter Identification
**Track 4 (Cognitive Radio / PLS) | Fit 8.4 | N 7 · F 9 · D 10 · A 8 · S 10 · I 8 | Competition: MEDIUM–HIGH**

- **Problem.** RF fingerprinting promises physical-layer authentication of transmitters — invaluable for detecting spoofed or unauthorised emitters on a military net. It works beautifully in-lab and degrades in deployment.
- **Gap.** Well documented and still open: deep SEI achieves near-perfect same-day accuracy but must generalise from a labelled source day to an unlabelled target day, where day-to-day propagation drift induces distribution shift and direct transfer degrades substantially; shortcut learning drives models to latch onto transient channel features instead of stable hardware fingerprints; and cross-receiver transfer fails similarly. Emerging directions include self-supervision, disentanglement, adversarial domain alignment and even LLM-assisted interpretable fingerprinting.
- **Novel contribution.** (1) A controlled study isolating *which* shift (day, receiver, channel, SNR) hurts most — rarely disentangled. (2) A physics-informed augmentation suite (CFO/IQ-imbalance/phase-noise perturbations that preserve hardware identity while destroying channel shortcuts) with an ablation proving it addresses shortcut learning. (3) Open-set verification framing ("is this the enrolled radio?" with FAR/FRR) rather than closed-set classification — the actual security question. (4) A deployment-oriented recommendation table.
- **Method.** Public RF fingerprinting datasets (multi-day/multi-receiver where available) + Sionna/synthetic channel augmentation; baselines = plain CNN, DANN, self-supervised pretraining; metrics = same-day vs cross-day vs cross-receiver accuracy, EER for verification.
- **Tools/datasets.** Open SEI/RFF datasets, PyTorch, Sionna (channel augmentation).
- **Complexity.** Medium (dataset hunting is the risk). 2–3 weeks.
- **Defence relevance.** Very high (spoofing detection, EW/ESM support, IFF-adjacent).
- **Competition.** Medium–high, but the verification/open-set framing is much less crowded than classification.
- **Acceptance estimate.** **75–85%.**
- **Career impact.** High.
- **Future potential.** High; converges with authentication, zero-trust radio and continual enrolment.
- **Reviewer 2 attack.** "Another domain-adaptation paper." → Lead with the *shift-decomposition* result and the security-relevant verification metric.

---

## Idea 11 — Semantic / Goal-Oriented Transmission of Tactical Situation Reports over Ultra-Low-Bandwidth Links
**Track 4 (Channel Modelling/NGMA + Speech/Language) | Fit 8.3 | N 8 · F 9 · D 9 · A 7 · S 10 · I 9 | Competition: MEDIUM**

- **Problem.** A forward unit needs to move situational meaning (position, contact report, imagery cue) over a link that cannot carry the underlying data. Bit-accurate transmission is the wrong objective; task-sufficient transmission is the right one.
- **Gap.** Semantic communication is a hot but abstract field, rich in frameworks and metrics (Age/Value/Urgency of Information, goal-oriented tensors) and thin in *task-grounded, bandwidth-honest, safety-checked* evaluations. Crucially: a semantic decoder that reconstructs a *plausible but wrong* report is worse than useless in combat, and almost no paper measures that.
- **Novel contribution.** (1) A tactical report schema and a semantic codec that transmits structured meaning (entity/position/activity/confidence) instead of text or pixels, with graceful degradation levels. (2) **Semantic-error taxonomy and measurement** — specifically hallucinated/confabulated fields under channel noise, with a verification/rejection mechanism. (3) Bits-per-decision comparison against gzip+text and against image transmission baselines. (4) Operator-relevant metrics: decision accuracy at fixed link budget.
- **Method.** Small local language model or trained encoder–decoder for schema extraction/reconstruction; channel = BSC/AWGN/burst-loss models over a low-rate link; task metric = correct decision/field-level F1 at each SNR; ablate a checksum/verification layer.
- **Tools/datasets.** Synthetic + open text corpora recast into report schema, PyTorch, small LLM, Python channel sim.
- **Complexity.** Medium. 2–3 weeks.
- **Defence relevance.** High (DDIL comms, EMCON, satellite-denied operations).
- **Competition.** Medium.
- **Acceptance estimate.** **72–82%.**
- **Career impact.** High; semantic comms is a defining 6G theme and this is a distinctive, safety-aware take.
- **Future potential.** Very high through 2035.
- **Reviewer 2 attack.** "Where is the communication theory?" → Provide rate–distortion-style curves in *semantic* distortion and compare against classical source+channel coding at equal bits.

---

## Idea 12 — Learned Underwater Acoustic Receiver with Physics-Informed Transfer for AUV Data Links
**Track 4 (Underwater Communications) | Fit 8.2 | N 8 · F 8 · D 9 · A 8 · S 9 · I 8 | Competition: LOW**

- **Problem.** Underwater acoustic links are the harshest practical channel: severe multipath, strong Doppler, kilohertz bandwidths, long delay spread — and they carry naval sensor and AUV traffic where nothing else propagates.
- **Gap.** DL receivers for UWA OFDM are established and trained on the measured-at-sea WATERMARK dataset, with complex-valued networks reported to reach near-optimal tracking at half the spatial resource cost. The unsolved parts: dataset scarcity, generalisation across deployment sites/seasons, and how to transfer from simulated (BELLHOP/VirTEX/WOSS) channels to measured ones.
- **Novel contribution.** (1) A **sim-to-real transfer study**: pretrain on BELLHOP-generated channels, fine-tune/evaluate on WATERMARK, quantify how much measured data you can save. (2) Physics-informed augmentation (sound-speed profile, surface roughness, Doppler priors) with ablation. (3) Cross-site generalisation table (train on one WATERMARK environment, test on others). (4) Complexity budget for an AUV-class embedded processor.
- **Method.** BELLHOP/acoustic-toolbox channel generation → complex-valued CNN/LSTM receiver → fine-tune on WATERMARK → BER/MSE vs SNR curves, data-efficiency curves, cross-environment matrix.
- **Tools/datasets.** WATERMARK, BELLHOP/Acoustics Toolbox (or `arlpy`), PyTorch.
- **Complexity.** Medium (acoustic toolchain setup). 2–4 weeks.
- **Defence relevance.** High (submarine/AUV/harbour-defence; strong NPOL-style relevance).
- **Competition.** Low — a genuinely quiet field.
- **Acceptance estimate.** **78–86%.**
- **Career impact.** High and distinctive (underwater ML is a small, well-funded club).
- **Future potential.** High; semantic underwater messaging is the natural sequel (see #13).
- **Reviewer 2 attack.** "Marginal gain over existing DL receivers." → Make *data efficiency and cross-site generalisation* the claim, not BER supremacy.

---

## Idea 13 — Goal-Oriented Semantic Messaging for Underwater/AUV Telemetry at Bits-per-Second Rates
**Track 4 (Underwater + NGMA) | Fit 8.0 | N 9 · F 8 · D 8 · A 7 · S 10 · I 9 | Competition: VERY LOW**

- **Problem.** Underwater links can be limited to tens or hundreds of bits per second over range. Classical compression cannot deliver useful mission telemetry at that budget; task-oriented encoding can.
- **Gap.** Semantic communication for underwater systems is only now being architected in survey form (2026); there is essentially no empirical, physics-grounded evaluation of goal-oriented codecs on realistic UWA channels.
- **Novel contribution.** (1) A goal-oriented codec for AUV telemetry (contact classification, track updates, health status) with explicit mission-utility metrics. (2) Evaluation over BELLHOP-simulated channels *and* WATERMARK, including delay/Doppler effects, at fixed bit budgets. (3) Reliability engineering for semantics: confidence transmission, rejection of low-confidence reconstructions, retransmission policy. (4) Utility-vs-bits Pareto curves against classical baselines.
- **Method.** As #12 for the channel; semantic encoder/decoder over structured telemetry; mission-utility scoring; ablations.
- **Tools/datasets.** BELLHOP/arlpy, WATERMARK, PyTorch.
- **Complexity.** Medium. 3 weeks.
- **Defence relevance.** High (naval ISR, AUV swarms).
- **Competition.** Very low — you would be early.
- **Acceptance estimate.** **72–82%** (novelty is high, so is reviewer unfamiliarity).
- **Career impact.** High; first-mover position in a nascent niche.
- **Future potential.** Very high.
- **Reviewer 2 attack.** "Toy task." → Ground the telemetry schema in published AUV mission literature and report absolute bit budgets.

---

## Idea 14 — Safe Reinforcement Learning for Priority-Assured Slicing in Tactical 5G/6G Networks
**Track 2 (Military 5G/B5G/6G + SDN) | Fit 8.0 | N 7 · F 9 · D 9 · A 8 · S 9 · I 8 | Competition: MEDIUM**

- **Problem.** When commercial 5G/6G stacks carry military traffic, command-and-control must never starve — but learned resource allocators optimise averages and can violate priority guarantees exactly when the network is stressed.
- **Gap.** RL for slicing/resource allocation is abundant; **constraint satisfaction under adversarial stress with hard priority guarantees** is not. Industry has moved to multi-transport DDIL orchestration in practice, which raises the same guarantee question at a higher layer.
- **Novel contribution.** (1) Formulate tactical slicing as a **constrained** MDP with hard C2 guarantees, not a reward-shaping problem. (2) Compare unconstrained DRL, Lagrangian/CMDP methods and shielded RL for *constraint-violation counts*, not just throughput. (3) Stress test: jamming-induced capacity collapse, node loss, traffic surge. (4) A fallback/handover policy to a rule-based controller when the learned policy leaves its safe envelope.
- **Method.** ns-3/simplified slicing simulator with C2/ISR/logistics traffic classes; agents = PPO, PPO-Lagrangian, shielded PPO; metrics = violation count, C2 latency tail (p99), utilisation, recovery time.
- **Tools/datasets.** ns-3 or custom simulator, Stable-Baselines3/safety-gym patterns.
- **Complexity.** Medium. 2–3 weeks.
- **Defence relevance.** High.
- **Competition.** Medium.
- **Acceptance estimate.** **76–84%.**
- **Career impact.** Medium–high (safe RL is a strong, transferable credential).
- **Future potential.** High.
- **Reviewer 2 attack.** "Simulator is simplified." → Report the p99 tails and violation counts as the deliverable; those orderings survive abstraction.

---

## Idea 15 — Network Digital Twin for Tactical Link Planning: Quantifying the Twin-to-Reality Gap
**Track 2 (SDN) / Track 4 (Channel Modelling) | Fit 7.9 | N 7 · F 8 · D 9 · A 8 · S 9 · I 8 | Competition: LOW–MEDIUM**

- **Problem.** Digital twins are being proposed for military network planning, but a twin that is wrong in an unknown direction is a liability. Nobody quantifies the fidelity you actually need for a *decision* to be correct.
- **Gap.** Digital-twin-for-networks literature is architecture-heavy and validation-light. The differentiable toolchain now makes rigorous fidelity studies cheap: Sionna RT supplies environment-specific, geometry-aware channels and integrates with ns-3-style network simulation for digital-network-twin work.
- **Novel contribution.** (1) A tiered twin (statistical → ray-traced → measured-calibrated) for a tactical scenario. (2) **Decision-equivalence analysis**: at what fidelity does the twin's recommended plan (site selection, relay placement, channel assignment) stop matching the highest-fidelity reference? (3) Compute-cost vs decision-accuracy curves — an actionable engineering answer. (4) Sensitivity to material/terrain parameter error.
- **Method.** Sionna RT scenes (terrain/urban), ns-3 network layer, planning task defined as an optimisation over sites/relays; measure plan agreement (top-k overlap, achieved capacity of chosen plan) across fidelity tiers.
- **Tools/datasets.** Sionna RT/PHY/SYS, ns-3, open DEM/OSM geometry.
- **Complexity.** Medium–high (toolchain integration). 3–4 weeks.
- **Defence relevance.** High.
- **Competition.** Low–medium.
- **Acceptance estimate.** **76–84%.**
- **Career impact.** High (digital twin + wireless is an industry-hot phrase with substance here).
- **Future potential.** High.
- **Reviewer 2 attack.** "No ground truth." → Define the highest-fidelity tier as the reference and frame the contribution as *fidelity sufficiency*, which needs no field campaign.

---

## Idea 16 — Channel-Degraded Keyword Spotting and Priority-Voice Triage for Tactical Nets
**Track 4 (Speech/Audio/Language) | Fit 7.9 | N 6 · F 10 · D 8 · A 9 · S 10 · I 7 | Competition: VERY LOW**

- **Problem.** On a busy combat net, the operator's problem is attention, not bandwidth: which of forty transmissions contained a contact report, a casualty call or a grid reference?
- **Gap.** Keyword spotting is a solved task on clean speech and a benchmarked task for Indian languages (IndicSUPERB includes keyword spotting and speaker verification across 12 languages). It is **unbenchmarked under radio-channel degradation** — vocoder artefacts, 2–4 kHz bandwidth, fading, squelch noise, partial-band interference.
- **Novel contribution.** (1) A reproducible **channel-degradation augmentation pipeline** (vocoder + band-limiting + fading + jamming + clipping) applied to an Indian-language KWS benchmark. (2) Degradation curves showing where accuracy falls off a cliff, per language and per SNR. (3) A robustness recipe (augmentation-aware training, self-supervised front end) with measured recovery. (4) An edge-complexity budget for radio-side deployment.
- **Method.** IndicSUPERB/Kathbath KWS subsets → augmentation chain → train/evaluate small models (wav2vec2/Whisper-tiny/CNN-KWS) → report accuracy vs SNR, per-language and per-condition.
- **Tools.** Kathbath/IndicSUPERB, torchaudio, Codec 2 / open vocoder for artefact simulation, PyTorch. Colab-class compute.
- **Complexity.** **Very low.** Realistically a 24–36 hour paper. *This is your safest "submit by 5 August" option in Track 4.*
- **Defence relevance.** High and immediately legible.
- **Competition.** Very low.
- **Acceptance estimate.** **80–88%** (simple but complete, useful, and on-track).
- **Career impact.** Medium–high; strongest as a stepping stone into #4.
- **Future potential.** Medium–high (feeds voice-net analytics, ASR-assisted logging, semantic voice).
- **Reviewer 2 attack.** "Incremental." → Position as the missing benchmark and release the augmentation code; benchmarks are contributions.

---

## Idea 17 — Channel-Robust Speaker Verification for Tactical Voice Nets (Anti-Impersonation)
**Track 4 (Speech + PLS) | Fit 7.8 | N 7 · F 9 · D 9 · A 8 · S 10 · I 8 | Competition: VERY LOW**

- **Problem.** Voice on an open net is trivially impersonated, and voice cloning has made this a live threat. Speaker verification over degraded narrowband radio is the natural countermeasure and is essentially unstudied in that regime.
- **Gap.** Speaker verification is benchmarked for Indian languages on clean audio; its behaviour under vocoder + fading + low-bitrate transcoding — and under **synthetic-voice spoofing** — is not characterised.
- **Novel contribution.** (1) EER/FAR-FRR curves for speaker verification across radio-degradation conditions and languages. (2) A spoofing evaluation with modern TTS/voice-conversion attacks *after* channel degradation (the channel hides artefacts — a genuinely interesting negative result). (3) A lightweight countermeasure and its operating point. (4) A recommendation for a layered scheme combining voice biometrics with physical-layer emitter identity (links neatly to Idea #10).
- **Method.** Kathbath/IndicSUPERB speaker-verification splits + augmentation chain; ECAPA-TDNN/x-vector embeddings; open TTS for spoof generation; report EER by condition.
- **Tools.** IndicSUPERB, SpeechBrain/torchaudio, open TTS, PyTorch.
- **Complexity.** Low–medium. ~1 week.
- **Defence relevance.** High (impersonation on command nets is a real EW/deception vector).
- **Competition.** Very low.
- **Acceptance estimate.** **78–86%.**
- **Career impact.** High (biometrics + security + wireless).
- **Future potential.** High; deepfake-resistant voice authentication is a decade-long problem.
- **Reviewer 2 attack.** "Not a communications paper." → Anchor it in physical-layer + application-layer identity fusion and report link conditions rigorously.

---

## Idea 18 — Self-Supervised Detection of Low-Probability-of-Intercept Waveforms Below the Noise Floor
**Track 4 (Anti-Jamming & PLS / Cognitive Radio) | Fit 7.8 | N 8 · F 8 · D 10 · A 7 · S 9 · I 8 | Competition: LOW**

- **Problem.** Electronic support measures must decide whether *anything* is transmitting in a band where the adversary is deliberately hiding beneath the noise floor. Detection, not classification, is the hard problem.
- **Gap.** Covert/LPD research is overwhelmingly information-theoretic (achievable covert rates, square-root laws, warden models) and light on **practical learned detection**, with dataset scarcity repeatedly named as the blocker. Meanwhile self-supervised learning is exactly the right tool for "learn what normal noise looks like, flag deviations."
- **Novel contribution.** (1) An open synthetic corpus of LPI/spread-spectrum/covert transmissions at negative SNR with documented generation parameters (fixing the reproducibility complaint that plagues this area). (2) Self-supervised/anomaly-detection detectors (masked autoencoding on spectrograms, one-class objectives) versus energy-detection and cyclostationary baselines. (3) ROC curves as a function of SNR, spreading factor and observation window — the operationally meaningful result. (4) Honest statement of the detectability floor.
- **Method.** Generate DSSS/FHSS/chirp/noise-like waveforms with GNU Radio or Sionna/NumPy at −20 to 0 dB SNR under fading; train SSL detectors; compare against classical detectors at matched false-alarm rates.
- **Tools.** GNU Radio (optional) or pure NumPy/Sionna generation, PyTorch.
- **Complexity.** Medium (dataset design is the work). 2–3 weeks.
- **Defence relevance.** Maximal (ESM/EW support, spectrum policing).
- **Competition.** Low.
- **Acceptance estimate.** **74–84%.**
- **Career impact.** High.
- **Future potential.** High; the corpus becomes a reusable community asset.
- **Reviewer 2 attack.** "Synthetic data proves nothing." → Publish the generator, match classical-detector theory on the same data as a sanity check, and report absolute SNR thresholds against theory.

---

## Idea 19 — Quantum-Resistant Group Key Management for Swarms and Multi-Hop MANETs
**Track 2 (Cryptography) | Fit 7.7 | N 7 · F 9 · D 9 · A 8 · S 10 · I 8 | Competition: LOW**

- **Problem.** Drone swarms and tactical mesh nets need group keys with frequent rekeying (join/leave/compromise), and post-quantum primitives make every rekey message dramatically larger.
- **Gap.** PQC evaluation focuses on pairwise handshakes (TLS-style). **Group/multicast rekeying cost under PQC on lossy multi-hop links is unmeasured**, despite being the operationally dominant cost for swarms.
- **Novel contribution.** (1) Cost model for logical-key-hierarchy and tree-based group rekeying instantiated with ML-KEM/ML-DSA vs classical primitives. (2) Measured rekey completion time and message overhead versus swarm size, churn rate and packet loss. (3) A hybrid scheme (PQC for long-term, symmetric ratcheting for high-churn periods) with quantified savings. (4) Design table: recommended scheme by swarm size and link class.
- **Method.** liboqs primitives + group-key protocol implementation in Python/C, driven over ns-3 or netem multi-hop topologies with churn traces.
- **Tools.** liboqs, ns-3/netem, Python.
- **Complexity.** Low–medium. ~1.5 weeks.
- **Defence relevance.** Very high (swarm C2 is a top Indian priority).
- **Competition.** Low.
- **Acceptance estimate.** **78–86%.**
- **Career impact.** High; pairs with #2 into a coherent "quantum-safe tactical comms" research line.
- **Future potential.** High.
- **Reviewer 2 attack.** "Standard group-key schemes, just re-benchmarked." → Foreground the churn×loss×PQC-size interaction and the hybrid design recommendation.

---

## Idea 20 — GNN-Based Spectrum Deconfliction and Frequency Assignment at Brigade Scale
**Track 2 (ML for Comms) / Track 4 | Fit 7.6 | N 7 · F 9 · D 9 · A 8 · S 9 · I 7 | Competition: LOW–MEDIUM**

- **Problem.** Assigning frequencies to hundreds of collocated emitters with interference, harmonic and doctrinal constraints is a hard combinatorial problem solved today by planners with spreadsheets under time pressure.
- **Gap.** Learning-for-combinatorial-optimisation has strong graph-neural-network machinery; its application to *military spectrum deconfliction with real constraint structure and re-planning latency requirements* is thin, and comparisons to the heuristics planners actually use are usually missing.
- **Novel contribution.** (1) Interference-graph formulation with military constraint classes (guard bands, co-site, EMCON zones, priority nets). (2) GNN + greedy-decoding assignment vs. DSATUR/tabu/CP-SAT baselines on solution quality **and** re-planning latency after a disruption. (3) Robustness: how gracefully each method handles losing spectrum (a jammed band) mid-plan. (4) Scaling curves to brigade size.
- **Method.** Synthetic scenario generator (emitters, geometry, constraints); PyTorch Geometric GNN; OR-Tools CP-SAT and classical heuristics as baselines; metrics = feasible-assignment rate, interference margin, latency.
- **Tools.** PyTorch Geometric, OR-Tools, NetworkX.
- **Complexity.** Medium. ~2 weeks.
- **Defence relevance.** High.
- **Competition.** Low–medium.
- **Acceptance estimate.** **76–84%.**
- **Career impact.** Medium–high.
- **Future potential.** Medium–high; pairs naturally with the LLM copilot (#7) as its tool layer.
- **Reviewer 2 attack.** "CP-SAT already solves this." → Then say so honestly and sell **re-planning latency under disruption**, where learned methods genuinely win.

---

## Idea 21 — Position- and Sensor-Aided Beam Prediction for Airborne Tactical Data Links
**Track 4 (Digital Beamforming) | Fit 7.5 | N 7 · F 8 · D 9 · A 8 · S 8 · I 8 | Competition: MEDIUM–HIGH**

- **Problem.** Airborne platforms (AEW&C, UAVs, fighters) need directional links maintained through high-speed manoeuvre; exhaustive beam sweeping wastes time the link does not have.
- **Gap.** AI beam management is standardised for terrestrial UE mobility (Rel-19 specifies signalling for AI-based beam management and positioning); **airborne 3D high-dynamics geometry with platform attitude and sparse feedback** is comparatively under-studied, and defence framing is essentially absent.
- **Novel contribution.** (1) A beam-prediction model conditioned on 6-DoF platform state (position, velocity, attitude) plus sparse measurement history. (2) Evaluation on air-to-ground and air-to-air geometries generated in Sionna RT/DeepMIMO-style scenarios. (3) Overhead-reduction quantification (sweeps avoided per second of link time) and outage analysis during manoeuvre. (4) Behaviour under deliberate interference in the chosen beam.
- **Method.** Generate ray-traced channels along flight trajectories; train sequence model (GRU/transformer) for top-k beam prediction; metrics = top-1/top-k accuracy, spectral-efficiency retention, overhead saved, outage duration.
- **Tools.** Sionna RT/PHY, PyTorch, trajectory generator.
- **Complexity.** Medium–high (scenario generation). 3 weeks.
- **Defence relevance.** Very high (DEAL builds exactly these datalinks).
- **Competition.** Medium–high (beam prediction is popular) — the airborne/defence framing is the differentiator.
- **Acceptance estimate.** **74–84%.**
- **Career impact.** Medium–high.
- **Future potential.** High.
- **Reviewer 2 attack.** "Beam prediction is done." → Emphasise the 3D-attitude conditioning and the manoeuvre/outage analysis that terrestrial work never needs.

---

## Idea 22 — RIS Control-Policy Learning for Anti-Jamming and Covert Links with EM-Consistent Channels
**Track 5 (Meta Surfaces & RIS) | Fit 7.4 | N 7 · F 8 · D 9 · A 7 · S 9 · I 8 | Competition: MEDIUM–HIGH**

- **Problem.** A reconfigurable surface can, in principle, be steered to null a jammer or to shape a link so an eavesdropper cannot hear it. Whether learned control can do this with realistic overhead and low-bit phase quantisation is the practical question.
- **Gap.** The AI-for-RIS field is broad and well-surveyed (channel estimation, sum-rate, energy efficiency, security, across supervised/DRL/federated/graph/meta learning), and codebook-based control was introduced specifically to escape prohibitive pilot overhead. But defence objectives (jammer nulling, covertness, LPI) with **EM-consistent, geometry-aware channels** and hardware-realistic quantisation are rare; most work uses idealised cascaded models and continuous phases.
- **Novel contribution.** (1) Anti-jam/covert objective functions for RIS control instead of sum-rate. (2) Codebook-learning under 1–2 bit phase quantisation with explicit overhead accounting. (3) Ray-traced (Sionna RT) evaluation so the geometry is physically consistent — directly addressing the standard EM reviewer objection. (4) Sensitivity to jammer mobility and CSI staleness.
- **Method.** Sionna RT scene with RIS + legitimate pair + jammer/warden; DRL or codebook-learning controller; metrics = SINR gain vs jammer, detection probability at the warden, overhead, robustness to outdated CSI.
- **Tools.** Sionna RT (supports RIS), PyTorch.
- **Complexity.** Medium–high. 3 weeks.
- **Defence relevance.** High.
- **Competition.** Medium–high in the general RIS field; low for this defence formulation.
- **Acceptance estimate.** **70–80%** (Track 5 reviewer mismatch risk).
- **Career impact.** Medium–high.
- **Future potential.** High.
- **Reviewer 2 attack.** "Idealised RIS assumptions." → Pre-empt with quantisation, coupling and CSI-staleness ablations; that is the whole reason to run ray tracing.

---

## Idea 23 — Data-Driven Fault Diagnosis and Pattern Recovery for Phased Arrays
**Track 5 (Advanced Phased Array & Beamforming) | Fit 7.3 | N 7 · F 8 · D 10 · A 7 · S 8 · I 7 | Competition: LOW**

- **Problem.** Large AESAs degrade element-by-element in service. Diagnosing which elements failed, and re-optimising excitations to restore an acceptable pattern, is a maintenance-critical capability for radar and AEW&C platforms.
- **Gap.** Array diagnostics has a classical literature (pattern-difference methods, compressed sensing) but comparatively little modern learned treatment, and almost no work on **joint diagnosis + graceful pattern recovery with partial/noisy observations** framed as a deployable software capability.
- **Novel contribution.** (1) A learned diagnoser mapping measured/simulated far-field patterns to element-failure maps, robust to measurement noise and partial angular coverage. (2) A recovery stage that re-optimises remaining element weights to restore mainlobe gain and suppress sidelobe regrowth, with quantified residual degradation. (3) Failure-severity curves (how many elements can you lose before the pattern is operationally unacceptable). (4) Explainability output for a maintenance operator.
- **Method.** Fully synthetic but physically exact: array-factor computation for planar arrays in NumPy; inject amplitude/phase/dead-element faults; train CNN/transformer diagnoser; recovery via convex/gradient re-optimisation; validate against classical baselines.
- **Tools.** NumPy/SciPy (array factor), PyTorch, CVXPY. **No hardware whatsoever.**
- **Complexity.** Low–medium. ~1.5 weeks.
- **Defence relevance.** Maximal for the host ecosystem (radar, AEW&C, missile seekers).
- **Competition.** Low, and it is the one Track 5 idea that speaks the antenna reviewer's language natively.
- **Acceptance estimate.** **76–84%** — high, *provided* the array modelling is exact and the terminology is correct.
- **Career impact.** Medium–high; unusual and memorable.
- **Future potential.** Medium–high (predictive maintenance for phased arrays).
- **Reviewer 2 attack.** "Simulation-only, idealised elements." → Add mutual-coupling and element-pattern perturbations as robustness tests.

---

## Idea 24 — Encrypted-Traffic and Covert-Channel Detection for Tactical IP Networks
**Track 2 (Cyber Security) | Fit 7.2 | N 6 · F 10 · D 8 · A 8 · S 10 · I 7 | Competition: MEDIUM**

- **Problem.** A compromised node on a tactical IP network can exfiltrate over covert channels that look like ordinary traffic; classical DPI fails on encrypted flows.
- **Gap.** ML covert-channel detection exists but the literature itself notes that **oversimplified attack assumptions make detection artificially easy** and that dataset realism is the core issue; field measurements show real covert techniques are already deployed operationally.
- **Novel contribution.** (1) A realistic covert-channel corpus for a *tactical* traffic profile (low rate, bursty, high loss) rather than a datacentre profile. (2) Detection under bandwidth-constrained monitoring (you cannot mirror all traffic on a tactical link) — a sampling-budget-aware detector. (3) False-positive cost analysis in an operational context. (4) Adaptive-adversary evaluation (attacker tunes rate to evade).
- **Method.** Generate benign tactical-profile traffic + covert injections in an emulated topology; flow-feature and sequence models; evaluate under sampling budgets and adaptive evasion.
- **Tools.** ns-3/netem, Scapy, scikit-learn/PyTorch. Your professional domain.
- **Complexity.** Low. ~1 week.
- **Defence relevance.** High.
- **Competition.** Medium.
- **Acceptance estimate.** **76–84%.**
- **Career impact.** Medium–high (closest to your day job; be careful to use only self-generated data — see Part VIII).
- **Future potential.** Medium.
- **Reviewer 2 attack.** "Not wireless." → Tie explicitly to tactical radio-borne IP links: constrained monitoring capacity *is* the wireless constraint.

---

## Idea 25 — Cross-Dataset Reality Check and Open-Set Protocol for Deep Modulation Classification
**Track 4 (Cognitive Radio) | Fit 7.1 | N 6 · F 10 · D 8 · A 8 · S 10 · I 7 | Competition: HIGH (field) / LOW (this framing)**

- **Problem.** Deep AMC is reported as solved. Deployed spectrum-awareness systems disagree.
- **Gap.** The community has begun documenting its own methodological problems: single-modulation captures with known centre frequency and simplified impairments that overstate real-world readiness; missing sampling-rate/baud-rate metadata; no uniform dataset splits, which makes cross-paper comparison unreliable.
- **Novel contribution.** (1) A **standard evaluation protocol** (fixed splits, cross-dataset transfer, SNR-stratified reporting, unknown-class rejection, compute budget) applied to 4–6 representative published architectures reimplemented at matched capacity. (2) Evidence on how much of the reported progress survives the protocol. (3) A leaderboard + released code, which is what the field is explicitly missing. (4) Guidance for practitioners deploying spectrum awareness.
- **Method.** RadioML 2016/2018 + HisarMod (and one synthetic co-channel set); matched-capacity reimplementations; open-set scoring; full ablation and compute accounting.
- **Tools.** RadioML/HisarMod, PyTorch.
- **Complexity.** Low–medium. ~10 days.
- **Defence relevance.** Medium–high.
- **Competition.** The field is saturated; **this framing is not**, and a rigour paper is very hard for a reviewer to reject.
- **Acceptance estimate.** **76–84%.**
- **Career impact.** Medium–high (reproducibility work builds a reputation for seriousness).
- **Future potential.** Medium–high; benchmarks persist.
- **Reviewer 2 attack.** "No new method." → State plainly that the contribution is measurement and protocol; cite the field's own self-critiques as motivation.

---

## Idea 26 — Learned Co-Channel Signal Separation for Congested Tactical Spectrum
**Track 4 (Adaptive Signal Processing) | Fit 7.0 | N 8 · F 7 · D 9 · A 7 · S 9 · I 8 | Competition: LOW–MEDIUM**

- **Problem.** Real tactical spectrum contains overlapping emitters; nearly all wireless-ML benchmarks assume one signal per capture — the single most consequential unrealistic assumption in the field.
- **Gap.** Explicitly identified in dataset critiques: public corpora typically contain one modulation per capture. Source-separation methods from audio (permutation-invariant training, masking, Conv-TasNet-style architectures) have barely been transplanted to RF with proper evaluation.
- **Novel contribution.** (1) A co-channel RF mixture benchmark with controlled power ratios and overlap fractions. (2) Separation-then-classification pipeline versus joint multi-label classification versus classical interference cancellation. (3) Performance as a function of SIR/overlap — the operational curve. (4) Analysis of what separation buys downstream (classification/identification accuracy recovered).
- **Method.** Synthesise mixtures from RadioML-style single-emitter data; PIT-trained separator on complex spectrograms; evaluate SDR-style separation metrics + downstream accuracy.
- **Tools.** PyTorch, asteroid/torchaudio patterns, NumPy signal generation.
- **Complexity.** Medium. ~2 weeks.
- **Defence relevance.** High (ESM in dense EM environments).
- **Competition.** Low–medium.
- **Acceptance estimate.** **72–80%.**
- **Career impact.** Medium–high.
- **Future potential.** High.
- **Reviewer 2 attack.** "Synthetic mixtures." → Document the mixing model, sweep SIR widely, and report downstream task gains, not just separation metrics.

---

## Idea 27 — Attestation and Provenance for AI Models Inside the Radio Stack
**Track 2 (Cyber Security / SDN) | Fit 6.9 | N 8 · F 8 · D 9 · A 7 · S 10 · I 8 | Competition: VERY LOW**

- **Problem.** If a waveform-adaptation or scheduling model can be updated in the field, its provenance is a weapons-grade concern. Who signed it, what data trained it, and can the radio verify that before loading it?
- **Gap.** Model supply-chain security is discussed in AI-security literature and in O-RAN threat analyses, but there is almost no concrete, measured architecture for **attested model loading on constrained radio platforms**, and none in a defence framing.
- **Novel contribution.** (1) A model-provenance and attestation pipeline (signed model artefacts + training-data manifest + policy checks + verification-at-load) specified for a radio platform. (2) Measured overhead on constrained hardware profiles, including post-quantum signatures where the artefact is large. (3) Detection of unauthorised or downgraded models in an update flow. (4) Threat/mitigation matrix.
- **Method.** Implement signing/verification with classical and PQ signatures (liboqs); measure load-time verification overhead vs model size on CPU-only profiles; simulate an update-flow attack.
- **Tools.** liboqs, sigstore-style tooling patterns, Python/C, PyTorch model artefacts.
- **Complexity.** Low–medium. ~10 days.
- **Defence relevance.** Very high (Aatmanirbhar supply-chain assurance is a stated national concern).
- **Competition.** Very low.
- **Acceptance estimate.** **72–80%** (novel but may read as "systems engineering" — add measurement rigour).
- **Career impact.** High; extremely aligned with your CTEM/security professional identity.
- **Future potential.** High.
- **Reviewer 2 attack.** "This is standard code signing." → Show what is *not* standard: training-data manifests, PQ signature sizes on constrained links, and verification latency budgets on radio-class CPUs.

---

## Idea 28 — Jamming-Aware Multi-Path Transport Selection Across Heterogeneous Tactical Links
**Track 2 (Military 5G/6G + SDN) | Fit 6.8 | N 7 · F 8 · D 9 · A 7 · S 9 · I 7 | Competition: LOW**

- **Problem.** A forward node may have SATCOM, a 5G bubble, a MANET waveform and a legacy radio available at once. Choosing and blending them under attack is the DDIL problem industry is productising right now.
- **Gap.** Multi-transport orchestration is being commercialised, but published, reproducible policy evaluations under EW-induced link degradation are scarce; academic multipath work optimises throughput, not survivability.
- **Novel contribution.** (1) A transport-selection MDP over heterogeneous links with EW-driven state transitions. (2) Learned vs rule-based (A-PACE-style) policies compared on **mission-continuity metrics** — time-to-restore, C2 message delivery under attack — not throughput. (3) Detection-to-switch latency analysis (how fast must you notice jamming for switching to help). (4) Cost of wrong switches (thrash).
- **Method.** Simulator with 3–4 link types (rate, latency, loss, vulnerability profiles); jamming events; RL and heuristic policies; metrics = C2 delivery ratio, restore time, thrash count.
- **Tools.** Python/ns-3, Stable-Baselines3.
- **Complexity.** Low–medium. ~10 days.
- **Defence relevance.** Very high.
- **Competition.** Low.
- **Acceptance estimate.** **74–82%.**
- **Career impact.** Medium–high.
- **Future potential.** Medium–high.
- **Reviewer 2 attack.** "Abstract link models." → Parameterise from published waveform specs and make the sensitivity analysis prominent.

---

## Idea 29 — Sim-to-Real Transfer Study for Neural Receivers on Public Over-the-Air Data
**Track 4 (Adaptive SP) / Track 2 | Fit 6.7 | N 7 · F 7 · D 8 · A 7 · S 9 · I 8 | Competition: MEDIUM**

- **Problem.** Neural receivers trained in differentiable simulators degrade on real captures. How much, and what closes the gap cheapest?
- **Gap.** Everyone acknowledges the sim-to-real gap; few quantify it systematically with a recipe. Differentiable simulators plus calibration methods (learning radio materials and environment parameters by differentiable ray tracing) make this newly tractable.
- **Novel contribution.** (1) A quantified gap measurement (train in Sionna, test on public over-the-air captures). (2) Comparison of gap-closing strategies: domain randomisation, fine-tuning with N real samples, channel-parameter calibration. (3) A data-efficiency curve — the number that matters to any programme manager. (4) Practical guidance.
- **Method.** Sionna PHY training pipelines; public OTA datasets; systematic transfer experiments.
- **Tools.** Sionna, PyTorch/TensorFlow, public OTA datasets.
- **Complexity.** Medium–high (dataset matching is fiddly). ~3 weeks.
- **Defence relevance.** Medium–high.
- **Competition.** Medium.
- **Acceptance estimate.** **70–80%.**
- **Career impact.** Medium–high.
- **Future potential.** High.
- **Reviewer 2 attack.** "Dataset mismatch confounds your conclusions." → Control carefully; report per-dataset results separately.

---

## Idea 30 — On-Device Small Language Model for Offline Tactical Network Operations Support
**Track 2 (ML for Comms / Military 6G) | Fit 6.5 | N 7 · F 9 · D 8 · A 7 · S 10 · I 7 | Competition: LOW**

- **Problem.** A signals detachment troubleshooting a link has no cloud, no bandwidth for an API call, and possibly no connectivity at all. Any useful AI assistant must be local, small and quantised.
- **Gap.** Telecom-LLM research runs on frontier-scale models; the constrained-deployment question ("what capability survives at 3–8B parameters quantised on a rugged laptop, and where does it become dangerous?") is under-examined, while benchmarks show a stark gap between linguistic competence and procedural execution.
- **Novel contribution.** (1) Capability-vs-footprint curves: accuracy on network-troubleshooting tasks across model sizes/quantisations, with latency on CPU-only hardware. (2) Retrieval as a substitute for scale — how much RAG compensates for parameter count. (3) A refusal/uncertainty layer, with measured error-avoidance. (4) A deployment recommendation for an air-gapped field kit.
- **Method.** Build a 100-item tactical-network-ops task set (from open documentation only); evaluate 3–5 local models at multiple quantisations; measure accuracy, latency, memory, hallucination and refusal rates.
- **Tools.** llama.cpp/Ollama, small open models, a local RAG stack (your existing toolchain).
- **Complexity.** Low. ~1 week.
- **Defence relevance.** High (air-gapped operation is a hard requirement).
- **Competition.** Low.
- **Acceptance estimate.** **70–80%.**
- **Career impact.** Medium–high; strong internal-enablement crossover.
- **Future potential.** Medium–high.
- **Reviewer 2 attack.** "Engineering evaluation, not research." → Make the capability-vs-footprint frontier and the retrieval-substitutes-for-scale finding the scientific claims.

---

# Part VI — The five leaderboards

## VI.1 Top 10 by estimated probability of acceptance at WiCOMM-2026

| # | Idea | Est. acceptance | Why it clears review so easily |
|---|---|---|---|
| 1 | **#2 PQC on constrained tactical links** | 85–92% | Measurement paper, no contestable theory, urgent policy relevance, actionable tables, zero dataset risk |
| 2 | **#1 QKD/PQC key-rate-aware routing** | 85–90% | Answers the exact question DRDO has just publicly posed; almost no competing submissions |
| 3 | **#3 Terrain-aware propagation surrogate** | 85–90% | Speaks the host lab's founding discipline in the host lab's terrain |
| 4 | **#6 Open-set cross-domain drone RF ID** | 80–88% | Urgent counter-UAS topic, public datasets, honest framing beats accuracy-chasing |
| 5 | **#4 Neural speech over HF/VHF (Indic)** | 80–88% | Empty sub-track, high mission relevance, strong tooling |
| 6 | **#16 Channel-degraded keyword spotting** | 80–88% | Simple, complete, useful, unopposed |
| 7 | **#5 Federated spectrum awareness (DDIL)** | 80–88% | Fresh, explicit literature gap; defence-native framing |
| 8 | **#9 Generalisation-first anti-jamming RL** | 78–86% | Core DEAL theme; benchmark contribution is hard to argue against |
| 9 | **#19 PQ group key management for swarms** | 78–86% | Unmeasured, obviously needed, cheap to do well |
| 10 | **#8 Backdoor resilience of radio-stack AI** | 78–86% | Demonstrated threat + missing defence engineering; you have domain credibility |

## VI.2 Top 10 by lowest competition (best novelty-per-crowding)

| # | Idea | Competition | Evidence of the vacancy |
|---|---|---|---|
| 1 | **#13 Underwater goal-oriented semantic messaging** | Very low | Underwater semantic comms is only now being framed in survey form (2026); no empirical body of work |
| 2 | **#17 Channel-robust speaker verification for radio nets** | Very low | Speaker verification benchmarked only on clean Indic audio; radio-degraded + spoofing case unstudied |
| 3 | **#27 Attestation/provenance for radio-stack AI models** | Very low | Threat discussed, architecture unmeasured, no defence framing in print |
| 4 | **#16 Channel-degraded keyword spotting** | Very low | KWS benchmarks exist for Indian languages; nobody degrades them through a radio channel |
| 5 | **#4 Neural speech over HF for code-mixed Indic** | Very low | Neural HF speech work is English-centric; Indic + code-mixed is untouched |
| 6 | **#1 QKD/PQC multi-hop key orchestration** | Low | Quantum networking rarely meets tactical network constraints; near-zero Indian conference presence |
| 7 | **#3 Terrain-aware propagation surrogate** | Low | Learned radio maps are urban; terrain-dominated long-range is a gap |
| 8 | **#12 UWA receiver sim-to-real transfer** | Low | Small, quiet field with mature open tooling |
| 9 | **#18 SSL detection of LPI waveforms** | Low | Covert-comms literature is theory-dominated; learned detection is dataset-starved |
| 10 | **#23 Phased-array fault diagnosis + recovery** | Low | Classical literature exists; modern learned + recovery framing is rare, and it is the only ML-friendly Track 5 slot |

## VI.3 Top 10 by long-term research and industry impact (2026–2035)

| # | Idea | Why it compounds |
|---|---|---|
| 1 | **#1 QKD/PQC hybrid key orchestration** | Quantum networks are a declared national capability build-out; systems-layer questions will be needed for a decade |
| 2 | **#5 Federated / continual spectrum awareness** | Distributed edge learning under DDIL is a permanent requirement of every future tactical architecture |
| 3 | **#8 Security of AI inside the radio stack** | AI-native RAN ships in Rel-20/6G; its assurance becomes mandatory, not optional |
| 4 | **#3 Terrain-aware learned propagation** | Radio-map surrogates become infrastructure for planning, digital twins and autonomous relay placement |
| 5 | **#11 Semantic/goal-oriented tactical reporting** | Semantic communication is a defining 6G paradigm; safety-checked semantics is the missing piece |
| 6 | **#7 Doctrine-grounded agentic decision support** | Agentic operations will enter network and spectrum management; benchmarks and reliability measurement will be the gatekeepers |
| 7 | **#2 PQC on constrained links** | Migration runs to 2035 under binding mandates; crypto-agility becomes a permanent engineering discipline |
| 8 | **#4 Neural speech over radio** | Voice is never going away; neural codecs will replace legacy vocoders across tactical and public-safety radio |
| 9 | **#15 Digital-twin fidelity sufficiency** | Twins are being adopted faster than they are validated; fidelity economics will matter for years |
| 10 | **#21 Beam prediction for airborne links** | Directional links + high mobility is the trajectory of every airborne and satellite datalink programme |

## VI.4 Top 10 best aligned to your AI/ML + software engineering background

Ranked by how little you must learn outside your existing stack, weighted by payoff.

| # | Idea | What it uses that you already have |
|---|---|---|
| 1 | **#16 Channel-degraded KWS** | PyTorch audio, augmentation pipelines, benchmarking discipline |
| 2 | **#2 PQC on tactical links** | Security tooling, Linux networking, measurement/benchmark engineering, data presentation |
| 3 | **#6 Drone RF open-set / cross-domain** | Classification, OOD detection, dataset wrangling, honest evaluation |
| 4 | **#4 Neural speech over HF (Indic)** | Speech ML, fine-tuning, ASR-in-the-loop evaluation |
| 5 | **#7 LLM copilot + SpectrumOpsBench** | Agentic systems, RAG, tool-calling, eval design — literally your job |
| 6 | **#5 Federated spectrum awareness** | Distributed training, non-IID handling, adversarial robustness |
| 7 | **#24 Encrypted-traffic / covert-channel detection** | Network security, feature engineering, adversarial evaluation |
| 8 | **#30 On-device SLM for network ops** | Local model serving, quantisation, RAG, benchmark construction |
| 9 | **#9 Anti-jamming RL generalisation** | RL engineering, Gym environments, curriculum design |
| 10 | **#1 QKD/PQC key orchestration** | Discrete-event simulation, protocol design, systems thinking (physics is parameterised, not required) |

## VI.5 My Top 5 overall — with explicit justification

**Ranking criterion:** balanced expected value = (novelty × defence relevance × acceptance probability × career value) ÷ execution risk, judged against *your* constraints.

### 🥇 1. #3 — Terrain-Aware Learned Propagation Surrogate for Mountainous Tactical Link Planning
The strongest idea in this study, for one reason no competitor can copy: **institutional fit**. DEAL was born as the Himalayan Radio Propagation Unit, its current systems are trialled in Uttarakhand mountain terrain, and its transhorizon system exists precisely because mountains break normal links. Meanwhile the learned-radio-map literature is urban, benchmark-bound, and openly admits it is simulation-to-simulation. You can therefore make a real contribution (terrain-dominated, cross-region generalisation, calibrated uncertainty for link planning) using only open DEMs, published ITU-R models and Python. Novelty: high. Defence relevance: maximum. Competition: low. Career value: it is the paper most likely to make a DEAL scientist want to talk to you. **Risk:** label generation is the long pole — do not attempt the full version in 48 hours.

### 🥈 2. #1 — Key-Rate-Aware Routing and Hybrid QKD/PQC Fallback for Multi-Hop Tactical Quantum Networks
Timing is the entire argument. DRDO has just completed military field trials of an indigenous QKD system and publicly framed multi-hop quantum networking as the next objective; the free-space entanglement demonstration gives you concrete parameters (~240 bit/s, <7% QBER) to anchor a simulation. The systems questions that multi-hop trusted-node networks raise — key routing, admission control, hybrid PQC fallback, behaviour under outage — are unanswered, purely software, and answerable in mature open simulators. You get to work on the country's highest-prestige defence-comms topic without touching a photon. **Risk:** you must be scrupulous that your key-rate parameters are labelled as assumptions.

### 🥉 3. #4 — Neural Speech Transmission over HF/VHF Tactical Voice Channels for Code-Mixed Indian Speech
This is the best *arbitrage* in the CFP. Track 4 explicitly solicits speech and language processing at a conference whose submitting population is RF engineers; you hold a world-class Indian speech data advantage (12,000 hours across 22 languages; a 12-language benchmark; open Indic ASR models) and there is an open, published neural-HF-radio codec line of work that has never been taken to Indian code-mixed speech, intelligibility-first objectives, or hostile channels. Mission relevance is immediate — voice is the service commanders actually use. **Risk:** DSP reviewers will scrutinise your channel model; over-invest in that section.

### 4. #5 — Federated and Continually-Learning Spectrum Awareness over DDIL Tactical MANETs
Chosen because it converts a very hot civilian ML topic into a defence-native one with an explicit, freshly-documented gap: tactical ML components today are trained offline and deployed frozen, with no mechanism for nodes to jointly improve — while DDIL is now the operative environment term in industry. Adding the two things civilian FL papers omit (bytes-on-a-tactical-link accounting, and a poisoned participant) gives you two defensible contributions instead of one. Feasible entirely in simulation with public IQ datasets. **Risk:** must not read as "FedAvg on RadioML"; the framing discipline is everything.

### 5. #2 — Post-Quantum Cryptography on Constrained Tactical Links
Included in the top five deliberately as the **risk-adjusted pick**, and it is the one I would actually submit if the 5 August deadline holds. The migration is mandated and time-bound; the standards portfolio is still moving (HQC in 2025, FN-DSA aimed at bandwidth-constrained use, nine more signature candidates advanced in May 2026), which makes crypto-agility the real engineering problem; and nobody has characterised any of this on kilobit-per-second, high-latency, lossy tactical links. It needs no dataset, no GPU and no physics — only careful measurement, which is your strength. Highest acceptance probability in the set, genuine defence utility, and it doubles as a professionally valuable artefact in your day job.

**Honourable mention:** #6 (drone RF open-set) is the single fastest path from zero to a complete, credible, defence-relevant paper if you want maximum result-density in one day of GPU time.

---

# Part VII — Execution playbooks

## VII.1 Decision tree (run this first, today)

```
Check the WiCOMM site now.
│
├── Deadline extended beyond 5 Aug (say to mid/late August)?
│   ├── YES → Build Idea #2 or #16 to completion, and start #3 or #1 for the new date.
│   └── NO  → You have ~48 h. Go to VII.2 and pick ONE of #2 / #16 / #6.
│
├── Is the review double-blind?
│   ├── YES → No self-identifying phrasing; do not post the preprint before notification.
│   └── NO  → Use your institutional affiliation deliberately (see Part VIII).
│
└── Is in-person presentation in Dehradun (30–31 Oct) affordable/approvable?
    ├── YES → Submit.
    └── NO  → Do not submit. Non-presented papers are normally excluded from IEEE Xplore,
              so the credential evaporates. Redirect the work to a venue you can attend.
```

## VII.2 The 48-hour plan (if the 5 August deadline holds)

Pick **one**. Do not attempt two. Ranked by risk-adjusted output:

### Option A (safest) — Idea #2: PQC on constrained tactical links
| Block | Hours | Work |
|---|---|---|
| 1 | 0–2 | Install liboqs / OQS-OpenSSL; verify ML-KEM-768, ML-DSA-65, SLH-DSA-128s, HQC handshakes run locally |
| 2 | 2–5 | Define 4 link profiles (HF 2.4 kbit/s; VHF combat net; SATCOM 500 ms RTT; MANET 3-hop with 10% loss). Script them with `tc`/netem. Write the profile-justification table first — it is your credibility |
| 3 | 5–11 | Automate: for each profile × each suite × 100 trials → handshake completion time, bytes on wire, failure rate. Log to CSV |
| 4 | 11–14 | Sleep |
| 5 | 14–18 | Analysis: CDFs, failure-vs-loss curves, bytes-vs-profile bar charts, rekey-frequency model. 5 figures maximum |
| 6 | 18–24 | Write Sections III–V (method, results, discussion) around the figures |
| 7 | 24–30 | Write Introduction + Related Work + Conclusion. Add the crypto-agility cost model and the deployment-guidance table (this is your novelty claim) |
| 8 | 30–36 | Reference hygiene (cite FIPS 203/204/205, HQC selection, the migration mandate, ITU/waveform sources), IEEE template compliance, page-limit trim, proofread twice |
| 9 | 36–44 | Buffer for the thing that will break. Submit with ≥6 hours to spare |

### Option B (fastest to results) — Idea #16: channel-degraded keyword spotting
Hours 0–3 download Kathbath/IndicSUPERB KWS subset (2 languages is enough — say Hindi + one more); 3–7 build the degradation chain (band-limit 300–3400 Hz → vocoder artefact → Rayleigh/AWGN at −5/0/5/10/15 dB → burst loss → clipping); 7–15 train a small baseline plus an augmentation-aware variant; 15–19 sleep; 19–25 accuracy-vs-SNR-vs-condition tables and curves, per language; 25–34 write; 34–42 polish and submit. **Deliverable claim:** the first radio-degradation benchmark for Indian-language tactical keyword spotting, with a robustness recipe.

### Option C (highest result density) — Idea #6: drone RF open-set / cross-domain
Hours 0–4 acquire DroneRF + one of DroneDetect/RFUAV (check sizes early — this is the only real risk); 4–8 unified preprocessing to matched spectrogram/IQ format; 8–16 train the same backbone on each dataset; 16–20 sleep; 20–26 cross-dataset evaluation matrix + open-set rejection scoring (AUROC for unknown platforms) + interference condition slices; 26–34 write; 34–42 polish and submit. **Deliverable claim:** published near-ceiling accuracies do not survive cross-domain and open-set conditions; here is the measured collapse and a mitigation.

## VII.3 The 10-day plan (if extended, or for your next venue)
Days 1–2 scope + related-work table (20 papers, one row each: method / data / evaluated shift / gap). Days 3–6 implementation and experiments, with a hard freeze at end of Day 6. Day 7 ablations only (one ablation per claim). Day 8 figures final, then write results and method. Day 9 write intro/related/conclusion. Day 10 red-team your own paper against the Reviewer-2 attack listed in your idea's card, fix, submit. This schedule fits Ideas #1, #4, #5, #9, #19, #23, #24, #25, #27, #28, #30.

## VII.4 The 6–10 week plan (for Ideas #3, #1, #4 at journal/MILCOM quality)
Weeks 1–2: literature map + reproduce one baseline exactly. Weeks 3–5: build the pipeline; freeze the evaluation protocol *before* seeing results (write the results tables with blank cells first — it prevents unconscious cherry-picking). Weeks 6–7: generalisation experiments (the cross-region/cross-day/held-out axis that carries your novelty). Week 8: uncertainty/robustness analysis. Weeks 9–10: writing, code release, internal review by two people who will be rude to you.

## VII.5 Paper skeleton for a 6-page IEEE submission

| Section | Words | Content and the specific mistake to avoid |
|---|---|---|
| Title | ~12 | Name the *communications* problem and the defence context. Avoid "novel", avoid architecture names |
| Abstract | 150–200 | Problem → gap → what you did → **one quantitative headline result** → why it matters militarily. Reviewers decide here |
| I. Introduction | 500 | Operational scenario in the first two sentences (mountain relay, jammed net, HF voice link). Then the gap. Then a bulleted contribution list of exactly 3–4 items |
| II. Related Work | 400 | A comparison **table**, not prose. Columns: work / method / data / condition evaluated / what's missing. Your row is the last one |
| III. System Model / Method | 700 | Notation, assumptions **stated as assumptions**, architecture figure. If it is simulated, say "simulated" here — not in the limitations paragraph |
| IV. Experimental Setup | 400 | Datasets/simulators with versions, splits, hyperparameters, hardware, seeds. This is where reviewers judge whether you are serious |
| V. Results | 900 | 4–6 figures/tables maximum. Every figure answers one question posed in the introduction. Include the baseline you might lose to |
| VI. Discussion & Limitations | 300 | Volunteer your two biggest weaknesses. This *increases* acceptance probability at systems-lab venues; hiding them invites a reject |
| VII. Conclusion & Future Work | 200 | One paragraph, plus the hardware/measurement validation roadmap |
| References | — | 20–30. Include recent 2025–2026 work (reviewers check whether you know the current state), the relevant standards documents, and at least a few Indian/DRDO-context citations |

## VII.6 Reviewer-proofing checklist (tick every line before submitting)

- [ ] Title and abstract name a military communications problem, not an ML technique
- [ ] The word "simulation" appears before the results section, not only in limitations
- [ ] At least one baseline is the method a practising engineer trusts today (ITU-R model, classical detector, Codec 2, CP-SAT, energy detection…)
- [ ] Every claim in the abstract maps to a specific figure or table
- [ ] Generalisation is evaluated on something held out (day, receiver, region, jammer, dataset) — this single item separates you from most submissions
- [ ] Compute/latency/complexity budget is reported (defence reviewers think about the platform)
- [ ] Assumptions are enumerated in a list
- [ ] Two limitations volunteered
- [ ] Reproducibility statement (code/config availability, seeds, versions)
- [ ] 2025–2026 references present; standards cited correctly (FIPS numbers, ITU-R recommendation numbers, 3GPP releases)
- [ ] IEEE template unmodified; page limit respected; figures legible in greyscale at print size
- [ ] No plagiarism, no recycled text; every figure is yours
- [ ] Anonymised if double-blind; affiliation cleared if not (Part VIII)
- [ ] One author can and will present in Dehradun on 30–31 October

---

# Part VIII — Risks, ethics, and the things that can actually hurt you

**1. Dual-use framing discipline.** Everything in Tracks 2 and 4 sits near electronic warfare. Write every paper from the **defensive/resilience** side: detect jamming, survive jamming, authenticate emitters, assure AI, plan links. Do not publish anything that reads as an operational attack recipe (optimal jamming strategies against a named system, exploitation of a specific fielded waveform). This is both the right call ethically and materially better for acceptance at a defence venue, where offensive specifics belong in classified channels, not IEEE Xplore.

**2. Use only open, publicly releasable inputs.** Public datasets, published standards, open DEMs, open simulators, published DRDO press material. Do not use, infer, or appear to use non-public parameters of Indian systems. If a reviewer suspects restricted material, your paper becomes a problem rather than a contribution.

**3. Employer IP and affiliation.** You are an AI Engineer at a cybersecurity company. Before you put any affiliation on a submission, get written clearance from your reporting line (Ariza) on: (a) whether you may publish, (b) which affiliation to use, (c) confirmation that nothing internal — no internal project names, architectures, customer data, or classified internal terminology — appears anywhere in the paper. Ideas #8, #24 and #27 sit closest to your employer's domain and therefore need the clearest separation: build them entirely from public data and your own code. If clearance is slow, submit under your university affiliation with work done on your own time and resources, and say so.

**4. Authorship.** A single-author student conference paper is entirely normal. If a faculty member from NCU adds genuine value (review, framing, sanity checks on the communications theory), include them — a co-author who can defend the DSP section is worth a lot in review. Do not add anyone who contributed nothing.

**5. The overclaiming trap.** The most common cause of rejection at systems-lab venues is a mismatch between claim scale and evidence scale. "We show that X degrades by Y% under condition Z in simulation" is publishable. "We solve tactical anti-jamming" is not.

**6. Cost and logistics risk.** Registration + travel to Dehradun for 30–31 October is a real cost. Confirm the student fee and whether your employer or university will fund it *before* submitting, because withdrawal after acceptance wastes a reviewer's time and your own goodwill.

**7. Single-point-of-failure risk in a 48-hour build.** Dataset download failure and toolchain installation failure are the two things that will kill you. Option A (#2) has near-zero acquisition risk, which is precisely why it is the recommended sprint target.

---

# Part IX — Evidence base

**Venue and host lab.** DRDO's WiCOMM-2026 call for papers (conference identity, record no. 69954, IEEE UP Section technical co-sponsorship, 30–31 October 2026, extended deadline 5 August 2026); DEAL's published charter (SATCOM and surveillance, software radios, data links, microwave/mm-wave, satellite image processing, troposcatter); DEAL's origin as the Himalayan Radio Propagation Unit and its jam-resistant data-link mandate; DEAL's 2025 field trials of a compact SDR and transhorizon backhaul in Joshimath; the DEAL-led SATCOM datalink waveform programme for Tejas Mk2/AMCA; DRDO's completed military field trials of a fibre QKD system with Taqbit Labs and its stated multi-hop objective; the DRDO–IIT Delhi >1 km free-space entanglement demonstration (~240 bit/s, <7% QBER).

**Standards and policy.** 3GPP Rel-18 AI/ML air-interface study (CSI feedback, beam management, positioning); Rel-19 normative AI/ML beam management, positioning and CSI prediction; Rel-20 two-sided CSI compression work and the formal 6G study phase; Rel-20 public-safety-relevant features (ProSe multi-hop, NTN integration, ISAC, Ambient IoT). NIST FIPS 203/204/205 (Aug 2024) with key/signature sizes; HQC selected March 2025; FIPS 206/FN-DSA targeted at bandwidth-constrained applications; nine additional signature candidates advanced to a two-year third round in May 2026; the June 2026 executive order mandating accelerated federal PQC migration; crypto-agility identified as the operational bottleneck.

**Research state of the art and self-critique.** AMC dataset and protocol critiques (single-modulation captures, missing signal parameters, absent uniform splits); radio-map benchmarks and their limitations (RadioMapSeer scale and lack of vertical/multipath information; ICASSP path-loss challenges; explicit simulation-to-simulation framing); RF fingerprinting/SEI domain-shift literature (cross-day drift, shortcut learning, cross-receiver generalisation, open-set/OOD detection, LLM-assisted interpretability); drone-RF datasets and their diversity limits (DroneRF, DroneDetect, RFUAV, UAVSig, CrossRF cross-channel results); anti-jamming DRL lineage from the spectrum-waterfall DQN onward and its extensions; covert/LPD communication theory lineage; adversarial ML in wireless and O-RAN (survey findings on xApp attacks and federated-learning threats; demonstrated DRL xApp backdoors with success rates up to 0.9 on a live near-RT RIC); semantic and goal-oriented communication surveys, metrics and the emerging underwater framing; ISAC AI tutorials and open-challenge inventories; RIS AI surveys and codebook-based overhead reduction; telecom LLM/agent surveys and 2026 industrial benchmarks showing the linguistic-vs-procedural execution gap; hierarchical federated learning over tactical MANETs (offline-trained frozen classifiers as the stated gap); DDIL multi-transport orchestration in current industry practice; underwater acoustic DL receivers on WATERMARK and BELLHOP/VirTEX/WOSS channel-modelling practice; Sionna RT/PHY/SYS as a differentiable, GPU-accelerated toolchain including ns-3 integration for digital network twins; neural speech over HF radio (RADE/RADAE, Codec 2 baseline, ITU-R F.1487 channel simulation, Whisper-based evaluation) and the 2025 Low-Resource Audio Codec Challenge; Indian speech resources (IndicVoices 12,000 h/22 languages; Kathbath 1,684 h and the IndicSUPERB 6-task benchmark; Vistaar's 59 benchmarks and >10,700 h; VAANI 2,043 h/105 languages; IndicWhisper); QKD network simulators and standards (QKDNetSim, NetSquid, SeQUeNCe, QuISP, NuQKD; ETSI GS QKD 014/015; hybrid QKD-PQC key delivery).

---

# Appendix A — Tool and dataset quick reference

| Need | Use | Cost | Notes |
|---|---|---|---|
| Link-level / PHY simulation | **Sionna** (PHY, SYS, RT) | Free, GPU-friendly | Differentiable; ray tracing; RIS support; ns-3 bridge exists |
| Network simulation | **ns-3**, or netem/`tc` for quick link emulation | Free | netem is enough for PQC link profiles |
| Quantum networks | **QKDNetSim (ns-3)**, **SeQUeNCe**, **NetSquid**, QuISP | Free (some academic licences) | Model trusted-node multi-hop; ETSI 014/015 as the control interface |
| PQC primitives | **liboqs / OQS-OpenSSL** | Free | ML-KEM, ML-DSA, SLH-DSA, HQC; hybrid modes |
| Signal datasets | RadioML 2016/2018, HisarMod, DroneRF, DroneDetect(V2), RFUAV, UAVSig | Free | Read the metadata critiques before trusting the numbers |
| Propagation / terrain | SRTM & Copernicus DEM, OpenStreetMap, GDAL/rasterio; ITU-R P.452/P.526 implementations | Free | Basis for Idea #3 |
| Underwater | **WATERMARK** (measured at sea), **BELLHOP**/Acoustics Toolbox, `arlpy`, WOSS | Free | Basis for Ideas #12–13 |
| Speech | IndicVoices, Kathbath/IndicSUPERB, Vistaar, VAANI, IndicWhisper; Codec 2 / RADAE as radio baselines | Free | Basis for Ideas #4, #16, #17 |
| RL | Gymnasium, Stable-Baselines3/CleanRL; CQL/IQL for offline | Free | Basis for Ideas #9, #14, #28 |
| Optimisation baselines | OR-Tools CP-SAT, NetworkX, CVXPY | Free | Always include the classical baseline |
| Local LLM | Ollama / llama.cpp + small open models | Free | Basis for Ideas #7, #30 |
| Compute | Colab/Kaggle GPU is sufficient for Ideas #2, #6, #16, #17, #25, #30 | Free | Ideas #3, #21, #22 benefit from a real GPU |

# Appendix B — One-line summary of every idea

| # | Idea | Track | Comp. | Accept. | Fit |
|---|---|---|---|---|---|
| 1 | Key-rate-aware routing + hybrid QKD/PQC fallback for multi-hop tactical quantum networks | 2 | Low | 85–90% | 9.3 |
| 2 | PQC on constrained tactical links: crypto-agility and overhead study | 2 | Low–Med | 85–92% | 9.2 |
| 3 | Terrain-aware learned propagation surrogate for mountainous link planning | 4 | Low | 85–90% | 9.2 |
| 4 | Neural speech over HF/VHF for code-mixed Indian tactical voice | 4 | V.Low | 80–88% | 9.0 |
| 5 | Federated + continual spectrum awareness over DDIL tactical MANETs | 2 | Low–Med | 80–88% | 8.9 |
| 6 | Open-set, cross-domain drone RF identification for counter-UAS | 4/2 | Med | 80–88% | 8.8 |
| 7 | Doctrine-grounded LLM copilot for spectrum/EW planning + benchmark | 2 | Low | 72–82% | 8.7 |
| 8 | Backdoor/poisoning resilience of AI control loops in the radio stack | 2 | Low–Med | 78–86% | 8.6 |
| 9 | Generalisation-first anti-jamming RL (held-out jammers, offline RL) | 4 | Med–High | 78–86% | 8.5 |
| 10 | Cross-day / cross-receiver domain generalisation for emitter ID | 4 | Med–High | 75–85% | 8.4 |
| 11 | Semantic transmission of tactical situation reports at ultra-low rate | 4 | Med | 72–82% | 8.3 |
| 12 | Underwater acoustic receiver with physics-informed sim-to-real transfer | 4 | Low | 78–86% | 8.2 |
| 13 | Goal-oriented semantic messaging for AUV telemetry | 4 | V.Low | 72–82% | 8.0 |
| 14 | Safe RL for priority-assured tactical slicing | 2 | Med | 76–84% | 8.0 |
| 15 | Network digital twin: quantifying the twin-to-reality gap | 2/4 | Low–Med | 76–84% | 7.9 |
| 16 | Channel-degraded keyword spotting / priority-voice triage | 4 | V.Low | 80–88% | 7.9 |
| 17 | Channel-robust speaker verification for tactical voice nets | 4 | V.Low | 78–86% | 7.8 |
| 18 | Self-supervised detection of LPI waveforms below the noise floor | 4 | Low | 74–84% | 7.8 |
| 19 | Quantum-resistant group key management for swarms/MANETs | 2 | Low | 78–86% | 7.7 |
| 20 | GNN-based brigade-scale spectrum deconfliction | 2/4 | Low–Med | 76–84% | 7.6 |
| 21 | Position/attitude-aided beam prediction for airborne datalinks | 4 | Med–High | 74–84% | 7.5 |
| 22 | RIS control learning for anti-jamming/covert links, EM-consistent | 5 | Med–High | 70–80% | 7.4 |
| 23 | Data-driven phased-array fault diagnosis and pattern recovery | 5 | Low | 76–84% | 7.3 |
| 24 | Encrypted-traffic / covert-channel detection for tactical IP nets | 2 | Med | 76–84% | 7.2 |
| 25 | Cross-dataset reality check and open-set protocol for deep AMC | 4 | Low (framing) | 76–84% | 7.1 |
| 26 | Learned co-channel signal separation for congested spectrum | 4 | Low–Med | 72–80% | 7.0 |
| 27 | Attestation and provenance for AI models in the radio stack | 2 | V.Low | 72–80% | 6.9 |
| 28 | Jamming-aware multi-path transport selection (DDIL) | 2 | Low | 74–82% | 6.8 |
| 29 | Sim-to-real transfer study for neural receivers | 4/2 | Med | 70–80% | 6.7 |
| 30 | On-device small language model for offline tactical network ops | 2 | Low | 70–80% | 6.5 |

---

*Prepared 3 August 2026. All acceptance probabilities are structured estimates, not measured rates. All external facts are drawn from public sources; verify conference logistics on the official WiCOMM-2026 site before acting.*

I've finished the research. Before the report, one thing you need to see immediately:

**The extended submission deadline for IEEE WiCOMM-2026 is 5 August 2026 — that's 2 days from today.** DRDO's own announcement lists it as: IEEE International Conference on Wireless Communication for Military Applications (WiCOMM-2026), Defence Electronics Applications Laboratory Dehradun, Conference Record No. 69954, technically co-sponsored by IEEE Uttar Pradesh Section, in collaboration with the Society of Wireless Communication Engineers, 30–31 October 2026, physical mode, with an extended submission deadline of 5 August 2026.

That single fact reshapes the entire ranking, so the report ranks ideas twice: on pure research merit, and on what you can actually land in 48 hours. Let me build it.~18,000 words, 30 fully-specified ideas, all five leaderboards. The four things worth pulling out of it:

**1. The deadline is the binding constraint.** Extended deadline 5 August 2026, conference 30–31 October in Dehradun, physical mode. Check the site today for a further extension — if there isn't one, you have roughly 48 hours, and that changes which idea you should write.

**2. Your biggest edge is the host lab, not the technique.** DEAL began life as the Himalayan Radio Propagation Unit; its charter is SATCOM/surveillance, software radios, jam-resistant data links, mm-wave and troposcatter; it field-trialled a compact SDR and a transhorizon backhaul system in Joshimath; it leads the SATCOM datalink waveform for Tejas Mk2/AMCA; and DRDO just completed military field trials of an indigenous QKD system while naming multi-hop quantum networks as the next step. Papers pointed at those things get read by people who care. Generic AI-for-6G papers get triaged.

**3. Top 5 on merit** — terrain-aware learned propagation for mountainous tactical links; key-rate-aware routing with hybrid QKD/PQC fallback; neural speech over HF/VHF for code-mixed Indian voice; federated spectrum awareness over DDIL MANETs; PQC overhead and crypto-agility on constrained tactical links.

**4. Top pick for 48 hours: the PQC study.** No dataset to download, no GPU, no physics — liboqs plus netem link profiles, and the output is exactly the kind of clean measurement table a systems-lab reviewer trusts. Estimated 85–92% acceptance. Two alternates with similar risk profiles: channel-degraded keyword spotting on Kathbath (you'd likely be the only speech submission in Track 4), or the cross-domain/open-set drone-RF study.

Two cautions in the report you shouldn't skip: keep every paper framed defensively rather than as an attack recipe, and get written clearance from Ariza before putting a HivePro affiliation on anything in the security-adjacent lanes (Ideas 8, 24, 27) — build those purely from public data and your own code.

Tell me which idea you want and I'll build the paper with you — related-work table, experiment scripts, and draft sections.

Straight answer first, then I'll build both.**The honest answer to your core question, up front:** no — you cannot write these two papers "directly" without producing results. Not because of any rule about paper *type*, but because both drafts contain claims that only numbers can support, and inventing numbers for an IEEE submission is research misconduct with a permanent cost. What you *can* do is produce real results in hours rather than weeks, because both ideas were selected precisely for that property. Let me prove it by building them now.Pipeline works, but the key economy isn't binding — everything succeeds, so the policies look identical. That's the uninteresting regime. Let me put the network under realistic key scarcity, and add hop-accounting (trusted relaying multiplies key cost per hop, which is the physics that makes this problem hard).Idea 1 now has real, coherent results — including an honest trade-off rather than a magic win. Now Idea 3's pipeline. One constraint I have to flag: my sandbox can only reach package repositories, **not** DEM servers, so I'll build and validate the full pipeline on synthetic fractal terrain and hand you a drop-in loader for real SRTM tiles (a 20-minute job on your machine, and mandatory before you claim "Himalayan").The physics labels are misbehaving (mean 97 dB diffraction loss is unphysical — my Deygout recursion over-counts, and the terrain grid is smaller than the link ranges). Also, the "cross-region" test is accidentally *easier* than training, and the 90% intervals only cover 68%. All three would be fatal in review. Fixing properly:All artefacts are real and consistent. Now the three documents: the fact-check you asked for, and the two paper drafts populated with these actual numbers.**Your question, answered directly: no, you cannot write either paper without producing results — but you don't need weeks either. Both experiments now exist, ran in under a minute each, and produced real numbers.**

The reason is specific to *these* ideas. A survey or position paper needs no experiments, but both of your choices make quantitative claims — "this routing policy beats that one," "this surrogate approximates the physics within X dB." Those claims *are* the contribution; without measurements there's nothing to review. And inventing numbers at an IEEE venue is fabrication, detectable at camera-ready and fatal in exactly the community whose confidence you're trying to build.

**What Paper 1 (QKD/PQC) found — complete, needs nothing external:**
- Key-rate-aware routing lifts command-traffic service from 93.1% → 97.3%, pooled 82.8% → 86.7%
- But it consumes **14.4% more key**, because avoiding depleted links means longer paths, and trusted relaying multiplies key cost per hop. An honest trade-off, not a magic win
- Class-aware reservation + ML-KEM fallback: 100% availability, but only 85.1% quantum-keyed — availability bought with a *quantified* security-grade downgrade
- Under 16× disruption: C2 collapses to 44% (shortest-path) / 56% (key-aware); hybrid holds 100% with 33.6% falling back
- **Derived requirement:** at the ~240 bit/s reported for free-space demos, only 42–46% of OTP-grade ISR sessions can be quantum-keyed; ~960 bit/s per hop is needed for >90%

**Paper 2 (terrain surrogate) — one blocking gap:** my sandbox can't reach DEM servers, so it ran on synthetic fractal terrain. Physics, features, conformal calibration, cross-region protocol, timing: all real. Terrain: a stand-in. So **you cannot write "Himalayan" until you swap in real SRTM tiles** (~30 min via OpenTopography or Bhoonidhi) and re-run. Results found: 5.86 dB MAE in-region, 8.22 dB cross-region (+40%, biased *optimistic* — the dangerous direction), conformal coverage 91.3% → 83.1% under terrain shift, false-go rate 5.5% → 9.2%.

Along the way I had to fix three things that would have been fatal in review: unphysical 97 dB mean diffraction losses (over-counting Deygout recursion), a "cross-region" test that was accidentally *easier* than training, and 90% intervals covering only 68%.

**My recommendation, which contradicts your plan slightly:** submit Paper 1 only. It's finished and needs no external data. Then spend the leftover hours on Paper 2's DEM swap — submit it too if it comes out clean, but if it doesn't, take it to CONECCT or NCC 2027 where you can add measurement validation. It's the higher-ceiling idea; don't burn it on a rushed six pages.

Two things before you write: get Ariza's written clearance on publishing and affiliation, and verify every reference yourself — I've given you leads I believe are correct, but open each one. An unverified citation is the easiest thing for a reviewer to catch.