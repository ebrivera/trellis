"""
Matching Template - For assigning entities to targets based on compatibility.
Examples: volunteers → roles, mentees → mentors
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from ..schemas import (
    EntitySource, 
    NotificationConfig, 
    MatchStrategy, 
    TemplateType
)


class FieldWeight(BaseModel):
    """Weight for a single match field"""
    field: str = Field(..., description="Field name")
    weight: float = Field(..., description="Weight value (all weights must sum to 1.0)")


class MatchFields(BaseModel):
    """Which fields to score on for matching"""
    score_on: List[str] = Field(
        ..., 
        description="Field names to compare (e.g., ['interests', 'zip'])"
    )
    weights: List[FieldWeight] = Field(
        ..., 
        description="Weight for each field (must sum to 1.0)"
    )

    @field_validator('weights')
    @classmethod
    def validate_weights_sum(cls, v: List[FieldWeight]) -> List[FieldWeight]:
        total = sum(fw.weight for fw in v)
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class MatchConstraints(BaseModel):
    """Constraints for matching algorithm"""
    max_per_target: Optional[str] = Field(
        default=None,
        description="Field name in target entity that specifies capacity (e.g., 'sunday_count')"
    )
    respect_preferences: bool = Field(
        default=True,
        description="Whether to consider user preferences in matching"
    )
    min_score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum match score to accept (0-1)"
    )


class MatchingParams(BaseModel):
    """Parameters for the Matching template"""
    template: Literal[TemplateType.MATCHING] = TemplateType.MATCHING
    source: EntitySource = Field(
        ..., 
        description="Entities to be assigned (volunteers, mentees)"
    )
    target: EntitySource = Field(
        ..., 
        description="Targets to assign to (roles, mentors)"
    )
    match_strategy: MatchStrategy = Field(
        default=MatchStrategy.CAPACITY_BALANCED,
        description="Algorithm to use for matching"
    )
    match_fields: MatchFields = Field(
        ..., 
        description="Which fields to score on"
    )
    constraints: MatchConstraints = Field(
        default_factory=MatchConstraints,
        description="Constraints for matching"
    )
    notifications: List[NotificationConfig] = Field(
        default_factory=list,
        description="Notifications to send after approval"
    )