from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.research import sse, stream_research_response
from app.db.repository import Repository
from app.db.session import get_db
from app.models.schemas import AgentRequest

router = APIRouter()


@router.post("/run")
async def run_agent(body: AgentRequest, db: AsyncSession = Depends(get_db)):
    if not await Repository(db).get_project(body.project_id):
        raise HTTPException(status_code=404, detail="project not found")

    async def event_stream():
        async for item in stream_research_response(
            project_id=body.project_id,
            message=body.message,
            mode=body.mode,
        ):
            yield sse(item["event"], item["data"])

    return StreamingResponse(event_stream(), media_type="text/event-stream")
