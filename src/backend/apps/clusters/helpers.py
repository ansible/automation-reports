import os
from calendar import monthrange
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlencode

import pytz
from django.core.cache import cache
from django.db import connection
from django.db.models import (
    Count,
    Sum,
    F,
    CharField,
    Func,
    Value)

from backend.apps.clusters.models import (
    Costs,
    CostsChoices,
    JobStatusChoices,
    DateRangeChoices,
    Cluster)


def sec2time(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)

    if h > 0:
        h = f'{h:,}'
        return '%sh %dmin %dsec' % (h, m, s)
    else:
        return '%dmin %dsec' % (m, s)


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


def sum_items(qs):
    qs = qs.aggregate(
        total_runs=Sum("runs"),
        total_successful_runs=Sum("successful_runs"),
        total_failed_runs=Sum("failed_runs"),
        total_num_hosts=Sum("num_hosts"),
        total_elapsed=Sum("elapsed"),
        total_manual_time=Sum("manual_time"),
        total_manual_costs=Sum("manual_costs"),
        total_automated_costs=Sum("automated_costs"),
        total_savings=Sum("savings"),
        total_time_savings=Sum("time_savings"),
    )

    result = {}

    for (dbKey, resKey) in [
        ("total_runs", "total_runs"),
        ("total_successful_runs", "successful_count"),
        ("total_failed_runs", "failed_count"),
        ("total_num_hosts", "host_count"),
        ("total_manual_time", "total_manual_time"),
        ("total_manual_costs", "manual_costs"),
        ("total_automated_costs", "automated_costs"),
        ("total_savings", "savings"),
    ]:
        result[resKey] = round(qs[dbKey], 2) if qs[dbKey] is not None else 0
    result["total_elapsed_hours"] = round((qs["total_elapsed"] / 3600), 2) if qs["total_elapsed"] is not None else 0
    result["time_savings"] = round((qs["total_time_savings"] / 3600), 2) if qs["total_time_savings"] is not None else 0
    return result


def get_report_data(qs):
    res = sum_items(qs)

    successful_count = res["successful_count"]
    failed_count = res["failed_count"]
    total_elapsed_hours = res["total_elapsed_hours"]
    total_runs = res["total_runs"]
    automated_costs = res["automated_costs"]
    manual_costs = res["manual_costs"]
    savings = res["savings"]
    num_hosts = res["host_count"]
    time_savings = res["time_savings"]

    return {
        "total_number_of_successful_jobs": {
            "value": successful_count,
        },
        "total_number_of_failed_jobs": {
            "value": failed_count,
        },
        "total_number_of_job_runs": {
            "value": total_runs,
        },
        "total_number_of_host_job_runs": {
            "value": num_hosts,
        },
        "total_hours_of_automation": {
            "value": total_elapsed_hours,
        },
        "cost_of_automated_execution": {
            "value": automated_costs,
        },
        "cost_of_manual_automation": {
            "value": manual_costs,
        },
        "total_saving": {
            "value": savings,
        },
        "total_time_saving": {
            "value": time_savings,
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
            days = (result["date_range"].end - result["date_range"].start).days
            if days < 1:
                result["range"] = "hour"
                result["date_format"] = "YYYY-MM-DD HH24:00:00+00"
            else:
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
        for i in range(24):
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
    organizations = options.get("organization", None)
    clusters = options.get("cluster", None)
    job_templates = options.get("job_template", None)
    labels = options.get("label", None)
    params = {
        'successful': JobStatusChoices.SUCCESSFUL,
        'failed': JobStatusChoices.FAILED,
        'num_hosts': 0
    }
    sql = '''
        select count(*) from (
        select s.host_id
        FROM clusters_jobhostsummary s
        JOIN clusters_job job on job.id=s.job_id
        WHERE job.status IN (%(successful)s, %(failed)s)
        AND job.num_hosts > %(num_hosts)s
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
    if options.get("project", None) is not None:
        sql += ' AND job.project_id = ANY(%(projects)s)'
        params['projects'] = [int(n) for n in options["project"]]
    if labels is not None:
        sql += ' AND job.id in (select job_id from clusters_joblabel where label_id = ANY(%(labels)s))'
        params['labels'] = [int(n) for n in labels]

    sql += ' group by s.host_id)t'
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if len(rows) > 0 and len(rows[0]) > 0:
            retval = rows[0][0]
    return retval


def get_unique_host_count(options):
    date_range = options.get("date_range", None)
    start_date = None
    end_date = None

    if date_range is not None:
        start_date = date_range.start
        end_date = date_range.end

    total_number_of_unique_hosts = get_unique_hosts_db(start_date=start_date, end_date=end_date, options=options)

    return {
        "total_number_of_unique_hosts": {
            "value": total_number_of_unique_hosts,
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


def get_related_links(options):
    result = {
        "related_links": {
            "successful_jobs": "",
            "failed_jobs": "",
        }
    }

    cluster = Cluster.objects.first()
    if cluster is None:
        return result

    _date_range = options.query_params.get("date_range", None)

    initial_url = f'{cluster.protocol}://{cluster.address}:{cluster.port}#/jobs'
    failed_data = {
        "job.status__exact": JobStatusChoices.FAILED.value,
    }
    successful_data = {
        "job.status__exact": JobStatusChoices.SUCCESSFUL.value,
    }

    data = {}

    if _date_range is not None:
        data_range = DateRangeChoices.get_date_range(_date_range)
        if data_range is not None:
            data["job.finished__gte"] = data_range.start.isoformat()
            data["job.finished__lte"] = data_range.end.isoformat()

    result["related_links"] = {
        "successful_jobs": f'{initial_url}?{urlencode({**data, **successful_data})}',
        "failed_jobs": f'{initial_url}?{urlencode({**failed_data, **data})}',
    }
    return result
