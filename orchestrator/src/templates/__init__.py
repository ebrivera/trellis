"""
Workflow templates for the orchestrator.
Each template handles a specific type of church management workflow.
"""

from .matching import MatchingParams
from .monitoring import MonitoringParams
from .analysis import AnalysisParams

__all__ = [
    'MatchingParams',
    'MonitoringParams', 
    'AnalysisParams',
]


# Helper function for getting the right params model
def get_params_model(template_type):
    """
    Return the appropriate Pydantic model for a template type.
    
    Args:
        template_type: TemplateType enum value
        
    Returns:
        Matching/Monitoring/AnalysisParams class
    """
    from ..schemas import TemplateType
    
    if template_type == TemplateType.MATCHING:
        return MatchingParams
    elif template_type == TemplateType.MONITORING:
        return MonitoringParams
    elif template_type == TemplateType.ANALYSIS:
        return AnalysisParams
    else:
        raise ValueError(f"Unknown template type: {template_type}")