# agent/ : Gemini root-cause agent

**Owner: Htet Win.** This folder holds everything about the agent that does not need to run on the server:
the design, the test scenarios and an evaluation script. The code that runs live is in
`backend/app/analyzer.py` (called by `backend/app/engine.py`), with the prompt in
`backend/app/prompts/root_cause.md`.

## What the agent does

1. `engine.py` watches Wi-Fi and IoT readings. A flag trips only after several bad readings in a row.
2. The **rules** pick a first root cause: `ap_hardware_failure`, `congestion`, `isp_uplink_outage` or `iot_device_fault`.
3. The **agent** (`analyzer.explain`) sends the evidence to Gemini. Gemini checks the rule's guess and returns
   a cause, a confidence, a plain-English explanation (including why the most likely alternative was ruled out)
   and one recommended action.
4. `engine.py` uses that text in the ticket, the student advisory and the Telegram notification.

```
readings -> rules (guess) -> Gemini (check + explain) -> guard rails -> ticket / advisory / Telegram
                                  |
                                  +-- Gemini down or unusable? -> rule cause + template text
```

## Guard rails (why the demo cannot freeze or go wrong)

- **Gemini is optional.** No key, a timeout, bad JSON or an invented cause: the rule cause and template text are used.
- **Limited override** (tested with a fake Gemini; see "Latest real-Gemini results"). Gemini may correct `ap_hardware_failure` <-> `congestion`, and only when it reports
  `high` confidence. Uplink and IoT tickets always keep the rule cause, because `engine.py` clears them using
  `affected_aps` / `affected_devices`, and changing the cause there would resolve the ticket by mistake.
- **Text must match the ticket.** If Gemini argues for a cause the ticket does not keep, its explanation and action
  are discarded and the template text is used, so a ticket never says "uplink outage" with "replace the AP" instructions.
- **Evidence only.** The prompt tells Gemini to use only numbers present in the evidence.
- **Data, not instructions.** Evidence is passed as data; the explanation is cleaned and length-limited.
- **One door.** Every Gemini call goes through `backend/app/llm.py: call_gemini()`, so moving to Gemini
  Enterprise is a one-function change.

## Prompts

`backend/app/prompts/root_cause.md` is plain text with `{{location}}`, `{{rule_cause}}` and `{{evidence}}`
placeholders and a version comment at the top. Change the wording there; no Python edits are needed.
Run `evaluate.py` after every prompt change to see whether the behaviour got better or worse.

## Scenarios (`scenarios/*.json`)

| Name | What it simulates | Rules say | Expected |
|---|---|---|---|
| `ap_failure` | One AP dead, neighbours healthy | ap_hardware_failure | ap_hardware_failure |
| `congestion` | Many clients, high latency, low loss, good signal | congestion | congestion |
| `uplink_outage` | 4 APs in 3 locations degrade together | isp_uplink_outage | isp_uplink_outage |
| `iot_fault` | 2 IoT devices down, Wi-Fi healthy | iot_device_fault | iot_device_fault |
| `uplink_two_locations` | Cue-check: 2 APs in 2 locations, high loss, strong signal | isp_uplink_outage | isp_uplink_outage |
| `weak_signal_single_ap` | Cue-check: one AP, -88 dBm, few clients, neighbours healthy | ap_hardware_failure | ap_hardware_failure |
| `congestion_moderate_loss` | Cue-check: 2 overloaded APs, 2.5% loss, strong signal | congestion | congestion |
| `ap_looks_like_congestion` | Hard case (tuned on): rules say AP failure, numbers look like congestion | ap_hardware_failure | congestion |

### Latest real-Gemini results

`gemini-flash-lite-latest`, 3 runs per scenario (`python agent/evaluate.py --runs 3`):

| Prompt | Scenarios | Gemini's own answer correct | Final cause correct (after guard rails) | Notes |
|---|---|---|---|---|
| v1 | 5 | 12/15 | 12/15 | `ap_looks_like_congestion` missed 0/3: Gemini kept "AP failure" (anchored on the rule's guess) and argued backwards |
| v2 | 5 | 12/15 | 15/15 | Fixed that scenario (3/3), but Gemini called `uplink_outage` "AP hardware" 3/3. The guard rail kept the uplink cause, yet its text said "replace the AP hardware" |
| v3 | 8 | 24/24 (15/15 on the original 5) | 24/24 | Rules alone: 21/24 (they miss the hard case). Gemini overrode the rules 3 times, all on `ap_looks_like_congestion`, all correct. Guard rails blocked nothing. Gemini's text was used in all 24 tickets |
| v3.1 | 8 | 24/24 (3 full runs) | 24/24 | Rules alone 21/24. 3 overrides, all on `ap_looks_like_congestion`, all correct; nothing blocked; Gemini text used in 24/24 tickets. Explanations flagged for numbers not in the evidence: 1/24, 3/24 and 2/24 in three runs of the same prompt (one of the 2 in the third run was a false positive of the check) (v3: 3 of the 8 texts inspected). The 3 flagged in the second run were cue numbers: "-70 dBm" twice (`weak_signal_single_ap`) and "under 3%" once (`congestion_moderate_loss`). One 503 per run, cleared by the retry; no 429s in the last two runs |

Read this carefully:
- The 3 added scenarios (`uplink_two_locations`, `weak_signal_single_ap`, `congestion_moderate_loss`) were written to the
  v3 cues, so they check that Gemini follows the cues, not that the prompt generalises to borderline cases.
- Temperature is low, so the 3 runs of a scenario are near-copies, not independent samples. This is 8 simulated
  situations, not an accuracy rate. Expected answers are our own judgement.
- The free tier returned HTTP 429 on two calls; those may have been answered by the fallback model
  (`GEMINI_FALLBACK_MODEL`), not flash-lite. Use `--delay 3` or more.
- "Final correct" includes the guard rails and is not Gemini's score. Gemini can correct AP failure <-> congestion;
  it cannot change uplink or IoT tickets, by design.

The `evidence` in each file has the same shape `engine.py` builds, so the script exercises the real code path.
"Expected" is our own judgement of the correct answer (the hard case is debatable: one AP, 52 clients, 420 ms latency, 1.5% loss), and the data is simulated.

## Run the evaluation

From the repo root, with the backend's virtual environment active and `GEMINI_API_KEY` in `backend/.env`:

```bash
python agent/evaluate.py                 # all scenarios
python agent/evaluate.py ap_failure      # one scenario
python agent/evaluate.py --runs 3        # repeat 3x to check Gemini is consistent
python agent/evaluate.py --save          # also writes agent/results/report.md
pytest agent/tests                       # checks the scenario files and the script (Gemini faked)
```

Reading the output: `rules said` is the rule engine, `gemini said` is Gemini's own suggestion,
`final` is what the ticket would use after the guard rails, and `result` compares `final` with `expected`.
A line marked "template text" means Gemini was not used (no key, quota hit or model name changed). Check
`GEMINI_MODEL` in `backend/.env` first if that happens. The script never prints keys and does not change backend state.

## Add a scenario

Copy a file in `scenarios/`, change the numbers and `expected_cause`, run `pytest agent/tests`, then `evaluate.py`.

## Known limits

- The free Gemini tier has rate limits; `--delay` (default 3 s) spaces the calls.
- LLM answers vary between runs. Use `--runs 3` or more before quoting a result.
- Gemini cannot yet decide uplink vs AP failure or change IoT tickets (see guard rails). That needs a change in `engine.py`.
- v3 explanations sometimes quoted the prompt's rule-of-thumb numbers ("below 3%", "the -70 dBm threshold") as if they
  were system thresholds. v3.1 forbids this and reduced it, but did not remove it: 1/24 and 3/24 explanations were
  flagged in two runs. `evaluate.py` prints a `CHECK:` line and a summary count for any explanation with a measurement
  that is not in the evidence or that says "threshold". It is a lint, not proof: it does not catch wrong reasoning.
- Likely cause and follow-up (v3.2, not built): "-70 dBm" and "3%" are our own numbers in the prompt; the monitor's
  real limits are 5% and -80 dBm. Rewriting the cues relative to the real limits would leave nothing invented to quote.
  Explanation wording also varies between runs, so compare flagged counts over several runs, not one.
- Gemini sometimes computes numbers (e.g. "177 connected clients" = 92 + 85) or spells out units ("980 milliseconds"); the lint ignores both. Correct so far, but not measured values.
- Not tested: borderline evidence (e.g. 4% loss with -75 dBm), conflicting signals, or real (non-simulated) data.
