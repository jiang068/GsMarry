"""
强娶相关命令处理模块
"""
import random
from datetime import datetime
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger

from .config import marry_config
from .data_manager import (
    get_group_marry_file_path,
    get_group_force_marry_file_path,
    get_group_user_file_path,
    load_json_file,
    save_json_file
)
from .user_manager import get_avatar_image, get_multi_day_user_pool


async def force_marry_user(bot: Bot, ev: Event):
    """强娶指定用户功能"""
    # 确保只在群聊中使用
    if not ev.group_id:
        await bot.send('该功能只能在群聊中使用！')
        return
    
    # 确保消息以"强娶"开头
    if not ev.raw_text.strip().startswith('强娶'):
        return
    
    try:
        group_id = ev.group_id
        user_id = ev.user_id
        
        logger.info(f"用户 {user_id} 在群 {group_id} 发送强娶消息: {ev.raw_text}")
        logger.debug(f"at_list: {getattr(ev, 'at_list', [])}, is_tome: {getattr(ev, 'is_tome', False)}")
        
        # 检查是否@了机器人
        if getattr(ev, 'is_tome', False):
            await bot.send('不能强娶我哦！请@群里的其他人。')
            return
        
        # 检查是否有@用户
        target_user_id = None
        
        # 方法1：从at_list获取
        if hasattr(ev, 'at_list') and ev.at_list and len(ev.at_list) > 0:
            target_user_id = ev.at_list[0]
            logger.debug(f"从at_list获取目标用户: {target_user_id}")
        
        # 方法2：从content中解析at消息
        elif hasattr(ev, 'content') and ev.content:
            for msg in ev.content:
                if hasattr(msg, 'type') and msg.type == 'at' and hasattr(msg, 'data'):
                    target_user_id = msg.data
                    logger.debug(f"从content解析目标用户: {target_user_id}")
                    break
        
        # 方法3：从at属性获取
        elif hasattr(ev, 'at') and ev.at:
            target_user_id = ev.at
            logger.debug(f"从at属性获取目标用户: {target_user_id}")
        
        if not target_user_id:
            await bot.send('请@你要强娶的人！例如：强娶@某某某')
            return
        
        # 检查是否@了机器人
        if target_user_id == ev.bot_self_id:
            await bot.send('不能强娶我哦！请@其他群友。')
            return
        
        logger.info(f"目标用户ID: {target_user_id}")
        
        # 不能强娶自己
        if target_user_id == user_id:
            await bot.send('不能强娶自己哦！')
            return
        
        logger.info(f"用户 {user_id} 在群 {group_id} 尝试强娶 {target_user_id}")
        
        # 检查今日强娶次数
        force_file_path = get_group_force_marry_file_path(group_id)
        force_data = load_json_file(force_file_path)
        
        user_force_count = force_data.get(user_id, {}).get('count', 0)
        daily_limit = marry_config.get_config('force_marry_daily_limit').data
        
        if user_force_count >= daily_limit:
            await bot.send(f'你今天的强娶次数已用完！每日限{daily_limit}次。')
            return
        
        # 检查当前用户是否已有婚姻关系（排除已离婚）
        marry_file_path = get_group_marry_file_path(group_id)
        marry_data = load_json_file(marry_file_path)
        
        # 检查用户是否已娶或被娶（未离婚状态）
        if user_id in marry_data and marry_data[user_id].get('status') != '已离婚':
            await bot.send('你已经有老婆了，不能强娶！请先离婚。')
            return
        
        # 检查用户是否被别人娶了（未离婚状态）
        for husband_id, wife_info in marry_data.items():
            if wife_info.get('user_id') == user_id and wife_info.get('status') != '已离婚':
                await bot.send('你已经被娶了，不能强娶！请先离婚。')
                return
        
        # 检查目标用户是否已有婚姻关系
        target_married = False
        if target_user_id in marry_data and marry_data[target_user_id].get('status') != '已离婚':
            target_married = True
        
        for husband_id, wife_info in marry_data.items():
            if wife_info.get('user_id') == target_user_id and wife_info.get('status') != '已离婚':
                target_married = True
                break
        
        # 检查是否允许强娶已婚用户
        if target_married:
            allow_marry_married = marry_config.get_config('allow_force_marry_married_users').data
            if not allow_marry_married:
                denied_msg = marry_config.get_config('force_marry_married_user_denied_message').data
                await bot.send(denied_msg)
                return
        
        # 记录强娶尝试
        if user_id not in force_data:
            force_data[user_id] = {'count': 0, 'attempts': []}
        
        force_data[user_id]['count'] += 1
        force_data[user_id]['attempts'].append({
            'target': target_user_id,
            'time': datetime.now().isoformat(),
            'success': False  # 先设为失败，成功时再更新
        })
        
        # 判断是否成功（概率检查）
        success_rate = marry_config.get_config('force_marry_success_rate').data
        success = random.randint(1, 100) <= success_rate
        
        if not success:
            # 强娶失败
            save_json_file(force_file_path, force_data)
            remaining_attempts = daily_limit - force_data[user_id]['count']
            failed_msg = marry_config.get_config('force_marry_failed_message').data.format(remaining=remaining_attempts)
            await bot.send(failed_msg)
            return
        
        # 强娶成功
        force_data[user_id]['attempts'][-1]['success'] = True
        save_json_file(force_file_path, force_data)
        
        # 获取目标用户昵称
        user_data = get_multi_day_user_pool(group_id)
        target_user_info = user_data.get(target_user_id, {})
        target_nickname = target_user_info.get('nickname', target_user_id)
        
        # 如果目标用户不在用户池中，检查是否允许强娶
        if not target_user_info:
            allow_non_speakers = marry_config.get_config('allow_force_marry_non_speakers').data
            if not allow_non_speakers:
                await bot.send('该用户未在群内发言，无法强娶！')
                return
            
            logger.warning(f"强娶目标 {target_user_id} 不在用户池中，但配置允许")
            target_nickname = f"用户{target_user_id}"
        
        logger.debug(f"强娶目标信息: {target_nickname}({target_user_id}), 在用户池中: {'是' if target_user_info else '否'}")
        
        # 如果目标用户已有婚姻关系，先解除
        if target_married:
            # 解除目标用户的现有关系
            if target_user_id in marry_data:
                marry_data[target_user_id]['status'] = '已离婚'
                marry_data[target_user_id]['divorce_time'] = datetime.now().isoformat()
                marry_data[target_user_id]['divorce_reason'] = '被强娶'
            
            for husband_id, wife_info in marry_data.items():
                if wife_info.get('user_id') == target_user_id and wife_info.get('status') != '已离婚':
                    marry_data[husband_id]['status'] = '已离婚'
                    marry_data[husband_id]['divorce_time'] = datetime.now().isoformat()
                    marry_data[husband_id]['divorce_reason'] = '老婆被强娶'
                    break
        
        # 记录新的婚姻关系
        marry_data[user_id] = {
            'user_id': target_user_id,
            'nickname': target_nickname,
            'marry_time': datetime.now().isoformat(),
            'status': '已结婚',
            'marry_type': '强娶'
        }
        save_json_file(marry_file_path, marry_data)
        
        # 如果目标用户不在用户池中，将其添加到今日用户池
        if not target_user_info:
            today_user_file = get_group_user_file_path(group_id)
            today_user_data = load_json_file(today_user_file)
            today_user_data[target_user_id] = {
                'nickname': target_nickname,
                'last_speak_time': datetime.now().isoformat(),
                'added_reason': '被强娶时自动添加'
            }
            save_json_file(today_user_file, today_user_data)
            logger.info(f"将被强娶用户 {target_nickname}({target_user_id}) 自动添加到用户池")
        
        # 发送成功消息
        remaining_attempts = daily_limit - force_data[user_id]['count']
        
        # 根据是否横刀夺爱选择不同的消息模板
        if target_married:
            message_template = marry_config.get_config('force_marry_steal_success_message').data
        else:
            message_template = marry_config.get_config('force_marry_success_message').data
            
        message = message_template.format(nickname=target_nickname, remaining=remaining_attempts)
        
        # 发送头像
        avatar_image = await get_avatar_image(target_user_id)
        if avatar_image:
            await bot.send([message, avatar_image])
        else:
            await bot.send(message)
        
        logger.info(f"用户 {user_id} 强娶 {target_nickname}({target_user_id}) 成功")
        
    except Exception as e:
        logger.error(f"强娶功能执行失败: {e}")
        await bot.send('强娶失败，请稍后再试～')


async def check_force_marry_record(bot: Bot, ev: Event):
    """查看个人强娶记录"""
    if not ev.group_id:
        await bot.send('该功能只能在群聊中使用！')
        return
    
    try:
        force_file_path = get_group_force_marry_file_path(ev.group_id)
        force_data = load_json_file(force_file_path)
        
        user_data = force_data.get(ev.user_id, {})
        if not user_data:
            await bot.send('你今天还没有尝试过强娶呢！')
            return
        
        count = user_data.get('count', 0)
        daily_limit = marry_config.get_config('force_marry_daily_limit').data
        remaining = daily_limit - count
        
        attempts = user_data.get('attempts', [])
        success_count = sum(1 for attempt in attempts if attempt.get('success', False))
        
        message = f"你的强娶记录：\n"
        message += f"今日尝试次数：{count}/{daily_limit}\n"
        message += f"剩余次数：{remaining}\n"
        message += f"成功次数：{success_count}\n"
        message += f"成功率：{success_count/count*100:.1f}%" if count > 0 else "成功率：0%"
        
        await bot.send(message)
        
    except Exception as e:
        logger.error(f"查看强娶记录失败: {e}")
        await bot.send('查看失败，请稍后再试～')