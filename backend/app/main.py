"""
ASGI Application Server for AI-Powered Resume Generator.
Provides high-performance async endpoints, CORS handling, and real-time SSE streaming.
Engineered to run natively on Uvicorn with zero brittle external framework dependencies.
"""

import asyncio
import base64
import email
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
    TemplateConfig,
)
from backend.app.services.generator_chain import generator_chain
from backend.app.services.linkedin_extractor import linkedin_extractor
from backend.app.services.resume_parser import resume_parser
from backend.app.services.resume_score_checker import resume_score_checker
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

    # Route: POST /api/resume/upload (Ingests PDF, DOCX, TXT, MD, JSON resumes)
    if path == "/api/resume/upload" and method == "POST":
        raw = await read_body(receive)
        headers_dict = {k.lower(): v for k, v in scope.get("headers", [])}
        ct = headers_dict.get(b"content-type", b"").decode("latin-1")

        file_bytes = b""
        filename = "uploaded_resume.txt"
        auto_save = False
        llm_config = LLMConfig(provider="auto")

        if "multipart/form-data" in ct:
            try:
                raw_header = f"Content-Type: {ct}\r\n\r\n".encode("latin-1")
                msg = email.message_from_bytes(raw_header + raw)
                for part in msg.walk():
                    fn = part.get_filename()
                    if fn:
                        filename = fn
                        file_bytes = part.get_payload(decode=True) or b""
                        break
                    if part.get_param("name", header="content-disposition") == "save":
                        auto_save = (part.get_payload(decode=True) or b"").decode("utf-8").lower() in ("true", "1")
            except Exception as e:
                status, headers, body = send_json({"success": False, "error": f"Failed to parse multipart upload: {e}"}, status=400)
                await send({"type": "http.response.start", "status": status, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return
        else:
            try:
                data = json.loads(raw.decode("utf-8"))
                filename = data.get("filename", "resume.txt")
                auto_save = bool(data.get("save", False))
                llm_cfg_data = data.get("llm_config")
                if llm_cfg_data:
                    llm_config = LLMConfig.model_validate(llm_cfg_data)

                if "file_data" in data and data["file_data"]:
                    b64_str = str(data["file_data"])
                    if "," in b64_str:
                        b64_str = b64_str.split(",", 1)[1]
                    file_bytes = base64.b64decode(b64_str)
                elif "raw_text" in data and data["raw_text"]:
                    file_bytes = str(data["raw_text"]).encode("utf-8")
            except Exception as e:
                status, headers, body = send_json({"success": False, "error": f"Failed to decode upload payload: {e}"}, status=400)
                await send({"type": "http.response.start", "status": status, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return

        if not file_bytes:
            status, headers, body = send_json({"success": False, "error": "No file content or data received."}, status=400)
            await send({"type": "http.response.start", "status": status, "headers": headers})
            await send({"type": "http.response.body", "body": body})
            return

        try:
            parsed_resume, metadata = await resume_parser.parse_resume(file_bytes, filename, config=llm_config)
            if auto_save:
                resume_store.save_base_resume(parsed_resume)
                metadata["saved_as_base"] = True

            status, headers, body = send_json({
                "success": True,
                "resume": parsed_resume.model_dump(),
                "metadata": metadata,
            })
        except Exception as err:
            status, headers, body = send_json({
                "success": False,
                "error": f"Extraction error: {str(err)}",
            }, status=422)

        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: GET /api/templates
    if path == "/api/templates" and method == "GET":
        status, headers, body = send_json(template_engine.list_templates())
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: GET /api/template/config
    if path == "/api/template/config" and method == "GET":
        cfg = resume_store.get_template_config()
        status, headers, body = send_json(cfg.model_dump())
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: PUT /api/template/config
    if path == "/api/template/config" and method == "PUT":
        raw = await read_body(receive)
        data = json.loads(raw.decode("utf-8"))
        cfg = TemplateConfig.model_validate(data)
        saved = resume_store.save_template_config(cfg)
        status, headers, body = send_json(saved.model_dump())
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
            config=req.template_config,
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

    # Route: GET /api/evals/cases
    if path == "/api/evals/cases" and method == "GET":
        from backend.app.evals import BENCHMARK_DATASET
        cases_meta = [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "document_type": c.document_type,
                "target_title": c.job_input.target_title,
                "tags": c.tags,
                "minimum_match_score": c.minimum_match_score,
            }
            for c in BENCHMARK_DATASET
        ]
        status, headers, body = send_json({"cases": cases_meta, "total": len(cases_meta)})
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: POST /api/evals/run
    if path == "/api/evals/run" and method == "POST":
        from backend.app.evals import BENCHMARK_DATASET, evaluator
        raw = await read_body(receive)
        case_id = None
        provider = "heuristic"
        if raw:
            try:
                data = json.loads(raw.decode("utf-8"))
                case_id = data.get("case_id")
                provider = data.get("provider", "heuristic")
            except Exception:
                pass

        cases = BENCHMARK_DATASET
        if case_id:
            cases = [c for c in BENCHMARK_DATASET if c.id == case_id]

        report = await evaluator.evaluate_suite(
            cases=cases,
            config=LLMConfig(provider=provider),
        )
        status, headers, body = send_json(report.model_dump())
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: GET /api/evals/latest
    if path == "/api/evals/latest" and method == "GET":
        from backend.app.evals import evaluator
        report = evaluator.latest_report
        if report:
            status, headers, body = send_json(report.model_dump())
        else:
            status, headers, body = send_json({"message": "No evaluation run recorded yet. POST /api/evals/run to execute."}, status=404)
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: GET /api/resume/score (Audit Base Profile)
    if path == "/api/resume/score" and method == "GET":
        base = resume_store.get_base_resume()
        html = template_engine.render(base)
        score_report = resume_score_checker.audit(
            base, rendered_html=html, target_role="Senior Frontend Engineer"
        )
        status, headers, body = send_json(score_report)
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    # Route: POST /api/resume/score (Audit Tailored Profile or Custom Payload)
    if path == "/api/resume/score" and method == "POST":
        try:
            raw_body = await read_body(receive)
            data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception:
            data = {}

        if "resume" in data and data["resume"]:
            resume_obj = ResumeData.model_validate(data["resume"])
        else:
            resume_obj = resume_store.get_base_resume()

        target_role = data.get("target_role") or getattr(resume_obj, "target_role", None)
        job_desc = data.get("job_description")
        tmpl_id = data.get("template_id", "modern")

        html = template_engine.render(resume_obj, template_id=tmpl_id)
        score_report = resume_score_checker.audit(
            resume_obj,
            rendered_html=html,
            target_role=target_role,
            job_description=job_desc,
        )
        status, headers, body = send_json(score_report)
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
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
