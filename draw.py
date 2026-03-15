import io
import gsuid_core
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import marry_config

_font_cache = {}
_help_img_cache = None

def get_font(size: int) -> ImageFont.FreeTypeFont:
    if size in _font_cache:
        return _font_cache[size]
        
    path_str = marry_config.get_config('cp_font_path').data
    if path_str:
        font_path = Path(path_str)
        if font_path.exists():
            font = ImageFont.truetype(str(font_path), size)
            _font_cache[size] = font
            return font
            
    core_dir = Path(gsuid_core.__file__).parent
    default_font = core_dir / 'utils' / 'fonts' / 'MiSans-Bold.ttf'
    
    if default_font.exists():
        font = ImageFont.truetype(str(default_font), size)
        _font_cache[size] = font
        return font
        
    return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    lines, line = [], ""
    for char in text:
        if font.getlength(line + char) <= max_width:
            line += char
        else:
            lines.append(line)
            line = char
    if line: lines.append(line)
    return lines

def generate_glass_bg(width: int, height: int, panel_box: tuple, radius: int = 20) -> Image.Image:
    """生成带有局部毛玻璃面板的背景"""
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
        bg = bg.resize((width, height), Image.Resampling.BILINEAR)
    else:
        # 默认蓝粉双色渐变背景
        base = Image.new('RGB', (1, 2))
        base.putpixel((0, 0), (161, 196, 253))
        base.putpixel((0, 1), (255, 193, 204))
        bg = base.resize((width, height), Image.Resampling.BILINEAR)

    # 制作毛玻璃面板蒙版
    mask = Image.new('L', (width, height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle(panel_box, radius=radius, fill=255)
    
    # 抠出中心区域并模糊
    glass = bg.copy().crop(panel_box)
    glass = glass.filter(ImageFilter.BoxBlur(15))
    tint = Image.new('RGBA', glass.size, (255, 255, 255, 150))
    glass = Image.alpha_composite(glass.convert('RGBA'), tint).convert('RGB')
    
    # 贴回原图
    bg.paste(glass, (panel_box[0], panel_box[1]), mask.crop(panel_box))
    
    return bg

def draw_cp_image(cps_data: list, title: str) -> bytes:
    width, title_h, padding = 800, 100, 30
    font_title, font_item = get_font(42), get_font(30)
    
    footer_text = marry_config.get_config('footer_text').data
    font_footer = get_font(18)  # 进一步缩小字号
    
    # 动态布局边距：如果有页脚，则底部多留出空间
    side_margin = 25
    top_margin = 25
    bottom_margin = 45 if footer_text else 25
    
    assets_dir = Path(__file__).parent / 'assets'
    heart_path = assets_dir / 'heart.png'
    broken_heart_path = assets_dir / 'broken_heart.png'
    
    heart_img = Image.open(heart_path).convert("RGBA") if heart_path.exists() else None
    broken_heart_img = Image.open(broken_heart_path).convert("RGBA") if broken_heart_path.exists() else None
    
    icon_width = max(heart_img.width if heart_img else 40, broken_heart_img.width if broken_heart_img else 40)
    max_name_width = (width - side_margin * 2) // 2 - (icon_width // 2) - 20 
    
    parsed_cps, total_list_h = [], 0
    line_spacing, min_row_h = 38, 65    
    
    for n1, n2, is_married in cps_data:
        lines1 = wrap_text(n1, font_item, max_name_width)
        right_str = n2 if is_married else f"{n2} (离)"
        lines2 = wrap_text(right_str, font_item, max_name_width)
        row_h = max(min_row_h, max(len(lines1), len(lines2)) * line_spacing + 20)
        
        parsed_cps.append({
            'n1_text': "\n".join(lines1),
            'n2_text': "\n".join(lines2),
            'is_married': is_married,
            'row_h': row_h
        })
        total_list_h += row_h

    # 精确计算高度与毛玻璃面板的坐标
    panel_h = title_h + total_list_h + padding
    height = top_margin + panel_h + bottom_margin
    panel_box = (side_margin, top_margin, width - side_margin, top_margin + panel_h)
    
    bg = generate_glass_bg(width, height, panel_box)
    draw = ImageDraw.Draw(bg)
    center_x = width // 2
    
    draw.text((center_x, top_margin + 40), title, font=font_title, fill=(50, 50, 50), anchor="mm")
    line_y = top_margin + 85
    draw.line((side_margin + 40, line_y, width - side_margin - 40, line_y), fill=(180, 180, 180), width=2)
    
    current_y = line_y + 40
    for cp in parsed_cps:
        row_center_y = current_y + cp['row_h'] // 2 - 10
        if cp['is_married']:
            color_text, current_icon = (60, 60, 60), heart_img
        else:
            color_text, current_icon = (120, 120, 120), broken_heart_img

        draw.multiline_text((center_x - (icon_width // 2) - 10, row_center_y), cp['n1_text'], 
                            font=font_item, fill=color_text, anchor="rm", align="right", spacing=8)
        
        if current_icon:
            paste_x = center_x - current_icon.width // 2
            paste_y = int(row_center_y) - current_icon.height // 2
            bg.paste(current_icon, (paste_x, paste_y), current_icon)
        else:
            draw.text((center_x, row_center_y), "X", font=font_item, fill=(180, 180, 180), anchor="mm")
        
        draw.multiline_text((center_x + (icon_width // 2) + 10, row_center_y), cp['n2_text'], 
                            font=font_item, fill=color_text, anchor="lm", align="left", spacing=8)
        current_y += cp['row_h']
        
    # 在毛玻璃面板外面(底部空白处)绘制带白色描边的页脚
    if footer_text:
        footer_y = height - (bottom_margin // 2)
        draw.text((center_x, footer_y), footer_text, font=font_footer, fill=(50, 50, 50), 
                  stroke_width=1, stroke_fill=(255, 255, 255), anchor="mm")
    
    buf = io.BytesIO()
    bg.save(buf, format='PNG')
    return buf.getvalue()

def draw_help_image() -> bytes:
    global _help_img_cache
    if _help_img_cache:
        return _help_img_cache

    width, title_h, padding = 850, 110, 30
    font_title, font_cmd, font_desc = get_font(46), get_font(34), get_font(30)
    
    footer_text = marry_config.get_config('footer_text').data
    font_footer = get_font(18)  # 进一步缩小字号
    
    side_margin = 25
    top_margin = 25
    bottom_margin = 45 if footer_text else 25 
    
    help_items = [
        ("娶群友 / waifu", "随机娶一个群友做今日老婆"),
        ("强娶@用户", "强制娶指定用户 (受每日次数和成功率限制)"),
        ("离婚", "解除今日婚姻关系，双方恢复单身状态"),
        ("今日cp", "生成榜单图片，查看今天群内所有的CP配配对情况"),
        ("强娶记录", "查看个人今日的强娶次数记录和成功率"),
        ("娶群友设置", "查看当前群内的娶群友各项数值配置"),
        ("清除今日娶群友", "清除今日产生的所有数据 (仅限管理员使用)")
    ]
    
    cmd_x, desc_x = side_margin + 40, side_margin + 340
    desc_max_width = width - desc_x - side_margin - 20
    parsed_items, total_items_h = [], 0
    
    for cmd, desc in help_items:
        lines = wrap_text(desc, font_desc, desc_max_width)
        item_h = max(55, len(lines) * 40) + 20 
        parsed_items.append((cmd, lines, item_h))
        total_items_h += item_h
        
    # 精确计算高度与毛玻璃面板的坐标
    panel_h = title_h + total_items_h + padding
    height = top_margin + panel_h + bottom_margin
    panel_box = (side_margin, top_margin, width - side_margin, top_margin + panel_h)
    
    bg = generate_glass_bg(width, height, panel_box)
    draw = ImageDraw.Draw(bg)
    
    draw.text((width // 2, top_margin + 45), "娶群友 功能帮助", font=font_title, fill=(50, 50, 50), anchor="mm")
    line_y = top_margin + 100
    draw.line((side_margin + 40, line_y, width - side_margin - 40, line_y), fill=(180, 180, 180), width=2)
    
    current_y = line_y + 35
    for cmd, desc_lines, item_h in parsed_items:
        draw.text((cmd_x, current_y), cmd, font=font_cmd, fill=(220, 60, 100), anchor="lt")
        text_y = current_y + 2
        for line in desc_lines:
            draw.text((desc_x, text_y), line, font=font_desc, fill=(70, 70, 70), anchor="lt")
            text_y += 40
        current_y += item_h
        
    # 在毛玻璃面板外面(底部空白处)绘制带白色描边的页脚
    if footer_text:
        footer_y = height - (bottom_margin // 2)
        draw.text((width // 2, footer_y), footer_text, font=font_footer, fill=(50, 50, 50), 
                  stroke_width=1, stroke_fill=(255, 255, 255), anchor="mm")
    
    buf = io.BytesIO()
    bg.save(buf, format='PNG')
    
    _help_img_cache = buf.getvalue()
    return _help_img_cache