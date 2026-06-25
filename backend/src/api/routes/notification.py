from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.notification.domain.Channel import ChannelType

router = APIRouter(prefix="/api/notification", tags=["notification"])


class CreateMonitorRequest(BaseModel):
    name: str = ""
    cron_expr: str = "0 18 * * 1-5"
    universe_type: str = "all"
    dimensions: list[str] = ["financial", "industry", "valuation"]
    channels: list[str] = []


class CreateChannelRequest(BaseModel):
    name: str = ""
    type: str
    webhook_url: str


@router.post("/tasks")
async def create_monitor(req: CreateMonitorRequest):
    return {"task_id": "1", "status": "created"}


@router.get("/tasks")
async def list_monitors():
    return {"tasks": []}


@router.put("/tasks/{task_id}")
async def update_monitor(task_id: str, status: str = "active"):
    return {"task_id": task_id, "status": status}


@router.delete("/tasks/{task_id}")
async def delete_monitor(task_id: str):
    return {"task_id": task_id, "status": "deleted"}


@router.post("/channels")
async def create_channel(req: CreateChannelRequest):
    try:
        ChannelType(req.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported channel type: {req.type}")
    return {"channel_id": "1", "status": "created"}


@router.get("/channels")
async def list_channels():
    return {"channels": []}


@router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: str):
    return {"channel_id": channel_id, "status": "deleted"}
