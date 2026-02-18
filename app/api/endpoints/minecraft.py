import re
from fastapi import APIRouter, Query
from mcstatus import JavaServer
from pydantic import BaseModel
from typing import Optional
from app.core.logger import logger

router = APIRouter()


# --- Response Models ---

class PlayerInfo(BaseModel):
    online: int
    max: int


class MCStatusResponse(BaseModel):
    online: bool
    ip: str
    port: int
    motd: Optional[str] = None
    players: Optional[PlayerInfo] = None
    version: Optional[str] = None  # 原始版本字符串 (e.g. "Velocity 1.7.2-1.21.11")
    game_version: Optional[str] = None  # 纯净游戏版本 (e.g. "1.21.11" 或 "1.20.4")
    latency: Optional[float] = None
    error: Optional[str] = None


# --- Helper Functions ---

def extract_game_version(raw_version: str) -> str:
    """
    从原始版本字符串中提取纯净的 Minecraft 版本号。
    支持格式:
    - "1.20.4" -> "1.20.4"
    - "git-Paper-378 (MC: 1.16.5)" -> "1.16.5"
    - "Velocity 1.7.2-1.21.11" -> "1.21.11"
    - "BungeeCord 1.8.x-1.19.x" -> "1.8.x-1.19.x" (保持区间)
    """
    if not raw_version:
        return "Unknown"
    mc_match = re.search(r"\(MC:\s*([\d\.]+)\)", raw_version)
    if mc_match:
        return mc_match.group(1)
    versions = re.findall(r"\b1\.\d+(?:\.\d+|.x)?\b", raw_version)

    if versions:
        if len(versions) > 1:
            if "-" in raw_version and len(versions) >= 2:
                return versions[-1]
            return versions[-1]
        return versions[0]

    return raw_version.split(" ")[-1]

@router.get("/status", response_model=MCStatusResponse, summary="查询 Minecraft Java 服务器状态")
async def check_mc_server(
        ip: str = Query(..., description="服务器 IP 地址"),
        port: int = Query(25565, description="服务器端口")
):
    """
    检测指定 Minecraft 服务器的状态 (Java Edition)。
    """
    target = f"{ip}:{port}"
    logger.info(f"Checking MC Server status: {target}")

    try:
        server = await JavaServer.async_lookup(target)
        status = await server.async_status()

        raw_version_str = status.version.name
        clean_version = extract_game_version(raw_version_str)

        return MCStatusResponse(
            online=True,
            ip=ip,
            port=port,
            motd=status.description,
            players=PlayerInfo(
                online=status.players.online,
                max=status.players.max
            ),
            version=raw_version_str,
            game_version=clean_version,
            latency=status.latency
        )

    except Exception as e:
        logger.warning(f"Failed to query MC server {target}: {str(e)}")
        error_msg = "Server is offline"
        if "gaierror" in str(e):
            error_msg = "Invalid Hostname"
        elif "timed out" in str(e):
            error_msg = "Connection Timed Out"

        return MCStatusResponse(
            online=False,
            ip=ip,
            port=port,
            error=error_msg
        )