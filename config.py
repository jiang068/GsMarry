from typing import Dict
from gsuid_core.data_store import get_res_path
from gsuid_core.utils.plugins_config.gs_config import StringConfig
from gsuid_core.utils.plugins_config.models import GSC, GsStrConfig, GsBoolConfig, GsIntConfig

CONFIG_DEFAULT: Dict[str, GSC] = {
    'marry_triggers': GsStrConfig('娶群友触发词', '多词逗号分隔', '娶群友,waifu,wife'),
    'enable_avatar': GsBoolConfig('启用头像显示', '是否发送头像', True),
    'user_pool_days': GsIntConfig('用户池天数', '近几天发言有效', 3, 30),
    'marry_message': GsStrConfig('娶群友成功消息', '模板', '今天你的老婆是：{nickname}'),
    'already_married_message': GsStrConfig('已娶消息', '模板', '你已经有老婆啦！'),
    'already_married_by_others_message': GsStrConfig('已被娶消息', '模板', '今天你被娶过啦！'),
    'no_users_message': GsStrConfig('群里无人消息', '模板', '群里没人哦'),
    'force_marry_success_rate': GsIntConfig('强娶成功率', '1-100', 30, 100),
    'force_marry_daily_limit': GsIntConfig('强娶每日次数', '1-10', 3, 10),
    'allow_force_marry_non_speakers': GsBoolConfig('允许强娶未发言用户', '是/否', True),
    'allow_force_marry_married_users': GsBoolConfig('允许横刀夺爱', '是/否', True),
    'force_marry_married_user_denied_message': GsStrConfig('强娶已婚被拒消息', '模板', '该用户已经结婚了，无法强娶！'),
    'force_marry_success_message': GsStrConfig('强娶成功消息', '模板', '💪 强娶成功！老婆是：{nickname}\n今日还有 {remaining} 次。'),
    'force_marry_steal_success_message': GsStrConfig('横刀夺爱消息', '模板', '💪 横刀夺爱成功！老婆是：{nickname}\n今日还有 {remaining} 次。'),
    'force_marry_failed_message': GsStrConfig('强娶失败消息', '模板', '💥 强娶失败！今日还有 {remaining} 次。'),
    'divorce_success_message': GsStrConfig('离婚成功消息', '模板', '💔 {husband} 和 {wife} 已离婚！'),
    'no_marriage_message': GsStrConfig('无婚姻关系消息', '模板', '你今天还没有结婚呢！'),
    'no_marriage_today_message': GsStrConfig('今日无人结婚', '模板', '今天还没有人娶群友呢！'),
    'today_cp_list_title': GsStrConfig('今日CP榜标题', '模板', '今日群内CP榜：'),
}

# 指向官方指定目录下的 config.json
CONFIG_PATH = get_res_path('GsMarry') / 'config.json'
marry_config = StringConfig('GsMarry', CONFIG_PATH, CONFIG_DEFAULT)