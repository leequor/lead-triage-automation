"""Lead triage + reply-drafting automation for small businesses.

Reads raw inquiries (CSV or JSON), scores them, and produces a ranked triage
sheet plus ready-to-send reply drafts. Zero external dependencies, zero API
keys — drop in your own LLM call where marked if you want the drafts rewritten.

Usage:
    python leadbot.py --input inquiries.csv --out out/
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

URGENT = re.compile(r"\b(urgent|asap|emergency|today|tomorrow|this week|deadline|rush)\b", re.I)
BUDGET = re.compile(r"\$[\d,]{3,}|\b(budget|quote|pricing|per month|retainer)\b", re.I)
DECISION = re.compile(r"\b(i own|i'm the owner|founder|director|manager|ceo|we need)\b", re.I)
WEEKDAY_HOURS = re.compile(r"\b(\d{1,2}[:.]\d{2}\s*(am|pm))\b", re.I)
SPAM = re.compile(r"\b(seo service|backlink|guest post|web design offer|free audit)\b", re.I)
NEGATIVE = re.compile(r"\b(bill|invoice|overcharged|refund|complaint|broken|cancel)\b", re.I)
PRICING = re.compile(r"\b(price|pricing|cost|how much|quote)\b", re.I)
BOOKING = re.compile(r"\b(book|appointment|schedule|available|consultation)\b", re.I)


@dataclass
class Lead:
    name: str
    email: str
    source: str
    message: str
    score: int = 0
    tags: list[str] = field(default_factory=list)
    priority: str = "LOW"

    @property
    def is_spam(self) -> bool:
        return bool(SPAM.search(self.message))


def score_lead(lead: Lead) -> Lead:
    text = lead.message
    if URGENT.search(text):
        lead.score += 30
        lead.tags.append("urgent")
    if BUDGET.search(text):
        lead.score += 25
        lead.tags.append("budget-stated")
    if DECISION.search(text):
        lead.score += 20
        lead.tags.append("decision-maker")
    if WEEKDAY_HOURS.search(text):
        lead.score += 5
        lead.tags.append("phone-number")
    if lead.source.lower() in {"referral", "google", "website"}:
        lead.score += 15
        lead.tags.append(f"source:{lead.source.lower()}")

    if NEGATIVE.search(text):
        lead.score = max(lead.score, 85)
        lead.tags.append("existing-customer-issue")
    elif PRICING.search(text):
        lead.score += 10
        lead.tags.append("pricing-question")
    elif BOOKING.search(text):
        lead.score += 10
        lead.tags.append("booking-request")

    lead.priority = "HOT" if lead.score >= 70 else "WARM" if lead.score >= 40 else "COLD"
    return lead


def read_leads(path: Path) -> list[Lead]:
    if path.suffix.lower() == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [Lead(r["name"], r["email"], r.get("source", "unknown"), r["message"]) for r in raw]
    with path.open(newline="", encoding="utf-8") as fh:
        return [
            Lead(row["name"].strip(), row["email"].strip(), row.get("source", "unknown").strip(), row["message"].strip())
            for row in csv.DictReader(fh)
        ]


def draft_reply(lead: Lead, business: str) -> str:
    first = lead.name.split()[0]
    if "existing-customer-issue" in lead.tags:
        body = (
            "I'm sorry about the trouble with your bill — that's on me to sort out. "
            "I've flagged this for the owner and you'll hear back within 2 business hours with a correction."
        )
    elif "booking-request" in lead.tags:
        body = (
            "Thanks for reaching out — we'd love to get you booked in. Can you tell us which day works "
            "best, morning or afternoon? Once we confirm we'll hold the slot for you."
        )
    elif "pricing-question" in lead.tags:
        body = (
            "Thanks for asking about pricing. The short answer is that most jobs at {business} land in a "
            "clear fixed-price range, and we're happy to quote yours for free — just tell us what you need done."
        )
    elif lead.priority == "HOT":
        body = (
            "Thanks for reaching out — this sounds time-sensitive, so we're treating it as a priority. "
            "We can take this today if you'd like; reply with a phone number and time that works and we'll call you."
        )
    else:
        body = "Thanks for getting in touch. We'll review your message and reply with next steps within 24 hours."
    return f"Subject: Re: your message to {business}\n\nHi {first},\n\n{body.format(business=business)}\n\nBest,\n{business} team\n"


def run(input_path: Path, out_dir: Path, business: str) -> dict:
    leads = [score_lead(l) for l in read_leads(input_path)]
    spam = [l for l in leads if l.is_spam]
    triage = sorted([l for l in leads if not l.is_spam], key=lambda l: -l.score)

    out_dir.mkdir(parents=True, exist_ok=True)
    replies_dir = out_dir / "replies"
    replies_dir.mkdir(exist_ok=True)

    with (out_dir / "triage.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["priority", "score", "name", "email", "source", "tags", "message"])
        for l in triage:
            writer.writerow([l.priority, l.score, l.name, l.email, l.source, "|".join(l.tags), l.message])

    for l in triage:
        safe = re.sub(r"[^a-z0-9]+", "-", l.name.lower()).strip("-")
        (replies_dir / f"{l.priority}-{l.score}-{safe}.txt").write_text(draft_reply(l, business), encoding="utf-8")

    counts = {"HOT": 0, "WARM": 0, "COLD": 0}
    for l in triage:
        counts[l.priority] += 1
    summary = {
        "input": str(input_path),
        "leads_in": len(leads),
        "spam_filtered": len(spam),
        "triaged": len(triage),
        "by_priority": counts,
        "drafts_written": len(triage),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Triage inbound leads and draft replies.")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=Path("out"))
    ap.add_argument("--business", default="the business")
    args = ap.parse_args()
    summary = run(args.input, args.out, args.business)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
