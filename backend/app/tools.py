import json
import os
import re
from datetime import datetime, timezone

import psycopg


def record_user_details(
    email,
    consent_confirmed,
    visitor_emails=None,
    name=None,
    notes=None,
):
    if consent_confirmed is not True:
        raise ValueError("Explicit consent is required to save contact details")

    if not isinstance(email, str):
        raise ValueError("A valid email address is required")
    email = email.strip()
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("A valid email address is required")
    if email.casefold() not in {address.casefold() for address in visitor_emails or set()}:
        raise ValueError("Email must be provided by the visitor")

    if name is not None:
        if not isinstance(name, str) or len(name.strip()) > 120:
            raise ValueError("Name must be 120 characters or fewer")
        name = name.strip() or None

    if notes is not None:
        if not isinstance(notes, str) or len(notes.strip()) > 1000:
            raise ValueError("Notes must be 1000 characters or fewer")
        notes = notes.strip() or None

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.twin_contact_requests
                    (email, name, notes, consent_confirmed_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    email,
                    name,
                    notes,
                    datetime.now(timezone.utc),
                ),
            )
            inserted_row = cursor.fetchone()

    if inserted_row is None:
        raise RuntimeError("PostgreSQL did not confirm saving the contact request")

    return {"status": "saved"}


RECORD_USER_DETAILS_SCHEMA = {
    "name": "record_user_details",
    "description": (
        "Save a visitor's email and optional name or follow-up notes after they "
        "have explicitly consented to storage. The visitor must provide the email."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The visitor's email address"},
            "name": {"type": "string", "description": "The visitor's name, if provided"},
            "notes": {
                "type": "string",
                "description": "Brief professional context for follow-up, if provided",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

TOOLS = [{"type": "function", "function": RECORD_USER_DETAILS_SCHEMA}]
TOOL_MAP = {"record_user_details": record_user_details}


def handle_tool_calls(tool_calls, consent_confirmed=False, visitor_emails=None):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        tool = TOOL_MAP.get(tool_name)
        if tool is None:
            result = {"status": "error", "reason": "Unknown tool"}
        else:
            try:
                result = tool(
                    **arguments,
                    consent_confirmed=consent_confirmed,
                    visitor_emails=visitor_emails,
                )
            except ValueError as error:
                result = {"status": "error", "reason": str(error)}
            except Exception:
                result = {
                    "status": "error",
                    "reason": "Contact details could not be saved right now.",
                }
        results.append(
            {
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            }
        )
    return results