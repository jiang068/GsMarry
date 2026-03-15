import httpx
from gsuid_core.models import Event
from gsuid_core.logger import logger
from .config import marry_config

# 【优化 2】：全局头像缓存池
_avatar_cache = {}

def get_user_nickname(ev: Event) -> str:
    if isinstance(ev.sender, dict):
        return ev.sender.get('card') or ev.sender.get('nickname') or str(ev.user_id)
    if hasattr(ev.sender, 'card') and ev.sender.card: 
        return ev.sender.card
    if hasattr(ev.sender, 'nickname') and ev.sender.nickname: 
        return ev.sender.nickname
    return str(ev.user_id)

async def get_avatar_image(user_id: str) -> bytes:
    if not marry_config.get_config('enable_avatar').data: 
        return None
        
    # 命中内存缓存，直接秒回图片数据
    if user_id in _avatar_cache:
        return _avatar_cache[user_id]
        
    try:
        # 增加 5 秒超时保护，防止网络拥堵导致 Bot 假死
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640")
            if res.status_code == 200:
                # 存入缓存
                _avatar_cache[user_id] = res.content
                return res.content
    except Exception as e:
        logger.error(f"获取头像失败: {e}")
    return None