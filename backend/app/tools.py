import json
import logging
import os
import re
from datetime import datetime, timezone

import psycopg

from app.context import PUBLIC_CONTACT_DETAILS

logger = logging.getLogger(__name__)


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
        logger.error("contact_save_unconfigured variable=DATABASE_URL")
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

def get_contact_details():
    if not PUBLIC_CONTACT_DETAILS["email"] or not PUBLIC_CONTACT_DETAILS["phone"]:
        raise RuntimeError("Public contact details are not configured")
    return {"status": "ok", **PUBLIC_CONTACT_DETAILS}


def _submission_fields(fields, consent_confirmed, visitor_emails, visitor_text):
    if consent_confirmed is not True:
        raise ValueError("Explicit consent is required to save details")
    email = fields["email"]
    if not isinstance(email, str) or len(email.strip()) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        raise ValueError("A valid email address is required")
    if email.strip().casefold() not in {address.casefold() for address in visitor_emails or set()}:
        raise ValueError("Email must be provided by the visitor")
    normalized_visitor = " ".join(visitor_text.split()).casefold()
    limits = {"name": 120, "company": 200, "email": 254, "role": 200, "message": 4000, "preferred_time": 300}
    cleaned = {}
    for field, value in fields.items():
        if value is None and field == "preferred_time":
            cleaned[field] = None
            continue
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limits[field]:
            raise ValueError(f"Invalid {field}")
        value = value.strip()
        if " ".join(value.split()).casefold() not in normalized_visitor:
            raise ValueError(f"The visitor must provide {field}; do not invent or rewrite it")
        cleaned[field] = value
    return cleaned


def _save_submission(query, values):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("contact_save_unconfigured variable=DATABASE_URL")
        raise RuntimeError("DATABASE_URL is not configured")
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (*values, datetime.now(timezone.utc)))
            inserted = cursor.fetchone()
    if inserted is None:
        raise RuntimeError("PostgreSQL did not confirm saving the request")
    return {"status": "saved"}


def request_interview(name, company, email, role, message, preferred_time=None,
                      consent_confirmed=False, visitor_emails=None, visitor_text=""):
    fields = _submission_fields(
        {"name": name, "company": company, "email": email, "role": role,
         "message": message, "preferred_time": preferred_time},
        consent_confirmed, visitor_emails, visitor_text,
    )
    return _save_submission(
        """INSERT INTO public.twin_interview_requests
        (name, company, email, role, message, preferred_time, consent_confirmed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        tuple(fields.values()),
    )


def leave_message(name, email, message, consent_confirmed=False, visitor_emails=None, visitor_text=""):
    fields = _submission_fields(
        {"name": name, "email": email, "message": message},
        consent_confirmed, visitor_emails, visitor_text,
    )
    return _save_submission(
        """INSERT INTO public.twin_messages
        (name, email, message, consent_confirmed_at)
        VALUES (%s, %s, %s, %s) RETURNING id""",
        tuple(fields.values()),
    )


def get_skills_for_role(role_description, analysis_client=None, visitor_text=""):
    from app.role_match import analyze_role

    if not isinstance(role_description, str) or not role_description.strip():
        raise ValueError("A role description is required")
    if " ".join(role_description.split()).casefold() not in " ".join(visitor_text.split()).casefold():
        raise ValueError("The visitor must provide the role description")
    return analyze_role(role_description, analysis_client)


INTERVIEW_SCHEMA = {
    "name": "request_interview",
    "description": "Save an interview REQUEST, not a booking. Requires UI consent and visitor-supplied fields. Copy message and preferred_time verbatim; never invent a time, timezone or availability. Ask for missing required fields.",
    "parameters": {
        "type": "object", "additionalProperties": False,
        "properties": {field: {"type": "string"} for field in ("name", "company", "email", "role", "message", "preferred_time")},
        "required": ["name", "company", "email", "role", "message"],
    },
}
MESSAGE_SCHEMA = {
    "name": "leave_message",
    "description": "Save a message for Lorenzo with UI consent. Copy the visitor's actual message verbatim, not a summary or invented message. Ask for missing name or email. No notification is sent.",
    "parameters": {
        "type": "object", "additionalProperties": False,
        "properties": {field: {"type": "string"} for field in ("name", "email", "message")},
        "required": ["name", "email", "message"],
    },
}
CONTACT_SCHEMA = {
    "name": "get_contact_details",
    "description": "Get Lorenzo's owner-authorized public phone, email and location. No visitor consent or email required.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}
ROLE_SCHEMA = {
    "name": "get_skills_for_role",
    "description": "Analyze the job description pasted in the CURRENT user message against Lorenzo's verified skills. The server supplies the text; do not copy it into arguments. Use when the current message contains a job description and asks for fit or match. No storage consent required.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}
WRITE_TOOLS = {"record_user_details", "request_interview", "leave_message"}
TOOLS = [{"type": "function", "function": schema} for schema in (
    RECORD_USER_DETAILS_SCHEMA, INTERVIEW_SCHEMA, MESSAGE_SCHEMA, CONTACT_SCHEMA, ROLE_SCHEMA,
)]
TOOL_MAP = {
    "record_user_details": record_user_details, "request_interview": request_interview,
    "leave_message": leave_message, "get_contact_details": get_contact_details,
    "get_skills_for_role": get_skills_for_role,
}


def available_tools(consent_confirmed=False, visitor_emails=None):
    return [tool for tool in TOOLS if tool["function"]["name"] not in WRITE_TOOLS
            or (consent_confirmed is True and visitor_emails)]


def handle_tool_calls(tool_calls, consent_confirmed=False, visitor_emails=None, visitor_text="", current_message="", analysis_client=None):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        tool = TOOL_MAP.get(tool_name)
        if tool is None:
            result = {"status": "error", "reason": "Unknown tool"}
        else:
            try:
                arguments = json.loads(tool_call.function.arguments)
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be an object")
                schema = next(entry["function"]["parameters"] for entry in TOOLS if entry["function"]["name"] == tool_name)
                if arguments.keys() - schema["properties"].keys():
                    raise ValueError("Unexpected tool arguments")
                if tool_name in WRITE_TOOLS:
                    arguments.update(consent_confirmed=consent_confirmed, visitor_emails=visitor_emails)
                    if tool_name != "record_user_details":
                        arguments["visitor_text"] = visitor_text
                elif tool_name == "get_skills_for_role":
                    arguments.update(role_description=current_message or visitor_text,
                                     analysis_client=analysis_client, visitor_text=visitor_text)
                result = tool(**arguments)
            except (ValueError, TypeError) as error:
                reason = str(error) if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError) else "Invalid tool arguments"
                result = {"status": "error", "reason": reason}
            except Exception as error:
                logger.error(
                    "contact_save_failed error_type=%s sqlstate=%s",
                    type(error).__name__,
                    getattr(error, "sqlstate", None) or "none",
                )
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