"""
Monitoring Template - For time-based alerts and follow-up actions.
Examples: track first-time visitors, flag lapsed donors
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from ..schemas import EntitySource, Channel, TemplateType


class TimeCondition(BaseModel):
    """Time-based condition for monitoring"""
    time_field: str = Field(
        ..., 
        description="Date field to check (e.g., 'visit_date')"
    )
    threshold: str = Field(
        ..., 
        description="Time threshold (e.g., '14 days', '90 days')"
    )
    operator: Literal[">", "<", ">=", "<=", "="] = Field(
        default=">",
        description="Comparison operator"
    )
    additional_filters: Optional[List[str]] = Field(
        default=None,
        description="Extra SQL-like conditions (e.g., 'last_contact_date IS NULL')"
    )

    @field_validator('threshold')
    @classmethod
    def validate_threshold_format(cls, v: str) -> str:
        """Validate threshold is in format 'N days|weeks|months'"""
        parts = v.split()
        if len(parts) != 2:
            raise ValueError("Threshold must be in format 'N days|weeks|months'")
        try:
            int(parts[0])
        except ValueError:
            raise ValueError(f"Threshold must start with a number, got '{parts[0]}'")
        if parts[1] not in ['day', 'days', 'week', 'weeks', 'month', 'months']:
            raise ValueError(f"Threshold unit must be days/weeks/months, got '{parts[1]}'")
        return v


class Alert(BaseModel):
    """Alert configuration for monitoring"""
    recipient: str = Field(
        ..., 
        description="Email or phone to send alert to"
    )
    channel: Channel = Field(..., description="SMS or email")
    template: str = Field(..., description="Alert message template")


class OptionalAction(BaseModel):
    """Optional follow-up action after monitoring alert"""
    type: Literal["bulk_notification"] = Field(
        ..., 
        description="Type of action"
    )
    recipients: str = Field(
        ..., 
        description="Who gets the follow-up (e.g., 'flagged_visitors')"
    )
    channel: Channel = Field(..., description="SMS or email")
    template: str = Field(..., description="Message template")
    requires_approval: bool = Field(
        default=True, 
        description="Whether this needs approval"
    )


class MonitoringParams(BaseModel):
    """Parameters for the Monitoring template"""
    template: Literal[TemplateType.MONITORING] = TemplateType.MONITORING
    source: EntitySource = Field(
        ..., 
        description="Data to monitor (visitors, donors)"
    )
    condition: TimeCondition = Field(
        ..., 
        description="Time-based trigger condition"
    )
    alerts: List[Alert] = Field(
        ..., 
        description="Who to alert when condition is met"
    )
    optional_action: Optional[OptionalAction] = Field(
        default=None,
        description="Optional follow-up action (e.g., send bulk SMS to flagged entities)"
    )