from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Team, Checkpoint, RaceStatus
from app.services.event_bus import bus


async def start_race(session: AsyncSession) -> dict:
    bus.set_race_state("status", RaceStatus.IN_PROGRESS.value)

    first_cp_result = await session.execute(
        select(Checkpoint).order_by(Checkpoint.order_index.asc()).limit(1)
    )
    first_cp = first_cp_result.scalar_one_or_none()

    teams_result = await session.execute(select(Team))
    teams = teams_result.scalars().all()

    started_teams = []
    for team in teams:
        team.status = RaceStatus.IN_PROGRESS.value
        if first_cp:
            team.current_checkpoint_id = first_cp.checkpoint_id
        started_teams.append(team.chat_id)

    bus.set_race_state("started_at", datetime.utcnow().isoformat())

    await bus.publish_event("race_started", {
        "teams": started_teams,
        "first_checkpoint": first_cp.name if first_cp else None,
    })

    return {
        "action": "race_started",
        "teams": started_teams,
        "first_checkpoint": first_cp.name if first_cp else None,
    }


async def pause_race(session: AsyncSession) -> dict:
    bus.set_race_state("status", RaceStatus.PAUSED.value)

    result = await session.execute(select(Team))
    teams = result.scalars().all()
    for team in teams:
        if team.status == RaceStatus.IN_PROGRESS.value:
            team.status = RaceStatus.PAUSED.value

    await bus.publish_event("race_paused", {})
    return {"action": "race_paused"}


async def resume_race(session: AsyncSession) -> dict:
    bus.set_race_state("status", RaceStatus.IN_PROGRESS.value)

    result = await session.execute(select(Team))
    teams = result.scalars().all()
    for team in teams:
        if team.status == RaceStatus.PAUSED.value:
            team.status = RaceStatus.IN_PROGRESS.value

    await bus.publish_event("race_resumed", {})
    return {"action": "race_resumed"}


async def adjust_score(session: AsyncSession, chat_id: int, delta: int) -> dict:
    result = await session.execute(select(Team).where(Team.chat_id == chat_id))
    team = result.scalar_one_or_none()
    if not team:
        return {"action": "error", "reason": "team_not_found"}

    team.score += delta

    await bus.publish_event("score_adjusted", {
        "chat_id": chat_id,
        "team_name": team.team_name,
        "new_score": team.score,
        "delta": delta,
    })
    return {"action": "score_adjusted", "new_score": team.score}


async def advance_team(session: AsyncSession, chat_id: int) -> dict:
    result = await session.execute(select(Team).where(Team.chat_id == chat_id))
    team = result.scalar_one_or_none()
    if not team:
        return {"action": "error", "reason": "team_not_found"}

    if team.current_checkpoint_id is None:
        return {"action": "error", "reason": "already_completed"}

    next_result = await session.execute(
        select(Checkpoint)
        .where(
            Checkpoint.order_index > select(Checkpoint.order_index)
            .where(Checkpoint.checkpoint_id == team.current_checkpoint_id)
            .scalar_subquery()
        )
        .order_by(Checkpoint.order_index.asc())
        .limit(1)
    )
    next_cp = next_result.scalar_one_or_none()

    if next_cp is None:
        team.status = RaceStatus.COMPLETED.value
        team.current_checkpoint_id = None
        team.score += 100
        return {"action": "team_completed", "team_name": team.team_name, "score": team.score}

    team.current_checkpoint_id = next_cp.checkpoint_id
    return {
        "action": "team_advanced",
        "team_name": team.team_name,
        "checkpoint_id": next_cp.checkpoint_id,
        "checkpoint_name": next_cp.name,
    }


async def reset_race(session: AsyncSession) -> dict:
    bus.set_race_state("status", RaceStatus.NOT_STARTED.value)

    from app.models import Submission
    await session.execute(Submission.__table__.delete())

    result = await session.execute(select(Team))
    teams = result.scalars().all()
    for team in teams:
        team.status = RaceStatus.NOT_STARTED.value
        team.score = 0
        team.current_checkpoint_id = None

    bus.set_race_state("started_at", None)

    await bus.publish_event("race_reset", {})
    return {"action": "race_reset"}


async def end_race(session: AsyncSession) -> dict:
    bus.set_race_state("status", RaceStatus.COMPLETED.value)

    result = await session.execute(select(Team))
    teams = result.scalars().all()
    for team in teams:
        if team.status in (RaceStatus.IN_PROGRESS.value, RaceStatus.PAUSED.value):
            team.status = RaceStatus.COMPLETED.value

    await bus.publish_event("race_ended", {})
    return {"action": "race_ended"}
