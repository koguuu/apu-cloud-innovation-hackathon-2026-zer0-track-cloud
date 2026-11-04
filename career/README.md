# career/

**Owner: Pang Zai Jie**

This folder holds Pang Zai Jie's work: the Telegram alert and occupancy (core), and Lab Record (stretch). It also covers the pitch story ([../docs/pitch-outline.md](../docs/pitch-outline.md)).

## Core
- [ ] Create the Telegram bot (BotFather), store the token in `.env`
- [ ] `send_alert(notification)`: send a short message with location, root cause and recommended action, then mark `sent: true`
- [ ] Occupancy: turn `card_access` events into `seats_free` per lab
- [ ] Pitch deck story and demo script

## Stretch: Lab Record (start after the 7 Nov checkpoint)
Inputs: `lab_activity` events aggregated per anonymised student (hours per lab, modules completed).
Output: a `career_suggestion` and chatbot answers (see [../docs/event-schema.md](../docs/event-schema.md)).

- [ ] Aggregate hours and modules per student
- [ ] Gemini chatbot: "what should I pursue next?", answered only from that student's own data
- [ ] Outage rule: minutes spent elsewhere while a lab had an outage ticket are flagged, not counted as interest
- [ ] Add the "suggestion, not a decision" disclaimer and an opt-in notice

If the chatbot isn't working at the checkpoint, it becomes a "future roadmap" slide.
