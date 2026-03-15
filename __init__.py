from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger
from datetime import datetime

from .draw import draw_cp_image

from .core import (
    record_speak, process_marry, process_force_marry,
    process_divorce, get_cps_data, get_force_record, load_data, save_data
)
from .utils import get_user_nickname, get_avatar_image
from .config import marry_config

# 创建服务
gs_marry = SV(name='娶群友', pm=6, priority=5, enabled=True, area='GROUP')

# 监听所有消息以记录用户活跃度（静默处理）
@gs_marry.on_message(block=False)
async def _listen(bot: Bot, ev: Event):
    if ev.group_id and ev.user_id != ev.bot_id:
        try:
            record_speak(ev.group_id, ev.user_id, get_user_nickname(ev))
        except Exception as e:
            logger.error(f"记录发言失败: {e}")

# 娶群友
@gs_marry.on_fullmatch(('娶群友', 'waifu', 'wife'))
async def _marry(bot: Bot, ev: Event):
    if not ev.group_id: return
    
    status, partner, p_name = process_marry(ev.group_id, ev.user_id)
    
    if status == 3:
        await bot.send(marry_config.get_config('no_users_message').data)
        return

    base_msg = marry_config.get_config('marry_message').data.format(nickname=p_name)
    if status == 1:
        prefix = marry_config.get_config('already_married_message').data
        msg = f"{prefix}\n{base_msg}"
    else:
        msg = base_msg

    img = await get_avatar_image(partner)
    await bot.send([msg, img] if img else msg)

# 强娶
@gs_marry.on_keyword('强娶')
async def _force(bot: Bot, ev: Event):
    if not ev.group_id or not ev.raw_text.strip().startswith('强娶'): 
        return

    target_id = None
    if hasattr(ev, 'at') and ev.at: target_id = ev.at
    elif hasattr(ev, 'at_list') and ev.at_list: target_id = ev.at_list[0]
    elif hasattr(ev, 'content'):
        for msg in ev.content:
            if getattr(msg, 'type', '') == 'at' and hasattr(msg, 'data'):
                target_id = msg.data
                break

    if not target_id:
        return await bot.send('请@你要强娶的人！例如：强娶@某某某')
    if target_id == ev.bot_self_id:
        return await bot.send('不能强娶我哦！请@其他群友。')
    if target_id == ev.user_id:
        return await bot.send('不能强娶自己哦！')

    success, msg = process_force_marry(ev.group_id, ev.user_id, target_id, f"用户{target_id}")
    
    if success:
        img = await get_avatar_image(target_id)
        await bot.send([msg, img] if img else msg)
    else:
        await bot.send(msg)

# 离婚
@gs_marry.on_fullmatch('离婚')
async def _divorce(bot: Bot, ev: Event):
    if not ev.group_id: return
    success, u1, u2 = process_divorce(ev.group_id, ev.user_id)
    if success:
        await bot.send(marry_config.get_config('divorce_success_message').data.format(husband=u1, wife=u2))
    else:
        await bot.send(marry_config.get_config('no_marriage_message').data)

# 今日CP榜
# --- 2. 请替换掉旧的 _cp 函数 ---
@gs_marry.on_fullmatch('今日cp')
async def _cp(bot: Bot, ev: Event):
    if not ev.group_id: return
    
    # 获取结构化数据
    cps_data = get_cps_data(ev.group_id)
    if not cps_data:
        return await bot.send(marry_config.get_config('no_marriage_today_message').data)
    
    # 生成榜单图并发送
    title = marry_config.get_config('today_cp_list_title').data
    img_bytes = draw_cp_image(cps_data, title)
    await bot.send(img_bytes)

# 强娶记录
@gs_marry.on_fullmatch('强娶记录')
async def _record_cmd(bot: Bot, ev: Event):
    if not ev.group_id: return
    await bot.send(get_force_record(ev.group_id, ev.user_id))

# 娶群友设置
@gs_marry.on_fullmatch('娶群友设置')
async def _config(bot: Bot, ev: Event):
    if not ev.group_id: return
    c = marry_config
    msg = f"""当前娶群友设置：
🎯 触发词：{c.get_config('marry_triggers').data}
👥 用户池天数：{c.get_config('user_pool_days').data}天
🖼️ 头像显示：{'开启' if c.get_config('enable_avatar').data else '关闭'}
💕 娶群友消息：{c.get_config('marry_message').data}
💔 离婚成功消息：{c.get_config('divorce_success_message').data}
💪 强娶成功率：{c.get_config('force_marry_success_rate').data}%
🎯 强娶每日次数：{c.get_config('force_marry_daily_limit').data}次
🔇 允许强娶未发言：{'是' if c.get_config('allow_force_marry_non_speakers').data else '否'}
💔 允许强娶已婚：{'是' if c.get_config('allow_force_marry_married_users').data else '否'}
💡 提示：可在GsCore网页控制台修改配置"""
    await bot.send(msg)

# 清除今日数据
@gs_marry.on_fullmatch('清除今日娶群友')
async def _clear(bot: Bot, ev: Event):
    if not ev.group_id: return
    if ev.user_pm > 3:
        return await bot.send('仅管理员可以使用此功能！')
    
    d = load_data(ev.group_id)
    t = datetime.now().strftime('%Y-%m-%d')
    if t in d.get("daily", {}):
        del d["daily"][t]
        save_data(ev.group_id, d)
        await bot.send('今日娶群友数据已清除！')
    else:
        await bot.send('今日还没有娶群友数据！')