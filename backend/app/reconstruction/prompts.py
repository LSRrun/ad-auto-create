from ..styles import get_style
from .schemas import PageSnapshot


STYLE_DIRECTIONS = {
    "quiet-luxury": "克制的高端静奢风，大面积温暖留白，细腻材质，柔和自然光，精致而安静",
    "natural-spa": "自然疗愈风，柔和绿色、石材和木质氛围，松弛、干净、具有居家水疗感",
    "midnight-tech": "暗夜科技风，黑金对比，克制的光带和现代几何结构，专业、智能、未来感",
}


def build_reconstruction_prompt(snapshot: PageSnapshot) -> str:
    style = get_style(snapshot.style_id) or {}
    product = snapshot.product
    ad = snapshot.ad
    features = "、".join(ad.features) or product.selling_points or "未提供"
    palette = style.get("palette", {})
    direction = STYLE_DIRECTIONS.get(snapshot.style_id, "高端、简洁、适合卫浴品牌的商业摄影风格")
    return f"""
你是一名商业卫浴广告视觉设计师。请参考输入的真实商品图片，为下面的广告制作一张高级背景底图。

视觉方向：{direction}
建议色彩：背景 {palette.get('background', '#f3f0ea')}，强调色 {palette.get('accent', '#607966')}
商品名称：{product.product_name}
品牌：{product.brand or '未提供'}
广告标题：{ad.headline}
广告描述：{ad.description}
核心卖点：{features}

最高优先级约束：
1. 输入图片中的商品是唯一真实商品参考。必须理解其品类、材质、颜色和比例。
2. 最终底图中不要绘制、复制或重画商品本体；程序会在之后把原始商品像素合成进去。
3. 不要生成任何文字、字母、数字、Logo、水印、标签或伪文字。
4. 画面右侧预留约 45% 的干净商品展示区域，背景连续，不能出现其他商品或相似卫浴设备。
5. 画面左侧预留清晰的文案安全区，不要放置复杂高对比元素。
6. 输出应是完整的竖版商业广告背景，具有真实摄影质感、柔和光影和清晰层次。

只生成背景与空间氛围，不生成商品，不生成文字。
""".strip()
