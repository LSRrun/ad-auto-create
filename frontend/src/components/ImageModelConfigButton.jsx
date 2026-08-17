export default function ImageModelConfigButton({ config, onClick }) {
  return (
    <button className={`model-config-button image-model-button ${config ? 'configured' : ''}`} type="button" onClick={onClick}>
      <span className="model-status-dot" />
      <span>
        <small>{config ? '当前重构模型' : 'AI IMAGE MODEL'}</small>
        <strong>{config ? config.displayName || config.model : '选择重构模型'}</strong>
      </span>
      <b>↗</b>
    </button>
  )
}
