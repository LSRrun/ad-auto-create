export default function PreviewModeSwitch({ mode, hasReconstruction, stale, onChange }) {
  return (
    <div className="preview-mode-switch" aria-label="广告预览模式">
      <button type="button" className={mode === 'original' ? 'active' : ''} onClick={() => onChange('original')}>原始排版</button>
      <button type="button" className={mode === 'reconstructed' ? 'active' : ''} onClick={() => onChange('reconstructed')} disabled={!hasReconstruction}>
        AI 重构{stale ? <i title="当前重构图基于修改前的内容">!</i> : null}
      </button>
    </div>
  )
}
