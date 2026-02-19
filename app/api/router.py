from fastapi import APIRouter

from app.api.endpoints import discord, minecraft, gensokyo

api_router = APIRouter()

api_router.include_router(
    discord.router,
    prefix="/discord",
    tags=["Discord Utilities"]
)

api_router.include_router(
    minecraft.router,
    prefix="/mc",
    tags=["Minecraft Utilities"]
)

api_router.include_router(
    gensokyo.router,
    prefix="/gensokyo",
    tags=["Gensokyo Reimagined"]
)
