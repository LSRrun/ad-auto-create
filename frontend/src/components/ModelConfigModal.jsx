import { useEffect, useState } from 'react'

function createDraft(config, provider) {
  if (config) return { ...config }
  return {
    provider: provider?.id || 'custom',
    model: provider?.model || '',
    baseUrl: provider?.baseUrl || '',
    apiKey: '',
  }
}

export default function ModelConfigModal({
  open,
  config,
  providers,
  onClose,
  onSave,
  onTest,
  title = 'AI 模型配置',
  eyebrow = 'AI MODEL CONNECTION',
  intro = '选择 OpenAI 兼容的模型服务。API Key 只保存在当前页面内存中，刷新后自动清除。',
  backdropClassName = '',
}) {
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
  const needsKey = activeProvider?.requiresApiKey !== false

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
    })
    setMessage(null)
  }

  function validate() {
    if (!draft.model.trim()) return '请填写模型名称'
    if (!draft.baseUrl.trim()) return '请填写 Base URL'
    if (needsKey && !draft.apiKey.trim()) return '请填写 API Key'
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
      displayName: activeProvider?.name || '自定义模型',
    })
  }

  return (
    <div className={`modal-backdrop ${backdropClassName}`} onMouseDown={(event) => event.target === event.currentTarget && !testing && onClose()}>
      <section className="model-modal" role="dialog" aria-modal="true" aria-labelledby="model-modal-title">
        <div className="modal-heading">
          <div><span>{eyebrow}</span><h2 id="model-modal-title">{title}</h2></div>
          <button type="button" aria-label="关闭" onClick={onClose} disabled={testing}>×</button>
        </div>

        <p className="modal-intro">{intro}</p>

        <label className="modal-field">
          <span>服务商</span>
          <select value={draft.provider} onChange={(event) => selectProvider(event.target.value)}>
            {providers.map((provider) => <option value={provider.id} key={provider.id}>{provider.name}</option>)}
          </select>
        </label>
        <label className="modal-field">
          <span>模型名称</span>
          <input value={draft.model} onChange={(event) => updateField('model', event.target.value)} placeholder="例：deepseek-chat" autoComplete="off" />
          <small>模型名称可根据你的账号权限修改</small>
        </label>
        <label className="modal-field">
          <span>Base URL</span>
          <input value={draft.baseUrl} onChange={(event) => updateField('baseUrl', event.target.value)} placeholder="https://api.example.com/v1" spellCheck="false" autoComplete="off" />
          <small>后端会自动追加 /chat/completions</small>
        </label>
        <label className="modal-field">
          <span>API Key {needsKey && <b>*</b>}</span>
          <input type="password" value={draft.apiKey} onChange={(event) => updateField('apiKey', event.target.value)} placeholder={needsKey ? 'sk-...' : '本地模型可留空'} autoComplete="new-password" />
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
