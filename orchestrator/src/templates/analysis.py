"""
Analysis Template - For calculating metrics and identifying outliers.
Examples: giving trends, attendance patterns, budget analysis
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from ..schemas import EntityQuery, NotificationConfig, TemplateType


class MetricFormula(BaseModel):
    """A metric to calculate"""
    name: str = Field(
        ..., 
        description="Metric name (e.g., 'total_raised')"
    )
    formula: str = Field(
        ..., 
        description="SQL-like formula (e.g., 'SUM(amount)')"
    )
    group_by: Optional[str] = Field(
        default=None,
        description="Field to group by (e.g., 'initiative_name')"
    )
    format: Optional[Literal["currency", "percent", "number"]] = Field(
        default="number",
        description="How to format the result"
    )


class FlagCondition(BaseModel):
    """Condition to flag entities for attention"""
    name: str = Field(
        ..., 
        description="Flag name (e.g., 'lapsed_donors')"
    )
    condition: str = Field(
        ..., 
        description="SQL-like condition to detect outliers"
    )
    group_by: Optional[str] = Field(
        default=None,
        description="Field to group by (e.g., 'donor_id')"
    )
    action: Literal["notify", "flag", "report"] = Field(
        default="flag",
        description="What to do with flagged entities"
    )


class AnalysisParams(BaseModel):
    """Parameters for the Analysis template"""
    template: Literal[TemplateType.ANALYSIS] = TemplateType.ANALYSIS
    sources: List[EntityQuery] = Field(
        ...,
        description="Data sources to analyze"
    )
    join_on: Optional[str] = Field(
        default=None,
        description="Field to join sources on (e.g., 'initiative_name')"
    )
    metrics: List[MetricFormula] = Field(
        ...,
        description="Metrics to calculate"
    )
    flags: Optional[List[FlagCondition]] = Field(
        default=None,
        description="Conditions to flag outliers/issues"
    )
    notifications: List[NotificationConfig] = Field(
        default_factory=list,
        description="Notifications to send after approval"
    )

    @field_validator('sources')
    @classmethod
    def validate_multiple_sources(cls, v: List[EntityQuery]) -> List[EntityQuery]:
        if len(v) < 1:
            raise ValueError("Analysis requires at least one data source")
        return v