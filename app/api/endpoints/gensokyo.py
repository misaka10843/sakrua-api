import json
from typing import List, Optional, Union, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Body
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logger import logger
from app.utils.cache import CacheClient
from app.utils.http_client import HttpClient

router = APIRouter()

CACHE_KEY_RAW_MEMBERS = "gensokyo:discord:members:raw"
CACHE_TTL = 60 * 60 * 24 * 7  # 7天


class Contact(BaseModel):
    discord: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    youtube: Optional[str] = None
    other: Optional[str] = None


class ContributorOverride(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    avatarUseGithub: Optional[bool] = None
    position: Optional[str] = None
    contact: Optional[Contact] = None


class TeamConfig(BaseModel):
    role_ids: List[str] = Field(default_factory=list, description="绑定的 Discord 身份组 ID 列表 (任意一个匹配即可)")
    include_user_ids: List[str] = Field(default_factory=list, description="强制包含的用户 ID 列表")

    name: str = Field(..., description="显示的组名")
    image: Optional[str] = Field(None, description="该组显示的图标路径")
    color: Union[str, List[str]] = Field(..., description="颜色或渐变色数组")


class ContributorRequest(BaseModel):
    config: List[TeamConfig]
    overrides: Optional[Dict[str, ContributorOverride]] = {}


class DiscordRole(BaseModel):
    id: str
    name: str
    color: int
    color_hex: str
    position: int
    hoist: bool
    managed: bool
    mentionable: bool


def _int_to_hex_color(color_int: int) -> str:
    if color_int == 0:
        return "#000000"
    hex_str = hex(color_int)[2:].zfill(6)
    return f"#{hex_str}"


def _get_avatar_url(user_data: dict) -> str:
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


async def _fetch_raw_guild_members(guild_id: str) -> List[dict]:
    if not settings.DISCORD_BOT_TOKEN:
        logger.error("Discord Bot Token missing")
        return []

    url = f"https://discord.com/api/v10/guilds/{guild_id}/members"
    headers = {"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"}

    members = []
    last_id = "0"
    max_loops = 50
    loop_count = 0

    while loop_count < max_loops:
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
            loop_count += 1
        except Exception as e:
            logger.error(f"Error fetching members: {e}")
            break
    logger.info(f"Fetched {len(members)} raw members from Discord.")
    return members


async def _get_cached_members() -> List[dict]:
    cached = await CacheClient.get(CACHE_KEY_RAW_MEMBERS)
    if cached:
        return json.loads(cached)

    if not settings.DISCORD_GUILD_ID:
        logger.warning("DISCORD_GUILD_ID not set")
        return []

    raw_data = await _fetch_raw_guild_members(settings.DISCORD_GUILD_ID)
    if raw_data:
        await CacheClient.set(CACHE_KEY_RAW_MEMBERS, json.dumps(raw_data), ttl=CACHE_TTL)

    return raw_data


def _process_contributors(
        members: List[dict],
        configs: List[TeamConfig],
        overrides: Dict[str, ContributorOverride]
) -> List[dict]:
    result = []
    manual_map = {}

    for idx, cfg in enumerate(configs):
        result.append({
            "name": cfg.name,
            "image": cfg.image,
            "color": cfg.color,
            "list": []
        })
        for uid in cfg.include_user_ids:
            manual_map[uid] = idx

    for member in members:
        user = member.get("user", {})
        user_id = user.get("id")
        roles = member.get("roles", [])

        target_idx = -1

        if user_id in manual_map:
            target_idx = manual_map[user_id]

        if target_idx == -1:
            member_roles_set = set(roles)
            for idx, cfg in enumerate(configs):
                cfg_roles_set = set(cfg.role_ids)
                if not cfg_roles_set.isdisjoint(member_roles_set):
                    target_idx = idx
                    break

        if target_idx != -1:
            base_name = member.get("nick") or user.get("global_name") or user.get("username")
            base_avatar = _get_avatar_url(user)
            base_position = result[target_idx]["name"]

            override_data = overrides.get(user_id)

            final_name = override_data.name if (override_data and override_data.name) else base_name
            final_avatar = override_data.avatar if (override_data and override_data.avatar) else base_avatar
            final_use_github = override_data.avatarUseGithub if (
                    override_data and override_data.avatarUseGithub is not None) else False
            final_position = override_data.position if (override_data and override_data.position) else base_position

            final_contact = {
                "discord": user.get("username"),
                "twitter": None, "github": None, "youtube": None, "other": None
            }

            if override_data and override_data.contact:
                if override_data.contact.discord: final_contact["discord"] = override_data.contact.discord
                if override_data.contact.twitter: final_contact["twitter"] = override_data.contact.twitter
                if override_data.contact.github: final_contact["github"] = override_data.contact.github
                if override_data.contact.youtube: final_contact["youtube"] = override_data.contact.youtube
                if override_data.contact.other: final_contact["other"] = override_data.contact.other

            contributor = {
                "id": user_id,
                "name": final_name,
                "avatar": final_avatar,
                "avatarUseGithub": final_use_github,
                "position": final_position,
                "contact": final_contact
            }
            result[target_idx]["list"].append(contributor)

    return result


@router.post("/contributors", summary="根据配置获取贡献者列表")
async def get_contributors_dynamic(
        body: ContributorRequest = Body(..., description="配置对象")
):
    all_members = await _get_cached_members()
    final_data = _process_contributors(all_members, body.config, body.overrides or {})
    return final_data


@router.post("/contributors/refresh", summary="强制刷新 Discord 成员缓存")
async def refresh_contributors_cache(background_tasks: BackgroundTasks):
    async def task():
        logger.info("Starting background refresh of Discord members...")
        if not settings.DISCORD_GUILD_ID:
            return
        raw_data = await _fetch_raw_guild_members(settings.DISCORD_GUILD_ID)
        if raw_data:
            await CacheClient.set(CACHE_KEY_RAW_MEMBERS, json.dumps(raw_data), ttl=CACHE_TTL)
            logger.info("Discord members cache updated.")

    background_tasks.add_task(task)
    return {"status": "refreshing", "message": "Background refresh started"}


@router.get("/roles", response_model=List[DiscordRole], summary="获取服务器所有身份组")
async def get_guild_roles():
    if not settings.DISCORD_GUILD_ID:
        raise HTTPException(status_code=500, detail="Guild ID not set")

    cache_key = f"discord:roles:{settings.DISCORD_GUILD_ID}"
    cached_data = await CacheClient.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    if not settings.DISCORD_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot Token missing")

    url = f"https://discord.com/api/v10/guilds/{settings.DISCORD_GUILD_ID}/roles"
    headers = {"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"}

    try:
        response = await HttpClient.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch roles")

        roles_data = response.json()
        roles_data.sort(key=lambda x: x['position'], reverse=True)

        processed_roles = []
        for r in roles_data:
            processed_roles.append({
                "id": r["id"],
                "name": r["name"],
                "color": r["color"],
                "color_hex": _int_to_hex_color(r["color"]),
                "position": r["position"],
                "hoist": r.get("hoist", False),
                "managed": r.get("managed", False),
                "mentionable": r.get("mentionable", False)
            })

        await CacheClient.set(cache_key, json.dumps(processed_roles), ttl=3600)
        return processed_roles

    except Exception as e:
        logger.error(f"Get roles error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
