import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, delete
from app.database import async_session, engine, Base
from app.models import Checkpoint


CHECKPOINTS = [
    {
        "name": "Cheng San Community Club",
        "latitude": 1.36766,
        "longitude": 103.85431,
        "target_radius": 50,
        "task_description": "Take a group photo with cheng san 5 pillars board at the foyer",
        "order_index": 1,
    },
    {
        "name": "Dragon Playground",
        "latitude": 1.36980,
        "longitude": 103.84943,
        "target_radius": 50,
        "task_description": "Take a group photo with the dragon playground at the background & Video of someone playing",
        "order_index": 2,
    },
    {
        "name": "AMK Town Centre",
        "latitude": 1.36939,
        "longitude": 103.84848,
        "target_radius": 50,
        "task_description": "Take a group photo of Heart AMK at the background",
        "order_index": 3,
    },
    {
        "name": "Masjid Al-Muttaqin",
        "latitude": 1.37052,
        "longitude": 103.84590,
        "target_radius": 50,
        "task_description": "Take a group photo with mosque at the background",
        "order_index": 4,
    },
    {
        "name": "Church of Christ the King",
        "latitude": 1.36199,
        "longitude": 103.85241,
        "target_radius": 50,
        "task_description": "Take a group photo with church at the background",
        "order_index": 5,
    },
    {
        "name": "ActiveSG Sport Park @ Teck Ghee",
        "latitude": 1.36320,
        "longitude": 103.84992,
        "target_radius": 50,
        "task_description": "Take a group photo with ActiveSG Sports Park at the background",
        "order_index": 6,
    },
    {
        "name": "Teck Ghee Court Market & Food Centre",
        "latitude": 1.36411,
        "longitude": 103.84824,
        "target_radius": 50,
        "task_description": "Take a group with your favourite stall",
        "order_index": 7,
    },
    {
        "name": "Kebun Baru Birdsinging Club",
        "latitude": 1.36720,
        "longitude": 103.83920,
        "target_radius": 50,
        "task_description": "Take a group photo with birdsinging club at the background",
        "order_index": 8,
    },
    {
        "name": "Kebun Baru Market & Food Centre",
        "latitude": 1.36681,
        "longitude": 103.83914,
        "target_radius": 50,
        "task_description": "Take a group with your favourite stall",
        "order_index": 9,
    },
    {
        "name": "Ang Mo Kio Joint Temple",
        "latitude": 1.37170,
        "longitude": 103.84640,
        "target_radius": 50,
        "task_description": "Take a group photo with temple at the background",
        "order_index": 10,
    },
    {
        "name": "Merlion",
        "latitude": 1.36478,
        "longitude": 103.84112,
        "target_radius": 50,
        "task_description": "Take a group photo with Merlion at the background",
        "order_index": 11,
    },
    {
        "name": "Ang Mo Kio Community Centre",
        "latitude": 1.36686,
        "longitude": 103.84069,
        "target_radius": 50,
        "task_description": "Finish Point! Must be back at 10.50am",
        "order_index": 12,
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await session.execute(delete(Checkpoint))
        for cp_data in CHECKPOINTS:
            session.add(Checkpoint(**cp_data))
        await session.commit()
        print(f"Seeded {len(CHECKPOINTS)} checkpoints.")


if __name__ == "__main__":
    asyncio.run(seed())
