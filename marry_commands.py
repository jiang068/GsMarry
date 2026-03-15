"""
基础娶群友命令处理模块
"""
import random
from datetime import datetime
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger

from .config import marry_config
from .data_manager import (
    get_group_marry_file_path, 
    get_group_user_file_path,
    load_json_file, 
    save_json_file,
    record_user
)
from .user_manager import (
    get_user_nickname, 
    get_avatar_image, 
    get_multi_day_user_pool
)


async def marry_random_user(bot: Bot, ev: Event):
    """娶群友功能"""
    # 确保只在群聊中使用
    if not ev.group_id:
        await bot.send('该功能只能在群聊中使用！')
        return
    
    try:
        group_id = ev.group_id
        user_id = ev.user_id
        
        logger.info(f"用户 {user_id} 在群 {group_id} 尝试娶群友")
        
        # 检查今日是否已经娶了群友（排除已离婚）
        marry_file_path = get_group_marry_file_path(group_id)
        marry_data = load_json_file(marry_file_path)
        
        if user_id in marry_data and marry_data[user_id].get('status') != '已离婚':
            # 已经娶了，返回当前老婆信息
            wife_info = marry_data[user_id]
            wife_nickname = wife_info.get('nickname', '未知')
            
            # 获取配置的消息模板
            already_married_msg = marry_config.get_config('already_married_message').data
            marry_msg = marry_config.get_config('marry_message').data.format(nickname=wife_nickname)
            
            # 构建消息，包含头像
            message = f"{already_married_msg}\n{marry_msg}"
            
            # 如果启用头像显示，添加头像到消息中
            if wife_info.get('user_id'):
                avatar_image = await get_avatar_image(wife_info['user_id'])
                if avatar_image:
                    await bot.send([message, avatar_image])
                else:
                    await bot.send(message)
            else:
                await bot.send(message)
            
            return
        
        # 检查今日是否已被别人娶了（排除已离婚）
        for husband_id, wife_info in marry_data.items():
            if wife_info.get('user_id') == user_id and wife_info.get('status') != '已离婚':
                # 已被娶，返回娶Ta的人的信息
                user_data = get_multi_day_user_pool(group_id)
                husband_nickname = user_data.get(husband_id, {}).get('nickname', husband_id)
                
                # 获取配置的消息模板
                already_married_by_others_msg = marry_config.get_config('already_married_by_others_message').data
                marry_msg = marry_config.get_config('marry_message').data.format(nickname=husband_nickname)
                
                # 构建消息 - 统一叫老婆
                message = f"{already_married_by_others_msg}\n{marry_msg}"
                
                # 如果启用头像显示，一起发送
                avatar_image = await get_avatar_image(husband_id)
                if avatar_image:
                    await bot.send([message, avatar_image])
                else:
                    await bot.send(message)
                
                return
        
        # 读取近几天的群聊用户池
        user_data = get_multi_day_user_pool(group_id)
        
        # 移除自己
        available_users = {uid: info for uid, info in user_data.items() if uid != user_id}
        
        # 排除已经是别人老婆的用户（已被娶且未离婚的用户）
        # 修复bug: 避免随机选择到已经结婚的用户
        married_users = set()
        for husband_id, wife_info in marry_data.items():
            if wife_info.get('status') != '已离婚':
                # 排除作为老公的用户
                married_users.add(husband_id)
                # 排除作为老婆的用户
                if wife_info.get('user_id'):
                    married_users.add(wife_info['user_id'])
        
        # 从可用用户中排除已婚用户
        available_users = {uid: info for uid, info in available_users.items() if uid not in married_users}
        
        if not available_users:
            no_users_msg = marry_config.get_config('no_users_message').data
            await bot.send(no_users_msg)
            return
        
        # 随机选择一个用户
        wife_user_id = random.choice(list(available_users.keys()))
        wife_info = available_users[wife_user_id]
        wife_nickname = wife_info.get('nickname', wife_user_id)
        
        if wife_nickname == wife_user_id:
            logger.warning(f"用户 {wife_user_id} 昵称为空，使用用户ID作为昵称")
        
        logger.debug(f"选中的老婆: {wife_nickname}({wife_user_id})")
        
        # 记录娶群友信息
        marry_data[user_id] = {
            'user_id': wife_user_id,
            'nickname': wife_nickname,
            'marry_time': datetime.now().isoformat(),
            'status': '已结婚'
        }
        save_json_file(marry_file_path, marry_data)
        
        # 构建回复消息
        marry_msg = marry_config.get_config('marry_message').data.format(nickname=wife_nickname)
        
        # 发送消息和头像
        avatar_image = await get_avatar_image(wife_user_id)
        if avatar_image:
            await bot.send([marry_msg, avatar_image])
        else:
            await bot.send(marry_msg)
        
        logger.info(f"用户 {user_id} 娶了 {wife_nickname}({wife_user_id})")
        
    except Exception as e:
        logger.error(f"娶群友功能执行失败: {e}")
        await bot.send('哎呀，出错了，请稍后再试～')


async def check_today_marriages(bot: Bot, ev: Event):
    """查看今日群内所有CP"""
    if not ev.group_id:
        await bot.send('该功能只能在群聊中使用！')
        return
    
    try:
        marry_file_path = get_group_marry_file_path(ev.group_id)
        marry_data = load_json_file(marry_file_path)
        
        if not marry_data:
            no_marriage_today_msg = marry_config.get_config('no_marriage_today_message').data
            await bot.send(no_marriage_today_msg)
            return
        
        # 构建CP列表消息
        cp_list = []
        user_data = get_multi_day_user_pool(ev.group_id)
        
        for user_id, wife_info in marry_data.items():
            user_nickname = user_data.get(user_id, {}).get('nickname', user_id)
            wife_nickname = wife_info.get('nickname', '未知')
            status = wife_info.get('status', '已结婚')
            
            # 根据状态添加不同的标记
            if status == '已离婚':
                cp_list.append(f"{user_nickname} 💔 {wife_nickname} (已离婚)")
            else:
                cp_list.append(f"{user_nickname} ❤️ {wife_nickname}")
        
        cp_list_title = marry_config.get_config('today_cp_list_title').data
        message = f"{cp_list_title}\n" + "\n".join(cp_list)
        await bot.send(message)
        
    except Exception as e:
        logger.error(f"查看今日cp失败: {e}")
        await bot.send('查看失败，请稍后再试～')


async def divorce_couple(bot: Bot, ev: Event):
    """离婚功能"""
    # 确保只在群聊中使用
    if not ev.group_id:
        await bot.send('该功能只能在群聊中使用！')
        return
    
    try:
        group_id = ev.group_id
        user_id = ev.user_id
        
        logger.info(f"用户 {user_id} 在群 {group_id} 尝试离婚")
        
        # 读取今日娶群友记录
        marry_file_path = get_group_marry_file_path(group_id)
        marry_data = load_json_file(marry_file_path)
        
        if not marry_data:
            no_marriage_today_msg = marry_config.get_config('no_marriage_today_message').data
            await bot.send(no_marriage_today_msg)
            return
        
        divorced_couple = None
        user_data = get_multi_day_user_pool(group_id)
        
        # 检查用户是否为娶方
        if user_id in marry_data:
            wife_info = marry_data[user_id]
            wife_user_id = wife_info.get('user_id')
            wife_nickname = wife_info.get('nickname', wife_user_id)
            user_nickname = user_data.get(user_id, {}).get('nickname', user_id)
            
            # 标记为已离婚
            marry_data[user_id]['status'] = '已离婚'
            marry_data[user_id]['divorce_time'] = datetime.now().isoformat()
            
            divorced_couple = (user_nickname, wife_nickname)
            logger.info(f"娶方 {user_id} 提出离婚，对象是 {wife_user_id}")
        
        # 检查用户是否为被娶方
        else:
            for husband_id, wife_info in marry_data.items():
                if wife_info.get('user_id') == user_id and wife_info.get('status') != '已离婚':
                    husband_nickname = user_data.get(husband_id, {}).get('nickname', husband_id)
                    wife_nickname = user_data.get(user_id, {}).get('nickname', user_id)
                    
                    # 标记为已离婚
                    marry_data[husband_id]['status'] = '已离婚'
                    marry_data[husband_id]['divorce_time'] = datetime.now().isoformat()
                    
                    divorced_couple = (husband_nickname, wife_nickname)
                    logger.info(f"被娶方 {user_id} 提出离婚，对象是 {husband_id}")
                    break
        
        if divorced_couple:
            # 保存离婚记录
            save_json_file(marry_file_path, marry_data)
            
            # 发送离婚消息
            divorce_msg = marry_config.get_config('divorce_success_message').data.format(
                husband=divorced_couple[0], 
                wife=divorced_couple[1]
            )
            await bot.send(divorce_msg)
        else:
            no_marriage_msg = marry_config.get_config('no_marriage_message').data
            await bot.send(no_marriage_msg)
            
    except Exception as e:
        logger.error(f"离婚功能执行失败: {e}")
        await bot.send('离婚失败，请稍后再试～')