# Forced assurance loss in finite-reservoir QKD networks

This workspace contains the WiCOMM-2026 paper 167 revision: a key-service simulator, a constrained policy-learning study, official-review traceability, numerical evidence and manuscript sources. The model asks how finite stored key, interrupted generation and fallback permissions affect timely and compliant key service.

The current revision uses `revision/`, `experiments/revision_*.py` and `results/revision/`. Historical CSVs directly under `results/` belong to the earlier model and are preserved for audit. Their headline numbers must not be attributed to the corrected model. The original tracked code is archived at `archive/code_before_revision_0d1e2fa.zip`; original manuscripts and notes are under `archive/manuscripts_before_revision/`.

## Start with the evidence

| File or directory | Purpose |
|---|---|
| `docs/revision/RESEARCH_EXPLAINED.md` | Beginner explanation, terminology, repository map and limits of the evidence. |
| `docs/revision/official_review_matrix.md` | Every official reviewer comment and question. |
| `docs/revision/REVIEWER_RESPONSE.md` | Point-by-point responses and evidence links. |
| `docs/revision/literature_verified.md` | Primary-source verification, prior-art overlap and parameter provenance. |
| `docs/revision/independent_method_review.md` | Independent audit of model, metrics and completed main records. |
| `paper.tex` | Exactly six-page IEEE manuscript source. `paper_revised.tex` is a synchronized copy. |
| `paper_extended.tex` | Compatibility entry point for the current paper; the old extended draft is archived. |
| `submission/` | Final manuscript, reviewer compliance, beginner guide and source packages. |
| `results/revision/analysis/` | Per-seed tables, means, intervals, paired comparisons and verification records. |

## Numerical reproduction

Python 3.12 was tested. The exact numerical package versions are in `requirements.txt`; their package releases were checked on PyPI. The simulator needs no network connection or GPU. Keep the total number of concurrent simulation workers at eight or fewer. Complete recomputation is substantial; verified caches allow interrupted runs to resume without changing the protocol.

```powershell
python -m pip install -r requirements.txt
python tools/verify_research.py
python experiments/revision_theory_checks.py
python experiments/revision_suite.py --phase main --seeds 12 --workers 6
python experiments/revision_suite.py --phase sensitivity --seeds 8 --workers 6
python experiments/revision_suite.py --phase threshold --seeds 6 --workers 6
python experiments/revision_learning.py --phase all --workers 6
python experiments/revision_fallback.py
python experiments/analyze_revision_fallback.py
python experiments/revision_online_adversary.py --phase all --workers 6
python experiments/revision_online_persistence.py --phase all --workers 6
python tools/normalize_result_json.py
```

Run those commands sequentially when using six workers per command. Each main/sensitivity/threshold manifest records full configurations, seeds, source hash and completion. Learning records all candidate tables and training/validation outcomes, then writes `results/revision/learning_policy_freeze.json` before the reserved test seeds are used. It rejects a changed protocol or corrupted cache instead of silently reusing it. Changing a scientific source requires a separate output/archive decision; do not mix new runs with existing evidence.

After completion, regenerate analysis and manuscript inputs:

```powershell
python experiments/revision_analyze.py --phase main
python experiments/revision_analyze.py --phase sensitivity
python experiments/revision_analyze.py --phase threshold
python experiments/revision_learning_analysis.py
python experiments/revision_learning_weights.py
python experiments/revision_manuscript_data.py
python tools/export_refinement_tables.py
python experiments/revision_figures.py --figure main
python experiments/revision_figures.py --figure reserve
python experiments/revision_figures.py --figure learning
python experiments/revision_figures.py --figure learning-conditions
```

The analysis programs refuse incomplete registered data. Numeric configuration aliases are checked for exact duplicate outcomes and collapsed for reporting, with their original records preserved. Undefined fractions are encoded as JSON null by the documented normalization step. Intervals use independent simulator seeds; the learning aggregate first averages the seven fixed conditions within each seed. Conditions and repeated records are not independent extra replicates. The refinement exporter reproduces the additional load and attack-cost tables from existing sensitivity data, checks matched arrival cohorts, and independently recalculates the paired load intervals; `--check` detects stale table inputs. Full artifact verification is recorded under `results/revision/verification/`.

## What the model measures

These are modeled key-supply/session-admission outcomes, not measured payload throughput, an implemented KEM, field-tested security or a composable cryptographic proof. Timely service `A`, floor-compliant service `Q`, and below-floor service `L` share the arrival denominator, with `A=Q+L`. ITS-key-entitled requests are separately partitioned into ITS-delivered, below-ITS-delivered and blocked outcomes. Payload weighting is an associated-payload exposure proxy, not calibrated harm.

Stopping generation can leave previously accepted keys usable under the stated retention assumptions. Working-key purge is a separate scenario. Classical transport failure and online key-establishment failure are distinct. Default revision accounting uses seven authentication tags per relay request, with two and forty as sensitivity settings; this is not a universal protocol calibration. The main initial reserve is a stressed 2% of usable capacity, and larger starting reserves are evaluated explicitly. Historical provenance comments should be read alongside the current verification register, which distinguishes selected simulator parameters from measurements.

The 18-state learned policies and greedy baseline share an explicit per-class exception monitor. C2 receives no below-floor exceptions; ISR and LOG have declared 10% arrival-count allowances. The guarantee belongs to the monitor. A selected policy is a validation-selected candidate from a limited search, and its test intervals do not capture uncertainty across every possible training run.

## Manuscript tools

`docs/revision/build_environment.md` records the tested IEEEtran/Tectonic build, editable Word conversion, native equation/table preservation, fonts and page checks. Optional document packages are listed in `requirements-documents.txt`. The portable tool downloads and their hashes are recorded under `tools/`; Microsoft Word is required for the tested hidden Word export path. The conference permits 4-6 manuscript pages; the final author requirement is exactly six pages, including references, in both manuscript renderings. The explanatory guide and reviewer response have separate page counts.

`MANUSCRIPT_BUILD.md` explains the small LaTeX source package. `tools/verify_packaged_manuscript.py` checks its members and recompiles it with the prepared renderer. `tools/build_delivery.py` is a workspace packaging utility that requires the original or regenerated `build/final_word`, `build/final_latex` and reviewer QA products. The full archive supplies completed documents and copies of their QA evidence under `docs/revision/delivery_checks`; those evidence copies are not a replacement build tree. Numerical reproduction uses the commands above and does not require Word, TeX or those build directories.

On this Windows host, `platform.platform()` can trigger a native Python failure. The verification runner avoids pytest's system-version header and executes the same test functions through unittest; it does not skip parameterized checks. The minimal reproducer and safe `sys.getwindowsversion()` alternative are documented in `docs/revision/revision_layer_audit.md`.

PDF eXpress processing with conference ID 69954X is a separate external certification step. A local PDF build and embedded-font check are not that certification. Third-party standards/papers, tool caches and historical drafts should not be automatically redistributed with a reproducibility package.
