import { useEffect, useMemo, useState } from 'react'
import { generateAd, getStyles } from './api'

const fallbackStyles = [
  { id: 'quiet-luxury', name: '静奢白', description: '精致留白，适合高端单品', palette: { background: '#f3f0ea', surface: '#fff', text: '#20211f', accent: '#826b4d' } },
  { id: 'natural-spa', name: '自然疗愈', description: '自然色彩，营造松弛氛围', palette: { background: '#dfe7df', surface: '#f6f4ed', text: '#24352c', accent: '#607966' } },
  { id: 'midnight-tech', name: '暗夜科技', description: '黑金质感，突出智能科技', palette: { background: '#141718', surface: '#222728', text: '#f3f0e8', accent: '#c9a86a' } },
]

const sampleAd = {
  brand: 'MUJING',
  eyebrow: 'QUIET LUXURY',
  headline: '让日常，更有质感',
  productName: '智能恒温花洒',
  description: '从出水到恒温，每一处都用更贴心的细节，让沐浴回归纯粹享受。',
  price: '¥1,299 起',
  features: ['38°C 智能恒温', '钢琴按键出水', '大顶喷沉浸体验'],
  cta: '立即了解',
}

function UploadIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 15v4h14v-4" /></svg>
}

function SparkIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l1.5 5.5L19 9l-5.5 1.5L12 16l-1.5-5.5L5 9l5.5-1.5L12 2zM19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7L19 15z" /></svg>
}

function AdPreview({ ad, style, imageUrl }) {
  const palette = style?.palette || fallbackStyles[0].palette
  return (
    <article className={`ad-canvas style-${style?.id || 'quiet-luxury'}`} style={{ '--ad-bg': palette.background, '--ad-surface': palette.surface, '--ad-text': palette.text, '--ad-accent': palette.accent }}>
      <div className="ad-topline"><span>{ad.brand}</span><span>BATHROOM COLLECTION / 2026</span></div>
      <div className="ad-copy">
        <p className="ad-eyebrow">{ad.eyebrow}</p>
        <h2>{ad.headline}</h2>
        <h3>{ad.productName}</h3>
        <p className="ad-description">{ad.description}</p>
        <ul>{ad.features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
        <div className="ad-action"><strong>{ad.price}</strong><span>{ad.cta} <b>↗</b></span></div>
      </div>
      <div className={`product-stage ${imageUrl ? 'has-image' : ''}`}>
        {imageUrl ? <img src={imageUrl} alt={ad.productName} /> : <div className="empty-product"><SparkIcon /><span>上传商品图片</span><small>广告效果将在这里预览</small></div>}
      </div>
      <span className="ad-page-number">01</span>
    </article>
  )
}

export default function App() {
  const [styles, setStyles] = useState(fallbackStyles)
  const [selectedStyle, setSelectedStyle] = useState('quiet-luxury')
  const [imageFile, setImageFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [ad, setAd] = useState(sampleAd)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getStyles().then((data) => setStyles(data.items)).catch(() => {})
  }, [])

  useEffect(() => () => previewUrl && URL.revokeObjectURL(previewUrl), [previewUrl])

  const activeStyle = useMemo(() => styles.find((item) => item.id === selectedStyle) || styles[0], [styles, selectedStyle])

  function selectImage(event) {
    const file = event.target.files?.[0]
    if (!file) return
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setImageFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    formData.set('style_id', selectedStyle)
    if (imageFile) formData.set('image', imageFile)
    setLoading(true)
    setError('')
    try {
      const result = await generateAd(formData)
      setAd(result)
      if (result.imageUrl) setPreviewUrl(result.imageUrl)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top"><span>沐</span><div><strong>沐境</strong><small>MUJING STUDIO</small></div></a>
        <div className="header-note"><i /> 广告创意工作台</div>
      </header>

      <section className="intro" id="top">
        <p><span>01</span> PRODUCT TO CAMPAIGN</p>
        <h1>一件商品，<br /><em>一张好广告。</em></h1>
        <p className="intro-copy">上传你的卫浴产品，选择视觉风格。<br />我们为你组合文案、卖点与画面。</p>
      </section>

      <div className="workspace">
        <form className="control-panel" onSubmit={handleSubmit}>
          <div className="panel-title"><span>01</span><div><h2>商品信息</h2><p>PRODUCT DETAILS</p></div></div>
          <label className="upload-box">
            <input type="file" accept="image/png,image/jpeg,image/webp" onChange={selectImage} />
            {previewUrl ? <img src={previewUrl} alt="商品预览" /> : <><UploadIcon /><strong>上传商品图</strong><span>建议使用纯色背景，JPG / PNG / WebP</span></>}
            {previewUrl && <span className="replace-image">点击更换图片</span>}
          </label>

          <div className="field-row">
            <label><span>品牌名称</span><input name="brand" placeholder="例：MUJING" /></label>
            <label><span>商品价格</span><input name="price" placeholder="例：¥1,299 起" /></label>
          </div>
          <label><span>商品名称 <b>*</b></span><input name="product_name" required maxLength="80" placeholder="例：智能恒温花洒" /></label>
          <label><span>核心卖点</span><textarea name="selling_points" rows="3" placeholder="用逗号分隔，例：38°C 恒温，钢琴按键，大顶喷" /></label>

          <div className="panel-title style-title"><span>02</span><div><h2>选择风格</h2><p>VISUAL DIRECTION</p></div></div>
          <div className="style-list">
            {styles.map((style) => (
              <button type="button" className={selectedStyle === style.id ? 'selected' : ''} key={style.id} onClick={() => setSelectedStyle(style.id)}>
                <i style={{ background: `linear-gradient(135deg, ${style.palette.background} 50%, ${style.palette.accent} 50%)` }} />
                <span><strong>{style.name}</strong><small>{style.description}</small></span>
                <b>{selectedStyle === style.id ? '✓' : ''}</b>
              </button>
            ))}
          </div>
          {error && <p className="error-message">{error}</p>}
          <button className="generate-button" type="submit" disabled={loading}><SparkIcon />{loading ? '正在生成…' : '生成广告页面'}<span>→</span></button>
        </form>

        <section className="preview-panel">
          <div className="preview-heading"><div><span>LIVE PREVIEW</span><h2>广告预览</h2></div><small><i /> 实时画布</small></div>
          <div className="canvas-shell"><AdPreview ad={ad} style={activeStyle} imageUrl={previewUrl} /></div>
          <p className="preview-tip">* 预览会根据选择的风格自动调整色彩与排版</p>
        </section>
      </div>

      <footer><span>MUJING CREATIVE TOOL</span><span>用设计，让好产品被看见。</span><span>2026 / V0.1</span></footer>
    </main>
  )
}

