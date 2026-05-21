import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import webhook, admin
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Heritage Trail Race Engine...")

    from app.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.services.telegram_service import bot
    try:
        if settings.telegram_webhook_url:
            await bot.set_webhook(settings.telegram_webhook_url)
            logger.info(f"Telegram webhook set to {settings.telegram_webhook_url}")
    except Exception as e:
        logger.warning(f"Could not set webhook: {e}")

    yield

    from app.services.telegram_service import bot
    try:
        await bot.delete_webhook()
    except Exception:
        pass
    await bot.session.close()
    logger.info("Heritage Trail Race Engine stopped.")


app = FastAPI(
    title="Heritage Trail Race Engine",
    description="Amazing Race event platform backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(admin.router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="dashboard")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "heritage_trail_engine"}
