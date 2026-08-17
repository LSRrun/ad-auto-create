const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function parseResponse(response) {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || '请求失败，请稍后重试')
  }
  return response.json()
}

export async function getStyles() {
  return parseResponse(await fetch(`${API_BASE}/api/styles`))
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

export async function reconstructAd({ config, snapshot, productImage }) {
  const formData = new FormData()
  formData.set('config', JSON.stringify(serializeImageConfig(config)))
  formData.set('snapshot', JSON.stringify(snapshot))
  formData.set('product_image', productImage)
  return parseResponse(
    await fetch(`${API_BASE}/api/reconstruction/generate`, {
      method: 'POST',
      body: formData,
    }),
  )
}
