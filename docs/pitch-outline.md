# Pitch outline

Owner: Pang Zai Jie (everyone reviews). Format: **PDF, max 10 MB**. Judging criteria were not published yet, so update this when they are.

## Submission fields

- Project title and challenge track (Intelligent Automation & Digital Transformation)
- Summary (at least 50 characters)
- HTTPS repository link
- PDF pitch deck
- Demo link (optional)

## Draft summary (edit freely)

> Campus Lab Agent is an autonomous campus assistant that combines simulated Wi-Fi telemetry and lab card-reader
> data. It detects network failures, finds the root cause with Gemini, raises IT tickets automatically, tells
> students where to study right now, and turns lab activity into personalised career path suggestions.

## Slide outline (about 8-10 slides)

1. **Title and one-line pitch**
2. **Problem:** Wi-Fi failures, students don't know where to study, no data-driven career guidance
3. **Solution overview:** one data pipeline, two outputs
4. **Architecture:** IoT + Network + Cloud (diagram from the README)
5. **Live demo or screenshots:** fault injection to ticket to student reroute
6. **AI at work:** how Gemini does root-cause analysis and career mapping
7. **Career module:** lab hours to career fit to 6-month plan
8. **Impact:** faster IT response, better use of campus space, clearer student direction (add a measurable before/after)
9. **Privacy and ethics:** simulated data, hashed IDs, opt-in suggestions
10. **Roadmap:** real APU data integration, more labs, SOC-analyst lab bundles

## Demo script (3 minutes)

1. (0:00) One-sentence problem: "When Wi-Fi fails, nobody knows where to go and IT finds out late."
2. (0:20) Show the student page: all zones healthy.
3. (0:40) Click **Kill AP in Block B**.
4. (1:00) Show the agent's root cause and the auto-generated ticket on the staff dashboard.
5. (1:40) Show the student page rerouting to a healthy zone.
6. (2:10) Show the career panel for a sample student.
7. (2:40) Close with impact and roadmap.

## Before submitting

- [ ] Deck exported as PDF, under 10 MB
- [ ] Demo tested 3 times end to end
- [ ] Demo video recorded as a backup
- [ ] Repo access checked with the organisers (private vs public)
