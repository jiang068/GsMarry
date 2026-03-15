"""
娶群友插件
功能：
1. 记录群聊中发言的用户
2. 允许用户"娶群友"，随机匹配群内其他用户
3. 每日限制一次，记录在JSON文件中
"""
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger

from .user_manager import get_user_nickname
from .data_manager import record_user
from .marry_commands import marry_random_user, check_today_marriages, divorce_couple
from .force_marry_commands import force_marry_user, check_force_marry_record
from .admin_commands import check_marry_config, clear_today_marry_data
from .config import marry_config

# 创建服务
gs_marry = SV(
    name='娶群友',
    pm=6,  # 普通用户权限
    priority=5,
    enabled=True,
    area='GROUP'  # 只在群聊中可用
)

# 消息监听器 - 记录用户发言（不阻塞其他处理器）
# 暂时用空前缀触发器触发用户发言记录功能，没找到其他可以静默触发的方法
@gs_marry.on_prefix('', block=False)
async def message_listener(bot: Bot, ev: Event):
    """监听所有消息，记录用户发言"""
    if not ev.group_id or ev.user_id == ev.bot_id:
        return
    
    try:
        # 静默记录用户发言
        user_nickname = get_user_nickname(ev)
        record_user(ev.group_id, ev.user_id, user_nickname)
    except Exception as e:
        logger.error(f"记录用户发言失败: {e}")

# 娶群友命令 - 使用全匹配触发器
@gs_marry.on_fullmatch(('娶群友', 'waifu', 'wife'))
async def marry_handler(bot: Bot, ev: Event):
    """娶群友命令处理器"""
    await marry_random_user(bot, ev)

# 查看今日娶群友记录
@gs_marry.on_fullmatch('今日cp')
async def today_cp_handler(bot: Bot, ev: Event):
    await check_today_marriages(bot, ev)

# 查看娶群友配置
@gs_marry.on_fullmatch('娶群友设置')
async def config_handler(bot: Bot, ev: Event):
    await check_marry_config(bot, ev)

# 清除今日娶群友数据（管理员功能）
@gs_marry.on_fullmatch('清除今日娶群友')
async def clear_data_handler(bot: Bot, ev: Event):
    await clear_today_marry_data(bot, ev)

# 离婚功能
@gs_marry.on_fullmatch('离婚')
async def divorce_handler(bot: Bot, ev: Event):
    await divorce_couple(bot, ev)

# 强娶功能 - 使用关键词触发器
@gs_marry.on_keyword('强娶')
async def force_marry_handler(bot: Bot, ev: Event):
    await force_marry_user(bot, ev)

# 查看强娶记录
@gs_marry.on_fullmatch('强娶记录')
async def force_record_handler(bot: Bot, ev: Event):
    await check_force_marry_record(bot, ev)