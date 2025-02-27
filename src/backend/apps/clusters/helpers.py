import os
from calendar import monthrange
from datetime import datetime
from decimal import Decimal

import pytz
from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Sum, F, CharField, Func, Value

from backend.apps.clusters.models import Costs, CostsChoices, JobStatusChoices, DateRangeChoices


def get_costs(from_db=False):
    costs = cache.get('costs')
    if from_db:
        costs = None
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
    return round(((float(new_value) - float(old_value)) / float(old_value)) * 100)


def sum_items(items):
    result = {
        "successful_count": 0,
        "failed_count": 0,
        "total_elapsed_hours": 0,
        "total_runs": 0,
        "automated_costs": 0,
        "manual_costs": 0,
        "host_count": 0,
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
        result["host_count"] += item["num_hosts"]

    result["total_elapsed_hours"] = round((result["total_elapsed_hours"] / 3600), 2)
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
    num_hosts = res["host_count"]

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
        "total_number_of_host_job_runs": {
            "value": num_hosts,
            "index": get_diff_index(prev_res["host_count"] if prev_len > 0 else None, num_hosts),
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


def get_chart_range(request):
    result = {
        "range": None,
        "date_format": None,
        "date_range": None,
    }

    _date_range = request.query_params.get("date_range", None)
    _start_date = request.query_params.get("start_date", None)
    _end_date = request.query_params.get("end_date", None)

    if _date_range is None:
        return result

    result["date_range"] = DateRangeChoices.get_date_range(_date_range, _start_date, _end_date)
    if result["date_range"] is None:
        return result

    match _date_range:
        case DateRangeChoices.LAST_YEAR | DateRangeChoices.LAST_6_MONTH | DateRangeChoices.LAST_3_MONTH:
            result["range"] = "month"
            result["date_format"] = "YYYY-MM-01 00:00:00+00"

        case DateRangeChoices.LAST_MONTH | DateRangeChoices.MONTH_TO_DATE:
            result["range"] = "day"
            result["date_format"] = "YYYY-MM-DD 00:00:00+00"
        case DateRangeChoices.LAST_2_YEARS | DateRangeChoices.LAST_3_YEARS:
            result["date_format"] = "YYYY-01-01 00:00:00+00"
            result["range"] = "year"
        case _:
            days = (result["date_range"].end - result["date_range"].start).days
            if days < 1:
                result["range"] = "hour"
                result["date_format"] = "YYYY-MM-DD HH24:00:00+00"
            elif days <= 45:
                result["range"] = "day"
                result["date_format"] = "YYYY-MM-DD 00:00:00+00"
            elif days <= 365:
                result["range"] = "month"
                result["date_format"] = "YYYY-MM-01 00:00:00+00"
            elif result["date_range"].start.year == result["date_range"].end.year:
                result["range"] = "month"
                result["date_format"] = "YYYY-MM-01 00:00:00+00"
            else:
                result["date_format"] = "YYYY-01-01 00:00:00+00"
                result["range"] = "year"
    return result


def get_chart_x_axis(chart_range):
    result = []
    date_range = chart_range["date_range"]
    x_axis_range = chart_range["range"]
    start = date_range.start
    end = date_range.end
    if x_axis_range == "hour":
        for i in range(23):
            d = start.replace(hour=i, minute=0, second=0, microsecond=0)
            result.append(d)
    elif x_axis_range == "day":
        current_date = start.replace(hour=0, minute=0, second=0, microsecond=0)
        while current_date.date() <= end.date():
            result.append(current_date)
            _day = current_date.day + 1
            _month = current_date.month
            _year = current_date.year
            num_days = monthrange(_year, _month)[1]
            if _day > num_days:
                _day = 1
                _month += 1
                if _month > 12:
                    _month = 1
                    _year += 1
            current_date = current_date.replace(day=_day, month=_month, year=_year, second=0, microsecond=0, hour=0)
    elif x_axis_range == "month":
        current_date = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        while current_date.date() < end.date():
            result.append(current_date)
            _year = current_date.year
            _month = current_date.month
            if _month == 12:
                _year += 1
                _month = 1
            else:
                _month += 1
            current_date = current_date.replace(year=_year, month=_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_year = start.year
        end_year = end.year
        for i in range(start_year, end_year + 1):
            d = start.replace(year=i, day=1, month=1, hour=0, minute=0, second=0, microsecond=0)
            result.append(d)
    return result


def get_unique_hosts_db(start_date, end_date, options):
    retval = None
    params = {
        'successful': JobStatusChoices.SUCCESSFUL,
        'failed': JobStatusChoices.FAILED,
    }
    organizations = options.get("organization", None)
    clusters = options.get("cluster", None)
    job_templates = options.get("job_template", None)
    labels = options.get("label", None)

    sql = '''
            with jobs as (
            select job.id 
                from clusters_job job
            '''
    if labels is not None:
        sql += '''
            join clusters_joblabel label on label.job_id = job.id 
        '''
    sql += '''
                WHERE job.status IN (%(successful)s, %(failed)s) 
            '''
    if start_date is not None:
        sql += ' AND job.finished >= %(start_date)s'
        params['start_date'] = start_date
    if end_date is not None:
        sql += ' AND job.finished <= %(end_date)s'
        params['end_date'] = end_date
    if organizations is not None:
        sql += ' AND job.organization_id = ANY(%(organizations)s)'
        params['organizations'] = [int(n) for n in organizations]
    if clusters is not None:
        sql += ' AND job.cluster_id = ANY(%(clusters)s)'
        params['clusters'] = [int(n) for n in clusters]
    if job_templates is not None:
        sql += ' AND job.job_template_id = ANY(%(job_templates)s)'
        params['job_templates'] = [int(n) for n in job_templates]

    if labels is not None:
        sql += ' AND label.label_id = ANY(%(labels)s)'
        params['labels'] = [int(n) for n in labels]

    sql += ')'
    sql += '''
            select count(*) from (
            select
            host_id
            from clusters_jobhostsummary
            where job_id in (select id from jobs)
            group by host_id)a
    '''

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if len(rows) > 0 and len(rows[0]) > 0:
            retval = rows[0][0]

    return retval


def get_unique_host_count(options):
    prev_count = None
    date_range = options.get("date_range", None)
    start_date = None
    end_date = None

    prev_start_date = None
    prev_end_date = None

    if date_range is not None:
        start_date = date_range.start
        end_date = date_range.end
        prev_start_date = date_range.prev_start
        prev_end_date = date_range.prev_end

    total_number_of_unique_hosts = get_unique_hosts_db(start_date=start_date, end_date=end_date, options=options)

    if prev_start_date and prev_end_date:
        prev_count = get_unique_hosts_db(start_date=prev_start_date, end_date=prev_end_date, options=options)

    return {
        "total_number_of_unique_hosts": {
            "value": total_number_of_unique_hosts,
            "index": get_diff_index(prev_count, total_number_of_unique_hosts)
        }
    }


def get_chart_data(qs, request):
    chart_range = get_chart_range(request)
    x_axis = get_chart_x_axis(chart_range)
    result = {
        "host_chart": {
            "items": [],
            "range": chart_range["range"]
        },
        "job_chart": {
            "items": [],
            "range": chart_range["range"]
        }
    }

    qs = qs.values(
        date=Func(
            F('finished'),
            Value(chart_range["date_format"]),
            function='to_char',
            output_field=CharField()
        )
    ).annotate(
        runs=Count("*"),
        num_hosts=Sum("num_hosts"),
    ).order_by("date")

    y_data = {datetime.strptime(d["date"], '%Y-%m-%d %H:%M:%S+00').astimezone(pytz.UTC): d for d in qs}
    for x in x_axis:
        y = y_data.get(x, {"runs": 0, "num_hosts": 0})
        result["host_chart"]["items"].append({"x": x, "y": y["num_hosts"]})
        result["job_chart"]["items"].append({"x": x, "y": y["runs"]})

    return result
