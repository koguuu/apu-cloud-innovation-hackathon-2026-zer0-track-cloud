# career/

**Owner: Pang Zai Jie**

Turns lab activity into a career suggestion. Also owns the pitch story ([../docs/pitch-outline.md](../docs/pitch-outline.md)).

## Inputs
`lab_activity` events aggregated per anonymised student (hours per lab type, modules completed).

## Output
A `career_suggestion` object (see [../docs/event-schema.md](../docs/event-schema.md)).

## Tasks
- [ ] Aggregate hours and modules per student
- [ ] Role and certificate mapping (SOC Analyst, Cloud Infrastructure, IoT Security, etc.)
- [ ] Gemini prompt returning the career fit, certs, skills and a 6-month plan
- [ ] Add the "suggestion, not a decision" disclaimer

Note: time in a lab does not always mean interest, so present it as a suggestion and let the student opt in.
