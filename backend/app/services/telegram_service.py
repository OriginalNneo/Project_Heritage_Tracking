from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.config import get_settings

settings = get_settings()
bot = Bot(token=settings.telegram_bot_token)


async def send_message(chat_id: int, text: str, parse_mode: str = "HTML") -> None:
    await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


async def send_checkpoint_riddle(chat_id: int, checkpoint_name: str, riddle: str | None, hint: str | None) -> None:
    parts = [f"<b>Checkpoint: {checkpoint_name}</b>\n"]
    if riddle:
        parts.append(f"<i>Riddle:</i>\n{riddle}\n")
    if hint:
        parts.append(f"<i>Hint:</i> {hint}")
    parts.append("\nReply with your answer or share your live location to check in!")
    await send_message(chat_id, "".join(parts))


async def send_congratulation(chat_id: int, checkpoint_name: str) -> None:
    await send_message(
        chat_id,
        f"<b>You found it!</b> {checkpoint_name} is the correct location.\n"
        "Moving to the next checkpoint...",
    )


async def send_race_complete(chat_id: int, score: int) -> None:
    await send_message(
        chat_id,
        f"<b>Congratulations!</b> Your team has completed the race!\n"
        f"Final score: <b>{score}</b> points",
    )


async def send_wrong_answer(chat_id: int, hint: str | None = None) -> None:
    msg = "That's not the right answer. Try again!"
    if hint:
        msg += f"\n<i>Hint:</i> {hint}"
    await send_message(chat_id, msg)


async def broadcast_all(chat_ids: list[int], text: str) -> None:
    for chat_id in chat_ids:
        try:
            await send_message(chat_id, text)
        except Exception:
            pass


async def send_photo(chat_id: int, file_bytes: bytes, filename: str, caption: str | None = None) -> None:
    await bot.send_photo(
        chat_id=chat_id,
        photo=BufferedInputFile(file_bytes, filename),
        caption=caption,
        parse_mode="HTML",
    )


async def send_animation(chat_id: int, file_bytes: bytes, filename: str, caption: str | None = None) -> None:
    await bot.send_animation(
        chat_id=chat_id,
        animation=BufferedInputFile(file_bytes, filename),
        caption=caption,
        parse_mode="HTML",
    )
