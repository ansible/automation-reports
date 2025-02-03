import os
from decimal import Decimal

from django.core.cache import cache

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
