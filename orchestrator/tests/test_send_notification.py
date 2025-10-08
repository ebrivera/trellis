"""
Unit tests for send_notification.py functions.
No database required - uses db_insert=False for testing.
Run with: python tests/test_send_notification.py (from orchestrator/ directory)
"""

import asyncio
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.functions.send_notification import (
    send_notification,
    render_template_preview,
    extract_template_variables,
    _render_template
)
from src.schemas import Channel, NotificationConfig


def test_simple_template_rendering():
    """Test basic variable substitution"""
    print("\n=== Test 1: Simple template rendering ===")

    template = "Hi {{name}}, welcome!"
    recipient = {'name': 'Alice'}
    result = _render_template(template, recipient, {})

    assert result == "Hi Alice, welcome!"
    print(f"✓ Rendered: '{result}'")


def test_multiple_variables():
    """Test template with multiple variables"""
    print("\n=== Test 2: Multiple variables ===")

    template = "Hi {{name}}, you're assigned to {{role}} on {{day}}!"
    recipient = {'name': 'Bob'}
    global_vars = {'role': 'Youth Leader', 'day': 'Sunday'}

    result = _render_template(template, recipient, global_vars)

    assert result == "Hi Bob, you're assigned to Youth Leader on Sunday!"
    print(f"✓ Rendered: '{result}'")


def test_recipient_overrides_global():
    """Test that recipient variables override global variables"""
    print("\n=== Test 3: Recipient overrides global ===")

    template = "Name: {{name}}"
    recipient = {'name': 'Alice'}
    global_vars = {'name': 'Default'}

    result = _render_template(template, recipient, global_vars)

    assert result == "Name: Alice"
    print(f"✓ Recipient variable overrode global: '{result}'")


def test_whitespace_tolerance():
    """Test template with extra whitespace"""
    print("\n=== Test 4: Whitespace tolerance ===")

    template = "Hi {{ name }}, role: {{  role  }}!"
    recipient = {'name': 'Charlie', 'role': 'Mentor'}

    result = _render_template(template, recipient, {})

    assert result == "Hi Charlie, role: Mentor!"
    print(f"✓ Whitespace handled: '{result}'")


def test_missing_variable():
    """Test that missing variables are kept as-is"""
    print("\n=== Test 5: Missing variable ===")

    template = "Hi {{name}}, your code is {{code}}"
    recipient = {'name': 'Alice'}
    # 'code' is missing

    result = _render_template(template, recipient, {})

    assert result == "Hi Alice, your code is {{code}}"
    print(f"✓ Missing variable preserved: '{result}'")


def test_nested_access():
    """Test nested variable access"""
    print("\n=== Test 6: Nested variable access ===")

    template = "Contact: {{person.name}} at {{person.email}}"
    recipient = {
        'person': {
            'name': 'Alice',
            'email': 'alice@example.com'
        }
    }

    result = _render_template(template, recipient, {})

    assert result == "Contact: Alice at alice@example.com"
    print(f"✓ Nested access: '{result}'")


def test_extract_variables():
    """Test extracting variable names from template"""
    print("\n=== Test 7: Extract variables ===")

    template = "Hi {{name}}, assigned to {{role}} on {{day}}!"
    variables = extract_template_variables(template)

    assert set(variables) == {'name', 'role', 'day'}
    print(f"✓ Extracted: {variables}")


def test_extract_variables_with_duplicates():
    """Test that duplicate variables are deduplicated"""
    print("\n=== Test 8: Extract with duplicates ===")

    template = "{{name}} is {{name}}'s name"
    variables = extract_template_variables(template)

    assert variables == ['name']
    print(f"✓ Deduplicated: {variables}")


async def test_send_notification_sms():
    """Test sending SMS notification"""
    print("\n=== Test 9: Send SMS notification ===")

    recipients = [
        {'id': 'v1', 'name': 'Alice', 'phone': '555-0001'},
        {'id': 'v2', 'name': 'Bob', 'phone': '555-0002'}
    ]

    config = NotificationConfig(
        channel=Channel.SMS,
        template="Hi {{name}}, you're assigned to {{role}}!"
    )

    global_vars = {'role': 'Youth Leader'}

    result = await send_notification(
        recipients,
        config,
        global_vars,
        db_insert=False  # Don't insert to DB in test
    )

    assert result['sent'] == 2
    assert result['failed'] == 0
    assert len(result['messages']) == 2
    assert result['messages'][0]['content'] == "Hi Alice, you're assigned to Youth Leader!"
    assert result['messages'][1]['content'] == "Hi Bob, you're assigned to Youth Leader!"
    print(f"✓ Sent {result['sent']} SMS messages")


async def test_send_notification_email():
    """Test sending email notification"""
    print("\n=== Test 10: Send email notification ===")

    recipients = [
        {'id': 'm1', 'name': 'Alice', 'email': 'alice@example.com'}
    ]

    config = NotificationConfig(
        channel=Channel.EMAIL,
        template="Hello {{name}}, welcome to {{program}}!"
    )

    global_vars = {'program': 'Mentorship Program'}

    result = await send_notification(
        recipients,
        config,
        global_vars,
        db_insert=False
    )

    assert result['sent'] == 1
    assert result['messages'][0]['channel'] == 'email'
    assert result['messages'][0]['recipient_contact'] == 'alice@example.com'
    print(f"✓ Sent {result['sent']} email message")


async def test_validation_missing_id():
    """Test validation catches missing recipient ID"""
    print("\n=== Test 11: Validation - missing ID ===")

    recipients = [
        {'name': 'Alice', 'phone': '555-0001'}  # Missing 'id'
    ]

    config = NotificationConfig(
        channel=Channel.SMS,
        template="Hi {{name}}!"
    )

    result = await send_notification(recipients, config, {}, db_insert=False)

    assert result['sent'] == 0
    assert result['failed'] == 1
    assert 'id' in result['errors'][0]['error']
    print(f"✓ Caught missing ID: {result['errors'][0]['error']}")


async def test_validation_missing_phone():
    """Test validation catches missing phone for SMS"""
    print("\n=== Test 12: Validation - missing phone ===")

    recipients = [
        {'id': 'v1', 'name': 'Alice'}  # Missing 'phone'
    ]

    config = NotificationConfig(
        channel=Channel.SMS,
        template="Hi {{name}}!"
    )

    result = await send_notification(recipients, config, {}, db_insert=False)

    assert result['sent'] == 0
    assert result['failed'] == 1
    assert 'phone' in result['errors'][0]['error']
    print(f"✓ Caught missing phone: {result['errors'][0]['error']}")


async def test_validation_missing_email():
    """Test validation catches missing email for email channel"""
    print("\n=== Test 13: Validation - missing email ===")

    recipients = [
        {'id': 'v1', 'name': 'Alice'}  # Missing 'email'
    ]

    config = NotificationConfig(
        channel=Channel.EMAIL,
        template="Hi {{name}}!"
    )

    result = await send_notification(recipients, config, {}, db_insert=False)

    assert result['sent'] == 0
    assert result['failed'] == 1
    assert 'email' in result['errors'][0]['error']
    print(f"✓ Caught missing email: {result['errors'][0]['error']}")


async def test_partial_success():
    """Test that some recipients can fail while others succeed"""
    print("\n=== Test 14: Partial success ===")

    recipients = [
        {'id': 'v1', 'name': 'Alice', 'phone': '555-0001'},  # Valid
        {'id': 'v2', 'name': 'Bob'},  # Missing phone
        {'id': 'v3', 'name': 'Charlie', 'phone': '555-0003'}  # Valid
    ]

    config = NotificationConfig(
        channel=Channel.SMS,
        template="Hi {{name}}!"
    )

    result = await send_notification(recipients, config, {}, db_insert=False)

    assert result['sent'] == 2
    assert result['failed'] == 1
    assert len(result['messages']) == 2
    assert len(result['errors']) == 1
    print(f"✓ Partial success: {result['sent']} sent, {result['failed']} failed")


async def test_message_structure():
    """Test that message records have correct structure"""
    print("\n=== Test 15: Message structure ===")

    recipients = [
        {'id': 'v1', 'name': 'Alice', 'phone': '555-0001'}
    ]

    config = NotificationConfig(
        channel=Channel.SMS,
        template="Hi {{name}}!"
    )

    result = await send_notification(
        recipients,
        config,
        {},
        db_insert=False,
        workflow_run_id='test-run-123'
    )

    message = result['messages'][0]

    assert 'recipient_id' in message
    assert 'recipient_contact' in message
    assert 'channel' in message
    assert 'template' in message
    assert 'content' in message
    assert 'status' in message
    assert 'workflow_run_id' in message

    assert message['recipient_id'] == 'v1'
    assert message['recipient_contact'] == '555-0001'
    assert message['channel'] == 'sms'
    assert message['status'] == 'queued'
    assert message['workflow_run_id'] == 'test-run-123'

    print(f"✓ Message structure valid")


async def test_template_preview():
    """Test template preview function"""
    print("\n=== Test 16: Template preview ===")

    template = "Hi {{name}}, assigned to {{role}}!"
    sample_recipient = {'name': 'Sample User'}
    global_vars = {'role': 'Test Role'}

    preview = render_template_preview(template, sample_recipient, global_vars)

    assert preview == "Hi Sample User, assigned to Test Role!"
    print(f"✓ Preview: '{preview}'")


async def test_empty_recipients():
    """Test handling of empty recipient list"""
    print("\n=== Test 17: Empty recipients ===")

    config = NotificationConfig(
        channel=Channel.SMS,
        template="Hi {{name}}!"
    )

    result = await send_notification([], config, {}, db_insert=False)

    assert result['sent'] == 0
    assert result['failed'] == 0
    assert len(result['messages']) == 0
    print(f"✓ Empty recipients handled")


async def test_workflow_run_id():
    """Test workflow_run_id is properly included"""
    print("\n=== Test 18: Workflow run ID ===")

    recipients = [
        {'id': 'v1', 'name': 'Alice', 'phone': '555-0001'}
    ]

    config = NotificationConfig(
        channel=Channel.SMS,
        template="Test"
    )

    result = await send_notification(
        recipients,
        config,
        {},
        db_insert=False,
        workflow_run_id='workflow-abc-123'
    )

    assert result['messages'][0]['workflow_run_id'] == 'workflow-abc-123'
    print(f"✓ Workflow run ID preserved")


async def test_numeric_and_list_values():
    """Test that numeric and list values are converted to strings"""
    print("\n=== Test 19: Numeric and list values ===")

    template = "Count: {{count}}, Items: {{items}}"
    recipient = {'count': 42, 'items': ['a', 'b', 'c']}

    result = _render_template(template, recipient, {})

    assert "42" in result
    assert "['a', 'b', 'c']" in result
    print(f"✓ Values converted: '{result}'")


async def test_multiple_recipients_unique_content():
    """Test that each recipient gets personalized content"""
    print("\n=== Test 20: Unique content per recipient ===")

    recipients = [
        {'id': 'v1', 'name': 'Alice', 'role': 'Leader', 'phone': '555-0001'},
        {'id': 'v2', 'name': 'Bob', 'role': 'Member', 'phone': '555-0002'}
    ]

    config = NotificationConfig(
        channel=Channel.SMS,
        template="Hi {{name}}, you're a {{role}}!"
    )

    result = await send_notification(recipients, config, {}, db_insert=False)

    assert result['messages'][0]['content'] == "Hi Alice, you're a Leader!"
    assert result['messages'][1]['content'] == "Hi Bob, you're a Member!"
    print(f"✓ Each recipient got unique content")


def run_all_tests():
    """Run all send_notification tests"""
    print("=" * 60)
    print("Testing send_notification.py functions (unit tests - no DB)")
    print("=" * 60)

    # Sync tests
    try:
        test_simple_template_rendering()
        test_multiple_variables()
        test_recipient_overrides_global()
        test_whitespace_tolerance()
        test_missing_variable()
        test_nested_access()
        test_extract_variables()
        test_extract_variables_with_duplicates()
    except AssertionError as e:
        print(f"\n✗ Sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Async tests
    async def run_async_tests():
        try:
            await test_send_notification_sms()
            await test_send_notification_email()
            await test_validation_missing_id()
            await test_validation_missing_phone()
            await test_validation_missing_email()
            await test_partial_success()
            await test_message_structure()
            await test_template_preview()
            await test_empty_recipients()
            await test_workflow_run_id()
            await test_numeric_and_list_values()
            await test_multiple_recipients_unique_content()

            print("\n" + "=" * 60)
            print("✓ All 20 send_notification tests passed!")
            print("=" * 60)

        except AssertionError as e:
            print(f"\n✗ Async test failed: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(run_async_tests())


if __name__ == "__main__":
    run_all_tests()
