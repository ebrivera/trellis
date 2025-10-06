# src/functions/send_notification.py
from src.database import insert_many
from typing import List, Dict, Any
import re

async def send_notification(
    recipients: List[Dict[str, Any]],
    channel: str,
    template: str,
    variables: Dict[str, Any],
    workflow_run_id: str = None
) -> Dict[str, Any]:
    """
    Queue notifications (mock sending for hackathon).
    Inserts into messages table.
    """
    messages = []
    
    for recipient in recipients:
        # Render template with variables
        content = template
        # Replace {{variable}} with values
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        
        # Also replace recipient-specific fields
        for key, value in recipient.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        
        messages.append({
            'recipient_id': str(recipient['id']),
            'channel': channel,
            'template': template,
            'content': content,
            'status': 'queued',  # For demo: immediately mark as 'sent'
            'workflow_run_id': workflow_run_id
        })
    
    # Insert into messages table
    if messages:
        await insert_many('messages', messages)
        # For demo, immediately update to 'sent'
        # In production, background worker would actually send
    
    return {
        'sent': len(messages),
        'failed': 0,
        'messages': messages
    }