"""
数据管理模块
负责文件路径管理、JSON数据读写、数据目录管理等功能
"""
import json
import os
from datetime import datetime
from pathlib import Path
from gsuid_core.logger import logger

# 获取数据目录路径 - 使用插件自己的data目录
DATA_PATH = Path(__file__).parent / 'data'


def ensure_data_dir():
    """确保数据目录存在"""
    if not DATA_PATH.exists():
        DATA_PATH.mkdir(parents=True, exist_ok=True)


def get_today_str():
    """获取今日日期字符串"""
    return datetime.now().strftime('%Y-%m-%d')


def get_group_user_file_path(group_id: str) -> Path:
    """获取群聊用户记录文件路径"""
    today = get_today_str()
    return DATA_PATH / f"{group_id}-{today}.json"


def get_group_marry_file_path(group_id: str) -> Path:
    """获取群聊娶群友记录文件路径"""
    today = get_today_str()
    return DATA_PATH / f"{group_id}-{today}-marry.json"


def get_group_force_marry_file_path(group_id: str) -> Path:
    """获取群聊强娶记录文件路径"""
    today = get_today_str()
    return DATA_PATH / f"{group_id}-{today}-force.json"


def load_json_file(file_path: Path) -> dict:
    """加载JSON文件"""
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败: {file_path}, 错误: {e}")
            return {}
    return {}


def save_json_file(file_path: Path, data: dict):
    """保存JSON文件"""
    ensure_data_dir()
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存JSON文件失败: {file_path}, 错误: {e}")


def record_user(group_id: str, user_id: str, nickname: str):
    """记录发言用户"""
    try:
        file_path = get_group_user_file_path(group_id)
        user_data = load_json_file(file_path)
        
        # 记录用户信息
        user_data[user_id] = {
            'nickname': nickname,
            'last_speak_time': datetime.now().isoformat()
        }
        
        save_json_file(file_path, user_data)
        logger.debug(f"记录用户 {nickname}({user_id}) 发言到群 {group_id}")
    except Exception as e:
        logger.error(f"记录用户发言失败: {e}")