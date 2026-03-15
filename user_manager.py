"""
用户管理模块
负责用户昵称获取、头像处理、用户池管理等功能
"""
import httpx
from datetime import datetime, timedelta
from gsuid_core.models import Event
from gsuid_core.logger import logger
from .config import marry_config
from .data_manager import DATA_PATH, load_json_file


def get_user_nickname(ev: Event) -> str:
    """获取用户昵称"""
    # 尝试从不同的事件属性中获取用户昵称
    if hasattr(ev, 'sender') and ev.sender:
        # 如果是字典类型
        if isinstance(ev.sender, dict):
            if ev.sender.get('card'):
                return ev.sender['card']
            if ev.sender.get('nickname'):
                return ev.sender['nickname']
        # 如果是对象类型
        else:
            if hasattr(ev.sender, 'card') and ev.sender.card:
                return ev.sender.card
            if hasattr(ev.sender, 'nickname') and ev.sender.nickname:
                return ev.sender.nickname
    
    # 如果都没有，使用用户ID
    return str(ev.user_id)


async def get_avatar_image(user_id: str) -> bytes:
    """获取用户头像图片数据"""
    if not marry_config.get_config('enable_avatar').data:
        return None
    
    try:
        # 构建QQ头像URL（适配多平台时可能需要调整）
        avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(avatar_url)
            if response.status_code == 200:
                return response.content
    except Exception as e:
        logger.error(f"获取头像失败: {e}")
    
    return None


def get_avatar_message(user_id: str) -> str:
    """获取用户头像消息（旧版本兼容，现在建议使用get_avatar_image）"""
    if marry_config.get_config('enable_avatar').data:
        # 构建QQ头像URL（适配多平台时可能需要调整）
        avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
        return f"[CQ:image,file={avatar_url}]"
    return ""


def get_multi_day_user_pool(group_id: str) -> dict:
    """获取近几天的用户池"""
    user_pool_days = marry_config.get_config('user_pool_days').data
    all_users = {}
    
    # 获取今天及前几天的日期
    today = datetime.now()
    for i in range(user_pool_days):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        
        # 构建该日期的用户文件路径
        file_path = DATA_PATH / f"{group_id}-{date_str}.json"
        day_users = load_json_file(file_path)
        
        # 合并用户数据，保留最新的昵称和发言时间
        for user_id, user_info in day_users.items():
            if user_id not in all_users:
                all_users[user_id] = user_info
            else:
                # 如果用户已存在，比较发言时间，保留最新的
                existing_time = datetime.fromisoformat(all_users[user_id]['last_speak_time'])
                current_time = datetime.fromisoformat(user_info['last_speak_time'])
                if current_time > existing_time:
                    all_users[user_id] = user_info
    
    logger.debug(f"群 {group_id} 近 {user_pool_days} 天用户池包含 {len(all_users)} 个用户")
    return all_users