import httpx
from gsuid_core.models import Event
from gsuid_core.logger import logger
from .config import marry_config

def get_user_nickname(ev: Event) -> str:
    """快速安全地获取用户昵称"""
    if isinstance(ev.sender, dict):
        return ev.sender.get('card') or ev.sender.get('nickname') or str(ev.user_id)
    if hasattr(ev.sender, 'card') and ev.sender.card: 
        return ev.sender.card
    if hasattr(ev.sender, 'nickname') and ev.sender.nickname: 
        return ev.sender.nickname
    return str(ev.user_id)

async def get_avatar_image(user_id: str) -> bytes:
    """获取用户QQ头像数据"""
    if not marry_config.get_config('enable_avatar').data: 
        return None
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640")
            if res.status_code == 200: return res.content
    except Exception as e:
        logger.error(f"获取头像失败: {e}")
    return None