import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Team, Checkpoint, Submission, LiveTelemetry, RaceStatus
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.schemas.checkpoint import CheckpointCreate, CheckpointUpdate, CheckpointResponse
from app.services.race_master import start_race, pause_race, resume_race, adjust_score, advance_team, reset_race, end_race
from app.services.event_bus import bus
from app.services.telegram_service import broadcast_all, send_message, send_photo, send_animation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/race/start")
async def api_start_race(db: AsyncSession = Depends(get_db)):
    return await start_race(db)


@router.post("/race/pause")
async def api_pause_race(db: AsyncSession = Depends(get_db)):
    return await pause_race(db)


@router.post("/race/resume")
async def api_resume_race(db: AsyncSession = Depends(get_db)):
    return await resume_race(db)


@router.post("/race/reset")
async def api_reset_race(db: AsyncSession = Depends(get_db)):
    return await reset_race(db)


@router.post("/race/end")
async def api_end_race(db: AsyncSession = Depends(get_db)):
    return await end_race(db)


@router.get("/race/status")
async def api_race_status():
    status = bus.get_race_state("status")
    started_at = bus.get_race_state("started_at")
    return {"status": status, "started_at": started_at}


@router.post("/teams")
async def create_team(data: TeamCreate, db: AsyncSession = Depends(get_db)):
    team = Team(chat_id=data.chat_id, team_name=data.team_name)
    db.add(team)
    await db.flush()
    return TeamResponse.model_validate(team)


@router.get("/teams")
async def list_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    return [TeamResponse.model_validate(t) for t in result.scalars().all()]


@router.get("/teams/{chat_id}")
async def get_team(chat_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.chat_id == chat_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.model_validate(team)


@router.put("/teams/{chat_id}")
async def update_team(chat_id: int, data: TeamUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.chat_id == chat_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    await db.flush()
    return TeamResponse.model_validate(team)


@router.post("/teams/{chat_id}/score")
async def team_adjust_score(chat_id: int, delta: int, db: AsyncSession = Depends(get_db)):
    return await adjust_score(db, chat_id, delta)


@router.post("/teams/{chat_id}/advance")
async def team_advance(chat_id: int, db: AsyncSession = Depends(get_db)):
    return await advance_team(db, chat_id)


@router.post("/teams/{chat_id}/register")
async def register_team_group(chat_id: int, team_name: str, db: AsyncSession = Depends(get_db)):
    from app.models import Team
    result = await db.execute(select(Team).where(Team.chat_id == chat_id))
    team = result.scalar_one_or_none()
    if team:
        raise HTTPException(status_code=400, detail="Team already registered")
    team = Team(chat_id=chat_id, team_name=team_name)
    db.add(team)
    await db.flush()
    return TeamResponse.model_validate(team)


@router.post("/broadcast")
async def broadcast_message(message: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team.chat_id))
    chat_ids = [row[0] for row in result.all()]
    await broadcast_all(chat_ids, message)
    return {"sent_to": len(chat_ids)}


@router.post("/send-message")
async def send_message_endpoint(
    message: str = Form(""),
    chat_id: int = Form(0),
    file: UploadFile | None = None,
    db: AsyncSession = Depends(get_db),
):
    if chat_id:
        targets = [chat_id]
    else:
        result = await db.execute(select(Team.chat_id))
        targets = [row[0] for row in result.all()]

    file_bytes = None
    filename = None
    if file:
        file_bytes = await file.read()
        filename = file.filename

    for cid in targets:
        try:
            if file_bytes:
                if file.content_type == "image/gif":
                    await send_animation(cid, file_bytes, filename, caption=message or None)
                else:
                    await send_photo(cid, file_bytes, filename, caption=message or None)
            else:
                await send_message(cid, message)
        except Exception as e:
            logger.error(f"Failed to send to {cid}: {e}")

    return {"sent_to": len(targets), "success": True}


@router.post("/checkpoints")
async def create_checkpoint(data: CheckpointCreate, db: AsyncSession = Depends(get_db)):
    cp = Checkpoint(**data.model_dump())
    db.add(cp)
    await db.flush()
    return CheckpointResponse.model_validate(cp)


@router.get("/checkpoints")
async def list_checkpoints(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Checkpoint).order_by(Checkpoint.order_index))
    return [CheckpointResponse.model_validate(c) for c in result.scalars().all()]


@router.put("/checkpoints/{checkpoint_id}")
async def update_checkpoint(checkpoint_id: int, data: CheckpointUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Checkpoint).where(Checkpoint.checkpoint_id == checkpoint_id))
    cp = result.scalar_one_or_none()
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cp, field, value)
    await db.flush()
    return CheckpointResponse.model_validate(cp)


@router.delete("/checkpoints/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Checkpoint).where(Checkpoint.checkpoint_id == checkpoint_id))
    cp = result.scalar_one_or_none()
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    await db.delete(cp)
    return {"deleted": checkpoint_id}


@router.get("/submissions")
async def list_submissions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Submission)
        .order_by(Submission.timestamp.desc())
        .limit(200)
    )
    return result.scalars().all()


@router.get("/telemetry")
async def list_telemetry(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LiveTelemetry)
        .order_by(LiveTelemetry.timestamp.desc())
        .limit(500)
    )
    return result.scalars().all()


@router.get("/leaderboard")
async def get_leaderboard(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Team)
        .where(Team.status != RaceStatus.NOT_STARTED.value)
        .order_by(Team.score.desc())
    )
    return [TeamResponse.model_validate(t) for t in result.scalars().all()]


@router.get("/events/stream")
async def event_stream():
    import asyncio
    import json
    from fastapi.responses import StreamingResponse

    async def generate():
        tracking_queue = await bus.subscribe("race_tracking")
        events_queue = await bus.subscribe("race_events")
        try:
            while True:
                done, _ = await asyncio.wait(
                    [
                        asyncio.create_task(tracking_queue.get()),
                        asyncio.create_task(events_queue.get()),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    data = json.loads(task.result())
                    yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe("race_tracking", tracking_queue)
            bus.unsubscribe("race_events", events_queue)

    return StreamingResponse(generate(), media_type="text/event-stream")


IMAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "checkpoint_images"


@router.get("/checkpoints/{checkpoint_id}/image")
async def get_checkpoint_image(checkpoint_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Checkpoint).where(Checkpoint.checkpoint_id == checkpoint_id))
    cp = result.scalar_one_or_none()
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    prefix = f"{cp.order_index:02d}_"
    for img_path in IMAGE_DIR.iterdir():
        if img_path.name.startswith(prefix):
            return FileResponse(str(img_path))

    raise HTTPException(status_code=404, detail="No image for this checkpoint")


@router.get("/teams/{chat_id}/progress")
async def get_team_progress(chat_id: int, db: AsyncSession = Depends(get_db)):
    team_result = await db.execute(select(Team).where(Team.chat_id == chat_id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    completed = await db.execute(
        select(Submission.checkpoint_id).where(
            Submission.team_id == chat_id,
            Submission.status == "correct",
        )
    )
    completed_ids = set(row[0] for row in completed.all())

    return {
        "chat_id": chat_id,
        "team_name": team.team_name,
        "score": team.score,
        "status": team.status,
        "completed_checkpoints": list(completed_ids),
    }


@router.get("/progress/all")
async def get_all_progress(db: AsyncSession = Depends(get_db)):
    teams_result = await db.execute(select(Team))
    teams = teams_result.scalars().all()

    result = []
    for team in teams:
        completed = await db.execute(
            select(Submission.checkpoint_id).where(
                Submission.team_id == team.chat_id,
                Submission.status == "correct",
            )
        )
        completed_ids = list(row[0] for row in completed.all())
        result.append({
            "chat_id": team.chat_id,
            "team_name": team.team_name,
            "score": team.score,
            "status": team.status,
            "completed_checkpoints": completed_ids,
        })

    return result


@router.get("/teams/{chat_id}/submissions")
async def get_team_submissions(chat_id: int, db: AsyncSession = Depends(get_db)):
    team_result = await db.execute(select(Team).where(Team.chat_id == chat_id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    sub_result = await db.execute(
        select(Submission)
        .where(Submission.team_id == chat_id, Submission.status == "correct")
        .order_by(Submission.timestamp.asc())
    )
    submissions = sub_result.scalars().all()

    cp_result = await db.execute(select(Checkpoint).order_by(Checkpoint.order_index))
    checkpoints = {cp.checkpoint_id: cp for cp in cp_result.scalars().all()}

    return {
        "chat_id": chat_id,
        "team_name": team.team_name,
        "submissions": [
            {
                "sub_id": s.sub_id,
                "checkpoint_id": s.checkpoint_id,
                "checkpoint_name": checkpoints.get(s.checkpoint_id, Checkpoint()).name,
                "checkpoint_order": checkpoints.get(s.checkpoint_id, Checkpoint()).order_index or 0,
                "task_description": checkpoints.get(s.checkpoint_id, Checkpoint()).task_description,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                "has_image": s.image_path is not None,
            }
            for s in submissions
        ],
    }


@router.get("/submissions/{sub_id}/image")
async def get_submission_image(sub_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Submission).where(Submission.sub_id == sub_id))
    sub = result.scalar_one_or_none()
    if not sub or not sub.image_path:
        raise HTTPException(status_code=404, detail="Image not found")

    img_file = Path(__file__).resolve().parent.parent.parent.parent / sub.image_path
    if not img_file.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(str(img_file))