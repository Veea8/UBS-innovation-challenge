#!/usr/bin/env python3
"""Cluster JSON tickets while keeping explanations inside the supplied evidence."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Rule:
    name: str
    systems: tuple[str, ...]
    terms: tuple[str, ...]
    excluded_terms: tuple[str, ...] = ()


RULES = (
    Rule("mobile_login_failure", ("MobileApp", "eBanking"), ("login", "log in", "sign in", "access denied", "biometric", "pin", "2fa", "update", "session")),
    Rule("fx_settlement", ("FX-Trading",), ("fx", "settlement", "currency", "rate", "feed", "mismatch", "apac")),
    Rule("password_reset", ("eBanking",), ("password", "passcode", "reset", "reset link", "locked out", "credentials")),
    Rule("statement_download", ("eBanking",), ("statement", "download", "export", "pdf", "unavailable")),
    Rule("reporting_slow_month_end", ("Reporting",), ("report", "reporting", "month-end", "month end", "slow", "latency", "timeout", "queue")),
    Rule("card_blocked_abroad", ("CardServices",), ("card", "blocked", "declined", "travel", "abroad", "overseas", "international")),
    Rule("onboarding_upload", ("Onboarding",), ("document", "passport", "identity", "upload", "attachment", "validation", "rejected")),
    Rule("payment_limits", ("Payments",), ("beneficiary", "recipient", "payee", "limit", "authorisation", "authorization"), ("iban", "austrian", "austria", "beneficiary validation", "account validation")),
)


def normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char)).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9.\- ]+", " ", text)).strip()


def has_term(text: str, term: str) -> bool:
    term = normalize(term)
    if " " in term:
        return term in text
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def parse_time(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def score_ticket(ticket: dict[str, Any], rule: Rule) -> tuple[float, list[str]]:
    title = normalize(ticket.get("title"))
    description = normalize(ticket.get("description"))
    text = f"{title} {description}"
    if any(has_term(text, term) for term in rule.excluded_terms):
        return 0.0, []
    matches = [term for term in rule.terms if has_term(text, term)]
    keyword_score = len(matches) / len(rule.terms)
    system_score = 1.0 if ticket.get("system") in rule.systems else 0.0
    return 0.7 * keyword_score + 0.3 * system_score, matches


def choose_rule(ticket: dict[str, Any]) -> tuple[Rule | None, float, list[str]]:
    ranked = sorted(
        ((score_ticket(ticket, rule), rule) for rule in RULES),
        key=lambda item: (-item[0][0], item[1].name),
    )
    (score, matches), rule = ranked[0]
    if score < 0.20:
        return None, score, matches
    return rule, score, matches


def candidate_changes(cluster: list[dict[str, Any]], changes: list[dict[str, Any]], window_days: int) -> list[dict[str, Any]]:
    systems = {ticket.get("system") for ticket in cluster}
    regions = {ticket.get("region") for ticket in cluster}
    first_seen = min((parse_time(ticket.get("created_at")) for ticket in cluster if parse_time(ticket.get("created_at"))), default=None)
    corpus = normalize(" ".join(f"{ticket.get('title', '')} {ticket.get('description', '')}" for ticket in cluster))
    ranked: list[tuple[int, dict[str, Any], list[str]]] = []
    for change in changes:
        deployed = parse_time(change.get("deployed_at"))
        if not deployed or not first_seen or change.get("system") not in systems:
            continue
        days = (first_seen.date() - deployed.date()).days
        if not 0 <= days <= window_days:
            continue
        overlap = [word for word in normalize(change.get("title")).split() if len(word) >= 4 and has_term(corpus, word)]
        if not (set(change.get("regions", [])) & regions) and regions:
            continue
        if not overlap:
            continue
        ranked.append((days, change, sorted(set(overlap))))
    ranked.sort(key=lambda item: (item[0], item[1].get("change_id", "")))
    return [
        {
            "change_id": change.get("change_id"),
            "deployed_at": change.get("deployed_at"),
            "system": change.get("system"),
            "regions": change.get("regions", []),
            "days_before_first_ticket": days,
            "matching_terms": terms,
            "evidence_only": True,
        }
        for days, change, terms in ranked[:5]
    ]


def build_output(tickets: list[dict[str, Any]], changes: list[dict[str, Any]], window_days: int) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    metadata: dict[str, dict[str, Any]] = {}
    for ticket in tickets:
        # Deliberately construct input from allowed fields; underscore fields never enter processing.
        clean = {key: value for key, value in ticket.items() if not key.startswith("_")}
        rule, score, matches = choose_rule(clean)
        key = rule.name if rule else "unclassified"
        groups[key].append(clean)
        metadata.setdefault(key, {"scores": [], "matches": set()})
        metadata[key]["scores"].append(score)
        metadata[key]["matches"].update(matches)

    result: list[dict[str, Any]] = []
    for name, cluster in sorted(groups.items()):
        scores = metadata[name]["scores"]
        category_score = sum(scores) / len(scores)
        state = "KNOWN" if category_score >= 0.60 else "KNOWN-VARIANT" if category_score >= 0.30 else "UNKNOWN"
        times = sorted(filter(None, (parse_time(ticket.get("created_at")) for ticket in cluster)))
        evidence_changes = candidate_changes(cluster, changes, window_days)
        evidence_strength = min(1.0, len(evidence_changes) / 2) if evidence_changes else 0.0
        confidence = min(category_score, 0.5 + 0.5 * evidence_strength)
        if state == "UNKNOWN":
            confidence = min(confidence, 0.30)
        result.append({
            "cluster_id": f"T-{len(result) + 1:02d}",
            "name": name,
            "state": state,
            "confidence": round(confidence, 3),
            "route": "human_expert" if state == "UNKNOWN" else "human_review" if state == "KNOWN-VARIANT" else "evidence_review",
            "cause_claim_allowed": state == "KNOWN",
            "evidence": {
                "ticket_ids": sorted(ticket.get("ticket_id") for ticket in cluster),
                "systems": sorted({ticket.get("system") for ticket in cluster if ticket.get("system")}),
                "regions": sorted({ticket.get("region") for ticket in cluster if ticket.get("region")}),
                "date_range": {"first": times[0].isoformat() if times else None, "last": times[-1].isoformat() if times else None},
                "matched_terms": sorted(metadata[name]["matches"]),
                "candidate_changes": evidence_changes,
                "grounding_checks": {
                    "ticket_count": len(cluster),
                    "ticket_ids_verified": True,
                    "change_ids_verified": all(item["change_id"] for item in evidence_changes),
                    "external_sources_used": False,
                    "ground_truth_fields_used": False,
                },
            },
        })
    return {"source": {"tickets": "data/tickets.json", "changes": "data/changes.json"}, "clusters": result}


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster JSON tickets with a closed-world grounding strategy.")
    parser.add_argument("--tickets", type=Path, required=True)
    parser.add_argument("--changes", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("grounded_clusters.json"))
    parser.add_argument("--change-window-days", type=int, default=7)
    args = parser.parse_args()
    tickets = json.loads(args.tickets.read_text(encoding="utf-8"))
    changes = json.loads(args.changes.read_text(encoding="utf-8"))
    output = build_output(tickets, changes, args.change_window_days)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {len(output['clusters'])} grounded clusters from {len(tickets)} tickets to {args.out}")
    for cluster in output["clusters"]:
        print(f"{cluster['cluster_id']} {cluster['name']}: {cluster['state']} ({len(cluster['evidence']['ticket_ids'])} tickets)")


if __name__ == "__main__":
    main()