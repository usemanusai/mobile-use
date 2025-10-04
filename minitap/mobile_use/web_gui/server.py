import asyncio
import os
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from minitap.mobile_use.web_gui.events import broadcaster
from minitap.mobile_use.sdk.agent import Agent
from minitap.mobile_use.sdk.builders import Builders
from minitap.mobile_use.utils.logger import get_logger
from minitap.mobile_use.config import settings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

logger = get_logger(__name__)

app = FastAPI(title="Mobile-Use Web GUI")

# Serve static assets (index.html, css, js)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class AgentManager:
    def __init__(self):
        self.agent: Agent | None = None
        self.lock = asyncio.Lock()
        self.status: str = "Initializing..."
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.worker: asyncio.Task | None = None

    async def ensure_agent(self):
        async with self.lock:
            if self.agent is None:
                # Build default config; GUI will manage tasks
                config = Builders.AgentConfig.build()
                self.agent = Agent(config=config)
                self.status = "Initializing..."
                try:
                    await asyncio.get_event_loop().run_in_executor(None, self.agent.init)
                    self.status = "Ready"
                    await broadcaster.publish({"type": "status", "status": self.status})
                except Exception as e:
                    self.status = "Error"
                    await broadcaster.publish({"type": "error", "message": str(e)})
                    raise

    async def start(self):
        await self.ensure_agent()
        if self.worker is None or self.worker.done():
            self.worker = asyncio.create_task(self._worker_loop())

    async def shutdown(self):
        # Graceful shutdown: stop worker and clean agent
        if self.worker and not self.worker.done():
            self.worker.cancel()
            try:
                await self.worker
            except asyncio.CancelledError:
                pass
        if self.agent:
            try:
                await asyncio.get_event_loop().run_in_executor(None, self.agent.clean)
            except Exception as e:
                logger.warning(f"Agent clean failed: {e}")
            self.agent = None
        self.status = "Stopped"
        await broadcaster.publish({"type": "status", "status": self.status})

    async def enqueue(self, goal: str, output_description: str | None):
        await self.ensure_agent()
        await self.queue.put({"goal": goal, "output_description": output_description})
        await broadcaster.publish({"type": "queued", "goal": goal})
        await broadcaster.publish({"type": "queue", "size": self.queue.qsize()})

    async def _worker_loop(self):
        while True:
            item = await self.queue.get()
            goal = item.get("goal")
            output_description = item.get("output_description")
            await broadcaster.publish({"type": "dequeued", "goal": goal})
            await broadcaster.publish({"type": "queue", "size": max(self.queue.qsize(), 0)})
            # Run the single task
            await self._run_task(goal=goal, output_description=output_description)
            self.queue.task_done()
            await broadcaster.publish({"type": "queue", "size": max(self.queue.qsize(), 0)})

    async def _run_task(self, goal: str, output_description: str | None) -> dict[str, Any]:
        assert self.agent is not None
        self.status = "Executing task"
        await broadcaster.publish({"type": "status", "status": self.status, "goal": goal})
        try:
            if output_description:
                result = await self.agent.run_task(goal=goal, output=output_description)
            else:
                result = await self.agent.run_task(goal=goal)
            self.status = "Waiting for next task"
            await broadcaster.publish({"type": "final", "result": result})
            await broadcaster.publish({"type": "status", "status": self.status})
            return {"ok": True, "result": result}
        except Exception as e:
            self.status = "Error"
            await broadcaster.publish({"type": "error", "message": str(e)})
            await broadcaster.publish({"type": "status", "status": self.status})
            return {"ok": False, "error": str(e)}


manager = AgentManager()
_last_enhance_call: float = 0.0


@app.on_event("startup")
async def on_startup():
    # Server should be ready before agent starts; warm status only
    port = int(os.getenv("WEB_GUI_PORT", "8086"))
    logger.info(f"Web GUI starting on port {port}")
    await broadcaster.publish({"type": "status", "status": "Initializing..."})
    await broadcaster.publish({"type": "queue", "size": 0})
    # Start the persistent worker loop
    await manager.start()


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/status")
async def api_status():
    return {"status": manager.status}


@app.get("/api/stream")
async def stream():
    async def event_generator():
        async for event in broadcaster.subscribe():
            yield event

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/history")
async def api_history():
    # Client stores history in localStorage by default; return empty list here
    return {"history": []}


@app.post("/api/clear-history")
async def api_clear_history():
    # Nothing persisted server-side for now
    return {"ok": True}


@app.post("/api/task")
async def api_task(req: Request):
    body = await req.json()
    goal = body.get("task") or body.get("goal")
    output_description = body.get("output_description")
    if not goal or not isinstance(goal, str):
        raise HTTPException(status_code=400, detail="Missing 'task' (string)")
    await broadcaster.publish({"type": "user_task", "text": goal})
    await manager.enqueue(goal=goal, output_description=output_description)
    return JSONResponse({"ok": True, "queued": True})


@app.post("/api/shutdown")
async def api_shutdown():
    await manager.shutdown()
    return {"ok": True}


@app.post("/api/enhance")
async def api_enhance(req: Request):
    global _last_enhance_call
    body = await req.json()
    text = body.get("text")
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Missing 'text' (string)")
    now = time.time()
    if now - _last_enhance_call < 3.0:
        raise HTTPException(status_code=429, detail="Enhance rate limit: wait a moment")
    _last_enhance_call = now
    sys_prompt = (
        "You are an expert at writing clear, specific instructions for mobile device automation. "
        "Rewrite the following vague or ambiguous task into a clear, step-by-step description optimized "
        "for a mobile automation agent. Be specific about app names, actions, and expected outcomes."
    )
    try:
        if not settings.OPEN_ROUTER_API_KEY:
            # Fallback: just echo back if no key
            return {"ok": True, "enhanced": text}
        llm = ChatOpenAI(
            model="qwen/qwen-2.5-coder:free",
            api_key=settings.OPEN_ROUTER_API_KEY.get_secret_value(),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.2,
        )
        msg = llm.invoke(
            [SystemMessage(content=sys_prompt), HumanMessage(content=f"Original task: {text}")]
        )
        enhanced = msg.content if isinstance(msg.content, str) else str(msg.content)
        return {"ok": True, "enhanced": enhanced}
    except Exception as e:
        logger.error(f"Enhance failed: {e}")
        return {"ok": False, "error": str(e), "enhanced": text}


def run():
    import uvicorn

    port = int(os.getenv("WEB_GUI_PORT", "8086"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
