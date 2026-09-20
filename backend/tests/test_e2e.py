"""
End-to-end integration test verifying the ASGI server, HTTP routes, and SSE streaming pipeline.
"""

import asyncio
import json
import unittest
from backend.app.main import app


class TestE2EIntegration(unittest.TestCase):

    def test_asgi_health_and_base_resume(self):
        """Tests health and base resume routes via direct ASGI invocation."""
        async def run_calls():
            # Test /api/health
            received_messages = []
            async def send_health(msg):
                received_messages.append(msg)

            scope_health = {
                "type": "http",
                "method": "GET",
                "path": "/api/health",
                "headers": [],
            }
            async def receive_dummy():
                return {"type": "http.request", "body": b"", "more_body": False}

            await app(scope_health, receive_dummy, send_health)
            status_msg = next(m for m in received_messages if m["type"] == "http.response.start")
            body_msg = next(m for m in received_messages if m["type"] == "http.response.body")
            self.assertEqual(status_msg["status"], 200)
            data = json.loads(body_msg["body"].decode("utf-8"))
            self.assertEqual(data["status"], "healthy")

            # Test /api/resume/base
            received_res = []
            async def send_res(msg):
                received_res.append(msg)

            scope_res = {
                "type": "http",
                "method": "GET",
                "path": "/api/resume/base",
                "headers": [],
            }
            await app(scope_res, receive_dummy, send_res)
            res_status = next(m for m in received_res if m["type"] == "http.response.start")
            res_body = next(m for m in received_res if m["type"] == "http.response.body")
            self.assertEqual(res_status["status"], 200)
            resume_data = json.loads(res_body["body"].decode("utf-8"))
            self.assertIn("name", resume_data)
            self.assertIn("experience", resume_data)

            # Test /api/generate/stream SSE
            received_stream = []
            async def send_stream(msg):
                received_stream.append(msg)

            payload = json.dumps({
                "job_input": {
                    "job_description": "We need a Senior Angular Architect experienced with Nx and TypeScript."
                },
                "llm_config": {"provider": "heuristic"},
                "template_id": "modern"
            }).encode("utf-8")

            async def receive_stream():
                return {"type": "http.request", "body": payload, "more_body": False}

            scope_stream = {
                "type": "http",
                "method": "POST",
                "path": "/api/generate/stream",
                "headers": [(b"content-type", b"application/json")],
            }
            await app(scope_stream, receive_stream, send_stream)
            stream_start = next(m for m in received_stream if m["type"] == "http.response.start")
            self.assertEqual(stream_start["status"], 200)
            
            # Check for SSE data
            chunks = [m.get("body", b"").decode("utf-8") for m in received_stream if m["type"] == "http.response.body"]
            full_stream = "".join(chunks)
            self.assertIn("event: step", full_stream)
            self.assertIn("event: thought", full_stream)
            self.assertIn("event: complete", full_stream)

        asyncio.run(run_calls())


if __name__ == "__main__":
    unittest.main()
