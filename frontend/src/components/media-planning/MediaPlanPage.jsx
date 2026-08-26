import { useEffect, useMemo, useState } from 'react'
import {
  createMediaPlanJob,
  getMediaPlan,
  getMediaPlanExportUrl,
  getMediaPlanJob,
  recalculateMediaPlan,
  serializeAIConfig,
  updateMediaPlan,
} from '../../api'

const OBJECTIVES = [
  ['lead_generation', '获取咨询'],
  ['sales', '商品成交'],
  ['store_visit', '到店咨询'],
  ['awareness', '品牌曝光'],
]

const PLATFORMS = [
  ['generic_cn_paid_social', '国内信息流（平台中立）'],
  ['tiktok', 'TikTok Ads'],
  ['google_ads', 'Google Ads'],
]

const TABS = [
  ['overview', '方案总览'],
  ['structure', '计划与单元'],
  ['audience', '城市与人群'],
  ['budget', '预算测算'],
  ['evidence', '数据来源'],
]

function formatMoney(value, currency = 'CNY') {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(Number(value || 0))
}

function splitValues(value) {
  return value.split(/[，,、\n]/).map((item) => item.trim()).filter(Boolean)
}

function SetupStep({ snapshot, modelConfig, onConfigureAI, onStart, busy, error }) {
  const detectedPrice = Number(String(snapshot?.product?.price_text || '').replace(/[^\d.]/g, '')) || ''
  const [form, setForm] = useState({
    objective: 'lead_generation',
    platform: 'generic_cn_paid_social',
    durationDays: 14,
    budgetCap: 20000,
    targetCpa: 180,
    actualPrice: detectedPrice,
    grossMargin: 35,
    serviceAreas: '上海，杭州，苏州',
    conversionDestination: 'lead_form',
    researchEnabled: true,
  })

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function submit(event) {
    event.preventDefault()
    onStart({
      objective: form.objective,
      platforms: [form.platform],
      duration_days: Number(form.durationDays),
      budget_cap: Number(form.budgetCap),
      currency: 'CNY',
      service_areas: splitValues(form.serviceAreas),
      conversion_destination: form.conversionDestination,
      actual_price: form.actualPrice ? Number(form.actualPrice) : null,
      gross_margin_rate: form.grossMargin === '' ? null : Number(form.grossMargin) / 100,
      target_cpa_cap: form.targetCpa ? Number(form.targetCpa) : null,
      researchEnabled: form.researchEnabled,
    })
  }

  return (
    <div className="media-plan-setup-shell">
      <section className="media-plan-source-card">
        <div className="media-plan-source-preview">
          {snapshot?.creativeUrl ? <img src={snapshot.creativeUrl} alt="当前广告素材" /> : <div>AD<br />PREVIEW</div>}
          <span>{snapshot?.creativeSource?.type === 'reconstructed' ? 'AI 成图' : '原始广告'}</span>
        </div>
        <div>
          <small>CREATIVE SOURCE</small>
          <h2>{snapshot?.product?.name || '当前广告'}</h2>
          <p>{snapshot?.product?.headline || '系统将结合当前广告、商品资料和公开信息生成投放草案。'}</p>
        </div>
      </section>

      <form className="media-plan-setup-form" onSubmit={submit}>
        <div className="media-plan-section-title"><span>01</span><div><small>BUSINESS CONSTRAINTS</small><h2>确认投放目标与约束</h2></div></div>
        <div className="media-plan-form-grid">
          <label><span>投放目标</span><select value={form.objective} onChange={(event) => update('objective', event.target.value)}>{OBJECTIVES.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
          <label><span>候选平台</span><select value={form.platform} onChange={(event) => update('platform', event.target.value)}>{PLATFORMS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
          <label><span>投放周期（天）</span><input type="number" min="1" max="180" required value={form.durationDays} onChange={(event) => update('durationDays', event.target.value)} /></label>
          <label><span>总预算上限（元）</span><input type="number" min="1" required value={form.budgetCap} onChange={(event) => update('budgetCap', event.target.value)} /></label>
          <label><span>目标 CPA 上限（可选）</span><input type="number" min="1" value={form.targetCpa} onChange={(event) => update('targetCpa', event.target.value)} /></label>
          <label><span>实际成交价（可选）</span><input type="number" min="1" value={form.actualPrice} onChange={(event) => update('actualPrice', event.target.value)} /></label>
          <label><span>毛利率 %（可选）</span><input type="number" min="0" max="100" value={form.grossMargin} onChange={(event) => update('grossMargin', event.target.value)} /></label>
          <label><span>转化落点</span><select value={form.conversionDestination} onChange={(event) => update('conversionDestination', event.target.value)}><option value="lead_form">咨询表单</option><option value="ecommerce">电商详情页</option><option value="store">线下门店</option><option value="landing_page">品牌落地页</option></select></label>
          <label className="media-plan-wide-field"><span>业务可服务地区 <b>*</b></span><input required value={form.serviceAreas} onChange={(event) => update('serviceAreas', event.target.value)} placeholder="使用逗号分隔，例如：上海，杭州，苏州" /></label>
        </div>
        <div className="media-plan-research-options">
          <label><input type="checkbox" checked={form.researchEnabled} onChange={(event) => update('researchEnabled', event.target.checked)} /><span><strong>联网检索公开资料</strong><small>检索行业、平台与人群资料，并为建议附上来源</small></span></label>
          <div><span>策略模型</span><strong>{modelConfig ? `${modelConfig.displayName || modelConfig.provider} · ${modelConfig.model}` : '未配置，将使用规则模式'}</strong><button type="button" onClick={onConfigureAI}>{modelConfig ? '更换模型' : '配置 AI'}</button></div>
        </div>
        {error && <p className="media-plan-error">! {error}</p>}
        <button className="media-plan-primary-action" type="submit" disabled={busy}>{busy ? '正在创建研究任务…' : '开始生成投放方案 →'}</button>
      </form>
    </div>
  )
}

function ProgressStep({ job, onBack }) {
  const stages = [
    ['creative_analysis', '读取商品资料与广告创意', 12],
    ['research', '检索行业、城市与平台资料', 52],
    ['strategy', '生成计划、广告单元和创意', 78],
    ['completed', '计算预算并保存方案', 100],
  ]
  return (
    <section className="media-plan-progress-card">
      <span className="media-plan-progress-orbit">✦</span>
      <small>AI MEDIA RESEARCH</small>
      <h1>正在生成投放方案</h1>
      <p>{job?.message || '正在准备研究任务…'}</p>
      <div className="media-plan-progress-bar"><i style={{ width: `${job?.progress || 3}%` }} /></div>
      <div className="media-plan-stage-list">
        {stages.map(([stage, label, threshold]) => {
          const done = (job?.progress || 0) >= threshold
          const active = job?.stage === stage
          return <div className={done ? 'done' : active ? 'active' : ''} key={stage}><b>{done ? '✓' : active ? '●' : '○'}</b><span>{label}</span></div>
        })}
      </div>
      <div className="media-plan-source-progress"><span>已找到资料 {job?.source_count || 0} 条</span><span>官方来源 {job?.official_source_count || 0} 条</span></div>
      {job?.status === 'failed' && <><p className="media-plan-error">! {job.error}</p><button className="media-plan-secondary-action" type="button" onClick={onBack}>返回重新配置</button></>}
    </section>
  )
}

function UnitEditor({ unit, currency, onChange }) {
  function patch(field, value) {
    onChange({ ...unit, [field]: value })
  }
  return (
    <div className="media-plan-unit-editor">
      <label><span>广告单元名称</span><input value={unit.name} onChange={(event) => patch('name', event.target.value)} /></label>
      <label><span>测试假设</span><textarea rows="3" value={unit.hypothesis} onChange={(event) => patch('hypothesis', event.target.value)} /></label>
      <div className="media-plan-inline-fields">
        <label><span>预算占比 %</span><input type="number" min="1" max="100" value={Math.round(unit.budget_share * 100)} onChange={(event) => patch('budget_share', Number(event.target.value) / 100)} /></label>
        <label><span>日预算</span><input value={formatMoney(unit.daily_budget, currency)} readOnly /></label>
      </div>
      <label><span>推荐理由</span><textarea rows="3" value={unit.reason} onChange={(event) => patch('reason', event.target.value)} /></label>
      <div className="media-plan-unit-confidence"><span>建议置信度</span><b>{unit.confidence === 'high' ? '高' : unit.confidence === 'medium' ? '中' : '低'}</b></div>
      <h3>使用的广告创意</h3>
      {unit.creatives.map((creative) => <article className="media-plan-creative-card" key={creative.id}><small>{creative.angle}</small><strong>{creative.headline}</strong><p>{creative.body || '当前广告描述'}</p><span>{creative.cta}</span></article>)}
    </div>
  )
}

function Workspace({ plan, setPlan, onSave, saving, error }) {
  const [tab, setTab] = useState('overview')
  const [selectedUnitId, setSelectedUnitId] = useState(plan.campaigns[0].ad_units[0].id)
  const campaign = plan.campaigns[0]
  const selectedUnit = campaign.ad_units.find((unit) => unit.id === selectedUnitId) || campaign.ad_units[0]

  function updateBusiness(field, value) {
    setPlan((current) => ({ ...current, business_inputs: { ...current.business_inputs, [field]: value } }))
  }

  function updateUnit(nextUnit) {
    setPlan((current) => ({
      ...current,
      campaigns: current.campaigns.map((item, index) => index ? item : { ...item, ad_units: item.ad_units.map((unit) => unit.id === nextUnit.id ? nextUnit : unit) }),
    }))
  }

  function updateAudience(field, rawValue) {
    updateUnit({ ...selectedUnit, audiences: { ...selectedUnit.audiences, [field]: splitValues(rawValue) } })
  }

  function renderContent() {
    if (tab === 'overview') return (
      <div className="media-plan-overview-grid">
        <article className="media-plan-summary-story"><small>STRATEGY SUMMARY</small><h2>{plan.product.name}</h2><p>{plan.strategy_summary}</p><div><span>创意定位</span><strong>{plan.creative_analysis.creative_positioning}</strong></div></article>
        <article className="media-plan-alert-card"><small>需要确认</small><ul>{plan.warnings.slice(0, 5).map((item) => <li key={item}>{item}</li>)}</ul></article>
        <article className="media-plan-assumption-card"><small>关键假设</small><ul>{plan.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></article>
      </div>
    )
    if (tab === 'structure') return (
      <div className="media-plan-structure-layout">
        <aside className="media-plan-tree"><small>CAMPAIGN STRUCTURE</small><strong>{campaign.name}</strong>{campaign.ad_units.map((unit) => <button className={selectedUnit.id === unit.id ? 'active' : ''} type="button" key={unit.id} onClick={() => setSelectedUnitId(unit.id)}><i /> <span>{unit.name}<small>{Math.round(unit.budget_share * 100)}% · {formatMoney(unit.daily_budget, plan.currency)}/日</small></span></button>)}</aside>
        <UnitEditor unit={selectedUnit} currency={plan.currency} onChange={updateUnit} />
      </div>
    )
    if (tab === 'audience') return (
      <div className="media-plan-audience-layout">
        <aside className="media-plan-unit-selector">{campaign.ad_units.map((unit) => <button className={selectedUnit.id === unit.id ? 'active' : ''} type="button" key={unit.id} onClick={() => setSelectedUnitId(unit.id)}>{unit.name}</button>)}</aside>
        <div className="media-plan-audience-editor">
          <label><span>投放城市</span><textarea rows="3" value={selectedUnit.geo.include.join('，')} onChange={(event) => updateUnit({ ...selectedUnit, geo: { ...selectedUnit.geo, include: splitValues(event.target.value) } })} /></label>
          <div className="media-plan-city-chips">{selectedUnit.geo.include.map((city) => <span key={city}>{city}<small>业务覆盖</small></span>)}</div>
          <label><span>年龄范围</span><input value={selectedUnit.demographics.age_ranges.join('，')} onChange={(event) => updateUnit({ ...selectedUnit, demographics: { ...selectedUnit.demographics, age_ranges: splitValues(event.target.value) } })} /></label>
          <label><span>性别</span><select value={selectedUnit.demographics.genders[0]} onChange={(event) => updateUnit({ ...selectedUnit, demographics: { ...selectedUnit.demographics, genders: [event.target.value] } })}><option value="all">不限</option><option value="female">女性</option><option value="male">男性</option></select></label>
          <label><span>兴趣标签</span><textarea rows="3" value={selectedUnit.audiences.interests.join('，')} onChange={(event) => updateAudience('interests', event.target.value)} /></label>
          <label><span>行为标签</span><textarea rows="3" value={selectedUnit.audiences.behaviors.join('，')} onChange={(event) => updateAudience('behaviors', event.target.value)} /></label>
          <label><span>购买意图</span><textarea rows="3" value={selectedUnit.audiences.purchase_intents.join('，')} onChange={(event) => updateAudience('purchase_intents', event.target.value)} /></label>
        </div>
      </div>
    )
    if (tab === 'budget') return (
      <div className="media-plan-budget-page">
        <div className="media-plan-budget-controls"><label><span>总预算</span><input type="number" min="1" value={plan.business_inputs.budget_cap} onChange={(event) => updateBusiness('budget_cap', Number(event.target.value))} /></label><label><span>周期（天）</span><input type="number" min="1" max="180" value={plan.business_inputs.duration_days} onChange={(event) => updateBusiness('duration_days', Number(event.target.value))} /></label><label><span>目标 CPA</span><input type="number" min="1" value={plan.business_inputs.target_cpa_cap || ''} onChange={(event) => updateBusiness('target_cpa_cap', event.target.value ? Number(event.target.value) : null)} /></label></div>
        <div className="media-plan-scenario-grid">{plan.budget_scenarios.map((scenario) => <article className={scenario.id === 'standard' ? 'recommended' : ''} key={scenario.id}><small>{scenario.id === 'standard' ? 'RECOMMENDED' : 'SCENARIO'}</small><h3>{scenario.name}</h3><strong>{formatMoney(scenario.total_budget, plan.currency)}</strong><span>{formatMoney(scenario.daily_budget, plan.currency)} / 日</span>{scenario.estimated_conversions_low != null ? <p>预估转化 {scenario.estimated_conversions_low}—{scenario.estimated_conversions_high}<br /><em>基于目标 CPA，并非效果保证</em></p> : <p>成本数据待实投验证</p>}<small>{scenario.note}</small></article>)}</div>
        <table className="media-plan-budget-table"><thead><tr><th>广告单元</th><th>占比</th><th>日预算</th></tr></thead><tbody>{campaign.ad_units.map((unit) => <tr key={unit.id}><td>{unit.name}</td><td>{Math.round(unit.budget_share * 100)}%</td><td>{formatMoney(unit.daily_budget, plan.currency)}</td></tr>)}</tbody></table>
      </div>
    )
    return <div className="media-plan-evidence-list">{plan.sources.map((source) => <article key={source.id}><div><span>{source.reliability === 'official' ? '官方来源' : '公开网页'}</span><small>{source.publisher}</small></div><h3>{source.title}</h3><p>{source.summary}</p><a href={source.url} target="_blank" rel="noreferrer">查看原始资料 ↗</a></article>)}</div>
  }

  return (
    <>
      <section className="media-plan-kpi-strip"><div><small>总预算</small><strong>{formatMoney(campaign.total_budget, plan.currency)}</strong></div><div><small>投放周期</small><strong>{campaign.duration_days} 天</strong></div><div><small>广告单元</small><strong>{campaign.ad_units.length} 个</strong></div><div><small>主要指标</small><strong>{campaign.primary_kpi}</strong></div><div><small>目标</small><strong>{OBJECTIVES.find(([value]) => value === plan.objective)?.[1]}</strong></div></section>
      <nav className="media-plan-tabs">{TABS.map(([value, label]) => <button className={tab === value ? 'active' : ''} type="button" key={value} onClick={() => setTab(value)}>{label}{value === 'evidence' && <span>{plan.sources.length}</span>}</button>)}</nav>
      <main className="media-plan-content">{renderContent()}</main>
      <div className="media-plan-status-bar"><span>数据来源 {plan.sources.length} 条</span><span>AI 假设 {plan.assumptions.length} 条</span><span>合规与风险 {plan.warnings.length} 条</span><button type="button" onClick={onSave} disabled={saving}>{saving ? '正在保存并重算…' : '保存并重新计算'}</button></div>
      {error && <p className="media-plan-floating-error">! {error}</p>}
    </>
  )
}

export default function MediaPlanPage({ initialPlanId, snapshot, creativeFile, modelConfig, onConfigureAI, onBack, onPlanCreated }) {
  const [plan, setPlan] = useState(null)
  const [job, setJob] = useState(null)
  const [phase, setPhase] = useState(initialPlanId ? 'loading' : 'setup')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!initialPlanId) return
    setPhase('loading')
    getMediaPlan(initialPlanId).then((data) => { setPlan(data); setPhase('workspace') }).catch((requestError) => { setError(requestError.message); setPhase('setup') })
  }, [initialPlanId])

  useEffect(() => {
    if (!job || !['queued', 'running'].includes(job.status)) return undefined
    let cancelled = false
    const timer = window.setTimeout(async () => {
      try {
        const next = await getMediaPlanJob(job.id)
        if (cancelled) return
        setJob(next)
        if (next.status === 'completed' && next.plan_id) {
          const result = await getMediaPlan(next.plan_id)
          if (cancelled) return
          setPlan(result)
          setPhase('workspace')
          onPlanCreated(next.plan_id)
        }
      } catch (requestError) {
        if (!cancelled) setError(requestError.message)
      }
    }, 650)
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [job, onPlanCreated])

  async function start(business) {
    if (!snapshot?.product?.name) {
      setError('缺少广告商品信息，请返回广告制作页重新生成')
      return
    }
    setBusy(true)
    setError('')
    try {
      const result = await createMediaPlanJob({
        payload: {
          product: snapshot.product,
          creative_source: snapshot.creativeSource,
          business: { ...business, researchEnabled: undefined },
          research: { enabled: business.researchEnabled, max_queries: 4, max_pages: 6, freshness_days: 365 },
          model_config: serializeAIConfig(modelConfig),
        },
        creativeFile: snapshot.creativeSource.type === 'original' ? creativeFile : null,
        creativeUrl: snapshot.creativeSource.type === 'reconstructed' ? snapshot.creativeUrl : '',
      })
      setJob(result)
      setPhase('progress')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  async function saveAndRecalculate() {
    setBusy(true)
    setError('')
    try {
      await updateMediaPlan(plan)
      const result = await recalculateMediaPlan(plan.id)
      setPlan(result)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  const exportLinks = useMemo(() => plan ? { markdown: getMediaPlanExportUrl(plan.id, 'markdown'), json: getMediaPlanExportUrl(plan.id, 'json') } : null, [plan])

  return (
    <div className="media-plan-page">
      <header className="media-plan-header">
        <button type="button" onClick={onBack}>← 返回广告制作</button>
        <div><small>MUJING MEDIA PLANNER</small><strong>{plan?.name || 'AI 投放策划'}</strong></div>
        <div className="media-plan-header-actions">{exportLinks && <><a href={exportLinks.markdown}>导出简报</a><a href={exportLinks.json}>导出 JSON</a></>}</div>
      </header>
      {phase === 'setup' && <SetupStep snapshot={snapshot} modelConfig={modelConfig} onConfigureAI={onConfigureAI} onStart={start} busy={busy} error={error} />}
      {phase === 'progress' && <ProgressStep job={job} onBack={() => setPhase('setup')} />}
      {phase === 'loading' && <ProgressStep job={{ message: '正在读取已保存方案', progress: 40, stage: 'research' }} onBack={onBack} />}
      {phase === 'workspace' && plan && <Workspace plan={plan} setPlan={setPlan} onSave={saveAndRecalculate} saving={busy} error={error} />}
    </div>
  )
}

