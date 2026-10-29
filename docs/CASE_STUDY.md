# Case Study — Inbox Triage for a Local Service Business

**Setting:** HVAC / dental / clinic / auto shop — any SMB where one shared inbox receives inquiries from Google Ads, a Facebook page, referrals, and the website.

**Problem:** every message waits for the same attention. An owner reporting a double-billed invoice queues behind a link-spam pitch, and after-hours leads go cold by morning.

## Run under review

```bash
python leadbot.py --input sample/inquiries.csv --out out --business "BrightCare HVAC"
```

| Metric | Result |
|---|---|
| Inquiries processed | 8 |
| Vendor spam auto-filtered | 1 |
| HOT surfaced first | 2 |
| WARM | 3 |
| COLD | 2 |
| Reply drafts generated | 7 |

Full output in [`demo-output/`](../demo-output/).

## What the ranking got right

Three cases are the ones that decide whether an owner trusts a tool like this:

1. **The complaint.** "Urgent — our service invoice looks double billed, need this fixed today, I'm the owner" → HOT at 85, with a de-escalation draft, not a sales pitch. Existing-customer problems are floored at 85 deliberately: retention beats acquisition, and a generic "we'd love to get you booked in!" to an angry customer is how reviews get lost.
2. **The whale.** 14 properties, $40k/yr budget, deadline this week → 90, ranked #1. Urgency + stated budget + decision-maker language plus a high-intent source stack to the top without any judgment call being needed.
3. **The noise.** A backlink/guest-post pitch was filtered out rather than drafted-to. Automating replies to spam is how businesses end up in a conversation with a scammer; suppression is a feature.

The COLD rows are still written to the queue rather than discarded — a $0-scoring "do you also replace filters?" is a real customer whose message just doesn't need to be answered first.

## Manual baseline

Roughly 40 inquiries/week at 4–5 minutes of read-and-decide each ≈ 3–4 hours. The pipeline runs in well under a second, so the human only touches the top of the list. That is the whole argument: *stop reading every email; answer the ones worth money.*

## Honest limits of this demo

- Keyword heuristics misfire on unusual phrasing. The scoring table is short because it's legible — that's the trade, and it's the reason the tags column exists: every score is explainable back to the text that produced it.
- The drafts are templates. They read fine as starting points and would need an LLM pass or human edit before sending at volume.
- It processes an export, not a live mailbox — ingestion is the next layer, not this one.
- No persistence or dedupe across runs; feed it the same export twice and you get the same queue twice. Intentional for a stateless demo, wrong for production.

## Where a real deployment goes

1. IMAP or Gmail API ingestion on a schedule.
2. Owner alert (email/Slack) when any lead scores `>= 70`.
3. `draft_reply()` swapped for a model call carrying the business's tone.
4. Weekly reporting aggregated from `summary.json`: volume, source mix, response rate.
