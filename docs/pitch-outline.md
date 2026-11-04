# Pitch outline

Owner: Pang Zai Jie (everyone reviews). Format: **PDF, max 10 MB**. Judging criteria were not published yet, so update this when they are.

**Product:** Smart Lab Companion (working title)
**Line:** "From finding a working lab to knowing what to learn next, one companion for every student's lab journey."

**Pitch rule:** one character, one journey. We follow one student, **Raja**, from finding a working lab to knowing what to learn next. We never present "two features". Show results, not logs.

## Submission fields

- Project title and challenge track (Intelligent Automation & Digital Transformation)
- Summary (at least 50 characters)
- HTTPS repository link
- PDF pitch deck
- Demo link (optional)

## Draft summary (edit freely)

> Smart Lab Companion is an autonomous campus agent that monitors simulated Wi-Fi and IoT health across blocks
> and labs, finds the root cause of failures with Gemini, opens IT tickets and alerts the admin on Telegram
> automatically, and shows students which labs are free and working right now. A lab-record chatbot turns
> a student's lab hours into guidance on what to learn next.

## 3-minute script

| Time | What | Notes |
|---|---|---|
| 0:00-0:25 | **Problem through Raja.** Labs are where skills are built, but Raja can't tell which labs are working or where his hours lead. | One sentence of problem, no jargon |
| 0:25-1:15 | **Live demo: lab fails.** Raja opens the app and sees which labs are free. Click "Kill AP". The agent finds the root cause, a ticket is created, the admin gets a Telegram alert, and the app sends Raja to a healthy lab. | About 50 seconds. Show the result, not the logs |
| 1:15-2:05 | **Chatbot demo (stretch).** Raja asks "what should I pursue next?" and it answers from his own lab hours. | If not ready, replace with the roadmap slide |
| 2:05-2:35 | **Architecture in one slide.** IoT, network and cloud (Gemini). All data simulated for the prototype. | Use the diagram from the README |
| 2:35-3:00 | **Impact and close.** Faster IT response, less lost lab time, clearer student direction. Ready for real APU data. | Add a measurable before/after |

## Slide outline (about 8 slides)

1. **Title and one-line pitch**
2. **Problem:** Raja's story (labs fail, nobody knows where to go, IT finds out late)
3. **Solution:** Smart Lab Companion, the journey in one picture
4. **Architecture:** IoT + Network + Cloud (diagram from the README)
5. **Live demo or screenshots:** fault injection to ticket to Telegram alert to reroute
6. **AI at work:** how Gemini does the root-cause analysis
7. **Lab Record (stretch):** lab hours to "what should I pursue next?" (or "future roadmap" if cut)
8. **Impact, privacy and roadmap:** simulated data, hashed IDs, opt-in suggestions, real APU data next

## Before submitting

- [ ] Deck exported as PDF, under 10 MB
- [ ] Demo tested 3 times end to end
- [ ] Demo video recorded as a backup
- [ ] Repo access checked with the organisers (private vs public)
