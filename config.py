"""
配置文件
"""
from typing import Dict
from pathlib import Path
from gsuid_core.utils.plugins_config.gs_config import StringConfig
from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsStrConfig,
    GsBoolConfig,
    GsIntConfig,
)

# 建立配置项
CONFIG_DEFAULT: Dict[str, GSC] = {
    'marry_triggers': GsStrConfig(
        '娶群友触发词',
        '娶群友命令的触发词，多个词用逗号分隔（如：娶群友,waifu,wife）',
        '娶群友,waifu,wife',
    ),
    'enable_avatar': GsBoolConfig(
        '启用头像显示',
        '是否在娶群友时显示头像',
        True,
    ),
    'user_pool_days': GsIntConfig(
        '用户池天数',
        '娶群友时从近几天的发言用户中选择（1-30天）',
        3,
        30,
    ),
    'marry_message': GsStrConfig(
        '娶群友成功消息',
        '娶群友成功时的消息模板，{nickname}会被替换为对方昵称',
        '今天你的老婆是：{nickname}',
    ),
    'already_married_message': GsStrConfig(
        '已娶群友消息',
        '已经娶过群友时的消息模板',
        '你已经有老婆啦！',
    ),
    'already_married_by_others_message': GsStrConfig(
        '已被娶消息',
        '已被别人娶过时的消息模板',
        '今天你被娶过啦！',
    ),
    'no_users_message': GsStrConfig(
        '群里无人消息',
        '群里除了自己没有其他人时的消息',
        '群里没人哦',
    ),
    'force_marry_success_rate': GsIntConfig(
        '强娶成功率',
        '强娶功能的成功概率（1-100）',
        30,
        100,
    ),
    'force_marry_daily_limit': GsIntConfig(
        '强娶每日次数',
        '每人每天可以使用强娶的次数（1-10）',
        3,
        10,
    ),
    'allow_force_marry_non_speakers': GsBoolConfig(
        '允许强娶未发言用户',
        '是否允许强娶不在用户池中（未发言）的用户',
        True,
    ),
    'allow_force_marry_married_users': GsBoolConfig(
        '允许强娶已婚用户',
        '是否允许强娶已经结婚的用户（横刀夺爱）',
        True,
    ),
    'force_marry_married_user_denied_message': GsStrConfig(
        '强娶已婚用户被拒绝消息',
        '不允许强娶已婚用户时的提示消息',
        '该用户已经结婚了，无法强娶！请选择其他人。',
    ),
    'force_marry_success_message': GsStrConfig(
        '强娶成功消息',
        '强娶成功时的消息模板，{nickname}会被替换为对方昵称，{remaining}会被替换为剩余次数',
        '💪 强娶成功！今天你的老婆是：{nickname}\n今日还有 {remaining} 次强娶机会。',
    ),
    'force_marry_steal_success_message': GsStrConfig(
        '横刀夺爱成功消息',
        '强娶已婚用户成功时的特殊消息模板，{nickname}会被替换为对方昵称，{remaining}会被替换为剩余次数',
        '💪 横刀夺爱成功！今天你的老婆是：{nickname}\n今日还有 {remaining} 次强娶机会。',
    ),
    'force_marry_failed_message': GsStrConfig(
        '强娶失败消息',
        '强娶失败时的消息模板，{remaining}会被替换为剩余次数',
        '💥 强娶失败！今日还有 {remaining} 次强娶机会。',
    ),
    'divorce_success_message': GsStrConfig(
        '离婚成功消息',
        '离婚成功时的消息模板，{husband}和{wife}会被替换为对应昵称',
        '💔 {husband} 和 {wife} 已离婚！\n双方现在都可以重新娶群友了~',
    ),
    'no_marriage_message': GsStrConfig(
        '无婚姻关系消息',
        '用户没有结婚时尝试离婚的消息',
        '你今天还没有结婚呢，无法离婚！',
    ),
    'no_marriage_today_message': GsStrConfig(
        '今日无人结婚消息',
        '今日群内无人结婚时的消息',
        '今天还没有人娶群友呢！',
    ),
    'today_cp_list_title': GsStrConfig(
        '今日CP榜标题',
        '查看今日CP榜时的标题消息',
        '今日群内CP榜：',
    ),
}

# 配置文件路径 - 存放在插件自己的目录中
CONFIG_PATH = Path(__file__).parent / 'config.json'

# 创建配置对象
marry_config = StringConfig('GsMarry', CONFIG_PATH, CONFIG_DEFAULT)