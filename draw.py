import io
import gsuid_core
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import marry_config

def get_font(size: int) -> ImageFont.FreeTypeFont:
    """动态获取字体，支持用户配置或自动溯源 GsCore 默认字体"""
    path_str = marry_config.get_config('cp_font_path').data
    if path_str:
        font_path = Path(path_str)
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)
    
    # 动态获取 gsuid_core 包的真实路径，无视外部文件夹叫什么名字
    core_dir = Path(gsuid_core.__file__).parent
    default_font = core_dir / 'utils' / 'fonts' / 'MiSans-Bold.ttf'
    
    if default_font.exists():
        return ImageFont.truetype(str(default_font), size)
    return ImageFont.load_default()

def draw_cp_image(cps_data: list, title: str) -> bytes:
    """绘制半透明毛玻璃质感的 CP 榜单图"""
    width = 800
    item_h = 65
    title_h = 120
    margin = 50
    padding = 40
    
    # 动态计算整个画布的高度
    panel_h = title_h + len(cps_data) * item_h + padding
    height = panel_h + margin * 2
    
    # 处理背景图
    bg_path_str = marry_config.get_config('cp_bg_image').data
    bg_path = Path(bg_path_str) if bg_path_str else None
    
    if bg_path and bg_path.exists():
        bg = Image.open(bg_path).convert('RGB')
        # 居中裁剪适配比例
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
        base.putpixel((0, 0), (161, 196, 253))  # 顶部蓝色
        base.putpixel((0, 1), (255, 193, 204))  # 底部粉色
        bg = base.resize((width, height), Image.Resampling.BICUBIC)

    # 计算中间毛玻璃面板的坐标
    panel_box = (margin, margin, width - margin, height - margin)
    
    # 1. 制作圆角遮罩
    mask = Image.new('L', (width, height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle(panel_box, radius=25, fill=255)
    
    # 2. 抠出背景部分进行高斯模糊（核心毛玻璃特效）
    glass = bg.copy().crop(panel_box)
    glass = glass.filter(ImageFilter.GaussianBlur(18))
    
    # 3. 盖上一层半透明白色薄膜提亮，确保黑色文字清晰可见
    tint = Image.new('RGBA', glass.size, (255, 255, 255, 130))
    glass = Image.alpha_composite(glass.convert('RGBA'), tint).convert('RGB')
    
    # 4. 把处理好的毛玻璃贴回原图
    bg.paste(glass, (margin, margin), mask.crop(panel_box))
    
    # 准备绘制文字
    draw = ImageDraw.Draw(bg)
    font_title = get_font(45)
    font_item = get_font(32)
    
    # 绘制标题
    draw.text((width // 2, margin + 50), title, font=font_title, fill=(60, 60, 60), anchor="mm")
    
    # 绘制标题下的分割线
    line_y = margin + 100
    draw.line((margin + 60, line_y, width - margin - 60, line_y), fill=(200, 200, 200), width=3)
    
    # 绘制CP条目
    start_y = line_y + 45
    for i, (n1, n2, is_married) in enumerate(cps_data):
        y = start_y + i * item_h
        if is_married:
            text = f"{n1} ❤️ {n2}"
            color = (220, 70, 110)  # 热恋的深粉红色
        else:
            text = f"{n1} 💔 {n2} (已离婚)"
            color = (130, 130, 130) # 离婚的灰色
            
        draw.text((width // 2, y), text, font=font_item, fill=color, anchor="mm")
    
    # 导出为图片字节流
    buf = io.BytesIO()
    bg.save(buf, format='PNG')
    return buf.getvalue()