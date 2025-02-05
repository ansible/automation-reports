import os
from datetime import datetime
from decimal import Decimal

import pytz
from django.core.cache import cache
from django.db.models import Count, Sum, F, CharField, Func, Value

from backend.apps.clusters.models import Costs, CostsChoices


def get_costs():
    costs = cache.get('costs')
    set_cache = False

    if not costs:
        costs = {cost.type: cost for cost in list(Costs.objects.all())}
        cache.set('costs', costs, 3600)

    manual_cost = costs.get(CostsChoices.MANUAL, None)

    if manual_cost is None:
        set_cache = True
        default_value = Decimal(os.environ.get("DEFAULT_MANUAL_COST_AUTOMATION", "50"))
        Costs.objects.create(
            type=CostsChoices.MANUAL,
            value=default_value,
        )

    automated_cost = costs.get(CostsChoices.AUTOMATED, None)

    if automated_cost is None:
        default_value = Decimal(os.environ.get("DEFAULT_AUTOMATED_PROCESS_COST", "20"))
        Costs.objects.create(
            type=CostsChoices.AUTOMATED,
            value=default_value,
        )
        set_cache = True

    if set_cache:
        costs = {cost.type: cost for cost in list(Costs.objects.all())}
        cache.set('costs', costs, 3600)

    return costs


def get_diff_index(old_value, new_value):
    if old_value is None or new_value is None:
        return None
    if old_value == new_value:
        return 0
    if old_value == 0:
        return 100
    return round(((new_value - old_value) / old_value) * 100)


def sum_items(items):
    result = {
        "successful_count": 0,
        "failed_count": 0,
        "total_elapsed_hours": 0,
        "total_runs": 0,
        "automated_costs": 0,
        "manual_costs": 0,
        "savings": 0
    }
    for item in items:
        result["successful_count"] += item["successful_runs"]
        result["failed_count"] += item["failed_runs"]
        result["total_elapsed_hours"] += item["elapsed"]
        result["total_runs"] += item["runs"]
        result["automated_costs"] += item["automated_costs"]
        result["manual_costs"] += item["manual_costs"]
        result["savings"] += item["savings"]

    result["total_elapsed_hours"] = round(result["total_elapsed_hours"], 2)
    result["automated_costs"] = round(result["automated_costs"], 2)
    result["manual_costs"] = round(result["manual_costs"], 2)
    result["savings"] = round(result["savings"], 2)
    return result


def get_report_data(items, prev_items):
    res = sum_items(items)
    prev_res = sum_items(prev_items)

    successful_count = res["successful_count"]
    failed_count = res["failed_count"]
    total_elapsed_hours = res["total_elapsed_hours"]
    total_runs = res["total_runs"]
    automated_costs = res["automated_costs"]
    manual_costs = res["manual_costs"]
    savings = res["savings"]

    prev_len = len(prev_items)

    return {
        "total_number_of_successful_jobs": {
            "value": successful_count,
            "index": get_diff_index(prev_res["total_elapsed_hours"] if prev_len > 0 else None, total_elapsed_hours),
        },
        "total_number_of_failed_jobs": {
            "value": failed_count,
            "index": get_diff_index(prev_res["failed_count"] if prev_len > 0 else None, failed_count),
        },
        "total_number_of_job_runs": {
            "value": total_runs,
            "index": get_diff_index(prev_res["total_runs"] if prev_len > 0 else None, total_runs),
        },
        "total_hours_of_automation": {
            "value": total_elapsed_hours,
            "index": get_diff_index(prev_res["total_elapsed_hours"] if prev_len > 0 else None, total_elapsed_hours),
        },
        "cost_of_automated_execution": {
            "value": automated_costs,
            "index": get_diff_index(prev_res["automated_costs"] if prev_len > 0 else None, automated_costs),
        },
        "cost_of_manual_automation": {
            "value": manual_costs,
            "index": get_diff_index(prev_res["manual_costs"] if prev_len > 0 else None, manual_costs),
        },
        "total_saving": {
            "value": savings,
            "index": get_diff_index(prev_res["savings"] if prev_len > 0 else None, savings),
        },
    }


def get_chart_range(date_range):
    result = {
        "range": None,
        "date_format": None,
    }
    start = date_range.start
    end = date_range.end
    if start is None or end is None:
        raise NotImplementedError
    if end.day == start.day and end.month == start.month and end.year == start.year:
        result["date_format"] = "YYYY-MM-DD HH24:00:00+00"
        result["range"] = "hour"
    elif end.month == start.month and end.year == start.year:
        result["date_format"] = "YYYY-MM-DD 00:00:00+00"
        result["range"] = "day"
    elif end.year == start.year:
        result["date_format"] = "YYYY-MM-01 00:00:00+00"
        result["range"] = "month"
    else:
        result["date_format"] = "YYYY-01-01 00:00:00+00"
        result["range"] = "year"
    return result


def get_jobs_chart(qs, date_range):
    result = {
        "items": [],
        "range": None
    }
    if date_range is None:
        return []

    chart_range = get_chart_range(date_range)
    result["range"] = chart_range["range"]

    qs = qs.values(
        date=Func(
            F('finished'),
            Value(chart_range["date_format"]),
            function='to_char',
            output_field=CharField()
        )
    ).annotate(
        count=Count("id"),
    ).order_by("date")

    for job in qs:
        result["items"].append({
            "x": datetime.strptime(job["date"], '%Y-%m-%d %H:%M:%S+00').astimezone(pytz.UTC),
            "y": job["count"],
        })
    return result


def get_hosts_chart(qs, date_range):
    result = {
        "items": [],
        "range": None
    }
    if date_range is None:
        return []
    chart_range = get_chart_range(date_range)
    result["range"] = chart_range["range"]
    qs = qs.values(
        date=Func(
            F('finished'),
            Value(chart_range["date_format"]),
            function='to_char',
            output_field=CharField()
        )
    ).annotate(
        hosts=Sum("num_hosts"),
    ).order_by("date")
    for job in qs:
        result["items"].append({
            "x": datetime.strptime(job["date"], '%Y-%m-%d %H:%M:%S+00').astimezone(pytz.UTC),
            "y": job["hosts"],
        })
    return result
