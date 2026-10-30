# A Beginner's Guide to Paper 167

**"Fail-Closed or Fail-Degraded? A Simulation Study of Forced Assurance Loss in Contested Multi-Hop QKD Networks"**
Lakshya Jain and Siddhi Arora, WiCOMM 2026

This guide assumes no physics or cryptography. It builds the background first, then walks through the paper in its own order. Every number comes from the camera-ready `paper.tex`. Where I use an everyday comparison, I label it **Analogy** so you never mistake it for a claim of the paper.

---

## 0. The paper in one paragraph, and a gentle correction

Some secure networks distribute secret keys using quantum physics, passing each key along a chain of relay sites. Every hop spends stored key, so the supply can run out, and an attacker can drain it faster by adding noise to selected links. When key runs short, the network can **fail closed** (refuse the request, so everyone sees an outage) or **fail degraded** (quietly switch to a weaker, computationally secure method and keep serving). The authors simulate both on an eight-node tactical network and four other graphs. If an attacker holds the network's weakest "cut" for 24 hours, fail-closed service collapses from 97.5% to 6.7%, while fail-degraded still serves 97.5% but only 6.6% at the protection level the traffic was entitled to. About 90.1% of traffic entitled to the strongest kind of key ends up with something weaker. The attack only works if the attacker has the right capability, targets the right links, and lasts longer than the stored key. The advice: report the protection grade of served traffic, not only whether it was served.

**A correction to your starting assumption.** You described the domain as "quantum computing and the integration of AI in it". That is not quite right, and it is worth fixing before the talk. The paper is about quantum **communication** security: specifically **quantum key distribution (QKD) networks with trusted relays**, plus **post-quantum cryptography (ML-KEM)** as the fallback when quantum key is short. Quantum *computers* appear only as the reason today's public-key cryptography is under threat. No quantum computer is built or simulated, and no photonics is simulated at all.

The "AI" part is small. It is a tiny learned controller, a lookup table found by a simple search (the cross-entropy method) behind a safety shield, which the authors **audit** against a plain heuristic. It is one of five contributions and occupies one subsection (Section V-E). If someone asks about "AI in quantum", the honest answer is that a very small piece of machine learning is used to test how much room a simple heuristic leaves, and the gain is small and has a cost.

---

## Part 1. Background, step by step

### 1.1 Encryption and keys

A **bit** is a 0 or a 1. **Encryption** scrambles a readable message (the **payload**) so an eavesdropper sees nonsense. A **key** is a secret bit string that sender and receiver share to scramble and unscramble. *Analogy:* a key is a lock combination that both of you know and nobody else does. The practical difficulty is getting fresh shared secrets to both ends, which is what the rest of this part is about.

### 1.2 Why quantum computers threaten today's public-key cryptography

Today most key exchange uses **public-key cryptography**: maths problems that are easy one way and believed very hard to reverse. A large quantum computer could in principle reverse the problems that current systems rely on (general background, not a paper claim). Two responses follow. **Post-quantum cryptography (PQC)** uses new maths problems believed to resist quantum computers, and runs on ordinary computers and links. **Quantum key distribution (QKD)** makes keys whose secrecy rests on physics instead. The paper uses QKD as the strong, scarce option and PQC as the cheap fallback.

### 1.3 The one-time pad and information-theoretic security

A **one-time pad (OTP)** combines your message with a random secret string as long as the message, used exactly once. The result carries no information about the original, **even for an attacker with unlimited computing power**. That property is **information-theoretic security (ITS)**. *Analogy:* a disposable notebook of codebook pages; tear one out, use it once, burn it.

The cost is that **key bits spent equal payload bits sent**: protecting a 144,000-bit message burns 144,000 bits of key. A modern symmetric cipher such as AES (background example) protects huge amounts of data with a 256-bit key, but its security is *computational*: it assumes certain calculations are infeasible. So there is a trade-off between key cost and kind of protection, and the whole paper lives inside it.

### 1.4 What QKD is, and why its keys are ITS

**QKD** lets two parties generate a shared random key by sending specially prepared photons and comparing a few results over an authenticated ordinary channel. The principle (general background) is that measuring a quantum state disturbs it, so a listener shows up as extra disagreement. If disagreement is low enough, the parties distil a key and shorten it to remove anything an eavesdropper might know. That key is ITS.

A subtlety the paper keeps: an ITS-**delivered** key does not make the *payload* ITS. Use the key in AES and you have an ITS key under a computational cipher; use it as a one-time pad and the payload itself is ITS. That is why the paper has two QKD-based grades, G1 and G2.

### 1.5 QBER, and why more noise makes a link abort

The **quantum bit error rate (QBER)** is the fraction of compared bits on which the two ends disagree; 0.03 means 3%. Some is normal, and the paper assumes a baseline **e0 = 0.03**. The ends cannot tell harmless noise from an eavesdropper's footprints, so above a threshold they must assume listening and stop making key. The paper takes **e_abort = 0.075** as an engineering value (one real error-correction engine only codes below 7.5%). A baseline link therefore **aborts** once an attacker adds **Δe ≥ 0.075 - 0.03 = 0.045**. Below that, it keeps producing key, more slowly.

The remaining fraction of the nominal rate is a formula ρ(e) (Equation 1) built on the **binary entropy function H2**. You need not evaluate it: ρ is 1 at baseline, falls as errors grow, and reaches zero. A shape knob **γ** sets how sharply: γ = 1 is the textbook (asymptotic BB84) case, and γ = 3.4 is steeper, matched to one datapoint from another technology and used "for illustration only".

*Analogy:* a phone line with a "listening for taps" alarm. Normal static is tolerated; once static passes a level the alarm cannot tell static from a tap and cuts the call. An attacker who cannot read your calls can still **cut** them by adding static. That is the attack studied here, and it needs no eavesdropping skill, only the ability to inject noise on specific links. (Detector-blinding attacks that raise no QBER are invisible in this model, as the paper says.)

### 1.6 Limited distance, trusted relays, and why every hop spends key

Light is absorbed along the way and a quantum signal cannot simply be amplified (general background), so one QKD link has limited reach. Networks therefore use **trusted relays**: intermediate sites that each hold a QKD link-key with their neighbour. For an end-to-end key, each relay decrypts what it receives and re-encrypts it for the next hop with a one-time pad plus an ITS authentication tag. *Analogy:* a relay race where each runner reads the message on the baton; it works, but you must trust every runner.

So **an n-hop path consumes key on every one of its n links**, each with its own separate store. Free-space links make only around 10² bit/s per hop, so key supply, not connectivity, is the binding constraint. *Analogy:* a toll on every bridge; six bridges cost six tolls, and a full account at the start does not pay the last toll.

Relaying K bits of key across one hop costs **q = K + M_meta + n_auth × t** (Equation 2), where M_meta = 240 bits of metadata, t = 127 bits per authentication tag, and n_auth is the number of authenticated messages per delivery. No specification fixes n_auth: 2 is a lower bound, field data imply about 7, so 7 is the default (2 and 40 are tested). A G2 session thus costs 256 + 240 + 7×127 = **1385 bits per hop**. The overhead exceeds the key itself.

### 1.7 Key as a stock: stock versus generation

Each link has a **key store**, a counter of unused key bits that fills at the link's generation rate and drains as sessions spend it. *Analogy:* a bathtub with a tap (generation) and a drain (use). If someone turns off the tap, the water already in the tub is still there.

The model makes this explicit: generation and **stock** are separate. Store values come from the QKDNetSim simulator: capacity 52,428,800 bits, threshold 11,324,620 bits, and a protected reserve of 1,048,576 bits (the role SECOQC gave to authentication key). Overflow is discarded; the authors found no published capacity from vendors or ETSI. The main runs start every store at a declared **usable fill of 2%** (1.03 Mbit per link), a deliberately stressful scenario. Because stock outlives generation, an attacker who stops generation must then **outlast the stock**. That idea, endurance, is one of the paper's three requirements for forcing a downgrade.

### 1.8 Post-quantum cryptography, ML-KEM, hybrid versus downgrade

**ML-KEM** (here ML-KEM-768) is a post-quantum **key encapsulation mechanism (KEM)**, a method for two parties to agree a shared secret over an ordinary network. (Background: "ML" is module-lattice, not machine learning.) It needs no quantum hardware and, crucially, **no QKD key**, so when quantum key is exhausted an ML-KEM fallback still works, provided a classical path exists and the online key-establishment service is up. Setup takes 0.35 s in the model.

A **hybrid** combiner mixes two sources so the result is secure if either survives. The paper is careful: replacing QKD key with post-quantum key is **not** hybrid, because nothing is combined and the quantum part is gone. It calls this a **labelled grade downgrade**. A post-quantum-only session is probably fine against today's attackers, but it is no longer ITS, which is the very thing a QKD network exists to deliver.

### 1.9 The four grades and the traffic classes with their floors

| Grade | What it is | Quantum key needed |
|---|---|---|
| **G1** | One-time pad | key bits = payload bits |
| **G2** | QKD-keyed 256-bit symmetric cipher (ITS-*delivered* key, computational cipher) | 256 bits (1385 per hop with overhead) |
| **G3** | Hybrid: QKD (128 bits) plus ML-KEM-768 | 1257 bits per hop with overhead |
| **G4** | ML-KEM-768 only | none |

G1 and G2 count as ITS key; G3 and G4 count as below ITS. Each **traffic class** has an **authorised floor**, the lowest grade it may receive:

| Class | Meaning | Request | Floor | Deadline | Arrivals |
|---|---|---|---|---|---|
| **C2** | Command and control | 2048 bits | G2 | 5 s | 0.05 per s |
| **ISR** | Intelligence, surveillance, reconnaissance (OTP voice) | 144,000 bits | G1 | 30 s | 0.002 per s |
| **LOG** | Logistics, delay-tolerant bulk | 320,000 bits | G3 | 120 s | 0.03 per s |

Priority runs C2, ISR, LOG. ISR is set to a tenth of a rate that would exceed six times the supply across the formation's cut; overload (factor 1) and light load (0.03) are sensitivities. These workloads are built from published deployments, not measured military traffic.

The **fail modes** are now precise. If a floor cannot be met, the controller either **blocks at the deadline** (`fail_closed`) or **serves below the floor at once and records an auditable violation** (`fail_degraded`). *Analogy:* a vault that locks when the good lock breaks, versus one that fits a cheaper padlock and carries on without telling customers. The first is annoying but obvious; the second is convenient and invisible until audit.

---

## Part 2. The paper itself

### 2.1 The question

A brigade's command circuits, imagery and logistics all run through a chain of relay sites. If the network cannot supply quantum key for all of it, which failure is worse: a visible outage or a quiet loss of protection found only at audit? And **what must an attacker spend to force the choice**?

### 2.2 The gap in prior work

Four largely separate lines exist: routing, quality of service, exhaustion and fallback, and adversary models. Standards (ITU-T Y.3803), key managers and deployments allow recorded fallback; a layered post-quantum design (Spooren et al.) fails closed as a defence against downgrade attacks; and Schartner and Rass (2010) already warned that an adversary may deny quantum key to force classical cryptography. Almost all work uses one outcome model, **served or blocked**, which counts a post-quantum-only session as served. So **nobody reports how much ITS-entitled traffic was served without ITS**.

**Reading Table I.** Rows are representative studies; columns are dimensions: MH multi-hop, KS scarcity binds, TC traffic classes, AD adversary, SW pressure swept, FB computational fallback, FA assurance loss on entitled traffic. A tick is addressed, a circle partial, a dagger "specified, fails closed". The FA column has no full tick for anyone (the nearest, Zhu, is neither restricted to entitled traffic nor swept). That empty column is the gap on slide 3. The authors hedge with "to our knowledge".

### 2.3 The system model

**The eight-node formation** (Figure 1a): BASE (rear), REL1 and REL2 (relays), BDE1 and BDE2 (brigade nodes), FWD1 to FWD3 (forward posts). One 300 kbit/s fibre (BASE to REL1) and eight free-space links of 200 to 400 bit/s make nine links. Sessions run from the rear to the forward posts and debit every hop.

**The minimum cut.** A **cut** is a set of links whose removal disconnects the graph; the **minimum cut** is the smallest. Here it is two 240 bit/s links, REL1-BDE1 and REL2-BDE2, shown as dashed orange lines with X marks. Every session to the forward posts crosses one, and the fibre's surplus is stranded one hop away. *Analogy:* an island with two small bridges; close both and no highway behind them helps. Four more graphs add variety: a depth-d chain with one longer alternate (T2), an eight-node ring, a 3×3 grid, and 3- and 4-path parallel graphs (240 bit/s links), with minimum cuts of two, two, three and four.

**Three failure surfaces** (Figure 1b), kept separate because they stop different things:

1. **Quantum channel** (QBER too high): stops fresh key (the link is in ABORT); stored key above the reserve, classical relay and fallback still work.
2. **Classical transport denial**: stops relaying and fallback (OUTAGE); stored key is retained.
3. **Online key-establishment denial**: stops KEM fallback (G3, G4); QKD-keyed G1/G2 and pre-placed symmetric keys still work.

A link is therefore NOMINAL, DEGRADED, ABORT or OUTAGE.

**The adversary** injects extra error Δe on links it buys, at relative cost 1 per free-space link and 10 for the fibre (1 and 100 as sensitivities; scenario weights, not measured spending). It picks targets by **static betweenness per unit cost** (betweenness is how many shortest paths use a link, ranked once), **residual betweenness** (recomputed after each removal), the **cost-weighted minimum cut**, or **online** from committed routes it observes, updating every 60 s.

### 2.4 The metrics

Of N arriving requests, let S be those served within deadline and D ⊆ S those served below their floor (Equation 3):

- **A = |S|/N**, availability;
- **Q = |S∖D|/N**, compliant service;
- **L = |D|/N**, below-floor service.

So **A = Q + L**. This equation is the heart of the argument: availability mixes good and bad service; splitting it exposes the damage.

**Forced assurance loss, F.** Take requests **entitled** to ITS key (floors G1 or G2, so C2 and ISR). F is the number served at G3 or G4 divided by **all** entitled arrivals, blocked ones included. That shared denominator makes the fail modes comparable: fail-closed has F = 0 by construction but serves far less. Subtle case: an ISR request served at G2 misses its G1 floor (counted in L) but keeps an ITS-delivered key, so it is **not** in F. **F_B** weights by payload size, and class weights (5, 2, 1) and (10, 3, 1) for (C2, ISR, LOG) give two more "exposure proxies".

**Downgrade-forcing cost, k\*:** the smallest attack budget whose mean forced loss reaches 50% within 24 hours. Larger k\* means harder to force.

**The cut condition and T\*.** Equation 4 is an accounting argument. Every compliant session finishing by time T must spend at least its floor cost from some cut link, so total compliant spending cannot exceed the stock at the start plus what the cut links generate. If the attacker holds every cut link past abort, generation is zero, and compliant service lasts at most

**T\* = (usable stock behind the cut) / (average demand D̄).**

*Worked example.* Two cut links hold about 1.03 Mbit each, roughly 2.06 million bits. Average demand at the cut is D̄ ≈ 397 bit/s: C2 about 0.05 × 1385 ≈ 69, ISR about 0.002 × 145,129 ≈ 290, LOG about 0.03 × 1257 ≈ 38 (my arithmetic from the paper's inputs; it reproduces the paper's 397). So T\* ≈ 2.06 million ÷ 397 ≈ 5,200 s ≈ **1.44 hours**, the paper's figure. Over a full 24 hours the stock can fund only about 2.06 million ÷ (397 × 86,400) ≈ 6% of demand, matching the predicted **6.0%** fail-closed service. The condition is necessary, not sufficient: stock may sit on the wrong hop (a test graph of three two-hop branches strands 400 bits per branch and serves six requests where the bound allows seven).

### 2.5 Experimental setup and validation

**Setup.** Discrete-event simulation at 1 s resolution. Admission checks every hop before debiting any, and a pending request retries until its deadline; G3/G4 must also finish the 0.35 s online setup. Arrivals and the attack last 24 h. Free-space generation and each link's transport fail independently (mean up 3600 s, down 120 s); a severe-weather variant uses 900 s up, 600 s down, independently or all free-space generation together. A declared initial fill replaces a warm-up.

**Paired design.** Under **common random numbers**, every policy and attack sees identical arrivals and environment per seed, so attack effects are paired differences against the unattacked run. Reports are means with **95% percentile bootstrap intervals** (20,000 resamples) over twelve seeds (main grid, routing, floors, code comparison), eight (sensitivities) or six (online adversary, abort sweep). *Analogy:* give every student the same exam twice, with and without a disturbance, and compare each student to themselves.

**Validation, and why V2 and V3 "fail" honestly.** No established simulator models a trusted-relay key economy, so a **43-check gate and 127 regression tests** run before every result, and four published measurements test the accounting:

- **V1** (SECOQC rerouting) matches to the second, which only checks arithmetic.
- **V4** (one-time-pad demand law) is bounded to an order of magnitude (1.2 to 12.6 voice pairs against eleven).
- **V2** (Cambridge): relaying cost 3.69 times the delivered key, against 2.23 times in the model at n_auth = 2.
- **V3** (SECOQC tunnel): 91.2% of the rekey budget went to authentication overhead, against 65.9% in the model.

V2 and V3 miss **in the same direction**: reality spends more key on overhead than n_auth = 2 implies. Solved for n_auth they give about 7 per hop and 40 per tunnel. Neither pins the count down, but both show the bias, hence the default of 7. Reporting a mismatch and letting it drive a parameter choice is the honest move.

### 2.6 The results

#### R1. The fail-mode exchange rate (Table II)

**Reading Table II.** The first five rows are fail-closed ("closed"), the next five fail-degraded ("degr."). "Target" is who the attacker aims at: none, the cut first ("cut"), or the static-betweenness ranking ("betw."). **b** is the budget, so b = 2 buys the whole cut. A, Q and per-class Q are percentages of arrivals, F is a percentage of entitled arrivals, and the last column is the percentage of *served* sessions at G4. Bootstrap half-widths are at most 1.0 point, except ISR's Q (about 175 ISR arrivals per seed).

| Condition | Closed A | Degraded A | Degraded Q | F |
|---|---|---|---|---|
| No attack | 97.5 | 97.5 | 97.5 | below 0.1 |
| Cut, 1 link | 92.9 | 97.5 | 91.7 | 4.8 |
| Cut, 2 links | **6.7** | **97.5** | **6.6** | **90.1** |
| Betweenness, 2 links | 38.2 | 97.5 | 38.0 | 59.0 |

Holding the two-link cut for 24 hours drops fail-closed service from 97.5% to 6.7%. Fail-degraded serves 97.5% but only 6.6% at grade (paired ΔQ = -0.09 points, interval -0.11 to -0.07). The fallback turns 90.8 points of refused service into below-floor service and forces **90.1%** of entitled requests below ITS (interval 89.2 to 91.0; 90.3% payload-weighted), almost all at G4 (93.2% of served sessions) because G3 still needs 1257 bits of quantum key per hop.

With **one** cut link held, a second mechanism appears. Fail-closed service falls 4.6 points and ISR loses half its service (50.9%) because its 145 kbit debits no longer fit one 240 bit/s link. Fail-degraded forces 4.8% below ITS, and its compliant service ends 1.2 points **below** fail-closed's (interval -1.4 to -1.1), because it downgrades at once requests that waiting would have served. The static-betweenness adversary buys BDE1-BDE2 and BDE1-REL1, isolating FWD1 and FWD2 but not FWD3, and forces 59.0%; its first link alone costs fail-closed service 0.7 points.

Without an attack, F is 0 for fail-closed and 0.002% for fail-degraded (one request in twelve runs). ISR meets its OTP floor for 97.0% of arrivals, against 12.6% at factor 1, so a G1 floor fails through overload, not by design.

#### R2. Scaling over five graphs (Figure 2)

With budget equal to the cut, F is **87.6 to 92.9%** on all five graphs, and fail-closed service is roughly stock divided by demand: kU/(D̄T) predicts **6.0, 9.0 and 12.0%** for two-, three- and four-link cuts against **6.5 to 6.7, 9.6 and 12.3%** observed (slightly higher, since leftover stock serves cheaper requests once ISR's large debits stop fitting).

**Reading Figure 2.** Panel (a) plots predicted against observed service for the five graphs; the dashed line is perfect prediction, and points near it show the formula works. Solid markers are fail-closed A and hollow ones fail-degraded Q; sitting together is the Q-versus-A story again. Panel (b) plots forced loss (log scale) against residual supply (k-1)R/D̄ when one cut link is suppressed; the dotted line is supply equal to demand. Graphs left of it (formation, ring, grid) show large loss, those right of it (3-path, 4-path) almost none: 4.8 to 11.5% on two-link cuts, 0.71% and 0.05% elsewhere.

#### R3. Key-aware routing

Key-aware routing chooses paths using available key. Because a post-quantum fallback succeeds wherever a classical path exists, fail-degraded availability is identical to shortest-path routing (an identity of the model, not measured precision). Q still separates them: +0.12 points (interval 0.05 to 0.19) at the price of 5.0 Mbit (interval 2.3 to 7.7) more key per day, since its routes can be longer. At ISR factor 1 it loses 2.6 points of fail-closed service, but only after a 12 h warm-up from full stores; from t = 0 it gains 0.08, from 2% fill 0.11 to 0.13. So the penalty is a warm-up transient, and the 25 to 40% gains in earlier work measure blocking without a fallback.

#### R4. Reservation floors

Reserving 20 and 40% of each store against ISR and LOG is an admission decision, not a graded control. At 2% fill it denies logistics its quantum key (fail-closed service -37.6 points, logistics 98.9% to 0%) and fail-degraded forces 2.1% below ITS with **no adversary**; at full stock it has no effect. Under the cut it buys endurance: +14.3 points (interval 13.4 to 15.2) and F down from 90.1 to 63.6%, because logistics' hybrid debits stop draining the cut.

#### R5. Depth and online adversaries (Figure 3)

**Reading Figure 3.** The horizontal axis is chain depth d; the vertical axis is **k\***, the fewest links to force half the entitled traffic below ITS. A rising line means deeper is safer; a flat line means depth does not help.

For d ≥ 2 every chain link lies on one cycle with equal betweenness, so a static ranking is decided by tie order. The authors' order needs **d + 2** links (another needs d + 1). Residual betweenness needs only the two-link minimum cut **at every depth d ≥ 2**. An online adversary that keeps its slots holds the cut from its first choice (89.7 to 92.9% at depths 2, 4, 6; 48 link-hours); if it releases slots when its path is briefly unreachable, loss falls with depth from 72.3 to 35.5%. So linear growth under static ranking overstates resilience: against residual betweenness or a cut-holding adversary, **depth buys no protection**. Per-link cost matters: with the fibre 10 or 100 times dearer, residual betweenness avoids it and forces 10.1% at budget two instead of 89.8%.

#### R6. Capability and threshold (Table III)

**Reading Table III.** Each cell is F (%) after a 24 h outage-free attack from 2% fill over eight seeds, with a 95% interval. Rows are graph and budget b; columns are injected Δe. The left four columns use γ = 1, the right two γ = 3.4.

At γ = 1 the response is a cliff: below Δe = 0.045, F is under 0.1%; at or above it, with the cut covered, F is 93.1% (formation), 90.4% (3-path) or 87.7% (4-path). Budgets beyond the cut add nothing, and one link short forces under 0.1%. (93.1% is outage-free with eight seeds; Table II's 90.1% includes outages and twelve seeds.) At γ = 3.4 the attack bites earlier: Δe = 0.03 forces 63.0, 41.6 and 17.3% at the three cuts without aborting a link, and Δe = 0.04 forces 88.8, 83.8 and 78.2%. So the response shape matters below the abort threshold, not above it. Loss is forced once the cut's residual supply nears the entitled classes' cheapest ITS demand (about 72 bit/s, C2 plus ISR at G2) plus competing hybrid debits. Raising e_abort to 0.11 moves the threshold to Δe = 0.068, not 0.08, because the formula's own zero (at a QBER of 9.8%) comes first; Δe = 0.06 already forces 40.9% on the three-link cut.

#### R7. Endurance

Initial fills of 2, 10 and 100% give F = 89.9, 65.4 and 0%. Attacks of 1, 6 and 24 h at 2% fill give 0.06, 17.6 and 89.9%, with first forcing after about 1.5 h, the T\*. The bound predicts 7.2 and 72 h at 10 and 100% fill; the simulation shows a median first forcing of 6.6 h and none within 24 h. Stock also matters from full stores: at ISR factor 1, n_auth = 2, after a 12 h warm-up and under the two-link betweenness attack, treating an aborted link's stock as unusable leaves 30.4% fail-closed service and F = 65.1%, while spending it gives 76.7% and 4.1% (paired +46.4 points, interval 45.8 to 46.9). Leftover key on an aborted link is still good key.

#### R8 to R10. Load, authentication and weather

**Load.** Unattacked, the fail-mode gap vanishes at sustainable load (ΔA of 0.00 and +0.01 points at ISR factors 0.03 and 0.1) and appears only under overload (+17.2 at factor 1). Under the cut it persists (ΔA = 85.4, 90.6 and 94.7), and ΔQ ≤ 0 throughout, so fail-degraded never beats fail-closed on compliant service. **Authentication.** With n_auth of 2 or 40, fail-closed service under the cut is 8.5 or 3.3% (7.0% at 7) and F is 87.9 or 93.5% (89.9%). **Weather.** With 900/600 s up/down, unattacked F is 1.7% (independent links) or 3.0% (all free-space generation together), and attack excess stays at 88.1 and 86.9 points. A held correlated outage looks like an attack of the same duration, so attribution needs a weather-matched baseline.

#### R11. Classical channel and pre-placed keys

Fail-degraded availability survives QBER attack **only because aborted links keep their classical channels**; denying transport on the cut drops both modes to 0.06%. Pre-placed symmetric keys cannot fix that (ciphertext still needs a path) but remove dependence on a live key-establishment service. With that service down under the held cut, online KEM fallback serves 5.0% and pre-placed keys 97.5%, **still forcing 89.9% below ITS**. Pre-placed keys "move the dependency without reducing the assurance loss"; their lifetime, refresh and distribution are unmodelled, so 97.5% is an upper bound.

#### R12. The learned controller (Table IV)

The authors ask how much room a simple rule leaves. The **budget-greedy heuristic** picks the strongest grade the budget allows within the shield. A **cross-entropy method (CEM)** search tunes an 18-state, five-action table for J = A - 0.75 L behind a per-class **shield** capping class-c violations at floor(ε_c × N_c(t)), with ε = (0, 0.1, 0.1) for (C2, ISR, LOG). *Analogy:* CEM tries many recipes, keeps the best few and cooks more like them; the shield forbids changing certain dishes whatever the recipe says. Six training, four validation and twelve test seeds are disjoint; tables were frozen before testing on seven conditions, two on unseen graphs.

**Reading Table IV.** Columns are controllers against the heuristic (strict floor, 6 h nominal, multi-condition). Rows are differences: ΔJ (units of 10^-3), then ΔQ, ΔQ_ISR and ΔF_B in points, each with a 95% interval. Positive ΔJ and ΔQ are good, positive ΔF_B is bad.

Only the multi-condition learner beats the heuristic: ΔJ = +1.1×10^-3 (interval +0.2 to +2.0), and the heuristic reaches 99.8% of that, which reflects a modest search more than the room left. The gain **costs OTP payload**: ISR's Q falls 2.77 points and F_B rises 1.71, under every class weighting. By algebra, the heuristic beats the strict floor for λ < 0.98 (interval 0.96 to 1.00), and the learned gain reverses at a forced-loss price μ\* = 0.32 (interval 0.06 to 0.60). Tables trained on nominal traffic lose on every stressed condition, because nominal runs never reach depletion. Lesson: floors must be specified *and priced per class*.

### 2.7 Operator rules, limitations, future work

Choosing refusal or degradation amounts to choosing whether the adversary takes **availability** or **assurance**. Three rules: **(1) report Q and F beside A; (2) provision stock behind the minimum cut for T\* hours of the attacks of concern; (3) set fail modes and exception allowances per class, pricing each.**

**Limitations (the paper's own).** Key rates are parameters; response shapes are illustrative; relays are trusted; detector blinding is invisible; weights are exposure proxies; fill, outages and attack costs are declared scenarios (which are swept); no cipher or KEM is executed; the policy search was modest; the five graphs are synthetic. **Future work:** QKDNetSim cross-validation and a reimplemented published router. The paper also notes that Y.3803 asks key managers to record the relay method and prefer OTP-relayed keys, yet the ETSI interface exposes no grade a consumer could enforce. The Reproducibility section links the released simulator and scripts (github.com/LakshyaJ1/Quantum_ResearchPaper) and discloses that a large language model assisted with coding and drafting, while all modelling decisions and claims are the authors'.

---

## Part 3. Glossary

| Term or symbol | Meaning |
|---|---|
| QKD | Quantum key distribution: making shared secret keys with quantum signals |
| QBER | Quantum bit error rate; e, baseline e0 = 0.03, injected Δe, abort threshold e_abort = 0.075 |
| ITS | Information-theoretic security: secure against unlimited computing power |
| OTP | One-time pad: key as long as the message, used once |
| PQC, KEM, ML-KEM(-768) | Post-quantum cryptography; key encapsulation mechanism; a post-quantum KEM (module-lattice, not machine learning) |
| AES, BB84 | A common symmetric cipher; the classic QKD protocol (the γ = 1 case) |
| Trusted relay, hop | A site that decrypts and re-encrypts keys; one link in a path |
| Cut, minimum cut, δ(W) | Links whose removal disconnects the graph; the smallest such set; the cut between rear and forward posts |
| Betweenness | How many shortest paths run through a link |
| Fail-closed, fail-degraded | Refuse at the deadline; serve below the floor and log it |
| Hybrid, downgrade | Combiner secure if either source survives; a move to a lower grade (a "labelled grade downgrade") |
| G1 to G4 | Grades: OTP; QKD-keyed 256-bit; QKD + ML-KEM-768; ML-KEM-768 only |
| C2, ISR, LOG | Classes: command (floor G2); intelligence, surveillance, reconnaissance (G1); logistics (G3) |
| Floor, entitled | Lowest grade a class may receive; requests with floor G1 or G2 (C2, ISR) |
| NOMINAL, DEGRADED, ABORT, OUTAGE | Link states: full rate, reduced rate, no fresh key, no classical transport |
| REL, BDE, FWD, BASE | Relay, brigade, forward-post and rear nodes of the formation |
| SECOQC, QKDNetSim | A Vienna QKD network (buffer values, V1 and V3); the simulator whose buffer rules are adopted |
| ITU-T Y.3803, ETSI GS QKD 014 | Key-management standard allowing recorded fallback; key-delivery interface exposing no grade |
| CEM, shield | Cross-entropy method search; a hard rule that blocks forbidden actions |
| CI, SD | 95% bootstrap confidence interval; standard deviation across seeds |
| Common random numbers | Every policy sees identical random inputs per seed |
| MH, KS, TC, AD, SW, FB, FA | Table I columns (multi-hop, scarcity binds, traffic classes, adversary, pressure swept, fallback, assurance loss) |
| V1 to V4 | The four validation checks against published measurements |
| ISR factor | Multiplier on ISR arrivals (0.03 light, 0.1 default, 1 overload) |
| R0, R | Nominal link key rate (bit/s) |
| ρ(e), H2, f, γ | Rate fraction left at error e (Eq. 1); binary entropy; error-correction inefficiency (1.16); shape exponent (1 or 3.4) |
| K, M_meta, t, n_auth, q | Key bits relayed; metadata (240 bit); tag (127 bit); authenticated messages per delivery (7); per-hop debit |
| λ | Class arrival rate per second; in Section V-E also the below-floor penalty in J = A - λL |
| N, S, D, E | Arrivals; served; served below floor; entitled arrivals |
| A, Q, L | Availability, compliant service, below-floor service; A = Q + L |
| F, F_B | Forced assurance loss; payload-weighted version |
| b, k, d | Attacker budget; links in a cut; relay-chain depth |
| k\* | Smallest budget forcing 50% loss in 24 h |
| U_e(0), G_e(T) | Usable stock at the start and generation by time T on cut link e |
| D̄, T\* | Mean demand across the cut (about 397 bit/s); stock divided by demand (1.44 h) |
| J, ε, μ\* | Controller score A - 0.75 L; per-class exception allowance (0, 0.1, 0.1); forced-loss price at which the learned gain reverses (0.32) |

---

## Part 4. Likely audience questions, and good answers

**1. Is this a quantum computing paper? Where does AI come in?**
No. It concerns QKD networks and a post-quantum fallback; quantum computers matter only as the threat to classical public-key cryptography. The AI is a small learned grade controller behind a safety shield, used to audit a heuristic. It gains very little and costs one-time-pad payload.

**2. Is a downgrade to ML-KEM actually insecure?**
Not necessarily. We do not claim ML-KEM is broken. The traffic was *entitled* to information-theoretic security and got something computational. We measure lost entitlement, not decryption, and no cipher or KEM is executed in the simulator.

**3. Why is fail-degraded not simply better, since it serves 97.5%?**
Availability counts a G4 session as served. Under the held cut only 6.6% is served at its authorised grade, nearly the same as fail-closed's 6.7% (paired ΔQ = -0.09 points). The fallback changes a visible outage into an invisible loss of assurance. Which is better depends on whether operators value continuity or assurance, hence we argue for reporting both.

**4. Are the key rates and the 2% starting fill realistic?**
They are scenario parameters, not measurements of one deployed system, and we say no photonics is simulated. The 2% fill is deliberately stressful and swept: at 10% fill F is 65.4% and at full stores it is 0% within 24 hours. The finding that an attack must outlast the stock does not hinge on one fill value.

**5. Does this mean QKD networks are fragile?**
Not by itself. Forcing needs capability (Δe of at least 0.045), the cost-weighted minimum cut, and endurance beyond the stock. With full stores the same attack forces nothing in 24 hours. With thin stock, an attack on the right two links suffices, and the usual availability report would not show it.

**6. Two validation checks failed. Doesn't that undermine the model?**
Both missed in the same direction: real systems spend more key on authentication overhead than n_auth = 2 implies. We solved for n_auth (about 7 per hop, 40 per tunnel), defaulted to 7 and tested 2 and 40. Headline F stays between 87.9 and 93.5%, and we state that neither check pins the count down.

**7. The graphs are synthetic. Why would this transfer?**
We claim only scaling. On all five graphs a held cut forces 87.6 to 92.9%, and fail-closed service follows stock over demand (predicted 6.0, 9.0, 12.0%; observed 6.5 to 6.7, 9.6, 12.3%). QKDNetSim cross-validation and a reimplemented published router are our next steps.

**8. What can an operator do?**
Report Q and F beside A, provision stock behind the minimum cut for T\* hours (1.44 hours at 2% fill here), and set fail modes and exception allowances per class, with a price on each. The ETSI interface exposes no enforceable grade yet, so the signal is not available there.

**9. Does a deeper relay chain make the network safer?**
Only against a naive attacker. Static ranking needs d + 2 links, but residual betweenness needs just the two-link cut at every depth from 2 up, and an online adversary keeping its slots forces 89.7 to 92.9% at depths 2, 4 and 6.

**10. Doesn't a learned controller solve this?**
Not in our audit. The best learner gains ΔJ = +1.1×10^-3, the heuristic reaches 99.8% of that, ISR compliant service falls 2.77 points and payload-weighted forced loss rises 1.71. The search was modest, so we claim no ceiling, only that the gain spends one-time-pad payload.

**11. Could weather or equipment faults look like an attack?**
Yes. Unattacked F is 1.7% with independent links and 3.0% when all free-space generation fails together, and a held correlated outage looks like an attack of the same duration. Attribution needs a weather-matched baseline; the attack excess stays at 88.1 and 86.9 points.

**12. Would pre-placed keys or the classical channel fix it?**
Pre-placed keys remove dependence on a live key-establishment service (97.5% served versus 5.0% for online KEM when it is down) but still force 89.9% below ITS, and their refresh and distribution cost is unmodelled, so 97.5% is an upper bound. Deny classical transport on the cut and both modes fall to 0.06%.

**13. The paper mentions a language model. What does that mean?**
An LLM assisted with coding and drafting. Modelling decisions, parameters, experimental design and claims are the authors', and every number comes from the released simulator, configurations, per-seed results, validation gate (43 checks, 127 tests) and figure and table scripts.
