# Finite-reservoir accounting for trusted-relay key supply

This note supplies a conservation argument for the revised simulation study. It is a derivation from stated accounting assumptions, not a claim of a new theorem or a security proof. The argument distinguishes stopping new key generation from removing the ability to use already stored keys. The distinction determines whether a graph cut creates an immediate failure or a delayed shortage.

## Assumptions and notation

Consider a graph of trusted relay nodes. An edge is a neighboring pair with a shared pool of unused link-key bits. A session carries an end-to-end key along a path and consumes link key separately on every traversed edge. Both endpoints' records refer to the same shared key; they are not two separate supplies to add together.

Choose time zero as the beginning of the interval being studied, such as the start of an attack or the beginning of a reporting window. For edge $e$, let $M_e(t)$ be its stored key in bits and let $m_e$ be the fixed protected reserve that ordinary relay deliveries cannot consume. Assume $m_e \le M_e(0) \le M_{e,\max}$. Define the initially spendable stock as

$$
B_e^0 = M_e(0)-m_e.
$$

Let $r_e(t)\ge 0$ be the rate at which usable secret-key bits are offered to that store, measured in bits per second. Its cumulative offered production is

$$
G_e(T)=\int_0^T r_e(t)\,dt.
$$

The discrete simulator uses a sum of rate times tick duration instead of this integral. If an external key source, pre-established end-to-end key, a replenishment channel, or a change of reserve is allowed, its contribution must be included explicitly. Those resources cannot be silently added to this model.

Let $O_e(T)\ge0$ be generated key discarded because the store was full, $A_e(T)\ge0$ be any other consumption charged to this same store, and $C_e(T)\ge0$ be cumulative session-relay consumption. If the declared secret-key rate already subtracts production-related authentication, do not subtract that authentication a second time in $A_e$.

Let $c_e(i,g)$ be the link-key debit on edge $e$ when session $i$ is delivered at grade $g$. In this repository's uniform accounting model, it does not depend on the edge:

$$
c(i,g)=
\begin{cases}
D_i(g)+M_{\mathrm{meta}}+n_{\mathrm{auth}}t_{\mathrm{tag}},&D_i(g)>0,\\
0,&D_i(g)=0.
\end{cases}
$$

$D_i(g)$ is the quantum-key requirement of that session's selected grade, $M_{\mathrm{meta}}$ is the encrypted metadata length, $n_{\mathrm{auth}}$ is the assumed number of authenticated messages, and $t_{\mathrm{tag}}$ is the authentication charge per message. All terms in this sum are bits. The repository defines these in [qkdsim/config.py](../../qkdsim/config.py), particularly `quantum_key_demand()` and `AccountingConfig.cost_per_hop()`.

For each session, let $\mathcal A_i$ be the set of grades meeting its authorized floor. Define

$$
q_i=\min_{g\in\mathcal A_i} c(i,g).
$$

This minimum avoids assuming that grade cost is monotone for every conceivable payload length. For the configured traffic sizes, the least-cost compliant choice is the authorized floor. If a floor permits a grade needing no quantum key, then $q_i=0$ and this key-budget bound cannot constrain that session's service.

The bound concerns resource consumption. It assumes the keys counted as usable remain usable after generation stops and the classical relay path remains operational. It does not prove that a cryptographic implementation meets any security definition, and it does not cover an event that compromises or invalidates stored keys.

## Per-edge conservation

Accounting gives the identity

$$
M_e(T)-m_e=B_e^0+G_e(T)-O_e(T)-A_e(T)-C_e(T).
$$

The reserve rule requires $M_e(T)-m_e\ge0$. Rearranging therefore gives the necessary condition

$$
C_e(T)\le B_e^0+G_e(T)-O_e(T)-A_e(T)
\le B_e^0+G_e(T).
\tag{1}
$$

The last inequality is deliberately optimistic: it ignores overflow and other costs. Consequently, failure of this optimistic bound proves infeasibility, while satisfying it does not prove feasibility. The same inequality must hold at every intermediate time, not merely at the final horizon. Late generation cannot meet an earlier deadline.

The corresponding implementation is [qkdsim/physics.py](../../qkdsim/physics.py), `KeyStore.accumulate()`, `available()`, and `take()`. Session debits are applied by `_try_grade()` in [qkdsim/sim.py](../../qkdsim/sim.py). Inspection of those functions establishes the intended accounting; an executed conservation test is still required to establish that a particular run obeys it.

## A necessary budget across any cut

Choose a set of vertices $S$. The cut $\delta(S)$ is the set of edges with one endpoint in $S$ and the other outside it. Consider the set $\mathcal F_S(T)$ of floor-compliant sessions delivered by time $T$ whose source and destination are on opposite sides of that cut.

Every path of every such session traverses at least one edge of $\delta(S)$. A path can traverse more than one cut edge; each traversal is charged. Thus

$$
\sum_{i\in\mathcal F_S(T)}q_i
\le \sum_{e\in\delta(S)}C_e(T)
\le \sum_{e\in\delta(S)}\left[B_e^0+G_e(T)\right].
\tag{2}
$$

The first inequality holds because each counted session contributes at least $q_i$ to the cut's consumption. The total on the right may also contain other sessions, repeated cut crossings, and below-floor deliveries, all of which are nonnegative. The second inequality is obtained by summing (1). This proves (2).

For edge-dependent costs, replace $q_i$ by any established lower bound on the total cut debit required by a compliant route for session $i$. Choosing the minimum over feasible path-and-grade pairs is valid. Assuming the uniform cost without checking heterogeneous protocols is not.

Define $B_S=\sum_{e\in\delta(S)} B_e^0$ and $G_S(T)=\sum_{e\in\delta(S)}G_e(T)$. If every counted session costs at least the same positive $q$ on one cut crossing, then

$$
N_{\mathrm{compliant},S}(T)
\le \left\lfloor\frac{B_S+G_S(T)}q\right\rfloor.
\tag{3}
$$

For classes $j$ with different minimum compliant costs $q_j$, the stronger useful form is $\sum_j q_jN_{j,S}(T)\le B_S+G_S(T)$. A session count alone hides the difference between a short symmetric-key delivery and a long one-time-pad payload.

Equation (2) is a necessary condition, not an achievable pooled budget. Keys stored on one edge cannot generally substitute for keys missing on another edge. Path constraints, competing traffic, reserves, deadlines, and the actual scheduler can cause failure before the summed cut budget is exhausted. A minimum cut in an unweighted graph counts edges; it is not the minimum of these time-dependent bit budgets.

## Stopped generation and time to shortage

Suppose usable key generation is stopped on every edge crossing $S$ throughout $[0,T]$, while the stores and classical relay service remain available. Then $G_S(T)=0$ and (2) reduces to

$$
\sum_{i\in\mathcal F_S(T)}q_i\le B_S.
\tag{4}
$$

There is a finite stock of compliant deliveries left. A generation cut does not, by itself, make that stock zero. If the reporting interval contains only a few small requests and the stores began full, the cut can have no observed service effect during that interval.

For a single link, use a fluid approximation in which demand debits arrive at a constant rate $d$ bits/s and new usable key arrives at a constant rate $r$ bits/s. With initial spendable stock $B>0$, no other consumption, and $d>r$, the time when the spendable stock reaches zero is

$$
T_{\mathrm{empty}}=\frac{B}{d-r}.
\tag{5}
$$

This follows directly from $B(t)=B-(d-r)t$. With stopped generation, $r=0$ and the time is $B/d$. If $d\le r$, this constant-rate model does not force depletion; if $d=r=0$, no consumption occurs and the stock persists. These are statements about the assumed workload, not predictions of field endurance.

For discrete equal-size requests of debit $q$ with stopped generation, the link can afford exactly $\lfloor B/q\rfloor$ such requests in the absence of other consumption. The next request is unaffordable at that instant. The store need not reach exactly zero: fewer than $q$ spare bits can remain. Request arrival times and deadlines determine whether waiting results in eventual service or blocking. For variable-size requests, use the cumulative sum of their debits instead of an average that conceals bursts.

An ideal homogeneous cut has $m$ identical cut edges, stock $B$ and generation $r$ per edge, with total crossing demand $d$ balanced equally among them. Assume every session crosses exactly one cut edge and there are no additional bottlenecks. Each edge then sees demand $d/m$. If $d>mr$, all these edge stores empty together at

$$
T_{\mathrm{empty,balanced}}=\frac{mB}{d-mr}.
\tag{6}
$$

With stopped generation this becomes $mB/d$. Equal stock alone does not justify (6): equal load allocation and feasible onward paths are required. Under an uneven allocation, one critical store can become unusable while another still has key. For any cut with constant aggregate required debit rate $d_S$ and aggregate generation rate $r_S<d_S$, $B_S/(d_S-r_S)$ is the latest time through which uninterrupted fluid compliance could remain possible under the optimistic pooled budget. It need not be the first actual failure time.

As a numerical illustration, the repository's default capacity and reserve give $B=52{,}428{,}800-1{,}048{,}576=51{,}380{,}224$ spendable bits on a full edge. With $M_{\mathrm{meta}}=240$, $n_{\mathrm{auth}}=2$, and $t_{\mathrm{tag}}=127$, a 256-bit delivery debits 750 bits. Stopped generation still leaves room for 68,506 such deliveries on that edge, if nothing else consumes its key. At one delivery per second, the next one fails at about 19 hours. This is an illustrative accounting calculation, not a reported traffic experiment or measured device endurance.

## From key shortfall to denial or grade loss

Let $N_S(T)$ be requests across the cut that must be resolved within the interval. If their total minimum compliant debit exceeds $B_S+G_S(T)$, they cannot all be served at their authorized floors within the interval. Some service must be denied, delayed beyond the stated deadline, or delivered below the floor. The bound does not choose which outcome occurs; that is the controller's policy.

If all $N_S(T)$ requests are served, all have the same minimum compliant debit $q>0$, and all consume the cut's resources, then (3) yields

$$
\frac{N_{\mathrm{below\ floor},S}(T)}{N_S(T)}
\ge
\max\!\left(0,1-\frac{B_S+G_S(T)}{qN_S(T)}\right).
\tag{7}
$$

The expression without the integer floor is a slightly weaker but simpler bound. If some requests are blocked, substitute the number actually served into the denominator and the corresponding set of sessions into the argument. A controller can maintain zero observed below-floor fraction by refusing all service. Therefore a service-conditioned grade metric needs an availability metric beside it.

The repository distinguishes violating a class's floor from losing an information-theoretically delivered key. To bound `forced_below_its`, restrict the session set to the served sessions entitled to G1 or G2, and define

$$
q_i^{\mathrm{ITS}}=\min_{g\in\{\mathrm{G1},\mathrm{G2}\}}c(i,g).
$$

Use this cost in the cut argument instead of $q_i$. In the configured workloads, $q_i^{\mathrm{ITS}}=750$ bits per hop under default accounting. An ISR session at G2 violates its G1 floor but still meets this particular ITS-key classification. A bound calculated with its 144,494-bit G1 debit would therefore concern floor violations, not forced loss below ITS. The classification itself is a model convention whose cryptographic interpretation requires separate justification.

For an idealized, constant stream of eligible sessions all served across a generation-stopped cut, let their rate be $\lambda$ sessions/s, their common minimum ITS debit be $q^{\mathrm{ITS}}$, and $N_S(T)=\lambda T$. The resource argument gives

$$
\mathrm{FAL}_S(T)\ge
\max\!\left(0,1-\frac{B_S}{q^{\mathrm{ITS}}\lambda T}\right).
\tag{8}
$$

For a target fraction $0<\phi<1$, the right side reaches $\phi$ only once $T\ge B_S/[q^{\mathrm{ITS}}\lambda(1-\phi)]$. This is a sufficient resource-shortfall condition under the strong all-served, constant-workload assumptions. It is not the earliest possible forcing time, and it is not an equality for the simulator. A burst, other traffic, or a poor routing decision can cause loss earlier. Blocking, intermittent arrivals, a finite offered workload, or unmodeled replenishment can prevent the assumed metric trajectory.

For a real reporting window starting at $t_w$, replace $B_S$ by the actual spendable stock at $t_w$, and count generation and eligible service only within that window. Stock at the beginning of the entire run is not the same quantity. This also prevents mixing 24-hour consumption with a 12-hour service denominator.

## Why an edge cut is not a finite-time forcing guarantee

For a specified source and destination, the minimum edge cut is the smallest set of edges whose removal disconnects that pair. Removing those edges from the usable relay graph disconnects it immediately. Stopping their key generation is a different operation if unused keys on those edges remain safe and usable.

Under generation-only suppression, the minimum cut guarantees only the absence of replenishment across that cut. With finite stock, no outside supply, and an unbounded sustained positive requirement for quantum-supported service, cumulative fully compliant service is bounded by (4). Some later demand must fail or change grade. This is an eventual resource statement, conditional on continuing demand and service policy.

Consequently, choosing as many attacked edges as the minimum cut is not sufficient to guarantee a specified grade-loss fraction during a finite experiment. The selected edges must actually form the relevant cut; their generation must be suppressed; the remaining stock must be insufficient for the observed load; and the grade-loss policy must serve rather than block affected traffic. A budget number alone proves none of these.

Nor is that cardinality a universal lower bound on finite-time forcing cost. A smaller attack can reduce an already marginal supply enough to miss deadlines, exhaust one store on a chosen route, or divert competing traffic. The network can be below an authorized floor even without an attack if its initial workload is infeasible. Conversely, a full generation cut with large stock and low demand can leave service unchanged during the chosen horizon.

For multiple destinations, define the target explicitly. Separating one leaf post, a chosen group of posts, and all posts are different optimization problems. Their cut sizes and fractions of affected traffic can differ. In the original `formation_9node()` implementation, each forward post is a degree-one leaf, so separating one such post needs only one edge; that fact cannot support an unqualified statement that the formation's minimum cut is two.

If the simulator deliberately makes an abort invalidate stored-key relay on an edge, its immediate disconnection behavior follows that fail-stop rule. That is a legitimate scenario to label and compare, but it must not be described as a consequence of generation stoppage alone. The original `_usable()` rule in [qkdsim/network.py](../../qkdsim/network.py) accepted an edge only when its current generation rate was positive, making this distinction essential to the revision.

## Revision in progress

This derivation is independent of the old headline CSV values. The main revision is testing generation-only suppression and explicit relay suspension separately, with finite stores and a defined reporting horizon. Any new code must still be checked for consistency with the assumptions above, especially the reserve, available-stock treatment after an abort, reporting windows, and any additional authentication consumption.

Retaining stored key assumes it remains confidential, correctly synchronized, and permitted for use after the event. Some systems deliberately purge key on an interruption or loss of synchronization. Such a purge must appear as a stock removal in conservation, rather than being described only as zero production. The revised scenarios expose both policies. A transport interruption can independently block relay even when safely retained stock remains.

The derivation does not certify a particular topology, optimize an adversary, validate a physical channel, or establish a new scientific priority claim. Its role is to make the resource claim falsifiable and to prevent an instantaneous graph fact from being substituted for a finite-time key-supply result.
