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

