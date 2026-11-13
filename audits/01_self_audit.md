# Self-audit 01 (Checkpoint 2)

**Team:** _team name_
**Members:** _names_
**Branch / PR:** `checkpoint-2` → `main`, PR _link_

<!--
HOW TO FILL THIS IN (delete these comments when done)
- The raw review output is in audits/00_skeptical_review_output.md. Read each finding there.
- Grading: "the self-audit is honest. Finding real problems and saying so is a good
  self-audit, not a bad one." Don't mark something OK just to look good.
- Replace every _italic placeholder_. Keep it short: one or two sentences per cell.
-->

## 1. What the review flagged, and which findings are real

<!--
For each finding: Real? = Yes / No / Partly. Then say WHY in your own words.
"No" is fine if you can explain why it doesn't apply (e.g. the file isn't used anywhere).
-->

| # | Finding (from `00_skeptical_review_output.md`) | Severity | Real? | Why / why not |
|---|---|---|---|---|
| 1 | All GPU numbers are FAKE | High | yes | all the outputs from the data are meaningless till we put in real data|
| 2 | GPU timing assumption (17:00 ET) may be wrong; real Ornn stamps are 1–3 pm ET | High | yes | time is assumed to be 5, which is the next trading day; need to change to the current trading day |
| 3 | Chart scripts use a different, look-ahead timing rule than `poc.py` | High | yes | these 2 parts of the project disagree we need to fix this|
| 4 | Ken French factors downloaded live, not pinned; sample ends 2026-09-30 | Medium | yes | data ends sep 30 and it goes to nov 5 we need to update this to use all the data |
| 5 | No script in the repo regenerates `data/prices_adjusted/` | Medium | yes | we need to add the code to the repo  |
| 6 | Calendar-day price files fill weekends with a future price | Medium | partly | we can make a note to fix this or change the code by deleting something |
| 7 | Many correlations tested, no `specs_tried.md`, no multiple-testing adjustment | Medium | yes | the data is fake; this will be better once we put in the real data|
| 8 | Lead/lag sign conventions are opposite in `graph.py` vs `make_correlation.py` | Medium | yes | just a visual issue that we need to fix GPU and stock lead need to line uo |
| 9 | Levels charts can show spurious co-movement | Medium | partly| it's just a picture of the data both use beta and correlation |
| 10 | HC1 standard errors, not Newey-West | Low | partly | we can fix this once we have the real data in the project from Ornn |
| 11 | Compute beta not separated from a tech / AI factor (no QQQ or SMH control) | Low | yes | people could challenge this and say that our beta is just based on AI stock hype |
| 12 | `requirements.txt` not pinned to versions | Low | partly | we just need to pin it before we submit the final version |
| 13 | `STATUS.md.pdf` unreferenced, may be stale | Low | partly  | old file that we need to delete or update  |
| 14 | `outputs/stocks_vs_gpu.html` changes on every run (random plotly ID) | Low | partly | just a cosmetic issue that we need to fix, not that big a deal compared to other issues |

_Anything you found yourselves that the review missed:_

## 2. Project-seeds checklist (`00_PROJECT_SEEDS`)

<!--
One line each: OK / problem / not yet, plus a short reason.
"not yet" = the thing doesn't exist yet. "problem" = it exists but is wrong.
-->

| # | Item | Status | Note |
|---|---|---|---|
| 1 | **It reproduces.** `run_all.py` rebuilds every table and figure from raw inputs, no hand edits | Yes | _ |
| 2 | **Every input has a provenance.** Source, pull date, and code that gets it again | _ | _ |
| 3 | **Unit of observation is right.** Unique keys asserted; merges use `validate=`; we can say what one row is | _ | _ |
| 4 | **No look-ahead.** Only information public at each date (watch survivorship, filing dates) | _ | _ |
| 5 | **No LLM leakage.** | _ | _ |
| 6 | **No p-hacking.** `specs_tried.md` logs every specification run | _ | _ |
| 7 | **Magnitudes, not just stars.** Effect big enough to matter to whoever pays | _ | _ |
| 8 | **Checks by hand.** One number per pipeline step recomputed independently | _ | _ |
| 9 | **Honest limits.** "Threats to validity" section in the README | _ | _ |
| 10 | **We understand it.** Every teammate can explain every step | _ | _ |
