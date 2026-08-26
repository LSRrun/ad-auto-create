const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function parseResponse(response) {
  if (!response.ok) {
    if (response.status === 413) {
      throw new Error('上传图片过大，请使用不超过 8 MB 的 JPG、PNG 或 WebP 图片')
    }
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || '请求失败，请稍后重试')
  }
  return response.json()
}

export async function getStyles() {
  return parseResponse(await fetch(`${API_BASE}/api/styles`))
}

export async function createHtmlStyleDraft(file) {
  const formData = new FormData()
  formData.set('file', file)
  return parseResponse(await fetch(`${API_BASE}/api/style-templates/drafts/html`, { method: 'POST', body: formData }))
}

export async function createReferenceStyleDraft({ file, config, userDirection = '' }) {
  const formData = new FormData()
  formData.set('file', file)
  formData.set('analysis_config', JSON.stringify(serializeConfig(config)))
  formData.set('user_direction', userDirection.trim())
  return parseResponse(await fetch(`${API_BASE}/api/style-templates/drafts/reference`, { method: 'POST', body: formData }))
}

export async function updateStyleDraft(draftId, changes) {
  return parseResponse(
    await fetch(`${API_BASE}/api/style-templates/drafts/${draftId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(changes),
    }),
  )
}

export async function publishStyleDraft(draftId) {
  return parseResponse(await fetch(`${API_BASE}/api/style-templates/drafts/${draftId}/publish`, { method: 'POST' }))
}

export async function getStyleRenderSource(styleId) {
  return parseResponse(await fetch(`${API_BASE}/api/style-templates/${styleId}/render-source`))
}

export async function generateAd(formData) {
  return parseResponse(
    await fetch(`${API_BASE}/api/ads/generate`, {
      method: 'POST',
      body: formData,
    }),
  )
}

export async function getAIProviders() {
  return parseResponse(await fetch(`${API_BASE}/api/ai/providers`))
}

function serializeConfig(config) {
  return {
    provider: config.provider,
    model: config.model,
    base_url: config.baseUrl,
    api_key: config.apiKey,
  }
}

export function serializeAIConfig(config) {
  return config ? serializeConfig(config) : null
}

export async function testAIConnection(config) {
  return parseResponse(
    await fetch(`${API_BASE}/api/ai/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: serializeConfig(config) }),
    }),
  )
}

export async function polishAdCopy({ config, styleId, product, currentCopy }) {
  return parseResponse(
    await fetch(`${API_BASE}/api/ai/polish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        config: serializeConfig(config),
        style_id: styleId,
        product,
        current_copy: currentCopy,
      }),
    }),
  )
}

export async function getImageProviders() {
  return parseResponse(await fetch(`${API_BASE}/api/reconstruction/providers`))
}

function serializeImageConfig(config) {
  return {
    provider: config.provider,
    model: config.model,
    base_url: config.baseUrl,
    api_key: config.apiKey,
    size: config.size,
    quality: config.quality,
  }
}

export async function testImageConnection(config) {
  return parseResponse(
    await fetch(`${API_BASE}/api/reconstruction/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: serializeImageConfig(config) }),
    }),
  )
}

export async function reconstructAd({ config, snapshot, productImage, userPrompt = '' }) {
  const formData = new FormData()
  formData.set('config', JSON.stringify(serializeImageConfig(config)))
  formData.set('snapshot', JSON.stringify(snapshot))
  formData.set('product_image', productImage)
  formData.set('user_prompt', userPrompt.trim())
  return parseResponse(
    await fetch(`${API_BASE}/api/reconstruction/generate`, {
      method: 'POST',
      body: formData,
    }),
  )
}

export async function createMediaPlanJob({ payload, creativeFile, creativeUrl }) {
  const formData = new FormData()
  formData.set('payload', JSON.stringify(payload))
  if (creativeFile) {
    formData.set('creative_image', creativeFile)
  } else if (creativeUrl) {
    try {
      const response = await fetch(creativeUrl)
      if (response.ok) {
        const blob = await response.blob()
        const extension = blob.type === 'image/png' ? 'png' : blob.type === 'image/webp' ? 'webp' : 'jpg'
        formData.set('creative_image', new File([blob], `current-ad.${extension}`, { type: blob.type || 'image/jpeg' }))
      }
    } catch {
      // The structured ad snapshot is still sufficient for the rule fallback.
    }
  }
  return parseResponse(await fetch(`${API_BASE}/api/media-plans/jobs`, { method: 'POST', body: formData }))
}

export async function getMediaPlanJob(jobId) {
  return parseResponse(await fetch(`${API_BASE}/api/media-plans/jobs/${jobId}`))
}

export async function getMediaPlan(planId) {
  return parseResponse(await fetch(`${API_BASE}/api/media-plans/${planId}`))
}

export async function updateMediaPlan(plan) {
  return parseResponse(
    await fetch(`${API_BASE}/api/media-plans/${plan.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(plan),
    }),
  )
}

export async function recalculateMediaPlan(planId) {
  return parseResponse(await fetch(`${API_BASE}/api/media-plans/${planId}/recalculate`, { method: 'POST' }))
}

export function getMediaPlanExportUrl(planId, format = 'markdown') {
  return `${API_BASE}/api/media-plans/${planId}/export?format=${encodeURIComponent(format)}`
}
