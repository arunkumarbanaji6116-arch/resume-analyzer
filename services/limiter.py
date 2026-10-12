"""
Rate Limiting Extension for CareerForge AI
Protects API endpoints, authentication routes, and AI synthesis calls against brute-force,
credential stuffing, and denial-of-service (DoS) attacks.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per minute", "3000 per hour"],
    storage_uri="memory://",
    strategy="fixed-window",
)
