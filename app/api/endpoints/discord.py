from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from app.utils.http_client import HttpClient
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()


@router.get("/avatar/{user_id}", summary="获取 Discord 用户头像并重定向")
async def redirect_discord_avatar(user_id: str):
    """
    根据 Discord User ID 获取头像链接并返回 302 重定向。
    如果用户没有头像，返回默认头像。
    """
    if not settings.DISCORD_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Discord Bot Token not configured in .env"
        )

    # 1. 构建 Discord API 请求
    url = f"https://discord.com/api/v10/users/{user_id}"
    headers = {
        "Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"
    }

    try:
        response = await HttpClient.get(url, headers=headers)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")

        if response.status_code != 200:
            logger.error(f"Discord API Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch user data")

        data = response.json()
        avatar_hash = data.get("avatar")
        discriminator = data.get("discriminator", "0")

        if avatar_hash:
            ext = "gif" if avatar_hash.startswith("a_") else "png"
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}?size=1024"
        else:
            if discriminator == "0":
                default_avatar_index = (int(user_id) >> 22) % 6
            else:
                default_avatar_index = int(discriminator) % 5
            avatar_url = f"https://cdn.discordapp.com/embed/avatars/{default_avatar_index}.png"

        logger.info(f"Redirecting to avatar for user {user_id}: {avatar_url}")
        return RedirectResponse(url=avatar_url, status_code=302)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing discord avatar: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")