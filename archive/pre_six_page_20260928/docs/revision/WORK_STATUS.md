# Revision handoff status

The corrected simulator, completed studies, manuscript and reviewer response are delivered in `submission/`. The entry point is `submission/READ_ME.md`; file hashes and final checks are in `submission/DELIVERY_MANIFEST.json`. No experiment remains running. The original manuscript and tracked code remain archived separately.

The scientific source is frozen. The main study contains 360 recorded case-seed runs. Sensitivity contains 1,264 recorded runs, of which 1,152 remain after verified numeric configuration aliases are collapsed. The threshold study contains 408 records. Main and sensitivity reuse 64 records, so these three phases occupy 1,968 files rather than their summed request count. The learning cache contains 1,110 training, 60 validation and 420 test records; those counts describe stored rollouts, not independent replicates. Fallback contains 48 runs, online discovery 126, and the separate persistence diagnostic 126. Statistical units and paired controls are specified per study.

The completed regression gate reports 127 tests, no failures, no errors and no skips. The historical internal gate passes 43 checks; those checks are not empirical validation of the network model. Analysis, theory and artifact verifications are recorded under `results/revision/verification/` and the adjacent study directories.

`paper.tex` is the final five-page IEEE manuscript. `paper_revised.tex` matches it; `paper_extended.tex` includes it, and `abstract_new.tex` carries the current expanded abstract. The Word manuscript and its exported PDF have been checked for content parity, native equations, figures, references, embedded fonts and page layout. Reviewer-response page references use the Word-export PDF.

The author will check the preserved author list at submission. IEEE PDF eXpress certification with conference ID 69954X, actual CMT upload, registration and copyright transfer remain external author actions. The conference email specifies a 30 September 2026 deadline and three camera-ready files. Local completion does not imply online certification or submission.
