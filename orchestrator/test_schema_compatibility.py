"""
Test that debate extraction produces params compatible with new schema
"""

import asyncio
from dotenv import load_dotenv
from src.graph import create_orchestrator_graph
from src.schemas import TemplateType, EntityType

load_dotenv()

async def test_schema_compatibility():
    """Verify extracted params use EntityQuery, not EntitySource"""
    
    orchestrator = create_orchestrator_graph()
    
    # Run a matching workflow
    result = await orchestrator.ainvoke({
        'request': "Match volunteers to Sunday roles based on skills",
        'agent_initiated': False
    })
    
    params = result['params']
    
    # Verify no 'file' field (old schema)
    assert 'file' not in params.get('source', {}), "❌ Still using old EntitySource schema (has 'file' field)"
    assert 'file' not in params.get('target', {}), "❌ Still using old EntitySource schema (has 'file' field)"
    
    # Verify has entity_type (new schema)
    assert 'entity_type' in params['source'], "❌ Missing entity_type in source"
    assert 'entity_type' in params['target'], "❌ Missing entity_type in target"
    
    # Verify entity_type is lowercase table name
    source_type = params['source']['entity_type']
    assert source_type in ['people', 'groups', 'gifts'], f"❌ Invalid entity_type: {source_type}"
    
    # Verify has subtype
    assert params['source'].get('subtype') is not None, "❌ Missing subtype in source"
    
    # Verify filters use FilterCondition format if present
    if params['source'].get('filters'):
        for f in params['source']['filters']:
            assert 'field' in f, "❌ Filter missing 'field'"
            assert 'operator' in f, "❌ Filter missing 'operator'"
            assert 'value' in f, "❌ Filter missing 'value'"
    
    print("✅ ALL SCHEMA COMPATIBILITY TESTS PASSED")
    print(f"\nExtracted params:")
    print(f"  Source: {params['source']['entity_type']} (subtype: {params['source'].get('subtype')})")
    print(f"  Target: {params['target']['entity_type']} (subtype: {params['target'].get('subtype')})")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_schema_compatibility())