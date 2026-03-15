import io
import gsuid_core
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import marry_config

def get_font(size: int) -> ImageFont.FreeTypeFont:
    """动态获取字体"""
    path_str = marry_config.get_config('cp_font_path').data
    if path_str:
        font_path = Path(path_str)
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)
    
    # 动态获取 gsuid_core 包的真实路径
    core_dir = Path(gsuid_core.__file__).parent
    default_font = core_dir / 'utils' / 'fonts' / 'MiSans-Bold.ttf'
    
    if default_font.exists():
        return ImageFont.truetype(str(default_font), size)
    return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """长文本自动换行计算"""
    lines = []
    line = ""
    for char in text:
        if font.getlength(line + char) <= max_width:
            line += char
        else:
            lines.append(line)
            line = char
    if line:
        lines.append(line)
    return lines

def generate_glass_bg(width: int, height: int, margin: int, radius: int = 20) -> tuple:
    """生成通用的毛玻璃背景基底"""
    bg_path_str = marry_config.get_config('cp_bg_image').data
    bg_path = Path(bg_path_str) if bg_path_str else None
    
    if bg_path and bg_path.exists():
        bg = Image.open(bg_path).convert('RGB')
        bg_ratio = bg.width / bg.height
        target_ratio = width / height
        if bg_ratio > target_ratio:
            new_w = int(bg.height * target_ratio)
            offset = (bg.width - new_w) // 2
            bg = bg.crop((offset, 0, offset + new_w, bg.height))
        else:
            new_h = int(bg.width / target_ratio)
            offset = (bg.height - new_h) // 2
            bg = bg.crop((0, offset, bg.width, offset + new_h))
        bg = bg.resize((width, height), Image.Resampling.LANCZOS)
    else:
        # 默认蓝粉双色渐变背景
        base = Image.new('RGB', (1, 2))
        base.putpixel((0, 0), (161, 196, 253))
        base.putpixel((0, 1), (255, 193, 204))
        bg = base.resize((width, height), Image.Resampling.BICUBIC)

    panel_box = (margin, margin, width - margin, height - margin)
    mask = Image.new('L', (width, height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle(panel_box, radius=radius, fill=255)
    
    glass = bg.copy().crop(panel_box)
    glass = glass.filter(ImageFilter.GaussianBlur(15))
    tint = Image.new('RGBA', glass.size, (255, 255, 255, 150)) # 半透明白色提亮
    glass = Image.alpha_composite(glass.convert('RGBA'), tint).convert('RGB')
    bg.paste(glass, (margin, margin), mask.crop(panel_box))
    
    return bg

def draw_cp_image(cps_data: list, title: str) -> bytes:
    """绘制今日CP榜单图 (支持超长名字自动换行)"""
    width = 800
    title_h = 100
    margin = 25  
    padding = 30
    
    font_title = get_font(42)
    font_item = get_font(30)
    font_icon = get_font(28) 
    
    max_name_width = (width - margin * 2) // 2 - 60 
    
    # 1. 预计算每一行的高度，并进行文本换行处理
    parsed_cps = []
    total_list_h = 0
    line_spacing = 38 # 多行文本的行高
    min_row_h = 65    # 单行最小高度
    
    for n1, n2, is_married in cps_data:
        # 左侧名字换行计算
        lines1 = wrap_text(n1, font_item, max_name_width)
        
        # 右侧名字换行计算 (包含离婚后缀)
        right_str = n2 if is_married else f"{n2} (离)"
        lines2 = wrap_text(right_str, font_item, max_name_width)
        
        # 这一行的高度取决于左右哪边行数更多
        max_lines = max(len(lines1), len(lines2))
        row_h = max(min_row_h, max_lines * line_spacing + 20)
        
        parsed_cps.append({
            'n1_text': "\n".join(lines1),
            'n2_text': "\n".join(lines2),
            'is_married': is_married,
            'row_h': row_h
        })
        total_list_h += row_h

    # 2. 计算动态总高度并生成背景
    panel_h = title_h + total_list_h + padding
    height = panel_h + margin * 2
    
    bg = generate_glass_bg(width, height, margin)
    draw = ImageDraw.Draw(bg)
    center_x = width // 2
    
    # 3. 绘制标题与下划线
    draw.text((center_x, margin + 40), title, font=font_title, fill=(50, 50, 50), anchor="mm")
    line_y = margin + 85
    draw.line((margin + 40, line_y, width - margin - 40, line_y), fill=(180, 180, 180), width=2)
    
    # 4. 绘制CP条目 (支持多行、精准对齐)
    current_y = line_y + 40
    for cp in parsed_cps:
        # 当前行的垂直中心点
        row_center_y = current_y + cp['row_h'] // 2 - 10
        
        if cp['is_married']:
            color_text = (60, 60, 60)
            color_heart = (230, 60, 100)
        else:
            color_text = (120, 120, 120)
            color_heart = (150, 150, 150)

        # 左名字 (多行，向右对齐排版)
        draw.multiline_text(
            (center_x - 25, row_center_y), 
            cp['n1_text'], 
            font=font_item, 
            fill=color_text, 
            anchor="rm", 
            align="right",
            spacing=8
        )
        
        # 爱心 (绝对居中)
        draw.text(
            (center_x, row_center_y), 
            "❤", 
            font=font_icon, 
            fill=color_heart, 
            anchor="mm"
        )
        
        # 右名字 (多行，向左对齐排版)
        draw.multiline_text(
            (center_x + 25, row_center_y), 
            cp['n2_text'], 
            font=font_item, 
            fill=color_text, 
            anchor="lm", 
            align="left",
            spacing=8
        )
        
        current_y += cp['row_h']
    
    buf = io.BytesIO()
    bg.save(buf, format='PNG')
    return buf.getvalue()

def draw_help_image() -> bytes:
    """绘制帮助菜单图"""
    width = 850
    title_h = 110
    margin = 25
    padding = 30
    
    help_items = [
        ("娶群友 / waifu", "随机娶一个群友做今日老婆"),
        ("强娶@用户", "强制娶指定用户 (受每日次数和成功率限制)"),
        ("离婚", "解除今日婚姻关系，双方恢复单身状态"),
        ("今日cp", "生成榜单图片，查看今天群内所有的CP配对情况"),
        ("强娶记录", "查看个人今日的强娶次数记录和成功率"),
        ("娶群友设置", "查看当前群内的娶群友各项数值配置"),
        ("清除今日娶群友", "清除今日产生的所有数据 (仅限管理员使用)")
    ]
    
    font_title = get_font(46)
    font_cmd = get_font(34)
    font_desc = get_font(30)
    
    cmd_x = margin + 40
    desc_x = margin + 340
    desc_max_width = width - desc_x - margin - 20
    
    parsed_items = []
    total_items_h = 0
    
    for cmd, desc in help_items:
        lines = wrap_text(desc, font_desc, desc_max_width)
        item_h = max(55, len(lines) * 40) + 20 
        parsed_items.append((cmd, lines, item_h))
        total_items_h += item_h
        
    height = margin * 2 + title_h + total_items_h + padding
    
    bg = generate_glass_bg(width, height, margin)
    draw = ImageDraw.Draw(bg)
    
    draw.text((width // 2, margin + 45), "娶群友 功能帮助", font=font_title, fill=(50, 50, 50), anchor="mm")
    line_y = margin + 100
    draw.line((margin + 40, line_y, width - margin - 40, line_y), fill=(180, 180, 180), width=2)
    
    current_y = line_y + 35
    for cmd, desc_lines, item_h in parsed_items:
        draw.text((cmd_x, current_y), cmd, font=font_cmd, fill=(220, 60, 100), anchor="lt")
        
        text_y = current_y + 2
        for line in desc_lines:
            draw.text((desc_x, text_y), line, font=font_desc, fill=(70, 70, 70), anchor="lt")
            text_y += 40
            
        current_y += item_h
    
    buf = io.BytesIO()
    bg.save(buf, format='PNG')
    return buf.getvalue()