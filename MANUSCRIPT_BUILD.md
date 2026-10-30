# Building the camera-ready manuscript (WiCOMM-2026, paper 167)

`paper.tex` is the camera-ready source. It is the submitted manuscript
(`archive/manuscripts_before_revision/paper.tex`) refined for the reviews: same title,
structure and metrics, corrected model, reviewer-requested analyses, regenerated numbers.
The superseded first revision attempt is preserved in `archive/prior_revision_six_page_20260928/`.

## 1. Evidence

Every number in the paper comes from run files produced by the corrected simulator
(`qkdsim/` 0.2.0, `revision/`):

| Evidence | Script | Output |
|---|---|---|
| Five-graph main grid, sensitivities, thresholds | `experiments/revision_suite.py` | `results/revision/runs/` |
| Fallback-service study, online adversaries, learning | `experiments/revision_fallback.py`, `revision_online_*.py`, `revision_learning.py` | `results/revision/{fallback,online_*,learning}/` |
| Camera-ready additions: formation envelope, 3/4-path threshold grid, class-aware floors, betweenness headline, routing attribution, relay chains | `experiments/camera_ready_runs.py --phase {envelope,threshold,floors,routing,chain}` | `results/camera_ready/runs/` |
| Submitted vs corrected simulator on identical random streams | `experiments/camera_ready_bridge.py` | `results/camera_ready/bridge/rows.jsonl` |

The camera-ready scripts fingerprint only simulator code, so editing a case grid does
not invalidate finished runs; a run whose simulator hash differs is refused.

## 2. Tables, figures and the claims ledger

```
python experiments/camera_ready_manuscript_data.py      # Tables II-IV + claims.json
python experiments/make_fig_architecture_cr.py          # Fig. 1
python experiments/make_fig_cut_scaling_cr.py           # Fig. 2
python experiments/make_fig_forcing_cost_cr.py          # Fig. 3
python tools/order_bibliography.py paper.tex            # IEEE first-citation order
```

`results/camera_ready/manuscript/claims.json` records each tabulated or cited value with
its case identifiers and seeds. The table generator asserts that the headline replay equals
the frozen main grid seed by seed.

## 3. LaTeX

```
set TECTONIC_CACHE_DIR=<repo>/tools/tectonic_cache
tools/tectonic/tectonic.exe -X compile --keep-logs paper.tex
```

Tectonic 0.17.0 with IEEEtran; `\RequirePackage[T1]{fontenc}` before `\documentclass`
keeps Times-compatible fonts. The PDF must be exactly six A4 pages.

## 4. Word

`tools/build_word_cr.py` converts the compiled LaTeX into an editable Word file on the IEEE
A4 conference template (`tools/ieee_template/`, provenance recorded) with native equations
and tables, then exports a PDF through an invisible Microsoft Word instance.

## 5. Submission

The conference asks for the reviewer compliance PDF, the Word manuscript and the
PDF eXpress-certified PDF (conference ID 69954X). A local PDF build is not PDF eXpress
certification; certify the final Word/PDF through PDF eXpress before uploading.
