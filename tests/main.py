import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from discord_interactions import (
    register_commands,
    process_commands,
    command,
)
from discord_interactions.models import (
    ContentModel,
    EmbedModel,
    FooterEmbedModel,
    ThumbnailEmbedModel,
    InteractionType,
)
from discord_interactions.middleware import VerifyIncomingRequestsMiddleware


app = FastAPI()
load_dotenv()

app.add_middleware(VerifyIncomingRequestsMiddleware)


@app.post("/interactions")
async def interactions(request: Request):
    _json = await request.json()
    interaction_type = InteractionType(_json["type"])

    if interaction_type == InteractionType.PING:  # ping
        return {"type": InteractionType.PONG}  # pong

    if interaction_type == InteractionType.APPLICATION_COMMAND:  # command

        response = await process_commands(_json)
        return response


@command(name="ping")
async def ping(interaction: dict) -> ContentModel:
    """Ping Pong"""
    return ContentModel(content="Pong!")


@command(name="register")
async def register(interaction: dict) -> ContentModel:
    """Bulk registers all commands"""
    await register_commands()
    return ContentModel(content="Commands have been bulk registered!")


@command(name="info")
async def info(interaction: dict) -> EmbedModel:
    member = interaction["member"]
    user_id = member["user"]["id"]
    user_avatar = member["user"]["avatar"]
    joined_at = datetime.datetime.fromisoformat(member["joined_at"])
    footer = FooterEmbedModel(
        text="Joined: " + joined_at.strftime("%B %d, %Y %I:%M:%S %p")
    )
    thumbnail = ThumbnailEmbedModel(
        url=f"https://cdn.discordapp.com/avatars/{user_id}/{user_avatar}"
    )
    title = f'{member["user"]["global_name"]} - {member["user"]["username"]}'
    description = ", ".join([f"<@&{role}>" for role in member["roles"]])
    return EmbedModel(
        title=title,
        description=description,
        footer=footer,
        timestamp=datetime.datetime.utcnow(),
        color=int("ff0000", 16),
        thumbnail=thumbnail,
    )


if __name__ == "__main__":
    uvicorn.run(app)
