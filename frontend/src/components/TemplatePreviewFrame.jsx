import { useMemo } from 'react'

const EMPTY_PIXEL = 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='

function fieldValue(field, ad) {
  if (field.startsWith('feature')) {
    const index = Number(field.slice(-1)) - 1
    return ad.features?.[index] || ''
  }
  return ad[field] || ''
}

function buildDocument(templateHtml, ad, imageUrl) {
  if (!templateHtml || typeof DOMParser === 'undefined') return ''
  const parser = new DOMParser()
  const document = parser.parseFromString(templateHtml, 'text/html')
  document.querySelectorAll('[data-ad-field]').forEach((element) => {
    const field = element.getAttribute('data-ad-field')
    if (field === 'productImage') {
      let image = element.tagName === 'IMG' ? element : element.querySelector('img')
      if (!image) {
        image = document.createElement('img')
        image.style.cssText = 'width:100%;height:100%;object-fit:contain;display:block'
        element.appendChild(image)
      }
      image.setAttribute('src', imageUrl || EMPTY_PIXEL)
      image.setAttribute('alt', ad.productName || '商品图')
      element.toggleAttribute('data-empty-image', !imageUrl)
      return
    }
    element.textContent = fieldValue(field, ad)
  })
  const head = document.head || document.documentElement.insertBefore(document.createElement('head'), document.body)
  const csp = document.createElement('meta')
  csp.setAttribute('http-equiv', 'Content-Security-Policy')
  csp.setAttribute('content', "default-src 'none'; img-src data: blob: http: https:; style-src 'unsafe-inline'; font-src data:; script-src 'none'; connect-src 'none'; frame-src 'none'")
  head.prepend(csp)
  const base = document.createElement('style')
  base.textContent = 'html,body{margin:0;width:100%;height:100%;overflow:hidden}body{display:grid;place-items:center}[data-empty-image] img{opacity:0}'
  head.appendChild(base)
  return `<!doctype html>${document.documentElement.outerHTML}`
}

export default function TemplatePreviewFrame({ templateHtml, ad, imageUrl, aspectRatio = '4:5', title = '自定义广告模板预览' }) {
  const source = useMemo(() => buildDocument(templateHtml, ad, imageUrl), [templateHtml, ad, imageUrl])
  return (
    <div className="template-preview-frame" style={{ '--template-aspect': aspectRatio.replace(':', ' / ') }}>
      {source ? <iframe title={title} sandbox="" srcDoc={source} /> : <div className="template-preview-loading">正在读取风格模板…</div>}
    </div>
  )
}
