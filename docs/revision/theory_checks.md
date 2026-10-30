# Deterministic checks of finite key stock and attack ranking

The [machine-readable results](../../results/revision/theory_checks.json) record seven reservoir cases and 24 structural cases, with event-level accounting and hashes of the source files used. All checks passed. These are small implementation checks of stated accounting and graph conditions; they are not independent physical validation or Monte Carlo estimates. No confidence interval is needed for these deterministic fixtures.

The experiment is [revision_theory_checks.py](../../experiments/revision_theory_checks.py). Its [nine behavioral tests](../../tests/test_revision_theory_checks.py) were written and observed failing before implementation, then passed. It runs serially and does not change the main experiment grid or its outputs.

## The controlled reservoir experiment

The topology contains a source, a destination, and between one and four separate two-hop branches connecting them. Every edge begins with the same spendable key stock $B$, above a protected reserve of 10 bits. Every link's new key generation is stopped at time zero; classical transport remains available. There are no random outages or random arrivals.

Each request asks for exactly G2, whose per-hop debit in this fixture is $q=256+240+2(127)=750$ bits. The request therefore spends 750 bits on each of its two hops. Requests arrive at time zero and every five seconds thereafter, and have zero waiting allowance. The simulator resolves a failure immediately at its arrival. The normal corrected KAR selector tries the available two-hop routes; no custom routine spends or pools key for it.

The experiment calls the actual `RevisionSimulator` machinery for generation suppression and the retained-versus-purged stock policy, which in turn uses the corrected base `Simulator` for service, deadlines, and accounting. Only the arrival process and event recording are specialized. Thus it checks the production code's interpretation of a stopped generator, rather than computing a bound without running the simulator.

Across a cut leaving the source there are $m$ key stores, one per branch. The general necessary resource bound is

$$
Nq\le mB,
\qquad
N\le\left\lfloor\frac{mB}{q}\right\rfloor.
$$

$N$ is the number of successfully delivered requests, $m$ is the number of branches, and the brackets round down to an integer. This pooled relaxation ignores that stock on one edge cannot move to another edge. In this equal-stock fixture, each branch can actually serve only $\lfloor B/q\rfloor$ requests. Because the router eventually uses every affordable branch, the exact achievable count is

$$
N_{\mathrm{exact}}=m\left\lfloor\frac{B}{q}\right\rfloor.
$$

The exact count is a property of this fixture: all branches have two hops with matching stocks, all requests have equal debit, all candidate branches are enumerated, and there are no competing requests or transport outages. It is not a claim that an arbitrary network always achieves a sum of per-edge capacities.

| Branches $m$ | Spendable bits per edge $B$ | Stock policy | Pooled bound after discard | Actual served requests | First unserved arrival, seconds |
|---|---|---|---|---|---|
| 1 | 1,500 | Retain | 2 | 2 | 10 |
| 2 | 1,500 | Retain | 4 | 4 | 20 |
| 3 | 1,500 | Retain | 6 | 6 | 30 |
| 4 | 1,500 | Retain | 8 | 8 | 40 |
| 3 | 1,900 | Retain | 7 | 6 | 30 |
| 3 | 1,900 | Purge | 0 | 0 | 0 |
| 4 | 749 | Retain | 3 | 0 | 0 |

With three branches and 1,900 bits per edge, every branch serves two requests and leaves 400 spendable bits on its source-side edge. The cut therefore retains 1,200 bits in total, which exceeds the cost of one request. Nevertheless, no single branch has the required 750 bits on either hop. The pooled bound permits seven deliveries, while the actual maximum is six. With four 749-bit stores, the same effect is more pronounced: the aggregate cut contains enough bits for three deliveries, but no first delivery is possible.

The three-branch retained case consumes 4,500 bits across the source cut and 9,000 across the full two-hop network. The purge case discards all 11,400 spendable bits across all six edges, including 5,700 bits on the source cut. It records no useful key consumption and serves no requests. The protected reserve remains untouched. The JSON records purge as discarded stock, separate from useful relay consumption.

At every recorded arrival event, cut consumption is no greater than initial spendable stock plus generated bits minus discarded bits. Every event's cut conservation residual is zero; full-run conservation residuals are also zero. New generation is zero in all cases, and classical transport remains up. These checks rule out a result caused by an unnoticed refill or classical disconnection.

## Counts, arrival times, and the fluid reference

For arrivals every $\Delta$ seconds starting at zero, when exactly $N_{\mathrm{exact}}$ requests fit and each must be resolved immediately, the first unserved arrival is

$$
T_{\mathrm{first\ failure}}=N_{\mathrm{exact}}\Delta.
$$

This is a discrete arrival schedule, not a measured endurance curve. The additional test with two branches and seven-second spacing serves the same four requests as its five-second counterpart, but the first failure moves to 28 seconds. Workload timing changes failure time without changing total affordable service.

A continuous approximation treats demand as a smooth drain of $d=q/\Delta$ bits/s across the cut. If the cut's stock could be pooled, or if a continuous workload were balanced suitably across identical edges, its exhaustion reference would be

$$
T_{\mathrm{fluid}}=\frac{mB}{d}=\frac{mB\Delta}{q}.
$$

For $B=1,500$, the first-failure times happen to equal this reference because $B/q$ is an integer and the request schedule aligns with the budget. That numerical equality does not establish a continuous or equally balanced per-edge trajectory: the actual router can fill one branch's service capacity before choosing another.

For three 1,900-bit branches, the continuous reference is 38 seconds, whereas discrete service fails at the 30-second arrival. Separate residual fragments and whole-request granularity account for the difference. For the four 749-bit branches, the retained continuous reference is approximately 19.97 seconds, while the very first request fails. A fluid budget can therefore be a loose guide when individual requests are large relative to individual stores.

The broader [finite-reservoir derivation](finite_reservoir_theory.md) covers ongoing generation, nonuniform costs, intermediate deadlines, and conditions for balanced-fluid equality. These fixtures confirm special cases of that accounting. They do not claim that the first failure of an arbitrary workload equals its pooled exhaustion time.

## Structural attack ranking on the original chain family

The second check uses the original `chain_topology(depth)` for depths one through six. At depth one there is only one link. At every greater depth, a primary path of $d$ hops and an alternate path of $d+1$ hops connect the same source and destination without sharing edges. Thus their structural edge connectivity is two.

For each ranking, the check removes its edges from a copy of the graph until the destination first becomes unreachable. It records the smallest disconnecting prefix of that particular order and confirms the destination was still reachable immediately before its final removal. All these links have relative cost one, so edge count and relative cost coincide. The recorded costs are abstract structural costs, not measured attack effort.

| Primary depth | Original static ranking | Canonical-name static ranking | Residual-graph adaptive ranking | Weighted minimum cut |
|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 |
| 2 | 3 | 4 | 2 | 2 |
| 3 | 4 | 5 | 2 | 2 |
| 4 | 5 | 6 | 2 | 2 |
| 5 | 6 | 7 | 2 | 2 |
| 6 | 7 | 8 | 2 | 2 |

The original static ranking computes all-pairs edge betweenness once and resolves ties using NetworkX's original edge-orientation tuples. It reproduces the historical $d+1$ isolation count for depths two through six. The revised static helper uses canonical undirected edge names to resolve ties and gives $d+2$ in the same range. The graph and initial all-pairs centrality are otherwise the same. This dependence on a naming convention makes the exact static sequence unsuitable as an inherent property of a network's resilience.

The revised adaptive helper recomputes source-to-still-reachable-target betweenness after each removal. Once one route is cut, further edges lying only on that already unusable route have no value for reaching the remaining target. It selects the remaining route and isolates the target with two removals at every depth above one, matching the weighted minimum cut in this particular graph family.

The adaptive method changes both when scores are recomputed and which endpoint pairs contribute to the score. The experiment establishes that the historical static-rank penalty is not robust to this reachable-target adaptive strategy. It does not isolate the contribution of either change separately, and it does not prove that this heuristic finds the optimal cut in every graph.

This is offline structural adaptation on a known residual graph. It has no observations of key inventory, unknown topology, attack discovery, or changing traffic, and is not an online inventory-aware adversary. Removing an edge from the usable graph also differs from merely stopping its generator while retaining usable key. The structural count therefore cannot be substituted for the finite-time assurance-loss cost measured by the main experiments.

## Reproducing the checks

Run the artifact generator from the repository root:

```powershell
python -X faulthandler -u -c "from experiments.revision_theory_checks import main; raise SystemExit(main())"
```

Run the independent tests:

```powershell
python -X faulthandler -u -c "import runpy; runpy.run_path('tests/test_revision_theory_checks.py', run_name='__main__')"
```

The generator records the Python and NetworkX versions and the SHA-256 of each relevant source file. It checks those source hashes again after the cases finish and refuses to write a passing artifact if code changed during the run or an accounting check failed. The exact values in this note are drawn from the generated JSON; rerun and reconcile the note if the code or fixture assumptions change.
