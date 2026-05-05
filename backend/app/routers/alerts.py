from fastapi import APIRouter

from app.models.alert import Alert
from app.services.alert_service import evaluate_alerts

router = APIRouter()


@router.get("", response_model=list[Alert])
async def list_alerts(include_resolved: bool = False) -> list[Alert]:
    """List active alert rules. Set include_resolved=true to include resolved."""
    alerts = await evaluate_alerts()
    if include_resolved:
        return alerts
    return [a for a in alerts if not a.resolved]
