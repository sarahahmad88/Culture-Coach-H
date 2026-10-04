"""Bounded provider backoff; SDK retries stay disabled to avoid multiplication."""
import math
import random
import time
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from groq import APIConnectionError
from openai import APIConnectionError as OpenAIConnectionError

MAX_RETRIES=3
BASE_DELAY=1.0
MAX_DELAY=30.0
MAX_TOTAL_WAIT=60.0

def retry_after(exc):
    headers=getattr(getattr(exc,'response',None),'headers',{}) or {}
    raw=headers.get('retry-after') or headers.get('Retry-After')
    if raw is None:return None
    try:
        seconds=float(raw)
        return max(0.0,seconds) if math.isfinite(seconds) and seconds>=0 else None
    except (TypeError,ValueError):
        try:
            when=parsedate_to_datetime(raw)
            if when.tzinfo is None:when=when.replace(tzinfo=timezone.utc)
            return max(0.0,(when-datetime.now(timezone.utc)).total_seconds())
        except (TypeError,ValueError,OverflowError):return None

def retryable(exc):
    status=getattr(exc,'status_code',None)
    return isinstance(exc,(APIConnectionError,OpenAIConnectionError)) or status in (408,409,429) or (isinstance(status,int) and 500<=status<=599)

def call_with_provider_backoff(request,reserve):
    """One initial request plus at most three retries; reserve each HTTP attempt.

    Use exponential delays with additive jitter. Never retry before Retry-After;
    if that would exceed the wait limits, propagate for manual recovery.
    Retry connection/timeout errors, 408, 409, 429 and 5xx. Other failures and
    exhausted call/token budgets propagate immediately.
    """
    waited=0.0
    for retry in range(MAX_RETRIES+1):
        reserve()  # Budget errors are not HTTP failures and must never be retried.
        try:return request()
        except Exception as exc:
            if not retryable(exc) or retry==MAX_RETRIES:raise
            delay=BASE_DELAY*(2**retry)+random.uniform(0.0,0.25)
            suggested=retry_after(exc)
            if suggested is not None:delay=max(delay,suggested)
            if delay>MAX_DELAY or waited+delay>MAX_TOTAL_WAIT:raise
            time.sleep(delay)
            waited+=delay
