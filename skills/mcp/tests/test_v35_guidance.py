"""Keep MCP guidance bounded to evidence and current v3.5 requirements."""
from mcp_server.resources.registry import get_resource


def test_launch_checklist_contains_v35_boundary_requirements():
    result = get_resource('quick_start_checklist', tier='free')
    text = result['content']
    for control in ('S1.8', 'CP.11', 'CP.12', 'CP.13', 'CP.14', 'CP.15', 'F3.6', 'F3.7', 'A2.7', 'A2.8', 'A2.9', 'E5.5'):
        assert control in text
    assert 'not deployment authorization or conformance' in text
    assert 'Score 20/20' not in text
