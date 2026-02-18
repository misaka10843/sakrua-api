from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.logger import logger
from app.utils.cache import CacheClient
from app.utils.http_client import HttpClient

router = APIRouter()


@router.get("/avatar/{user_id}", summary="获取 Discord 用户头像并重定向")
async def redirect_discord_avatar(user_id: str):
    """
    根据 User ID 获取头像并 302 跳转。
    缓存策略：10分钟。
    """
    cache_key = f"discord:avatar:{user_id}"
    cached_url = await CacheClient.get(cache_key)
    if cached_url:
        return RedirectResponse(url=cached_url, status_code=302)

    if not settings.DISCORD_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot Token missing")

    url = f"https://discord.com/api/v10/users/{user_id}"
    headers = {"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"}

    try:
        response = await HttpClient.get(url, headers=headers)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")

        if response.status_code != 200:
            logger.error(f"Discord API Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch user data")

        data = response.json()
        avatar = data.get("avatar")
        discriminator = data.get("discriminator", "0")

        if avatar:
            ext = "gif" if avatar.startswith("a_") else "png"
            final_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}?size=1024"
        else:
            if discriminator == "0":
                idx = (int(user_id) >> 22) % 6
            else:
                idx = int(discriminator) % 5
            final_url = f"https://cdn.discordapp.com/embed/avatars/{idx}.png"

        await CacheClient.set(cache_key, final_url, ttl=600)
        return RedirectResponse(url=final_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar error: {e}")
        raise HTTPException(status_code=500, detail="Server Error")
