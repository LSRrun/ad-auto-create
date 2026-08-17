export default function ModelConfigButton({ config, onClick }) {
  return (
    <button className={`model-config-button ${config ? 'configured' : ''}`} type="button" onClick={onClick}>
      <span className="model-status-dot" />
      <span>
        <small>{config ? '当前 AI 模型' : 'AI COPY MODEL'}</small>
        <strong>{config ? config.displayName || config.model : '选择润色模型'}</strong>
      </span>
      <b>↗</b>
    </button>
  )
}

