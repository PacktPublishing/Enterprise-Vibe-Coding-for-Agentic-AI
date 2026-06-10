"""
app.py — Travel Agency multi-agent app with MAF Handoff orchestration.

Run:  python app.py
UI:   http://localhost:5001
"""

import sys
import os

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import json
import asyncio
import uuid
from queue import Queue, Empty

from flask import Flask, render_template, request, Response, jsonify

from agent_framework import WorkflowEvent
from agent_framework.orchestrations import HandoffBuilder, HandoffAgentUserRequest

from agents import triage, flights, hotels, _loop

app = Flask(__name__)

# Active workflow sessions
_sessions: dict = {}


# ── Workflow Factory ───────────────────────────────────────────────────

def _create_workflow():
    """Build a fresh Handoff workflow with 3 travel-agency agents."""
    return (
        HandoffBuilder(
            name="travel_agency",
            participants=[triage, flights, hotels],
        )
        .add_handoff(triage, [flights, hotels])
        .add_handoff(flights, [triage])
        .add_handoff(hotels, [triage])
        .with_start_agent(triage)
        .with_autonomous_mode(
            turn_limits={
                "triage_agent": 2,
                "flight_agent": 4,
                "hotel_agent": 3,
            }
        )
        .build()
    )


# ── Async Workflow Runner ──────────────────────────────────────────────

async def _run(session_id: str, message: str, q: Queue):
    """Execute one turn of the handoff workflow and push SSE events into *q*."""
    if session_id not in _sessions:
        _sessions[session_id] = {"workflow": _create_workflow(), "pending": []}
        q.put({"type": "info", "text": "Travel Agency agents initialized — processing your request..."})

    sess = _sessions[session_id]
    workflow = sess["workflow"]
    pending = sess["pending"]

    last_speaking_agent: list[str | None] = [None]
    initial_active_sent: list[bool] = [False]

    def _handle(event: WorkflowEvent):
        if event.type == "executor_invoked":
            if not initial_active_sent[0]:
                initial_active_sent[0] = True
                q.put({"type": "agent_active", "agent": event.executor_id})
                last_speaking_agent[0] = event.executor_id

        elif event.type == "handoff_sent":
            data = event.data
            source = getattr(data, "source", None)
            target = getattr(data, "target", None)
            if source and target:
                q.put({"type": "handoff", "from_agent": source, "to_agent": target})
                last_speaking_agent[0] = target
                print(f"  [handoff] {source} → {target}")

        elif event.type == "output":
            data = getattr(event, "data", None)
            if data is not None:
                text = getattr(data, "text", None) or ""
                agent = getattr(data, "author_name", None) or event.executor_id or last_speaking_agent[0] or ""
                if text.strip():
                    last_speaking_agent[0] = agent
                    q.put({"type": "agent_message", "agent": agent, "text": text})

        elif event.type == "request_info" and isinstance(event.data, HandoffAgentUserRequest):
            sess["pending"].append(event)
            agent = event.executor_id or last_speaking_agent[0]
            q.put({"type": "waiting_for_input", "agent": agent})

    if pending:
        responses = {
            r.request_id: HandoffAgentUserRequest.create_response(message)
            for r in pending
        }
        sess["pending"] = []
        async for ev in workflow.run(responses=responses, stream=True):
            _handle(ev)
        q.put({"type": "workflow_complete"})
    else:
        try:
            async for ev in workflow.run(message, stream=True):
                _handle(ev)
            q.put({"type": "workflow_complete"})
        except Exception as exc:
            import traceback
            traceback.print_exc()
            q.put({"type": "error", "text": str(exc)})
            return


async def _run_safe(session_id: str, message: str, q: Queue):
    """Wrapper that guarantees None sentinel is pushed to *q*."""
    try:
        await _run(session_id, message, q)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        q.put({"type": "error", "text": str(exc)})
    finally:
        q.put(None)


# ── Flask Routes ───────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not message:
        return jsonify(error="empty message"), 400

    q: Queue = Queue()
    asyncio.run_coroutine_threadsafe(_run_safe(session_id, message, q), _loop)

    def generate():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        while True:
            try:
                ev = q.get(timeout=180)
            except Empty:
                yield f"data: {json.dumps({'type': 'error', 'text': 'Timeout waiting for agent response'})}\n\n"
                break
            if ev is None:
                break
            yield f"data: {json.dumps(ev)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Travel Agency running at http://localhost:5001\n")
    app.run(debug=True, port=5001, threaded=True, use_reloader=False)
