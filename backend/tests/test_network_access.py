from __future__ import annotations
import re
import pytest
from app.core.config import settings

@pytest.mark.parametrize("origin", [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.29.217:5173",
    "http://192.168.29.220:5173",
    "http://10.0.0.12:5173",
])
def test_frontend_origins_match_configured_cors_regex(origin: str):
    assert re.fullmatch(settings.cors_origin_regex, origin)

def test_public_origin_does_not_match_private_network_cors_regex():
    assert not re.fullmatch(settings.cors_origin_regex, "https://example.com:5173")
