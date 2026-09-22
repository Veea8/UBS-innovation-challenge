#!/usr/bin/env python3
"""
Deterministic ticket clustering.

Scoring:
    Score(C, T) = 5*S + 3*K + 2*H + 2*D + 3*X + R

Where:
    S = ticket system matches cluster system
    K = ticket matches enough cluster concepts
    H = title matches at least one cluster concept
    D = description matches at least one cluster concept
    X = related recent change detected
    R = region matches a configured cluster region pattern

Assignment:
    - choose highest-scoring cluster
    - require score >= --threshold (default 7)
    - tie-break by:
        1. more matched concepts
        2. closer related change
        3. cluster name alphabetically
    - otherwise assign "singleton"

_ground-truth fields such as "_gt_theme" are NEVER used to assign a cluster.
They are copied through so they can be used later for evaluation.

Expected ticket CSV columns by default:
    incident_id,title,description,system,region,created_at,_gt_theme

Expected changes CSV columns by default:
    change_id,system,date,title,description

Example:
    python cluster_tickets.py \
        --tickets tickets.csv \
        --changes changes.csv \
        --out clustered_tickets.csv

The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClusterRule:
    name: str
    system: Optional[str]
    concepts: Dict[str, Sequence[str]]
    min_concepts: int = 1
    regions: Sequence[str] = field(default_factory=tuple)


CLUSTERS: Sequence[ClusterRule] = (
    ClusterRule(
        name="password_reset",
        system="eBanking",
        concepts={
            "password": ("password", "passcode", "credentials"),
            "reset": ("reset", "reset email", "reset link", "expired link"),
            "locked": ("locked out", "account locked", "failed attempts"),
        },
    ),
    ClusterRule(
        name="mobile_login_failure_v42",
        system="MobileApp",
        concepts={
            "login": (
                "login", "log in", "sign in", "access",
                "authentication", "authenticate", "pin"
            ),
            "biometric": (
                "face id", "biometric", "fingerprint", "touch id"
            ),
            "update": (
                "update", "latest version", "new app version", "4.2.0"
            ),
            "session": (
                "session expired", "session timeout", "session ended"
            ),
            "crash": (
                "app crash", "crashes", "crashed", "force close"
            ),
            "2fa": (
                "2fa", "mfa", "push", "push notification", "verification code"
            ),
        },
    ),
    ClusterRule(
        name="onboarding_upload",
        system="Onboarding",
        concepts={
            "document": (
                "document", "passport", "proof of id", "proof of identity",
                "identity document", "id document"
            ),
            "upload": ("upload", "uploaded", "attachment"),
            "validation": (
                "validation", "rejected", "invalid", "not accepted"
            ),
        },
    ),
    ClusterRule(
        name="statement_download",
        system="eBanking",
        concepts={
            "statement": ("statement", "account statement"),
            "download": ("download", "export", "pdf"),
            "unavailable": ("unavailable", "not available", "cannot open"),
        },
    ),
    ClusterRule(
        name="reporting_slow_month_end",
        system="Reporting",
        concepts={
            "reporting": ("report", "reporting", "dashboard"),
            "month_end": (
                "month-end", "month end", "monthend",
                "end of month", "eom"
            ),
            "performance": (
                "queue", "slow", "slowness", "latency",
                "timeout", "timed out", "performance"
            ),
        },
    ),
    ClusterRule(
        name="branch_hardware",
        system="eBanking",
        concepts={
            "branch": ("branch", "branch office"),
            "hardware": (
                "printer", "kiosk", "workstation",
                "branch device", "terminal", "scanner"
            ),
            "offline": ("offline", "not responding", "disconnected"),
        },
    ),
    ClusterRule(
        name="card_blocked_abroad",
        system="CardServices",
        concepts={
            "card": ("card", "credit card", "debit card"),
            "blocked": ("blocked", "declined", "rejected"),
            "abroad": (
                "abroad", "travel", "overseas", "foreign country",
                "international"
            ),
        },
    ),
    ClusterRule(
        name="payment_limits",
        system="Payments",
        concepts={
            "beneficiary": ("beneficiary", "recipient", "payee"),
            "limit": (
                "payment limit", "transfer limit", "daily limit",
                "limit query", "limit service"
            ),
            "authorisation": (
                "authorisation", "authorization",
                "authorise", "authorize", "approval"
            ),
        },
    ),
    ClusterRule(
        name="iban_validation_vendor_regression",
        system="Payments",
        concepts={
            "iban": ("iban",),
            "validation": (
                "beneficiary validation", "account validation",
                "account rejected", "invalid account", "rejected"
            ),
            "austria": (
                "austrian account", "austria", "at iban", "at account"
            ),
            "vendor": ("vendor", "provider", "third party", "third-party"),
        },
    ),
)


# ---------------------------------------------------------------------------
# Normalisation / matching
# ---------------------------------------------------------------------------

def normalize(value: object) -> str:
    """Deterministic text normalisation."""
    if value is None:
        return ""
    text = str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"[_/\\|]+", " ", text)
    text = re.sub(r"[^a-z0-9.\- ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def phrase_present(text: str, phrase: str) -> bool:
    """
    Match a phrase deterministically.

    Single-word terms use token boundaries, so "pin" does not match "spinning".
    Multi-word terms use normalised substring matching.
    """
    text = normalize(text)
    phrase = normalize(phrase)
    if not phrase:
        return False

    if " " in phrase:
        return phrase in text

    pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def matched_concepts(text: str, rule: ClusterRule) -> Set[str]:
    matches: Set[str] = set()
    for concept_name, synonyms in rule.concepts.items():
        if any(phrase_present(text, synonym) for synonym in synonyms):
            matches.add(concept_name)
    return matches


def system_matches(ticket_system: str, cluster_system: Optional[str]) -> bool:
    if not cluster_system:
        return False
    return normalize(ticket_system) == normalize(cluster_system)


def region_matches(ticket_region: str, regions: Sequence[str]) -> bool:
    if not regions:
        return False
    ticket_region_n = normalize(ticket_region)
    return any(ticket_region_n == normalize(region) for region in regions)


# ---------------------------------------------------------------------------
# Dates / change correlation
# ---------------------------------------------------------------------------

DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
)


def parse_date(value: object) -> Optional[datetime]:
    if value is None:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    # Python ISO parser first.
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        pass

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    return None


def safe_day_difference(later: datetime, earlier: datetime) -> int:
    """
    Return whole-day difference while avoiding aware/naive datetime mismatch.
    Calendar-date proximity is enough for this deterministic use case.
    """
    return (later.date() - earlier.date()).days


@dataclass(frozen=True)
class ChangeMatch:
    detected: bool
    days_before: Optional[int]
    change_id: str = ""


def find_related_change(
    ticket: Dict[str, str],
    rule: ClusterRule,
    changes: Sequence[Dict[str, str]],
    window_days: int,
) -> ChangeMatch:
    """
    A related change is detected when all of these are true:
      1. change system == ticket system == cluster system
      2. change happened from 0 to window_days before ticket creation
      3. change text matches at least one concept from the candidate cluster

    If several changes match, the closest prior change wins.
    """
    ticket_date = parse_date(ticket.get("created_at"))
    if ticket_date is None:
        return ChangeMatch(False, None)

    best: Optional[Tuple[int, str]] = None

    for change in changes:
        if not system_matches(ticket.get("system", ""), rule.system):
            continue

        if normalize(change.get("system", "")) != normalize(ticket.get("system", "")):
            continue

        change_date = parse_date(change.get("date"))
        if change_date is None:
            continue

        days_before = safe_day_difference(ticket_date, change_date)
        if not (0 <= days_before <= window_days):
            continue

        change_text = " ".join(
            [
                change.get("title", "") or "",
                change.get("description", "") or "",
            ]
        )
        if not matched_concepts(change_text, rule):
            continue

        candidate = (days_before, change.get("change_id", "") or "")
        if best is None or candidate < best:
            best = candidate

    if best is None:
        return ChangeMatch(False, None)

    return ChangeMatch(True, best[0], best[1])


# ---------------------------------------------------------------------------
# Scoring / assignment
# ---------------------------------------------------------------------------

@dataclass
class ClusterScore:
    cluster: str
    score: int
    system_match: int
    keyword_match: int
    title_match: int
    description_match: int
    change_match: int
    region_match: int
    matched_concept_count: int
    matched_concepts: List[str]
    change_days_before: Optional[int]
    related_change_id: str


def score_cluster(
    ticket: Dict[str, str],
    rule: ClusterRule,
    changes: Sequence[Dict[str, str]],
    change_window_days: int,
) -> ClusterScore:
    title = ticket.get("title", "") or ""
    description = ticket.get("description", "") or ""
    full_text = f"{title} {description}"

    title_concepts = matched_concepts(title, rule)
    description_concepts = matched_concepts(description, rule)
    all_concepts = matched_concepts(full_text, rule)

    S = int(system_matches(ticket.get("system", ""), rule.system))
    K = int(len(all_concepts) >= rule.min_concepts)
    H = int(bool(title_concepts))
    D = int(bool(description_concepts))

    change = find_related_change(
        ticket=ticket,
        rule=rule,
        changes=changes,
        window_days=change_window_days,
    )
    X = int(change.detected)

    R = int(region_matches(ticket.get("region", ""), rule.regions))

    score = 5 * S + 3 * K + 2 * H + 2 * D + 3 * X + R

    return ClusterScore(
        cluster=rule.name,
        score=score,
        system_match=S,
        keyword_match=K,
        title_match=H,
        description_match=D,
        change_match=X,
        region_match=R,
        matched_concept_count=len(all_concepts),
        matched_concepts=sorted(all_concepts),
        change_days_before=change.days_before,
        related_change_id=change.change_id,
    )


def tie_break_key(result: ClusterScore) -> Tuple[int, int, int, str]:
    """
    Sort key, ascending:
      1. higher score
      2. more matched concepts
      3. closer change
      4. alphabetical cluster name
    """
    change_distance = (
        result.change_days_before
        if result.change_days_before is not None
        else 10**9
    )
    return (
        -result.score,
        -result.matched_concept_count,
        change_distance,
        result.cluster,
    )


def assign_ticket(
    ticket: Dict[str, str],
    changes: Sequence[Dict[str, str]],
    threshold: int,
    change_window_days: int,
) -> Tuple[str, ClusterScore, List[ClusterScore]]:
    scores = [
        score_cluster(ticket, rule, changes, change_window_days)
        for rule in CLUSTERS
    ]
    ranked = sorted(scores, key=tie_break_key)
    winner = ranked[0]

    if winner.score < threshold:
        return "singleton", winner, ranked

    return winner.cluster, winner, ranked


# ---------------------------------------------------------------------------
# CSV I/O
# ---------------------------------------------------------------------------

def read_csv(path: Optional[Path]) -> List[Dict[str, str]]:
    if path is None:
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def write_results(
    tickets: Sequence[Dict[str, str]],
    changes: Sequence[Dict[str, str]],
    out_path: Path,
    threshold: int,
    change_window_days: int,
) -> None:
    if not tickets:
        raise ValueError("Ticket input is empty.")

    original_fields = list(tickets[0].keys())
    extra_fields = [
        "predicted_cluster",
        "cluster_score",
        "system_match",
        "keyword_match",
        "title_match",
        "description_match",
        "change_match",
        "region_match",
        "matched_concept_count",
        "matched_concepts",
        "related_change_id",
        "change_days_before",
        "runner_up_cluster",
        "runner_up_score",
    ]

    fieldnames = original_fields + [
        field for field in extra_fields if field not in original_fields
    ]

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for ticket in tickets:
            assigned, winner, ranked = assign_ticket(
                ticket=ticket,
                changes=changes,
                threshold=threshold,
                change_window_days=change_window_days,
            )

            runner_up = ranked[1] if len(ranked) > 1 else None

            row = dict(ticket)
            row.update(
                {
                    "predicted_cluster": assigned,
                    "cluster_score": winner.score,
                    "system_match": winner.system_match,
                    "keyword_match": winner.keyword_match,
                    "title_match": winner.title_match,
                    "description_match": winner.description_match,
                    "change_match": winner.change_match,
                    "region_match": winner.region_match,
                    "matched_concept_count": winner.matched_concept_count,
                    "matched_concepts": "|".join(winner.matched_concepts),
                    "related_change_id": winner.related_change_id,
                    "change_days_before": (
                        "" if winner.change_days_before is None
                        else winner.change_days_before
                    ),
                    "runner_up_cluster": (
                        "" if runner_up is None else runner_up.cluster
                    ),
                    "runner_up_score": (
                        "" if runner_up is None else runner_up.score
                    ),
                }
            )
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Optional evaluation against _gt_theme
# ---------------------------------------------------------------------------

def evaluate(
    rows: Sequence[Dict[str, str]],
    gt_field: str,
) -> Optional[Tuple[int, int, float]]:
    comparable = [
        row for row in rows
        if normalize(row.get(gt_field, ""))
    ]
    if not comparable:
        return None

    correct = sum(
        1
        for row in comparable
        if normalize(row.get("predicted_cluster", ""))
        == normalize(row.get(gt_field, ""))
    )
    total = len(comparable)
    return correct, total, correct / total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministically assign support tickets to incident clusters."
    )
    parser.add_argument(
        "--tickets",
        required=True,
        type=Path,
        help="Ticket CSV file.",
    )
    parser.add_argument(
        "--changes",
        type=Path,
        default=None,
        help="Optional changes CSV file.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("clustered_tickets.csv"),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=7,
        help="Minimum winning score required; otherwise singleton. Default: 7.",
    )
    parser.add_argument(
        "--change-window-days",
        type=int,
        default=7,
        help="How many days before a ticket a change can be correlated. Default: 7.",
    )
    parser.add_argument(
        "--gt-field",
        default="_gt_theme",
        help="Ground-truth column used only for optional evaluation.",
    )

    args = parser.parse_args()

    tickets = read_csv(args.tickets)
    changes = read_csv(args.changes)

    write_results(
        tickets=tickets,
        changes=changes,
        out_path=args.out,
        threshold=args.threshold,
        change_window_days=args.change_window_days,
    )

    # Re-read output so evaluation exactly reflects written predictions.
    output_rows = read_csv(args.out)

    print(f"Wrote {len(output_rows)} clustered tickets to: {args.out}")

    result = evaluate(output_rows, args.gt_field)
    if result is not None:
        correct, total, accuracy = result
        print(
            f"Evaluation against {args.gt_field}: "
            f"{correct}/{total} correct ({accuracy:.2%})"
        )


if __name__ == "__main__":
    main()