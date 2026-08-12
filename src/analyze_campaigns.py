"""Analyze synthetic campaign performance and write a Markdown report."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "synthetic_campaign_performance.csv"
REPORT_PATH = ROOT / "reports" / "sample_campaign_report.md"


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def money(value: float) -> str:
    return f"${value:,.2f}"


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def load_campaigns() -> list[dict[str, str]]:
    with DATA_PATH.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def summarize(rows: list[dict[str, str]]) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]]]:
    enriched = []
    by_channel: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "spend": 0.0,
            "impressions": 0.0,
            "clicks": 0.0,
            "leads": 0.0,
            "conversions": 0.0,
        }
    )

    for row in rows:
        spend = float(row["spend"])
        impressions = float(row["impressions"])
        clicks = float(row["clicks"])
        leads = float(row["leads"])
        conversions = float(row["conversions"])
        ctr = safe_divide(clicks, impressions)
        lead_rate = safe_divide(leads, clicks)
        conversion_rate = safe_divide(conversions, leads)
        cpl = safe_divide(spend, leads)

        enriched_row = {
            **row,
            "spend_float": spend,
            "ctr": ctr,
            "lead_rate": lead_rate,
            "conversion_rate": conversion_rate,
            "cpl": cpl,
        }
        enriched.append(enriched_row)

        channel = row["channel"]
        by_channel[channel]["spend"] += spend
        by_channel[channel]["impressions"] += impressions
        by_channel[channel]["clicks"] += clicks
        by_channel[channel]["leads"] += leads
        by_channel[channel]["conversions"] += conversions

    channel_summary = []
    for channel, totals in by_channel.items():
        channel_summary.append(
            {
                "channel": channel,
                **totals,
                "ctr": safe_divide(totals["clicks"], totals["impressions"]),
                "lead_rate": safe_divide(totals["leads"], totals["clicks"]),
                "conversion_rate": safe_divide(totals["conversions"], totals["leads"]),
                "cpl": safe_divide(totals["spend"], totals["leads"]),
            }
        )

    channel_summary.sort(key=lambda item: (item["cpl"], -item["conversions"]))
    return enriched, channel_summary


def build_report(rows: list[dict[str, str]]) -> str:
    campaigns, channels = summarize(rows)
    total_spend = sum(float(row["spend"]) for row in rows)
    total_leads = sum(float(row["leads"]) for row in rows)
    total_conversions = sum(float(row["conversions"]) for row in rows)

    best_channel = channels[0]
    highest_conversion_channel = max(channels, key=lambda item: item["conversions"])

    lines = [
        "# Sample Campaign Performance Report",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Data note: This report uses synthetic portfolio data only.",
        "",
        "## Executive Summary",
        "",
        (
            f"The synthetic portfolio covers {len(campaigns)} campaigns across {len(channels)} channels. "
            f"Total spend is {money(total_spend)}, generating {int(total_leads)} leads and "
            f"{int(total_conversions)} conversions. The lowest cost-per-lead channel is "
            f"{best_channel['channel']} at {money(best_channel['cpl'])}, while "
            f"{highest_conversion_channel['channel']} contributes the most conversions."
        ),
        "",
        "## Channel Summary",
        "",
        "| Channel | Spend | Impressions | Clicks | Leads | Conversions | CTR | CPL |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for channel in channels:
        lines.append(
            "| {channel} | {spend} | {impressions:,} | {clicks:,} | {leads:,} | {conversions:,} | {ctr} | {cpl} |".format(
                channel=channel["channel"],
                spend=money(channel["spend"]),
                impressions=int(channel["impressions"]),
                clicks=int(channel["clicks"]),
                leads=int(channel["leads"]),
                conversions=int(channel["conversions"]),
                ctr=percent(channel["ctr"]),
                cpl=money(channel["cpl"]),
            )
        )

    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            f"- Protect {best_channel['channel']} as an efficient lead source because it has the lowest cost per lead.",
            f"- Review the strongest conversion path in {highest_conversion_channel['channel']} and identify which message or audience quality is driving results.",
            "- Keep awareness campaigns separate from conversion campaigns when comparing efficiency.",
            "- Add weekly trend data before making budget-shift decisions.",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_report(load_campaigns())
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
