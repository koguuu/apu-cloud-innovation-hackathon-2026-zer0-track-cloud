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
- **Limited override.** Gemini may correct `ap_hardware_failure` <-> `congestion`, and only when it reports
  `high` confidence. Uplink and IoT tickets always keep the rule cause, because `engine.py` clears them using
  `affected_aps` / `affected_devices`, and changing the cause there would resolve the ticket by mistake.
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
| `ap_looks_like_congestion` | Tricky: rules say AP failure, numbers look like congestion | ap_hardware_failure | congestion |

The `evidence` in each file has the same shape `engine.py` builds, so the script exercises the real code path.
"Expected" is our own judgement of the correct answer, and the data is simulated.

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

- The free Gemini tier has rate limits; `--delay` (default 1 s) spaces the calls.
- LLM answers vary between runs. Use `--runs 3` or more before quoting a result.
- Gemini cannot yet decide uplink vs AP failure or change IoT tickets (see guard rails). That needs a change in `engine.py`.
