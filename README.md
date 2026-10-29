# Lead Triage & Reply Drafting Automation

Turns a small-business inquiry inbox into a ranked **HOT / WARM / COLD** queue plus a ready-to-send reply draft for every real lead. Python 3.10+, standard library only — no API keys, no database, no SaaS login.

## The problem it solves

Service businesses (HVAC, dental, clinics, shops) get inquiries from Google, Facebook, referrals and their website into one shared pile. A same-day billing complaint from the owner sits behind a backlink-spam email, and both wait until someone has time to scroll. This pipeline sorts them before a human looks.

## Quick start

```bash
python leadbot.py --input sample/inquiries.csv --out out --business "BrightCare HVAC"
```

Outputs:

| Path | Contents |
|---|---|
| `out/triage.csv` | Ranked queue: priority, score, contact, source, matched signals |
| `out/replies/PRIORITY-SCORE-name.txt` | One ready-to-send draft per real lead |
| `out/summary.json` | Run stats |

## Verified run on the included sample set

```
leads_in: 8   spam_filtered: 1   triaged: 7   HOT: 2   WARM: 3   COLD: 2   drafts_written: 7
```

Ranking behavior on the cases that actually matter:

- A property-management lead stating a $40k/yr budget and a this-week deadline scored **90 (HOT, #1)**.
- An owner's "urgent — double billed, fixed today" complaint scored **85 (HOT)** and received a de-escalation draft rather than a sales reply, because existing-customer problems are force-escalated.
- A link-building spam message was **filtered out entirely** instead of being replied to.

## Scoring model

| Signal | Weight | Rationale |
|---|---|---|
| Urgency language (`urgent`, `asap`, `today`, `deadline`) | +30 | Time-boxed buyers convert fastest |
| Stated budget (`$N`, `budget`, `retainer`, `per month`) | +25 | Money is already committed |
| Decision-maker self-identification (`owner`, `founder`, `manager`) | +20 | No gatekeeper in the path |
| High-intent source (`referral`, `google`, `website`) | +15 | Social feed inquiries are usually lower intent |
| Pricing or booking intent | +10 | Explicit buying action |
| Phone number present | +5 | Reachable now |
| Existing-customer complaint | floor of 85 | A lost customer costs more than a missed lead |

Thresholds: `>= 70` HOT, `>= 40` WARM, else COLD.

## Design notes

- **Deterministic by default.** Rules, not a model — the sort is explainable, debuggable, and costs nothing to run. `draft_reply()` is the single seam where an LLM call can be dropped in if you want rewrites.
- **Dataclass pipeline, not string soup.** Each `Lead` carries its own score and matched tags, so the CSV output explains itself to a non-technical owner.
- **Complaints bypass the sales logic.** Intent is checked before priority is derived, so an angry customer never gets "we'd love to get you booked in!"
- **UTF-8 declared on every file handle**, because inboxes contain em dashes and accented names.
- **Idempotent output.** Re-running overwrites `out/` cleanly; no state carried between runs.

## Extending it for a real deployment

1. Replace the CSV export with live mailbox ingestion (IMAP or the Gmail API).
2. Push an alert to the owner when a lead scores `>= 70` instead of waiting for someone to open the folder.
3. Swap the template drafts for an LLM call with the business's tone in the system prompt.
4. Aggregate `summary.json` across runs into a weekly report: lead volume, source mix, response rate.

See [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) for the walkthrough-style writeup of the demo run.

## Data & privacy

`sample/inquiries.csv` is entirely synthetic — invented names, businesses and messages. `demo-output/` is committed as evidence that the script runs; it is generated from that synthetic input. No real customer data was used anywhere in this repo. If you deploy this against a live inbox, keep exports out of version control (`out/` is gitignored) and get written consent before showing any of it publicly.

## License

MIT — see [LICENSE](LICENSE).
