import { useEffect, useState } from 'react'
import { createHtmlStyleDraft, createReferenceStyleDraft, publishStyleDraft, updateStyleDraft } from '../api'
import TemplatePreviewFrame from './TemplatePreviewFrame'

const MAPPING_FIELDS = [
  ['productImage', '商品图'],
  ['headline', '广告大标题'],
  ['productName', '商品名称'],
  ['brand', '品牌'],
  ['eyebrow', '英文眉题'],
  ['description', '广告描述'],
  ['price', '价格'],
  ['feature1', '卖点 1'],
  ['feature2', '卖点 2'],
  ['feature3', '卖点 3'],
  ['cta', '行动文案'],
]

function SourceIcon({ type }) {
  return <span aria-hidden="true">{type === 'html' ? '〈/〉' : '▣'}</span>
}

export default function StyleTemplateWizard({
  open,
  onClose,
  onPublished,
  visionConfig,
  onConfigureVision,
  previewAd,
  previewImageUrl,
}) {
  const [sourceType, setSourceType] = useState('html')
  const [file, setFile] = useState(null)
  const [userDirection, setUserDirection] = useState('')
  const [draft, setDraft] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setSourceType('html')
    setFile(null)
    setUserDirection('')
    setDraft(null)
    setBusy(false)
    setError('')
  }, [open])

  useEffect(() => {
    if (!open) return undefined
    function handleKeyDown(event) {
      if (event.key === 'Escape' && !busy) onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, busy, onClose])

  if (!open) return null

  async function analyzeSource() {
    if (!file) {
      setError(sourceType === 'html' ? '请选择 HTML 文件' : '请选择风格参考图')
      return
    }
    if (sourceType === 'reference' && !visionConfig) {
      setError('请先配置支持图片理解的视觉分析模型')
      return
    }
    setBusy(true)
    setError('')
    try {
      const result = sourceType === 'html'
        ? await createHtmlStyleDraft(file)
        : await createReferenceStyleDraft({ file, config: visionConfig, userDirection })
      setDraft(result)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  function updateField(field, value) {
    setDraft((current) => ({ ...current, [field]: value }))
    setError('')
  }

  function updatePalette(field, value) {
    setDraft((current) => ({ ...current, palette: { ...current.palette, [field]: value } }))
    setError('')
  }

  function updateBinding(field, nodeId) {
    setDraft((current) => {
      const bindings = { ...(current.bindings || {}) }
      if (nodeId) {
        Object.keys(bindings).forEach((currentField) => {
          if (currentField !== field && bindings[currentField] === nodeId) delete bindings[currentField]
        })
        bindings[field] = nodeId
      }
      else delete bindings[field]
      return { ...current, bindings }
    })
    setError('')
  }

  async function saveAndPublish() {
    if (!draft.name?.trim()) {
      setError('请填写风格名称')
      return
    }
    if (!draft.bindings?.headline || !draft.bindings?.productImage) {
      setError('请先完成广告大标题和商品图的字段映射')
      return
    }
    setBusy(true)
    setError('')
    try {
      const updated = await updateStyleDraft(draft.draft_id, {
        name: draft.name.trim(),
        description: draft.description.trim(),
        eyebrow: draft.eyebrow.trim(),
        headline: draft.headline.trim(),
        copy_tone: draft.copy_tone.trim(),
        headline_limit: Number(draft.headline_limit),
        visual_direction: draft.visual_direction.trim(),
        aspect_ratio: draft.aspect_ratio,
        palette: draft.palette,
        bindings: draft.bindings,
      })
      setDraft(updated)
      const published = await publishStyleDraft(draft.draft_id)
      onPublished(published)
      onClose()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="modal-backdrop template-wizard-backdrop" onMouseDown={(event) => event.target === event.currentTarget && !busy && onClose()}>
      <section className="template-wizard" role="dialog" aria-modal="true" aria-labelledby="style-template-wizard-title">
        <div className="modal-heading template-wizard-heading">
          <div><span>REUSABLE STYLE IMPORT</span><h2 id="style-template-wizard-title">添加风格模板</h2></div>
          <button type="button" aria-label="关闭" onClick={onClose} disabled={busy}>×</button>
        </div>

        {!draft ? (
          <div className="template-source-step">
            <p className="modal-intro">导入 HTML，或让视觉模型从参考图中提取可复用的配色、构图与文字层级。</p>
            <div className="template-source-options">
              <button type="button" className={sourceType === 'html' ? 'active' : ''} onClick={() => { setSourceType('html'); setFile(null); setError('') }} disabled={busy}>
                <SourceIcon type="html" /><strong>上传 HTML 模板</strong><small>无 AI 也可使用，推荐带 data-ad-field 标记</small>
              </button>
              <button type="button" className={sourceType === 'reference' ? 'active' : ''} onClick={() => { setSourceType('reference'); setFile(null); setError('') }} disabled={busy}>
                <SourceIcon type="image" /><strong>上传风格参考图</strong><small>使用视觉大模型生成可编辑模板草稿</small>
              </button>
            </div>

            <label className="template-file-drop">
              <input
                type="file"
                accept={sourceType === 'html' ? '.html,.htm,text/html' : 'image/png,image/jpeg,image/webp'}
                onChange={(event) => { setFile(event.target.files?.[0] || null); setError('') }}
                disabled={busy}
              />
              <span>{sourceType === 'html' ? '选择 HTML 文件' : '选择 JPG / PNG / WebP 参考图'}</span>
              <strong>{file ? file.name : '点击上传'}</strong>
            </label>

            {sourceType === 'reference' && (
              <div className="vision-analysis-settings">
                <div>
                  <span>视觉分析模型</span>
                  <strong>{visionConfig ? `${visionConfig.displayName || visionConfig.provider} · ${visionConfig.model}` : '尚未配置'}</strong>
                </div>
                <button type="button" onClick={onConfigureVision} disabled={busy}>{visionConfig ? '更换模型' : '配置模型'}</button>
                <label>
                  <span>补充分析要求（可选）</span>
                  <textarea rows="3" maxLength="500" value={userDirection} onChange={(event) => setUserDirection(event.target.value)} placeholder="例：保留左文右图构图，忽略原图品牌和水印" disabled={busy} />
                </label>
              </div>
            )}

            {error && <p className="template-wizard-error">! {error}</p>}
            <div className="template-wizard-actions single">
              <button className="save-button" type="button" onClick={analyzeSource} disabled={busy}>{busy ? (sourceType === 'html' ? '正在解析…' : 'AI 正在分析…') : '生成模板草稿'}</button>
            </div>
          </div>
        ) : (
          <div className="template-review-step">
            <div className="template-review-preview">
              <div className="template-review-label"><span>DRAFT PREVIEW</span><b>{draft.source_type === 'html' ? 'HTML 导入' : 'AI 参考图'}</b></div>
              <TemplatePreviewFrame templateHtml={draft.templateHtml} ad={previewAd} imageUrl={previewImageUrl} aspectRatio={draft.aspect_ratio} title="风格模板草稿预览" />
              {(draft.warnings || []).length > 0 && <ul className="template-warnings">{draft.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
            </div>

            <div className="template-review-form">
              <label className="modal-field"><span>风格名称 <b>*</b></span><input value={draft.name || ''} maxLength="40" onChange={(event) => updateField('name', event.target.value)} /></label>
              <label className="modal-field"><span>风格简介 <b>*</b></span><input value={draft.description || ''} maxLength="120" onChange={(event) => updateField('description', event.target.value)} /></label>
              <div className="modal-field-row">
                <label className="modal-field"><span>英文眉题</span><input value={draft.eyebrow || ''} maxLength="40" onChange={(event) => updateField('eyebrow', event.target.value)} /></label>
                <label className="modal-field"><span>默认大标题</span><input value={draft.headline || ''} maxLength="28" onChange={(event) => updateField('headline', event.target.value)} /></label>
              </div>
              <div className="modal-field-row">
                <label className="modal-field"><span>画布比例</span><select value={draft.aspect_ratio || '4:5'} onChange={(event) => updateField('aspect_ratio', event.target.value)}><option>4:5</option><option>1:1</option><option>3:4</option><option>16:9</option><option>9:16</option></select></label>
                <label className="modal-field"><span>标题字数上限</span><input type="number" min="8" max="28" value={draft.headline_limit || 16} onChange={(event) => updateField('headline_limit', event.target.value)} /></label>
              </div>
              <div className="palette-editor">
                {Object.entries({ background: '背景色', surface: '内容面', text: '文字色', accent: '强调色' }).map(([field, label]) => (
                  <label key={field}><span>{label}</span><div><input type="color" value={draft.palette?.[field] || '#ffffff'} onChange={(event) => updatePalette(field, event.target.value)} /><input value={draft.palette?.[field] || ''} maxLength="7" onChange={(event) => updatePalette(field, event.target.value)} /></div></label>
                ))}
              </div>

              {draft.nodes?.length > 0 && (
                <details className="field-mapping" open={!draft.bindings?.headline || !draft.bindings?.productImage}>
                  <summary>字段映射 <span>必须包含商品图和大标题</span></summary>
                  <div>
                    {MAPPING_FIELDS.map(([field, label]) => (
                      <label key={field}><span>{label}{['productImage', 'headline'].includes(field) && <b>*</b>}</span><select value={draft.bindings?.[field] || ''} onChange={(event) => updateBinding(field, event.target.value)}><option value="">不映射</option>{draft.nodes.map((node) => <option value={node.id} key={`${field}-${node.id}`}>{node.tag} · {node.text || node.class || node.id}</option>)}</select></label>
                    ))}
                  </div>
                </details>
              )}

              <label className="modal-field"><span>AI 文案语气</span><textarea rows="3" maxLength="300" value={draft.copy_tone || ''} onChange={(event) => updateField('copy_tone', event.target.value)} /></label>
              <label className="modal-field"><span>AI 视觉方向</span><textarea rows="4" maxLength="800" value={draft.visual_direction || ''} onChange={(event) => updateField('visual_direction', event.target.value)} /></label>

              {error && <p className="template-wizard-error">! {error}</p>}
              <div className="template-wizard-actions">
                <button className="test-button" type="button" onClick={() => { setDraft(null); setError('') }} disabled={busy}>重新选择</button>
                <button className="save-button" type="button" onClick={saveAndPublish} disabled={busy}>{busy ? '正在发布…' : '发布为可复用风格'}</button>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
