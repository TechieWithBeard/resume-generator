"""
ASGI Application Server for AI-Powered Resume Generator.
Provides high-performance async endpoints, CORS handling, and real-time SSE streaming.
Engineered to run natively on Uvicorn with zero brittle external framework dependencies.
"""

import asyncio
import json
import os
import urllib.parse
from typing import Any, Dict

from backend.app.models.resume import (
    JobInput,
    LLMConfig,
    RenderRequest,
    ResumeData,
    StreamRequest,
)
from backend.app.services.generator_chain import generator_chain
from backend.app.services.linkedin_extractor import linkedin_extractor
from backend.app.services.resume_store import resume_store
from backend.app.services.template_engine import template_engine


async def read_body(receive) -> bytes:
    """Reads complete ASGI request body."""
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body

Tuple_Response = tuple[int, list[tuple[bytes, bytes]], bytes]


def send_json(data: Any, status: int = 200) -> Tuple_Response:
    """Helper to prepare JSON response headers and body."""
    body_bytes = json.dumps(data).encode("utf-8")
    headers = [
        (b"content-type", b"application/json; charset=utf-8"),
        (b"content-length", str(len(body_bytes)).encode("ascii")),
        (b"access-control-allow-origin", b"*"),
        (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS"),
        (b"access-control-allow-headers", b"*"),
    ]
    return status, headers, body_bytes


def send_html(html_str: str, status: int = 200) -> Tuple_Response:
    """Helper to prepare HTML response."""
    body_bytes = html_str.encode("utf-8")
    headers = [
        (b"content-type", b"text/html; charset=utf-8"),
        (b"content-length", str(len(body_bytes)).encode("ascii")),
        (b"access-control-allow-origin", b"*"),
    ]
    return status, headers, body_bytes


async def app(scope, receive, send):
    """Main ASGI application handler."""
    if scope["type"] != "http":
        return

    path = scope.get("path", "")
    method = scope.get("method", "GET").upper()

    # Handle CORS preflight
    if method == "OPTIONS":
        headers = [
            (b"access-control-allow-origin", b"*"),
            (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS"),
            (b"access-control-allow-headers", b"*"),
            (b"content-length", b"0"),
        ]
        await send({"type": "http.response.start", "status": 204, "headers": headers})
        await send({"type": "http.response.body", "body": b""})
        return

    # Route: GET /api/health
    if path == "/api/health" and method == "GET":
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        status, headers, body = send_json({
            "status": "healthy",
            "server": "AI Resume Generator ASGI Engine",
            "version": "1.0.0",
            "providers": {
                "ollama": "available (local default http://localhost:11434)",
                "openai": "available" if has_openai else "unconfigured (provide key)",
                "heuristic": "active (high-precision zero-config engine)",
            },
        })
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: GET /api/resume/base
    if path == "/api/resume/base" and method == "GET":
        base_res = resume_store.get_base_resume()
        status, headers, body = send_json(base_res.model_dump())
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: PUT /api/resume/base
    if path == "/api/resume/base" and method == "PUT":
        raw = await read_body(receive)
        data = json.loads(raw.decode("utf-8"))
        res_model = ResumeData.model_validate(data)
        saved = resume_store.save_base_resume(res_model)
        status, headers, body = send_json(saved.model_dump())
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: POST /api/resume/reset
    if path == "/api/resume/reset" and method == "POST":
        res_model = resume_store.reset_to_default()
        status, headers, body = send_json(res_model.model_dump())
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: GET /api/templates
    if path == "/api/templates" and method == "GET":
        status, headers, body = send_json(template_engine.list_templates())
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: POST /api/render
    if path == "/api/render" and method == "POST":
        raw = await read_body(receive)
        data = json.loads(raw.decode("utf-8"))
        req = RenderRequest.model_validate(data)
        html = template_engine.render(
            req.resume,
            template_id=req.template_id,
            highlight_diff=req.highlight_diff,
            base_resume=req.base_resume,
        )
        status, headers, body = send_html(html)
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: POST /api/extract/linkedin
    if path == "/api/extract/linkedin" and method == "POST":
        raw = await read_body(receive)
        data = json.loads(raw.decode("utf-8"))
        url = data.get("url", "")
        result = linkedin_extractor.extract_from_url(url)
        status, headers, body = send_json(result)
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: POST /api/generate/stream (Server-Sent Events)
    if path == "/api/generate/stream" and method == "POST":
        raw = await read_body(receive)
        data = json.loads(raw.decode("utf-8"))
        stream_req = StreamRequest.model_validate(data)

        base_res = stream_req.base_resume or resume_store.get_base_resume()
        cfg = stream_req.llm_config or LLMConfig()
        tmpl_id = stream_req.template_id or "modern"

        # Begin SSE stream
        sse_headers = [
            (b"content-type", b"text/event-stream; charset=utf-8"),
            (b"cache-control", b"no-cache"),
            (b"connection", b"keep-alive"),
            (b"access-control-allow-origin", b"*"),
            (b"x-accel-buffering", b"no"),
        ]
        await send({"type": "http.response.start", "status": 200, "headers": sse_headers})

        try:
            async for event in generator_chain.generate_stream(
                job_input=stream_req.job_input,
                base_resume=base_res,
                config=cfg,
                template_id=tmpl_id,
            ):
                event_type = event.get("type", "message")
                payload = f"event: {event_type}\ndata: {json.dumps(event)}\n\n"
                await send({
                    "type": "http.response.body",
                    "body": payload.encode("utf-8"),
                    "more_body": True,
                })
        except Exception as err:
            err_payload = f"event: error\ndata: {json.dumps({'error': str(err)})}\n\n"
            await send({
                "type": "http.response.body",
                "body": err_payload.encode("utf-8"),
                "more_body": True,
            })

        # Terminate SSE stream
        await send({"type": "http.response.body", "body": b"", "more_body": False})
        return

    # Static file serving for Angular frontend
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist", "frontend", "browser"))
    if not path.startswith("/api") and os.path.isdir(dist_dir):
        clean_path = path.lstrip("/") or "index.html"
        file_path = os.path.join(dist_dir, clean_path)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(dist_dir, "index.html")

        if os.path.exists(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                ".html": "text/html; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".mjs": "application/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".ico": "image/x-icon",
                ".svg": "image/svg+xml",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".woff2": "font/woff2",
            }
            content_type = mime_types.get(ext, "application/octet-stream")
            with open(file_path, "rb") as f:
                content = f.read()

            headers = [
                (b"content-type", content_type.encode("ascii")),
                (b"content-length", str(len(content)).encode("ascii")),
                (b"access-control-allow-origin", b"*"),
            ]
            await send({"type": "http.response.start", "status": 200, "headers": headers})
            await send({"type": "http.response.body", "body": content})
            return

    # 404 Fallback
    status, headers, body = send_json({"error": "Not Found", "path": path}, status=404)
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


# Optional FastAPI wrapper if FastAPI is available
try:
    from fastapi import FastAPI
    fastapi_app = FastAPI(title="AI Resume Generator")
except ImportError:
    fastapi_app = None
