from fastapi import APIRouter, HTTPException, status

from app.models.alert import Alert, AlertRule, AlertRuleCreate
from app.services.alert_rules_service import (
    delete_rule,
    get_rule,
    list_rules,
    upsert_rule,
)
from app.services.alert_service import evaluate_alerts

router = APIRouter()


# ----------------------------- active alerts --------------------------------

@router.get("", response_model=list[Alert])
async def list_alerts(include_resolved: bool = False) -> list[Alert]:
    """List active alert rules. Set include_resolved=true to include resolved."""
    alerts = await evaluate_alerts()
    if include_resolved:
        return alerts
    return [a for a in alerts if not a.resolved]


# ----------------------------- rule management ------------------------------

@router.get("/rules", response_model=list[AlertRule])
def get_rules() -> list[AlertRule]:
    """Return all configured alert rules."""
    return list_rules()


@router.get("/rules/{rule_id}", response_model=AlertRule)
def get_rule_by_id(rule_id: str) -> AlertRule:
    rule = get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
    return rule


@router.put(
    "/rules/{rule_id}",
    response_model=AlertRule,
    status_code=status.HTTP_200_OK,
)
def put_rule(rule_id: str, payload: AlertRuleCreate) -> AlertRule:
    """Create or replace an alert rule by ID."""
    return upsert_rule(rule_id, payload)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_rule(rule_id: str) -> None:
    if not delete_rule(rule_id):
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
