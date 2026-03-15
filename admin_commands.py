"""
管理和配置相关命令处理模块
"""
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger

from .config import marry_config
from .data_manager import get_group_marry_file_path


async def check_marry_config(bot: Bot, ev: Event):
    """查看当前娶群友配置"""
    if not ev.group_id:
        await bot.send('该功能只能在群聊中使用！')
        return
    
    try:
        marry_triggers = marry_config.get_config('marry_triggers').data
        user_pool_days = marry_config.get_config('user_pool_days').data
        enable_avatar = marry_config.get_config('enable_avatar').data
        marry_message = marry_config.get_config('marry_message').data
        force_success_rate = marry_config.get_config('force_marry_success_rate').data
        force_daily_limit = marry_config.get_config('force_marry_daily_limit').data
        allow_non_speakers = marry_config.get_config('allow_force_marry_non_speakers').data
        allow_marry_married = marry_config.get_config('allow_force_marry_married_users').data
        divorce_success_message = marry_config.get_config('divorce_success_message').data
        
        config_info = f"""当前娶群友设置：
🎯 触发词：{marry_triggers}
👥 用户池天数：{user_pool_days}天
🖼️ 头像显示：{'开启' if enable_avatar else '关闭'}
💕 娶群友消息：{marry_message}
💔 离婚成功消息：{divorce_success_message}
💪 强娶成功率：{force_success_rate}%
🎯 强娶每日次数：{force_daily_limit}次
🔇 允许强娶未发言用户：{'是' if allow_non_speakers else '否'}
💔 允许强娶已婚用户：{'是' if allow_marry_married else '否'}
🎯 强娶每日次数：{force_daily_limit}次
🔇 允许强娶未发言用户：{'是' if allow_non_speakers else '否'}

💡 提示：可在GsCore网页控制台修改配置"""
        
        await bot.send(config_info)
        
    except Exception as e:
        logger.error(f"查看配置失败: {e}")
        await bot.send('查看配置失败，请稍后再试～')


async def clear_today_marry_data(bot: Bot, ev: Event):
    """清除今日娶群友数据（仅管理员可用）"""
    if not ev.group_id:
        await bot.send('该功能只能在群聊中使用！')
        return
    
    # 检查权限（只有管理员可用）
    if ev.user_pm > 3:  # 权限等级大于3的用户不能使用
        await bot.send('仅管理员可以使用此功能！')
        return
    
    try:
        marry_file_path = get_group_marry_file_path(ev.group_id)
        if marry_file_path.exists():
            marry_file_path.unlink()  # 删除文件
            await bot.send('今日娶群友数据已清除！')
            logger.info(f"管理员 {ev.user_id} 清除了群 {ev.group_id} 的今日娶群友数据")
        else:
            await bot.send('今日还没有娶群友数据！')
            
    except Exception as e:
        logger.error(f"清除今日娶群友数据失败: {e}")
        await bot.send('清除失败，请稍后再试～')