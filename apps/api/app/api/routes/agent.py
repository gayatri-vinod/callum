from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agents.research import sse, stream_research_response
from app.db.store import store
from app.models.schemas import AgentRequest

router = APIRouter()


@router.post("/run")
async def run_agent(body: AgentRequest):
    if not store.get_project(body.project_id):
        raise HTTPException(status_code=404, detail="project not found")

    async def event_stream():
        async for item in stream_research_response(
            project_id=body.project_id,
            message=body.message,
            mode=body.mode,
        ):
            yield sse(item["event"], item["data"])

    return StreamingResponse(event_stream(), media_type="text/event-stream")
