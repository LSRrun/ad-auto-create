import { useEffect, useState } from 'react'

function createDraft(config, provider) {
  if (config) return { ...config }
  return {
    provider: provider?.id || 'custom-image',
    model: provider?.model || '',
    baseUrl: provider?.baseUrl || '',
    apiKey: '',
    size: '1024x1536',
    quality: 'medium',
  }
}

export default function ImageModelConfigModal({ open, config, providers, onClose, onSave, onTest }) {
  const [draft, setDraft] = useState(() => createDraft(config, providers[0]))
  const [testing, setTesting] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    if (open) {
      setDraft(createDraft(config, providers[0]))
      setMessage(null)
    }
  }, [open, config, providers])

  useEffect(() => {
    if (!open) return undefined
    function handleKeyDown(event) {
      if (event.key === 'Escape' && !testing) onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, testing, onClose])

  if (!open) return null

  const activeProvider = providers.find((item) => item.id === draft.provider)

  function updateField(field, value) {
    setDraft((current) => ({ ...current, [field]: value }))
    setMessage(null)
  }

  function selectProvider(providerId) {
    const provider = providers.find((item) => item.id === providerId)
    setDraft({
      provider: providerId,
      model: provider?.model || '',
      baseUrl: provider?.baseUrl || '',
      apiKey: '',
      size: '1024x1536',
      quality: 'medium',
    })
    setMessage(null)
  }

  function validate() {
    if (!draft.model.trim()) return '请填写图片模型名称'
    if (!draft.baseUrl.trim()) return '请填写 Base URL'
    if (!draft.apiKey.trim()) return '请填写 API Key'
    return ''
  }

  async function testConnection() {
    const validationError = validate()
    if (validationError) {
      setMessage({ type: 'error', text: validationError })
      return
    }
    setTesting(true)
    setMessage(null)
    try {
      const result = await onTest(draft)
      setMessage({ type: 'success', text: result.message || '连接成功' })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setTesting(false)
    }
  }

  function saveConfig() {
    const validationError = validate()
    if (validationError) {
      setMessage({ type: 'error', text: validationError })
      return
    }
    onSave({
      ...draft,
      model: draft.model.trim(),
      baseUrl: draft.baseUrl.trim().replace(/\/$/, ''),
      apiKey: draft.apiKey.trim(),
      displayName: activeProvider?.name || '自定义图片模型',
    })
  }

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && !testing && onClose()}>
      <section className="model-modal" role="dialog" aria-modal="true" aria-labelledby="image-model-modal-title">
        <div className="modal-heading">
          <div><span>AI IMAGE CONNECTION</span><h2 id="image-model-modal-title">重构 AI 模型配置</h2></div>
          <button type="button" aria-label="关闭" onClick={onClose} disabled={testing}>×</button>
        </div>

        <p className="modal-intro">第一版支持 OpenAI Images 及同协议接口。API Key 只保存在当前页面内存中；测试连接不会生成图片。</p>

        <label className="modal-field">
          <span>服务商</span>
          <select value={draft.provider} onChange={(event) => selectProvider(event.target.value)}>
            {providers.map((provider) => <option value={provider.id} key={provider.id}>{provider.name}</option>)}
          </select>
        </label>
        <label className="modal-field">
          <span>图片模型名称</span>
          <input value={draft.model} onChange={(event) => updateField('model', event.target.value)} placeholder="例：gpt-image-2" autoComplete="off" />
          <small>模型必须支持图片输入和图片编辑接口</small>
        </label>
        <label className="modal-field">
          <span>Base URL</span>
          <input value={draft.baseUrl} onChange={(event) => updateField('baseUrl', event.target.value)} placeholder="https://api.example.com/v1" spellCheck="false" autoComplete="off" />
          <small>后端会自动追加 /images/edits</small>
        </label>
        <div className="modal-field-row">
          <label className="modal-field">
            <span>生成尺寸</span>
            <select value={draft.size} onChange={(event) => updateField('size', event.target.value)}>
              <option value="1024x1536">竖版 1024×1536</option>
              <option value="1024x1024">方形 1024×1024</option>
              <option value="1536x1024">横版 1536×1024</option>
            </select>
          </label>
          <label className="modal-field">
            <span>生成质量</span>
            <select value={draft.quality} onChange={(event) => updateField('quality', event.target.value)}>
              <option value="low">低 / 更快</option>
              <option value="medium">中 / 推荐</option>
              <option value="high">高 / 更慢</option>
            </select>
          </label>
        </div>
        <label className="modal-field">
          <span>API Key <b>*</b></span>
          <input type="password" value={draft.apiKey} onChange={(event) => updateField('apiKey', event.target.value)} placeholder="sk-..." autoComplete="new-password" />
        </label>

        {message && <p className={`connection-message ${message.type}`}>{message.type === 'success' ? '✓' : '!'} {message.text}</p>}

        <div className="modal-actions">
          <button className="test-button" type="button" onClick={testConnection} disabled={testing}>{testing ? '正在测试…' : '测试连接'}</button>
          <button className="save-button" type="button" onClick={saveConfig} disabled={testing}>保存配置</button>
        </div>
      </section>
    </div>
  )
}
