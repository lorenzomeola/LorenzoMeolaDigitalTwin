import hashlib
import hmac
import ipaddress
import logging
import os
import time
from datetime import datetime, timezone

import psycopg
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def visitor_key(identity, secret, day):
    try:
        address = ipaddress.ip_address(identity.strip())
        if isinstance(address, ipaddress.IPv6Address):
            address = address.ipv4_mapped or ipaddress.ip_network(f"{address}/64", strict=False).network_address
        canonical = str(address)
    except ValueError:
        canonical = "unknown"
    return hmac.new(secret.encode(), f"{day}:{canonical}".encode(), hashlib.sha256).hexdigest()


def enforce_rate_limit(identity, now=None):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=503, detail="The chat service is temporarily unavailable")
    try:
        minute_limit = max(1, int(os.getenv("CHAT_RATE_PER_MINUTE", "10")))
        day_limit = max(1, int(os.getenv("CHAT_RATE_PER_DAY", "100")))
        timestamp = int(time.time() if now is None else now)
        key = visitor_key(identity, os.getenv("RATE_LIMIT_SALT") or database_url, timestamp // 86400)
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '3s'")
                cursor.execute(
                    """
                    DELETE FROM public.twin_rate_limits WHERE ctid IN (
                        SELECT ctid FROM public.twin_rate_limits
                        WHERE expires_at < now() ORDER BY expires_at LIMIT 100
                        FOR UPDATE SKIP LOCKED
                    )
                    """
                )
                for seconds, limit in ((60, minute_limit), (86400, day_limit)):
                    start = timestamp // seconds * seconds
                    cursor.execute(
                        """
                        INSERT INTO public.twin_rate_limits
                            (visitor_hash, window_seconds, window_start, request_count, expires_at)
                        VALUES (%s, %s, %s, 1, %s)
                        ON CONFLICT (visitor_hash, window_seconds, window_start)
                        DO UPDATE SET request_count = twin_rate_limits.request_count + 1
                        WHERE twin_rate_limits.request_count < %s
                        RETURNING request_count
                        """,
                        (key, seconds, start, datetime.fromtimestamp(start + seconds, timezone.utc), limit),
                    )
                    if cursor.fetchone() is None:
                        raise HTTPException(
                            status_code=429,
                            detail="Too many messages. Please try again later.",
                            headers={"Retry-After": str(start + seconds - timestamp)},
                        )
    except HTTPException:
        raise
    except Exception as error:
        logger.warning("chat_rate_limit_failed error_type=%s", type(error).__name__)
        raise HTTPException(
            status_code=503, detail="The chat service is temporarily unavailable",
        ) from error