import json
import random
from datetime import datetime, timedelta
from gsuid_core.data_store import get_res_path
from .config import marry_config

# 使用框架自带的路径生成器规范化数据路径
DATA_DIR = get_res_path('GsMarry')
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)

def get_today() -> str:
    return datetime.now().strftime('%Y-%m-%d')

def load_data(gid: str) -> dict:
    f = DATA_DIR / f"{gid}.json"
    return json.loads(f.read_text('utf-8')) if f.exists() else {"users": {}, "daily": {}}

def save_data(gid: str, data: dict):
    (DATA_DIR / f"{gid}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')

def get_daily(data: dict) -> dict:
    t = get_today()
    if t not in data["daily"]: 
        data["daily"][t] = {"couples": {}, "forces": {}, "divorced": []}
    # 兼容老数据，如果没有 divorced 列表则补上
    if "divorced" not in data["daily"][t]:
        data["daily"][t]["divorced"] = []
    return data["daily"][t]

def record_speak(gid: str, uid: str, name: str):
    d = load_data(gid)
    d["users"][uid] = {"name": name, "last": get_today()}
    save_data(gid, d)

def get_active_users(d: dict) -> list:
    days = marry_config.get_config('user_pool_days').data
    cutoff = datetime.now() - timedelta(days=days)
    active = []
    for uid, info in d["users"].items():
        if datetime.strptime(info["last"], '%Y-%m-%d') >= cutoff:
            active.append(uid)
    return active

def process_marry(gid: str, uid: str) -> tuple[int, str, str]:
    # 状态码 -> 0: 成功, 1: 已有配偶, 3: 池子空
    d = load_data(gid)
    daily = get_daily(d)

    # 只要存在双向绑定中，就说明已婚
    if uid in daily["couples"]:
        partner = daily["couples"][uid]
        return 1, partner, d["users"].get(partner, {}).get("name", partner)

    active = get_active_users(d)
    available = [u for u in active if u != uid and u not in daily["couples"]]

    if not available:
        return 3, "", ""

    partner = random.choice(available)
    # 建立绝对对称的双向绑定
    daily["couples"][uid] = partner
    daily["couples"][partner] = uid
    save_data(gid, d)

    return 0, partner, d["users"][partner]["name"]

def process_force_marry(gid: str, uid: str, target: str, target_name: str) -> tuple[bool, str]:
    d = load_data(gid)
    daily = get_daily(d)

    limit = marry_config.get_config('force_marry_daily_limit').data
    forces = daily["forces"].get(uid, {"count": 0, "success": 0})
    if isinstance(forces, int): forces = {"count": forces, "success": 0}

    if forces["count"] >= limit:
        return False, f"你今天的强娶次数已用完！每日限{limit}次。"

    if uid in daily["couples"]:
        return False, "你已经有老婆了，不能强娶！请先离婚。"

    target_married = target in daily["couples"]
    if target_married and not marry_config.get_config('allow_force_marry_married_users').data:
        return False, marry_config.get_config('force_marry_married_user_denied_message').data

    if target not in d["users"] and not marry_config.get_config('allow_force_marry_non_speakers').data:
        return False, "该用户未在群内发言，无法强娶！"

    forces["count"] += 1
    rem = limit - forces["count"]
    daily["forces"][uid] = forces

    rate = marry_config.get_config('force_marry_success_rate').data
    if random.randint(1, 100) > rate:
        save_data(gid, d)
        return False, marry_config.get_config('force_marry_failed_message').data.format(remaining=rem)

    # 强娶成功
    forces["success"] += 1
    if target_married:
        old_partner = daily["couples"][target]
        # 【新增】横刀夺爱导致原配偶被动离婚，记录到离婚池中
        daily["divorced"].append((target, old_partner))
        del daily["couples"][old_partner] # 踢掉原来的配偶

    # 建立新的双向绑定
    daily["couples"][uid] = target
    daily["couples"][target] = uid

    if target not in d["users"]:
        d["users"][target] = {"name": target_name, "last": get_today()}

    save_data(gid, d)
    msg_key = 'force_marry_steal_success_message' if target_married else 'force_marry_success_message'
    return True, marry_config.get_config(msg_key).data.format(nickname=d["users"][target]["name"], remaining=rem)

def process_divorce(gid: str, uid: str) -> tuple[bool, str, str]:
    d = load_data(gid)
    daily = get_daily(d)
    
    if uid not in daily["couples"]:
        return False, "", ""

    # 解除双向绑定
    partner = daily["couples"][uid]
    
    # 【新增】将这对苦命鸳鸯加入离婚记录表
    daily["divorced"].append((uid, partner))

    del daily["couples"][uid]
    if partner in daily["couples"]: 
        del daily["couples"][partner]
    
    save_data(gid, d)
    return True, d["users"].get(uid, {}).get("name", uid), d["users"].get(partner, {}).get("name", partner)

def get_cps_data(gid: str) -> list:
    """返回结构化的CP列表供绘图使用：[(名字1, 名字2, 是否处于结婚状态)]"""
    d = load_data(gid)
    daily = get_daily(d)
    seen, res = set(), []
    
    # 1. 获取当前热恋中的CP
    for u1, u2 in daily["couples"].items():
        if u1 in seen or u2 in seen: continue
        seen.add(u1); seen.add(u2)
        n1 = d["users"].get(u1, {}).get("name", u1)
        n2 = d["users"].get(u2, {}).get("name", u2)
        res.append((n1, n2, True))
        
    # 2. 获取今日离婚的CP
    for u1, u2 in daily.get("divorced", []):
        n1 = d["users"].get(u1, {}).get("name", u1)
        n2 = d["users"].get(u2, {}).get("name", u2)
        res.append((n1, n2, False))
        
    return res

def get_force_record(gid: str, uid: str) -> str:
    d = load_data(gid)
    daily = get_daily(d)
    limit = marry_config.get_config('force_marry_daily_limit').data
    forces = daily["forces"].get(uid, {"count": 0, "success": 0})
    if isinstance(forces, int): forces = {"count": forces, "success": 0}

    c, s = forces["count"], forces["success"]
    rate = (s / c * 100) if c > 0 else 0
    return f"你的强娶记录：\n今日尝试：{c}/{limit}\n剩余次数：{limit - c}\n成功次数：{s}\n成功率：{rate:.1f}%"