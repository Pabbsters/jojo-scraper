"""Tests for feed module."""

from __future__ import annotations

import json
import time
from http.server import HTTPServer
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from feed import FeedHandler, start_feed_server


class _FakeSocket:
    """Minimal stand-in for a socket so BaseHTTPRequestHandler can write."""

    def __init__(self) -> None:
        self.output = BytesIO()

    def makefile(self, mode: str, buffering: int = -1) -> BytesIO:
        if "w" in mode:
            return self.output
        # For reading the request line
        return BytesIO(b"")


def _make_handler(path: str, db: object | None = None) -> tuple[FeedHandler, BytesIO]:
    """Create a FeedHandler for a fake GET request to *path*."""
    request_line = f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n"
    rfile = BytesIO(request_line.encode())
    wfile = BytesIO()

    # Temporarily set db on the class
    original_db = FeedHandler.db
    FeedHandler.db = db

    handler = FeedHandler.__new__(FeedHandler)
    handler.rfile = rfile
    handler.wfile = wfile
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.requestline = f"GET {path} HTTP/1.1"
    handler.request_version = "HTTP/1.1"
    handler.command = "GET"
    handler.path = path
    handler.headers = {}
    handler.close_connection = True

    handler.do_GET()

    FeedHandler.db = original_db
    wfile.seek(0)
    return handler, wfile


def _parse_response(wfile: BytesIO) -> tuple[int, dict]:
    """Extract status code and JSON body from raw HTTP response bytes."""
    raw = wfile.read().decode("utf-8", errors="replace")
    # Find the JSON body (after blank line)
    parts = raw.split("\r\n\r\n", 1)
    body_str = parts[1] if len(parts) > 1 else ""
    body = json.loads(body_str) if body_str.strip() else {}

    # Extract status from first line
    status_line = raw.split("\r\n", 1)[0]
    status_code = int(status_line.split(" ", 2)[1])
    return status_code, body


class TestFeedEndpoint:
    """Test /feed endpoint."""

    def test_returns_postings_with_default_since(self) -> None:
        mock_db = MagicMock()
        mock_db.get_feed_since.return_value = [
            {
                "posting_id": "1",
                "title": "Intern A",
                "track": "swe",
                "tier": "tier_1",
                "source_type": "direct",
                "matched_keyword": "software engineer",
                "key_skills": "python, distributed systems",
                "posted_at": "2026-04-13T10:00:00Z",
                "first_seen_at": 1713000000.0,
            },
            {
                "posting_id": "2",
                "title": "Intern B",
                "track": "ai_data",
                "tier": "tier_2",
                "source_type": "aggregator",
                "matched_keyword": "machine learning",
                "key_skills": "python, pytorch",
                "posted_at": "2026-04-12T09:00:00Z",
                "first_seen_at": 1713000300.0,
            },
        ]

        _, wfile = _make_handler("/feed", db=mock_db)
        status, body = _parse_response(wfile)

        assert status == 200
        assert len(body["postings"]) == 2
        assert "generated_at" in body
        assert body["postings"][0]["tier"] == "tier_1"
        assert body["postings"][0]["source_type"] == "direct"
        assert body["postings"][0]["matched_keyword"] == "software engineer"
        assert body["postings"][0]["key_skills"] == "python, distributed systems"
        assert body["postings"][0]["posted_at"] == "2026-04-13T10:00:00Z"
        assert body["postings"][0]["first_seen_at"] == 1713000000.0
        mock_db.get_feed_since.assert_called_once()

    def test_respects_since_query_param(self) -> None:
        mock_db = MagicMock()
        mock_db.get_feed_since.return_value = []

        ts = 1700000000.0
        _, wfile = _make_handler(f"/feed?since={ts}", db=mock_db)
        status, body = _parse_response(wfile)

        assert status == 200
        assert body["postings"] == []
        call_args = mock_db.get_feed_since.call_args[0]
        assert call_args[0] == ts

    def test_invalid_since_falls_back_to_24h(self) -> None:
        mock_db = MagicMock()
        mock_db.get_feed_since.return_value = []

        _, wfile = _make_handler("/feed?since=not_a_number", db=mock_db)
        status, body = _parse_response(wfile)

        assert status == 200
        call_args = mock_db.get_feed_since.call_args[0]
        assert call_args[0] < time.time()
        assert call_args[0] > time.time() - 86401

    def test_no_db_returns_500(self) -> None:
        _, wfile = _make_handler("/feed", db=None)
        status, body = _parse_response(wfile)

        assert status == 500
        assert "error" in body


class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_returns_ok(self) -> None:
        _, wfile = _make_handler("/health")
        status, body = _parse_response(wfile)

        assert status == 200
        assert body["status"] == "ok"


class TestNotFound:
    """Test unknown paths."""

    def test_unknown_path_returns_404(self) -> None:
        _, wfile = _make_handler("/unknown")
        raw = wfile.read().decode("utf-8", errors="replace")
        assert "404" in raw


class TestStartFeedServer:
    """Test server startup."""

    @patch("feed.threading.Thread")
    @patch("feed.HTTPServer")
    def test_starts_and_returns_server(self, mock_http_server: MagicMock, mock_thread: MagicMock) -> None:
        mock_db = MagicMock()
        mock_server = MagicMock(spec=HTTPServer)
        mock_http_server.return_value = mock_server

        server = start_feed_server(mock_db, port=0)  # port 0 = OS picks
        assert server is mock_server
        assert FeedHandler.db is mock_db
        mock_http_server.assert_called_once_with(("0.0.0.0", 0), FeedHandler)
        mock_thread.assert_called_once_with(target=mock_server.serve_forever, daemon=True)
        mock_thread.return_value.start.assert_called_once()
