# src/functions/send_notification.py
import re
from typing import List, Dict, Any, Optional
from ..schemas import Channel, NotificationConfig


async def send_notification(
    recipients: List[Dict[str, Any]],
    config: NotificationConfig,
    global_variables: Optional[Dict[str, Any]] = None,
    db_insert: bool = True,
    workflow_run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Queue notifications to be sent via SMS or email.

    This function:
    1. Renders template for each recipient with variable substitution
    2. Validates recipients have required contact information
    3. Queues messages to database (or returns them for testing)

    Args:
        recipients: List of recipient dicts, each must have:
            - id: recipient identifier
            - name: recipient name (optional but common)
            - email: for email channel (optional)
            - phone: for SMS channel (optional)
        config: NotificationConfig with channel and template
        global_variables: Variables available to all recipients (e.g., sender info)
        db_insert: Whether to insert into database (False for testing)
        workflow_run_id: ID of the workflow run that triggered this

    Returns:
        Dictionary with:
            - sent: number successfully queued
            - failed: number that failed
            - messages: list of message dicts
            - errors: list of error messages

    Examples:
        # Simple notification
        recipients = [
            {'id': 'v1', 'name': 'Alice', 'phone': '555-0001'},
            {'id': 'v2', 'name': 'Bob', 'phone': '555-0002'}
        ]
        config = NotificationConfig(
            channel=Channel.SMS,
            template="Hi {{name}}, you're assigned to {{role_name}}!"
        )
        global_vars = {'role_name': 'Youth Leader'}

        result = await send_notification(recipients, config, global_vars)
        # => {'sent': 2, 'failed': 0, 'messages': [...]}
    """
    if global_variables is None:
        global_variables = {}

    messages = []
    errors = []

    for recipient in recipients:
        try:
            # Validate recipient has required fields
            _validate_recipient(recipient, config.channel)

            # Render template with both global and recipient-specific variables
            content = _render_template(
                config.template,
                recipient,
                global_variables
            )

            # Build message record
            message = {
                'recipient_id': str(recipient['id']),
                'recipient_contact': _get_contact_info(recipient, config.channel),
                'channel': config.channel.value,
                'template': config.template,
                'content': content,
                'status': 'queued',
                'workflow_run_id': workflow_run_id
            }

            messages.append(message)

        except Exception as e:
            errors.append({
                'recipient_id': recipient.get('id', 'unknown'),
                'error': str(e)
            })

    # Insert into database if requested
    if db_insert and messages:
        try:
            from ..database import insert_many
            await insert_many('messages', messages)
        except Exception as e:
            # Database error - add to errors but don't lose message data
            errors.append({
                'type': 'database',
                'error': f"Failed to insert messages: {e}"
            })

    return {
        'sent': len(messages),
        'failed': len(errors),
        'messages': messages,
        'errors': errors if errors else []
    }


def _render_template(
    template: str,
    recipient: Dict[str, Any],
    global_variables: Dict[str, Any]
) -> str:
    """
    Render Handlebars-style template with variable substitution.

    Variables are resolved in this order (later overrides earlier):
    1. Global variables (e.g., shared context like role_name)
    2. Recipient-specific variables (e.g., name, email)

    Supports:
    - Simple variables: {{name}}
    - Nested access: {{person.name}}
    - Whitespace tolerance: {{ name }}

    Does NOT support (for MVP):
    - Conditionals: {{#if}}
    - Loops: {{#each}}
    - Helpers: {{formatDate}}

    Args:
        template: Template string with {{variable}} placeholders
        recipient: Recipient-specific variables
        global_variables: Global variables available to all recipients

    Returns:
        Rendered string with all variables replaced

    Examples:
        >>> _render_template(
        ...     "Hi {{name}}, assigned to {{role}}!",
        ...     {'name': 'Alice'},
        ...     {'role': 'Leader'}
        ... )
        'Hi Alice, assigned to Leader!'
    """
    # Merge variables (recipient overrides global)
    variables = {**global_variables, **recipient}

    # Find all {{variable}} patterns
    pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}'

    def replace_variable(match):
        var_name = match.group(1).strip()

        # Handle nested access (e.g., person.name)
        if '.' in var_name:
            parts = var_name.split('.')
            value = variables
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
        else:
            value = variables.get(var_name)

        # Convert to string, keep placeholder if not found
        if value is None:
            return match.group(0)  # Keep {{variable}} if not found
        return str(value)

    # Replace all variables
    return re.sub(pattern, replace_variable, template)


def _validate_recipient(recipient: Dict[str, Any], channel: Channel) -> None:
    """
    Validate that recipient has required fields for the channel.

    Args:
        recipient: Recipient dictionary
        channel: Communication channel

    Raises:
        ValueError: If validation fails
    """
    # Must have id
    if 'id' not in recipient:
        raise ValueError("Recipient must have 'id' field")

    # Must have appropriate contact info for channel
    if channel == Channel.EMAIL:
        if 'email' not in recipient or not recipient['email']:
            raise ValueError(f"Recipient {recipient.get('id')} missing 'email' for email channel")

    elif channel == Channel.SMS:
        if 'phone' not in recipient or not recipient['phone']:
            raise ValueError(f"Recipient {recipient.get('id')} missing 'phone' for SMS channel")


def _get_contact_info(recipient: Dict[str, Any], channel: Channel) -> str:
    """
    Extract the appropriate contact information based on channel.

    Args:
        recipient: Recipient dictionary
        channel: Communication channel

    Returns:
        Contact string (email address or phone number)
    """
    if channel == Channel.EMAIL:
        return recipient['email']
    elif channel == Channel.SMS:
        return recipient['phone']
    return ''


def render_template_preview(
    template: str,
    sample_recipient: Dict[str, Any],
    global_variables: Optional[Dict[str, Any]] = None
) -> str:
    """
    Render a template preview for approval UI.

    This is a convenience function for showing users what the message will look like.

    Args:
        template: Template string
        sample_recipient: Example recipient data
        global_variables: Global variables

    Returns:
        Rendered preview string
    """
    if global_variables is None:
        global_variables = {}

    return _render_template(template, sample_recipient, global_variables)


def extract_template_variables(template: str) -> List[str]:
    """
    Extract all variable names from a template.

    Useful for validation and preview UI.

    Args:
        template: Template string

    Returns:
        List of variable names found in template

    Examples:
        >>> extract_template_variables("Hi {{name}}, role: {{role_name}}")
        ['name', 'role_name']
    """
    pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}'
    matches = re.findall(pattern, template)
    return list(set(matches))  # Unique variables
