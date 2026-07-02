"""Report workflow cost summaries from safe offline cost records."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


def main() -> None:
    """Run the workflow cost report CLI."""

    parser = argparse.ArgumentParser(description="Report AI FitFabrica workflow cost summaries.")
    parser.add_argument("--since", help="Accepted for report compatibility; offline input is pre-filtered by caller.")
    parser.add_argument("--workflow", help="Filter records by workflow type.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--input-json", help="Path to an offline JSON export of workflow cost records.")
    args = parser.parse_args()

    records = _load_records(Path(args.input_json)) if args.input_json else []
    if args.workflow:
        records = [record for record in records if record.get("workflow_type") == args.workflow]
    report = _aggregate(records)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    print(_markdown(report))


def _load_records(path: Path) -> list[dict[str, object]]:
    """Load one offline JSON cost export."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("input JSON must be a list of workflow cost records")
    return [item for item in payload if isinstance(item, dict)]


def _aggregate(records: list[dict[str, object]]) -> dict[str, object]:
    """Aggregate workflow cost metrics from offline records."""

    total_jobs = len(records)
    successful_jobs = sum(1 for record in records if record.get("status") in {"completed", "succeeded"})
    failed_jobs = sum(1 for record in records if record.get("status") == "failed")
    provider_cost_by_agent: dict[str, Decimal] = {}
    provider_cost_by_model: dict[str, Decimal] = {}
    total_provider = Decimal("0")
    total_internal = Decimal("0")
    total_credits = Decimal("0")
    total_margin = Decimal("0")
    retry_cost_total = Decimal("0")
    repair_cost_total = Decimal("0")
    free_failed_job_cost_total = Decimal("0")

    for record in records:
        credits = _decimal(record.get("credits_charged"))
        total_credits += credits
        invocations = _invocations(record)
        record_internal = Decimal("0")
        for invocation in invocations:
            provider_cost = _decimal(invocation.get("estimated_provider_cost_usd"))
            internal_cost = _decimal(invocation.get("estimated_internal_cost_usd"))
            total_provider += provider_cost
            total_internal += internal_cost
            record_internal += internal_cost
            agent_name = str(invocation.get("agent_name") or "unknown")
            model = str(invocation.get("model") or "unknown")
            provider_cost_by_agent[agent_name] = provider_cost_by_agent.get(agent_name, Decimal("0")) + provider_cost
            provider_cost_by_model[model] = provider_cost_by_model.get(model, Decimal("0")) + provider_cost
            if invocation.get("retry_reason"):
                retry_cost_total += internal_cost
            if invocation.get("repair_reason"):
                repair_cost_total += internal_cost
        revenue = credits * Decimal("0.10")
        total_margin += revenue - record_internal
        if record.get("status") == "failed" and credits == 0:
            free_failed_job_cost_total += record_internal

    most_expensive_agent = _max_key(provider_cost_by_agent)
    return {
        "total_jobs": total_jobs,
        "successful_jobs": successful_jobs,
        "failed_jobs": failed_jobs,
        "avg_cost_usd": _decimal_string(_average(total_internal, total_jobs)),
        "avg_cost_kzt": _decimal_string(_average(total_internal * Decimal("500"), total_jobs)),
        "avg_credits_charged": _decimal_string(_average(total_credits, total_jobs)),
        "avg_margin": _decimal_string(_average(total_margin, total_jobs)),
        "most_expensive_agent": most_expensive_agent,
        "retry_cost_total": _decimal_string(retry_cost_total),
        "repair_cost_total": _decimal_string(repair_cost_total),
        "free_failed_job_cost_total": _decimal_string(free_failed_job_cost_total),
        "provider_cost_by_agent": _string_map(provider_cost_by_agent),
        "provider_cost_by_model": _string_map(provider_cost_by_model),
        "direct_provider_cost_total": _decimal_string(total_provider),
        "internal_cost_total": _decimal_string(total_internal),
    }


def _invocations(record: dict[str, object]) -> list[dict[str, object]]:
    """Return safe invocation dictionaries from one record."""

    value = record.get("agent_invocations")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _markdown(report: dict[str, object]) -> str:
    """Return a compact Markdown report."""

    lines = ["# Workflow Cost Report", "", "| metric | value |", "| --- | --- |"]
    for key, value in report.items():
        if isinstance(value, dict):
            lines.append(f"| {key} | `{json.dumps(value, ensure_ascii=False)}` |")
        else:
            lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _decimal(value: object) -> Decimal:
    """Convert report values to Decimal safely."""

    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str) and value:
        return Decimal(value)
    return Decimal("0")


def _average(total: Decimal, count: int) -> Decimal:
    """Return average for report metrics."""

    if count <= 0:
        return Decimal("0")
    return total / Decimal(count)


def _decimal_string(value: Decimal) -> str:
    """Format Decimal for stable JSON and Markdown output."""

    return f"{value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP):.6f}"


def _string_map(values: dict[str, Decimal]) -> dict[str, str]:
    """Return JSON-safe decimal map."""

    return {key: _decimal_string(value) for key, value in sorted(values.items())}


def _max_key(values: dict[str, Decimal]) -> str | None:
    """Return key with the highest Decimal value."""

    if not values:
        return None
    return max(values.items(), key=lambda item: item[1])[0]


if __name__ == "__main__":
    main()
