"""Synthetic ticket and change generation for the UBS challenge.

This script produces the operational dataset described in docs/LANE_B_DATA.md and the
contract in docs/SCHEMA.md. It is deterministic so the demo remains reproducible.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

END = datetime(2026, 9, 22, tzinfo=timezone.utc)
START = END - timedelta(days=90)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

REGIONS = ["CH", "EMEA", "APAC", "AMER"]
SYSTEMS = [
    "eBanking",
    "MobileApp",
    "FX-Trading",
    "Payments",
    "CardServices",
    "Onboarding",
    "Reporting",
]
BUSINESS_LINES = ["Retail", "Wealth", "InvestmentBank", "Operations"]
CHANNELS = ["phone", "email", "chat", "monitoring", "branch"]
ROLES = ["client", "client_advisor", "internal_ops", "monitoring_bot"]
STATUSES = ["open", "in_progress", "resolved", "closed"]

_counter = 0


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def next_ticket_id() -> str:
    global _counter
    _counter += 1
    return f"INC-{_counter:07d}"


def business_hours_in_utc(day: datetime, region: str) -> datetime:
    local_offset = {"CH": 2, "EMEA": 2, "APAC": 8, "AMER": -5}[region]
    local_hour = random.choices(
        population=list(range(6, 21)),
        weights=[1, 3, 6, 9, 10, 9, 7, 8, 9, 8, 6, 4, 3, 2, 1],
    )[0]
    return day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        hours=local_hour - local_offset,
        minutes=random.randint(0, 59),
    )


def weighted_choice(choices: dict[str, float]) -> str:
    return random.choices(list(choices.keys()), weights=list(choices.values()), k=1)[0]


def build_changes() -> list[dict]:
    changes: list[dict] = []

    guilty = [
        {
            "change_id": "CHG-0042",
            "deployed_at": "2026-09-14T22:00:00Z",
            "system": "MobileApp",
            "title": "Mobile App 4.2.0 — migrate to new auth SDK",
            "type": "release",
            "regions": ["CH", "EMEA", "APAC", "AMER"],
            "owner_team": "Digital Channels",
            "rollback_at": None,
        },
        {
            "change_id": "CHG-0091",
            "deployed_at": "2026-09-09T19:30:00Z",
            "system": "FX-Trading",
            "title": "FX Trading — vendor feed config refresh for APAC desk",
            "type": "vendor",
            "regions": ["APAC"],
            "owner_team": "Market Data Platform",
            "rollback_at": "2026-09-11T14:10:00Z",
        },
        {
            "change_id": "CHG-0103",
            "deployed_at": "2026-09-12T04:00:00Z",
            "system": "Payments",
            "title": "Payments — upgrade beneficiary validation library to v3.1",
            "type": "vendor",
            "regions": ["CH", "EMEA"],
            "owner_team": "Payments Engineering",
            "rollback_at": None,
        },
    ]

    decoy_specs = [
        {"title": "eBanking — dependency patch for account summary widgets", "system": "eBanking", "type": "release", "regions": ["EMEA"], "deployed_at": "2026-07-02T06:10:00Z"},
        {"title": "CardServices — issuer batch refresh for travel alerts", "system": "CardServices", "type": "config", "regions": ["CH"], "deployed_at": "2026-07-12T12:20:00Z"},
        {"title": "Onboarding — resume upload storage tuning", "system": "Onboarding", "type": "infra", "regions": ["EMEA"], "deployed_at": "2026-07-18T09:00:00Z"},
        {"title": "Reporting — month-end job prioritisation", "system": "Reporting", "type": "vendor", "regions": ["AMER"], "deployed_at": "2026-07-23T14:15:00Z"},
        {"title": "Payments — increase SEPA batch window", "system": "Payments", "type": "certificate", "regions": ["CH"], "deployed_at": "2026-07-28T16:00:00Z"},
        {"title": "eBanking — failover test, Zurich DC", "system": "eBanking", "type": "release", "regions": ["APAC"], "deployed_at": "2026-08-04T05:00:00Z"},
        {"title": "MobileApp — push notification telemetry clean-up", "system": "MobileApp", "type": "config", "regions": ["EMEA"], "deployed_at": "2026-08-08T13:40:00Z"},
        {"title": "eBanking — quarterly dependency patch", "system": "eBanking", "type": "release", "regions": ["CH"], "deployed_at": "2026-08-13T11:20:00Z"},
        {"title": "CardServices — fraud rule update for geolocation", "system": "CardServices", "type": "config", "regions": ["AMER"], "deployed_at": "2026-08-17T18:00:00Z"},
        {"title": "Onboarding — document OCR confidence tuning", "system": "Onboarding", "type": "release", "regions": ["EMEA"], "deployed_at": "2026-08-23T08:30:00Z"},
        {"title": "Reporting — report cache invalidation hotfix", "system": "Reporting", "type": "infra", "regions": ["CH"], "deployed_at": "2026-08-29T14:10:00Z"},
        {"title": "Payments — ACH routing rule adjustment", "system": "Payments", "type": "config", "regions": ["EMEA"], "deployed_at": "2026-09-01T09:40:00Z"},
        {"title": "FX-Trading — APAC market calendar update", "system": "FX-Trading", "type": "vendor", "regions": ["APAC"], "deployed_at": "2026-09-04T21:00:00Z"},
        {"title": "eBanking — certificate rotation on edge gateways", "system": "eBanking", "type": "release", "regions": ["EMEA"], "deployed_at": "2026-09-05T04:00:00Z"},
        {"title": "MobileApp — app startup instrumentation", "system": "MobileApp", "type": "config", "regions": ["CH"], "deployed_at": "2026-09-08T12:00:00Z"},
        {"title": "Reporting — performance tuning for month-end jobs", "system": "Reporting", "type": "release", "regions": ["AMER"], "deployed_at": "2026-09-10T17:40:00Z"},
        {"title": "eBanking — session timeout recalibration", "system": "eBanking", "type": "config", "regions": ["CH"], "deployed_at": "2026-09-13T06:20:00Z"},
        {"title": "CardServices — travel risk scoring patch", "system": "CardServices", "type": "release", "regions": ["EMEA"], "deployed_at": "2026-09-15T07:30:00Z"},
        {"title": "Onboarding — legal entity validation library bump", "system": "Onboarding", "type": "infra", "regions": ["AMER"], "deployed_at": "2026-09-16T20:00:00Z"},
        {"title": "Payments — limit query cache expiry adjustment", "system": "Payments", "type": "config", "regions": ["EMEA"], "deployed_at": "2026-09-18T04:30:00Z"},
        {"title": "FX-Trading — counterparty status service change", "system": "FX-Trading", "type": "vendor", "regions": ["APAC"], "deployed_at": "2026-09-19T10:10:00Z"},
        {"title": "eBanking — storage failover drill, Singapore", "system": "eBanking", "type": "release", "regions": ["APAC"], "deployed_at": "2026-09-19T22:30:00Z"},
        {"title": "CardServices — device health telemetry add-on", "system": "CardServices", "type": "config", "regions": ["EMEA"], "deployed_at": "2026-09-20T12:00:00Z"},
        {"title": "Onboarding — auth cookie TTL adjustment", "system": "Onboarding", "type": "release", "regions": ["CH"], "deployed_at": "2026-09-21T08:00:00Z"},
        {"title": "Reporting — EMV fallback config refresh", "system": "Reporting", "type": "config", "regions": ["AMER"], "deployed_at": "2026-09-21T14:40:00Z"},
        {"title": "Payments — OTP resend text copy update", "system": "Payments", "type": "release", "regions": ["EMEA"], "deployed_at": "2026-08-15T16:00:00Z"},
        {"title": "FX-Trading — data retention cleanup", "system": "FX-Trading", "type": "infra", "regions": ["APAC"], "deployed_at": "2026-08-20T06:30:00Z"},
        {"title": "eBanking — domestic payment routing patch", "system": "eBanking", "type": "config", "regions": ["CH"], "deployed_at": "2026-08-26T09:00:00Z"},
        {"title": "CardServices — rate source health check change", "system": "CardServices", "type": "vendor", "regions": ["EMEA"], "deployed_at": "2026-07-09T07:55:00Z"},
        {"title": "Onboarding — network policy update for APAC", "system": "Onboarding", "type": "release", "regions": ["APAC"], "deployed_at": "2026-07-15T18:25:00Z"},
        {"title": "Reporting — queue management update", "system": "Reporting", "type": "config", "regions": ["CH"], "deployed_at": "2026-07-22T04:50:00Z"},
        {"title": "Payments — address validation configuration", "system": "Payments", "type": "release", "regions": ["EMEA"], "deployed_at": "2026-07-30T09:00:00Z"},
        {"title": "FX-Trading — benefit name lookup patch", "system": "FX-Trading", "type": "vendor", "regions": ["APAC"], "deployed_at": "2026-08-05T13:10:00Z"},
        {"title": "eBanking — market data checksum validation", "system": "eBanking", "type": "release", "regions": ["EMEA"], "deployed_at": "2026-08-12T07:00:00Z"},
        {"title": "CardServices — ad-hoc export timeout tweak", "system": "CardServices", "type": "config", "regions": ["AMER"], "deployed_at": "2026-08-18T09:20:00Z"},
        {"title": "Onboarding — beneficiary name lookup patch", "system": "Onboarding", "type": "release", "regions": ["EMEA"], "deployed_at": "2026-08-28T11:30:00Z"},
        {"title": "Reporting — market data checksum validation", "system": "Reporting", "type": "config", "regions": ["CH"], "deployed_at": "2026-09-06T05:15:00Z"},
    ]

    for idx, spec in enumerate(decoy_specs, start=1):
        changes.append(
            {
                "change_id": f"CHG-{1000 + idx}",
                "deployed_at": spec["deployed_at"],
                "system": spec["system"],
                "title": spec["title"],
                "type": spec["type"],
                "regions": spec["regions"],
                "owner_team": random.choice([
                    "Digital Channels",
                    "Payments Engineering",
                    "Market Data Platform",
                    "Core Banking Ops",
                    "Infrastructure",
                    "Client Access Platform",
                ]),
                "rollback_at": random.choice([None, None, "2026-07-03T09:10:00Z"]),
            }
        )

    changes.extend(guilty)
    changes = sorted(changes, key=lambda item: item["deployed_at"])
    return changes


def make_ticket(theme: str, *, system: str, region: str, business_line: str, created_at: str,
               severity: int, channel: str, reporter_role: str, title: str,
               description: str, status: str, resolution_notes: str | None,
               linked_change_id: str | None) -> dict:
    return {
        "ticket_id": next_ticket_id(),
        "created_at": created_at,
        "channel": channel,
        "region": region,
        "business_line": business_line,
        "system": system,
        "title": title,
        "description": description,
        "reporter_role": reporter_role,
        "severity_reported": severity,
        "status": status,
        "resolution_notes": resolution_notes,
        "linked_change_id": linked_change_id,
        "_gt_theme": theme,
    }


def build_s1_tickets() -> list[dict]:
    theme = "mobile_login_failure_v42"
    tickets: list[dict] = []
    day_volumes = {
        "2026-09-14": 3,
        "2026-09-15": 48,
        "2026-09-16": 62,
        "2026-09-17": 54,
        "2026-09-18": 38,
        "2026-09-19": 26,
        "2026-09-20": 12,
        "2026-09-21": 9,
        "2026-09-22": 6,
    }

    templates = [
        "Cannot log in to mobile app after update",
        "Access Denied after entering PIN on the app",
        "Biometric login stopped working after 4.2.0",
        "2FA code not accepted on the new mobile app",
        "App crashes on the login screen after update",
        "Session expired immediately after PIN entry",
        "Client cannot log in on iPhone after update",
        "Login screen spins after app update",
        "Face ID no longer offered in the app",
        "Mobile app rejects valid credentials after update",
    ]

    descriptions = [
        "Client called: since updating the app yesterday evening she gets 'Access Denied' after entering her PIN. Biometric login also fails. Tried reinstalling, no change.",
        "2FA push never arrives on the new app version. Client has been locked out since this morning and needs to approve a payment today.",
        "App just spins after PIN entry; this was fine before the update. The client is using an iPhone 15 with iOS 18.4.",
        "Advisor reports several clients in the last two days are unable to log in to the app. Works on the website but not in the mobile app.",
        "Client says the app shows a session expired message immediately after entering the PIN. Face ID is no longer offered on the device.",
        "Client has been unable to access the app since the mobile update. Reinstalling and clearing cache did not fix the issue.",
        "Login fails repeatedly for a Wealth client on a corporate device. Same credentials work on the website but not in the new app version.",
        "Advisor notes that multiple retail clients are receiving a login error after the app update. They can authenticate on eBanking but not on MobileApp.",
        "Client cannot access account after the latest app version. The app crashes on the login screen and biometric login has stopped working.",
        "The app says the PIN is invalid despite it being correct. This started on the day after the update and affects both login and biometrics.",
    ]

    for day_key, count in day_volumes.items():
        day = datetime.strptime(day_key, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        for _ in range(count):
            region = weighted_choice({"CH": 35, "EMEA": 30, "APAC": 20, "AMER": 15})
            system = random.choices(["MobileApp", "eBanking"], weights=[82, 18], k=1)[0]
            business_line = weighted_choice({"Retail": 72, "Wealth": 28})
            severity = random.choices([3, 4], weights=[80, 20], k=1)[0]
            channel = random.choices(["phone", "chat"], weights=[60, 40], k=1)[0]
            reporter_role = random.choices(["client", "client_advisor"], weights=[55, 45], k=1)[0]
            created_at = iso(business_hours_in_utc(day, region))
            title = random.choice(templates)
            description = random.choice(descriptions)
            status = random.choices(["resolved", "closed", "open", "in_progress"], weights=[30, 30, 30, 10], k=1)[0]
            resolution_notes = None if status in {"open", "in_progress"} else "Client re-logged after clear credentials and device restart. No further issues."
            linked = "CHG-0042" if random.random() < 0.12 else None
            tickets.append(
                make_ticket(
                    theme,
                    system=system,
                    region=region,
                    business_line=business_line,
                    created_at=created_at,
                    severity=severity,
                    channel=channel,
                    reporter_role=reporter_role,
                    title=title,
                    description=description,
                    status=status,
                    resolution_notes=resolution_notes,
                    linked_change_id=linked,
                )
            )

    # Precisely enforce the 12% linkage pattern and keep the bucket plausible.
    linked_count = 0
    for ticket in tickets:
        if ticket["linked_change_id"] == "CHG-0042":
            linked_count += 1
    while linked_count < 31:
        candidate = random.choice(tickets)
        if candidate["linked_change_id"] is None:
            candidate["linked_change_id"] = "CHG-0042"
            linked_count += 1
    while linked_count > 31:
        candidate = random.choice([t for t in tickets if t["linked_change_id"] == "CHG-0042"])
        candidate["linked_change_id"] = None
        linked_count -= 1

    return tickets


def build_s2_tickets() -> list[dict]:
    theme = "apac_fx_settlement_recurrence"
    episodes = [
        ("2026-07-06", "2026-07-08", 14),
        ("2026-08-08", "2026-08-10", 14),
        ("2026-09-10", "2026-09-12", 14),
    ]
    tickets: list[dict] = []
    common_title_starts = [
        "FX settlement mismatch on APAC book",
        "Trade booked with stale APAC rate",
        "JPY/USD mismatch at APAC settlement",
        "Counterparty confirmation missing for FX trade",
        "APAC rate feed timestamp behind by 40 minutes",
        "Settlement queue shows FX discrepancy",
    ]
    common_descriptions = [
        "Monitoring flagged a mismatch between the book and counterparty confirmation for the APAC trade queue. The trade was re-booked after a manual refresh of the rate feed.",
        "Manual re-sync of the APAC rate feed was required after a stale rate was used for settlement. Same issue repeated on the same desk this morning.",
        "The FX desk reported a settlement discrepancy in the JPY/USD position. The rate feed was behind and the trade had to be re-booked by ops.",
        "We are seeing repeated settlement mismatch tickets in APAC. The quoted rate is out of sync with the latest vendor feed and the trade requires manual intervention.",
        "Rate mismatch at APAC close caused a settlement discrepancy. Counterparty confirmation waited for a manual vendor re-sync before the trade could close.",
    ]

    for start_str, end_str, count in episodes:
        start = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(end_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        for _ in range(count):
            day = start + timedelta(days=random.randint(0, (end - start).days))
            created = iso(business_hours_in_utc(day, "APAC"))
            title = random.choice(common_title_starts)
            description = random.choice(common_descriptions)
            status = random.choices(["resolved", "closed"], weights=[40, 60], k=1)[0]
            resolution_notes = random.choice([
                "Rates re-synced manually from the vendor feed and affected trades re-booked. Monitoring.",
                "Manual re-sync of APAC rate feed, 6 trades re-booked. Closed.",
                "Vendor feed refreshed and APAC desk re-booked impacted trades. Closed.",
            ])
            linked = "CHG-0091" if (start_str == "2026-09-10") and random.random() < 0.5 else None
            tickets.append(
                make_ticket(
                    theme,
                    system="FX-Trading",
                    region="APAC",
                    business_line="InvestmentBank",
                    created_at=created,
                    severity=4,
                    channel=random.choices(["monitoring", "email"], weights=[55, 45], k=1)[0],
                    reporter_role=random.choices(["internal_ops", "monitoring_bot"], weights=[65, 35], k=1)[0],
                    title=title,
                    description=description,
                    status=status,
                    resolution_notes=resolution_notes,
                    linked_change_id=linked,
                )
            )
    return tickets


def build_s3_tickets() -> list[dict]:
    theme = "iban_validation_vendor_regression"
    tickets: list[dict] = []
    sentences = [
        "Client cannot add a new beneficiary in Austria, the form says the account number is invalid. It matches the client statement exactly.",
        "Payment to AT61 1904 3002 3457 3201 was rejected at entry with a 'format not recognised' message. Same payee worked in July.",
        "Advisor reported two Wealth clients this week unable to set up standing orders to Austrian banks.",
        "Validation error on beneficiary create, payload rejected upstream with VAL_IBAN_MALFORMED.",
        "Transfer to Vienna account keeps bouncing back at the input screen. The client is frustrated and has tried three times.",
        "Cannot pay my Austrian supplier because the website says the IBAN is wrong even though the bank confirmed the account number.",
        "Austrian beneficiary set-up fails repeatedly even though the IBAN is valid. The same supplier was paid last quarter without issue.",
        "Client account number for a Vienna supplier is rejected as malformed even though the account format is standard for Austria.",
        "Payment screen fails when entering the Austrian bank account, and the client is unable to complete a standing order.",
        "Beneficiary validation error on a Swiss client sending to an Austrian account. The same account was accepted before the vendor update.",
        "The system says the Austrian account is malformed during validation, but the details match the client's bank statement.",
    ]

    for idx in range(11):
        day = datetime(2026, 9, 13) + timedelta(days=idx)
        created_at = iso(business_hours_in_utc(day, random.choice(["CH", "EMEA"])))
        region = random.choice(["CH", "EMEA"])
        title = random.choice([
            "Austrian IBAN rejected by validation",
            "Beneficiary account rejected as malformed",
            "Client payment to Vienna bank account fails",
            "AT account validation error on payment form",
            "Austrian supplier bank details rejected",
            "IBAN rejected during standing order setup",
            "Payment validation rejects valid Austrian account",
            "Beneficiary create fails for AT account",
            "Bank account rejected despite matching statement",
            "Validation fails for Austrian payment beneficiary",
            "AT account rejected in Payments portal",
        ])
        tickets.append(
            make_ticket(
                theme,
                system="Payments",
                region=region,
                business_line=random.choice(["Retail", "Wealth"]),
                created_at=created_at,
                severity=random.choice([2, 3]),
                channel=random.choice(["phone", "email", "chat"]),
                reporter_role=random.choice(["client", "client_advisor", "internal_ops"]),
                title=title,
                description=sentences[idx],
                status=random.choices(["open", "resolved", "closed"], weights=[50, 25, 25], k=1)[0],
                resolution_notes=None if random.random() < 0.5 else "Vendor library update suspected; customer rechecked account information and case routed to product team.",
                linked_change_id=None,
            )
        )
    return tickets


def build_background_tickets() -> list[dict]:
    specs = {
        "password_reset": {"count": 230, "system": "eBanking", "region_weights": {"CH": 30, "EMEA": 35, "APAC": 20, "AMER": 15}, "business_line": "Retail", "status_weights": ["resolved", "closed", "open", "in_progress"], "titles": [
            "Password reset link expired",
            "Reset email not received",
            "Account locked after 3 failed attempts",
            "Forgotten password request not working",
            "Client locked out after reset attempt",
            "Password reset page errors",
        ], "descriptions": [
            "Client cannot complete the reset flow because the link expires before they open it. They were locked out after multiple attempts.",
            "Reset email does not arrive for a retail client even though their account is active. They are unable to unlock access.",
            "Client says the account locks after three failed attempts and the reset flow loops back to the login page without sending a code.",
            "Advisor reports repeated reset failures for a corporate user after password expiry. The link opens but immediately says it has expired.",
            "Client reset their password but still receives a locked account state when trying to log in. Requesting help from support.",
        ], "_gt_theme": "password_reset"},
        "statement_download": {"count": 150, "system": "eBanking", "region_weights": {"CH": 35, "EMEA": 35, "APAC": 15, "AMER": 15}, "business_line": "Retail", "status_weights": ["resolved", "closed", "open"], "titles": [
            "Statement download fails",
            "PDF statements not loading",
            "Client cannot open PDF from statement page",
            "Monthly statement unavailable",
            "The statement downloads but won't open",
            "Statement export fails after login",
        ], "descriptions": [
            "Client is unable to download the monthly statement from the secure portal. The page loads but the PDF request fails.",
            "Advisor says statements are not available for a set of clients in the last few days. Download fails on the second attempt.",
            "The portal shows the statement as available but the browser rejects the file when opened. Reproducible on desktop and mobile.",
            "Client cannot access a PDF version of their statement and reports the browser says the document is corrupted.",
            "Statement export keeps timing out and the file never downloads despite a stable Internet connection.",
        ], "_gt_theme": "statement_download"},
        "card_blocked_abroad": {"count": 140, "system": "CardServices", "region_weights": {"CH": 25, "EMEA": 30, "APAC": 20, "AMER": 25}, "business_line": "Retail", "status_weights": ["resolved", "closed", "open"], "titles": [
            "Card blocked while travelling",
            "Travel card blocked unexpectedly",
            "Card declined abroad despite no fraud alert",
            "Client card blocked during trip",
            "Travel abroad blocked after location alert",
            "Card disabled on holiday",
        ], "descriptions": [
            "Client travelling in Spain reported their card was blocked on the first day of travel despite no fraud alert or unusual activity.",
            "Card was declined in Singapore while the client was abroad. The client says they were not notified of any suspicious activity.",
            "Card blocked while travelling. Client was able to complete a call to the service desk and the block was removed after verification.",
            "The card failed multiple times while abroad and the client had to contact support to unblock it.",
            "Client abroad reports that the card is blocked after a routine transaction and needs a temporary unblock for travel.",
        ], "_gt_theme": "card_blocked_abroad"},
        "reporting_slow_month_end": {"count": 120, "system": "Reporting", "region_weights": {"CH": 35, "EMEA": 30, "APAC": 20, "AMER": 15}, "business_line": "Operations", "status_weights": ["resolved", "closed", "open"], "titles": [
            "Month-end reporting latency",
            "Reporting job takes too long",
            "Monthly report generation slow",
            "Month-end report still running",
            "Slow export at month-end",
            "Reporting queue delay",
        ], "descriptions": [
            "Operations team reports a delay in generating month-end portfolio reports. The job remains queued longer than expected.",
            "The reporting stack is slow at month-end and the export takes several hours to complete. This is affecting downstream control checks.",
            "Management report generation is delayed over the month-end period with repeated timeouts and queue backlog.",
            "Reporting tasks are slower than normal in the last few days of the month, causing internal delays for team sign-off.",
            "Users are waiting long periods for reports to generate around the month-end close. This appears to be recurring but not critical.",
        ], "_gt_theme": "reporting_slow_month_end"},
        "onboarding_upload": {"count": 110, "system": "Onboarding", "region_weights": {"CH": 35, "EMEA": 30, "APAC": 20, "AMER": 15}, "business_line": "Retail", "status_weights": ["resolved", "closed", "open"], "titles": [
            "Document upload rejected",
            "ID upload error on onboarding",
            "Passport upload not accepted",
            "Onboarding file rejected",
            "Document validation failed during onboarding",
            "Client cannot upload proof of ID",
        ], "descriptions": [
            "Client was unable to upload a passport scan during onboarding. The portal says the document could not be processed.",
            "The onboarding workflow rejected an uploaded document even though the file was in the required format and size.",
            "Advisor says the system rejects client documents during onboarding and asks that the case be escalated for manual review.",
            "The upload process fails after the document is selected and the portal returns a generic validation message.",
            "Client document upload receives a rejection error on the onboarding form even when the file is readable and valid.",
        ], "_gt_theme": "onboarding_upload"},
        "payment_limits": {"count": 130, "system": "Payments", "region_weights": {"CH": 30, "EMEA": 35, "APAC": 20, "AMER": 15}, "business_line": "Retail", "status_weights": ["resolved", "closed", "open"], "titles": [
            "Beneficiary limit query fails",
            "Payment limit check returns wrong value",
            "Client cannot access payment limits",
            "Limit query is inaccurate for transfer",
            "Payment limits lookup fails",
            "Beneficiary limit service returns an error",
        ], "descriptions": [
            "Client cannot retrieve current transfer limits when preparing a payment. The system returns an error instead of the usual limit information.",
            "Payment screen is failing to load beneficiary limit information for an active client profile and the request times out.",
            "We are seeing repeated payment limit lookup failures in the session builder. Customer cannot proceed to authorisation.",
            "The limit service returns a generic error. Client is unable to see the beneficiary maximum for a domestic payment.",
            "Beneficiary limit query went wrong for a high-value transfer and the client had to call support to get the details.",
        ], "_gt_theme": "payment_limits"},
        "branch_hardware": {"count": 95, "system": "eBanking", "region_weights": {"CH": 35, "EMEA": 30, "APAC": 20, "AMER": 15}, "business_line": "Operations", "status_weights": ["resolved", "closed", "open"], "titles": [
            "Branch printer not working",
            "Device issue at branch counter",
            "Branch system printer offline",
            "Client device not connecting in branch",
            "Printer queue jam at branch office",
            "Branch access device issue",
        ], "descriptions": [
            "Branch reported that the printer was offline and could not process client statements. There was no obvious underlying issue with account access.",
            "The branch office reported that a counter device was not connecting to the workstation and manual processing was required.",
            "The printer queue at one branch is failing to complete print jobs, preventing statement delivery to customers.",
            "Branch hardware issue reported by internal operations: client device would not connect and staff had to use the fallback terminal.",
            "Branch staff came in to find a device issue and had to switch to manual documentation while the kiosk was out of service.",
        ], "_gt_theme": "branch_hardware"},
    }

    tickets: list[dict] = []
    for theme_name, cfg in specs.items():
        for _ in range(cfg["count"]):
            region = weighted_choice(cfg["region_weights"])
            system = cfg["system"]
            business_line = cfg["business_line"]
            created_at = iso(business_hours_in_utc(START + timedelta(days=random.randint(0, 89)), region))
            severity = random.randint(1, 4)
            channel = random.choice(["phone", "email", "chat", "branch"])
            reporter_role = random.choice(["client", "client_advisor", "internal_ops", "monitoring_bot"])
            title = random.choice(cfg["titles"])
            description = random.choice(cfg["descriptions"])
            weights = {"resolved": 40, "closed": 25, "open": 25, "in_progress": 10}
            if len(cfg["status_weights"]) == 3:
                weights = {"resolved": 40, "closed": 30, "open": 30}
            status = random.choices(
                cfg["status_weights"],
                weights=[weights[item] for item in cfg["status_weights"]],
                k=1,
            )[0]
            resolution_notes = None if status in {"open", "in_progress"} else "Performed standard resolution workflow; issue cleared and client notified."
            tickets.append(
                make_ticket(
                    cfg["_gt_theme"],
                    system=system,
                    region=region,
                    business_line=business_line,
                    created_at=created_at,
                    severity=severity,
                    channel=channel,
                    reporter_role=reporter_role,
                    title=title,
                    description=description,
                    status=status,
                    resolution_notes=resolution_notes,
                    linked_change_id=None,
                )
            )
    return tickets


def build_singletons() -> list[dict]:
    singleton_titles = [
        "ATM ate client card",
        "Duplicate complaint on closed account",
        "Credit fee dispute raised by client",
        "Account closure request submitted twice",
        "Currency conversion confusion on old transfer",
        "Request to update mailing address",
        "Test ticket filed by mistake",
        "New card replacement requested after loss",
        "Client asks for annual statement archive",
        "Call about foreign transaction fee question",
    ]
    singleton_descriptions = [
        "Client called to ask why a duplicate fee was charged on an overseas transaction. No evidence of a technical issue.",
        "The account was already closed and the client is confused about the duplicate complaint on file. No operational incident discovered.",
        "The customer would like an explanation for a fee applied to a transfer. The issue is resolved via customer support.",
        "The account closure request was accidentally filed twice. There is no production defect and no further action needed.",
        "The client wants clarification on why a conversion rate differed from the original estimate. This does not appear to be a platform issue.",
        "Address update request from a retail customer. No technical issue or operational disruption recorded.",
        "This appears to be a manual QA test ticket that was filed accidentally and should not be treated as an incident.",
        "Card replacement requested after a lost card. Customer service handled it without a platform error.",
        "Client requested an archived statement for a historical account. The request is valid and unrelated to current releases.",
        "Customer asked a general question about foreign transaction fees after a trip. This is a one-off support question.",
    ]
    tickets: list[dict] = []
    for _ in range(115):
        region = random.choice(REGIONS)
        system = random.choice(SYSTEMS)
        business_line = random.choice(BUSINESS_LINES)
        status = random.choice(["open", "resolved", "closed"])
        created_at = iso(business_hours_in_utc(START + timedelta(days=random.randint(0, 89)), region))
        tickets.append(
            make_ticket(
                "singleton",
                system=system,
                region=region,
                business_line=business_line,
                created_at=created_at,
                severity=random.randint(1, 3),
                channel=random.choice(CHANNELS),
                reporter_role=random.choice(ROLES),
                title=random.choice(singleton_titles),
                description=random.choice(singleton_descriptions),
                status=status,
                resolution_notes=None if status == "open" else "Reviewed and closed as a non-incident customer support case.",
                linked_change_id=None,
            )
        )
    return tickets


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tickets = []
    tickets.extend(build_s1_tickets())
    tickets.extend(build_s2_tickets())
    tickets.extend(build_s3_tickets())
    tickets.extend(build_background_tickets())
    tickets.extend(build_singletons())

    # Rebalance to a clean total of ~1400 entries and keep the ordering deterministic.
    # The deterministic generator above already produces about 1,401 tickets.
    random.shuffle(tickets)
    with (DATA_DIR / "tickets.json").open("w", encoding="utf-8") as fh:
        json.dump(tickets, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    changes = build_changes()
    with (DATA_DIR / "changes.json").open("w", encoding="utf-8") as fh:
        json.dump(changes, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # Small summary for quick verification when the script is run.
    counts = {}
    for ticket in tickets:
        counts[ticket["_gt_theme"]] = counts.get(ticket["_gt_theme"], 0) + 1
    print(f"Generated {len(tickets)} tickets across {len(counts)} themes.")
    print({key: counts[key] for key in sorted(counts)})
    print(f"Generated {len(changes)} change records.")


if __name__ == "__main__":
    main()
