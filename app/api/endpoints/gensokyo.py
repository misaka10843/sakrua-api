import json
from typing import List

from fastapi import APIRouter, BackgroundTasks

from app.core.config import settings
from app.core.logger import logger
from app.utils.cache import CacheClient
from app.utils.http_client import HttpClient

router = APIRouter()

TEAMS_CONFIG = [
    {
        "role_id": "1454433213135978658",
        "name": "Project Leads",
        "image": "/icons/staff/admin.webp",
        "color": ["#ff7a7b", "#ffc2c2"]
    },
    {
        "role_id": "1454664229553438806",
        "name": "Developers",
        "image": "/icons/staff/developer.webp",
        "color": ["#369876", "#4fff87"]
    },
    {
        "role_id": "1454432689062154331",
        "name": "Builders",
        "image": "/icons/staff/build-lead.webp",
        "color": "#194bb5"
    }
]

CACHE_KEY = "gensokyo:contributors:list"
CACHE_TTL = 60 * 60 * 24 * 7


def _get_avatar_url(user_data: dict) -> str:
    """计算头像URL"""
    user_id = user_data['id']
    avatar = user_data.get('avatar')
    discriminator = user_data.get('discriminator', '0')

    if avatar:
        ext = "gif" if avatar.startswith("a_") else "png"
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}?size=256"
    else:
        if discriminator == '0':
            idx = (int(user_id) >> 22) % 6
        else:
            idx = int(discriminator) % 5
        return f"https://cdn.discordapp.com/embed/avatars/{idx}.png"


async def _fetch_guild_members(guild_id: str) -> List[dict]:
    """分页拉取所有成员"""
    if not settings.DISCORD_BOT_TOKEN:
        logger.error("Discord Bot Token missing")
        return []

    url = f"https://discord.com/api/v10/guilds/{guild_id}/members"
    headers = {"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"}

    members = []
    last_id = "0"

    while True:
        try:
            resp = await HttpClient.get(url, headers=headers, params={"limit": 1000, "after": last_id})
            if resp.status_code != 200:
                logger.error(f"Failed to fetch members: {resp.text}")
                break

            batch = resp.json()
            if not batch:
                break

            members.extend(batch)
            last_id = batch[-1]["user"]["id"]

            if len(batch) < 1000:
                break
        except Exception as e:
            logger.error(f"Error fetching members: {e}")
            break

    return members


async def _build_data():
    """构建贡献者数据结构"""
    if not settings.DISCORD_GUILD_ID:
        logger.warning("DISCORD_GUILD_ID not set")
        return []

    members = await _fetch_guild_members(settings.DISCORD_GUILD_ID)
    print(members)
    with open("data.json", "w") as file:
        json.dump(members, file)

    result = []
    role_map = {}

    for idx, cfg in enumerate(TEAMS_CONFIG):
        result.append({
            "name": cfg["name"],
            "image": cfg.get("image"),
            "color": cfg.get("color"),
            "list": []
        })
        role_map[cfg["role_id"]] = idx

    for member in members:
        user = member.get("user", {})
        roles = member.get("roles", [])

        target_idx = -1
        for cfg in TEAMS_CONFIG:
            if cfg["role_id"] in roles:
                target_idx = role_map[cfg["role_id"]]
                break

        if target_idx != -1:
            display_name = member.get("nick") or user.get("global_name") or user.get("username")
            result[target_idx]["list"].append({
                "name": display_name,
                "avatar": _get_avatar_url(user),
                "avatarUseGithub": False,
                "position": TEAMS_CONFIG[target_idx]["name"],
                "contact": {
                    "discord": user.get("username")
                }
            })

    return result


@router.get("/contributors", summary="获取 Gensokyo 贡献者列表")
async def get_gensokyo_contributors():
    """
    获取 Gensokyo Reimagined 的贡献者列表。
    缓存策略：7天。
    """
    cached = await CacheClient.get(CACHE_KEY)
    if cached:
        return json.loads(cached)

    data = await _build_data()
    await CacheClient.set(CACHE_KEY, json.dumps(data), ttl=CACHE_TTL)
    return data


@router.post("/contributors/refresh", summary="强制刷新贡献者缓存")
async def refresh_gensokyo_contributors(background_tasks: BackgroundTasks):
    async def task():
        logger.info("Refreshing Gensokyo contributors...")
        data = await _build_data()
        await CacheClient.set(CACHE_KEY, json.dumps(data), ttl=CACHE_TTL)
        logger.info("Gensokyo contributors refreshed.")

    background_tasks.add_task(task)
    return {"status": "refreshing"}
