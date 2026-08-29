# 沐境 · 卫浴广告自动生成器

一个前后端分离的卫浴广告生成工具。用户上传商品图片、填写商品信息并选择视觉风格后，可以使用本地规则快速生成广告页面，也可以接入大模型润色文案、生成完整的 AI 场景广告图，并基于当前广告生成可编辑、可导出的投放方案。

项目目前定位为轻量级可运行原型：不依赖数据库，保留原有非 AI 模式，所有模型连接均由用户在页面中按需配置。

## 当前功能

### 基础广告生成

- 上传 JPG、PNG 或 WebP 商品图片，单张最大 8 MB。
- 填写品牌、商品名称、价格和核心卖点。
- 提供静奢白、自然疗愈、暗夜科技三种视觉风格。
- 切换风格时同步更新右侧广告预览的默认标题和视觉样式。
- 使用本地规则生成广告标题、描述和卖点，不配置 AI 也可以正常使用。

### AI 文案润色

- 根据当前商品信息、已有文案和所选风格生成广告文案。
- 保留商品事实，返回标题、描述、卖点和行动文案。
- 左侧广告文案编辑区可以直接修改大标题、英文眉题、描述、卖点和行动文案，AI 润色结果会同步写回这些输入框。
- 支持 DeepSeek、通义千问、OpenAI、Ollama 和自定义 OpenAI 兼容接口。
- AI 返回后直接更新右侧预览，不会再被风格默认标题覆盖。

### AI 广告图重构

- 识别上传的真实商品，并根据商品类型和所选风格生成完整广告图。
- 将商品融入高端卫浴场景，自由重构背景、空间、光影、构图和文案层级。
- 可以输入本次重构的场景、构图、光影和排版要求；留空时由 AI 自动设计。
- 尽量保持商品轮廓、结构、材质、颜色和关键部件完整。
- 品牌、商品名称和价格保持事实不变；其他文案允许在原意不变的情况下精炼。
- 支持原始广告与 AI 成图一键切换对比。
- 支持 OpenAI Images、OpenAI 图片兼容接口，以及阿里云百炼 `wan2.7-image`。

> AI 重构结果由图片模型直接生成。商品细节保持程度和中文文字准确性取决于所选模型，当前版本不能做到像素级保证。

### 可复用风格模板

- 在风格列表中通过“添加风格模板”导入新风格。
- 支持单个 HTML 文件；系统会清理脚本、事件属性和远程资源，并识别商品图、标题、品牌、价格和卖点容器。
- 支持上传广告参考图，通过具备图片理解能力的 OpenAI 兼容模型生成受控布局草稿。
- 两种导入都需先预览确认，发布后才会进入风格列表。
- 已发布模板使用沙箱 iframe 渲染，可实时替换商品图、品牌、标题、描述、价格、卖点和行动文案。
- 风格包保存在 `backend/data/style_templates/`，刷新页面或重启单机后端后仍可使用。

### AI 投放策划

- 基于当前商品资料、广告文案和原始广告或 AI 成图创建投放任务。
- 支持获取咨询、商品成交、到店咨询和品牌曝光四种投放目标。
- 可配置平台、投放周期、预算上限、目标 CPA、实际成交价、毛利率、转化落点和业务可服务地区。
- 可选联网检索公开资料；外网不可用时会保留官方备用证据并标注假设。
- 可选使用文本大模型辅助策略分析；未配置模型或 AI 返回异常时自动回退到规则模式。
- DeepSeek 策略分析只发送结构化文字资料，不向模型发送广告图片。
- 生成过程通过异步任务轮询显示进度，完成后自动进入方案工作区。
- 工作区包含方案总览、计划与单元、城市与人群、预算测算和数据来源，支持保存重算以及导出 Markdown/JSON。
- 任务和方案以 JSON 保存在 `backend/data/media_plans/`。

## 技术栈

- 前端：React、Vite
- 后端：Python、FastAPI、Pydantic
- AI 请求：httpx
- 图片处理：Pillow
- 数据与文件：本地文件系统，当前不使用数据库

## 项目结构

```text
广告自动生成器/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 入口、基础广告接口与静态文件服务
│   │   ├── generator.py          # 非 AI 规则文案生成
│   │   ├── styles.py             # 广告风格定义
│   │   ├── ai/                   # AI 文案模型、提示词、校验与接口
│   │   ├── reconstruction/       # 图片模型适配、重构提示词与成图处理
│   │   ├── media_planning/       # 投放任务、联网研究、AI 策略、预算与持久化
│   │   └── style_templates/      # HTML/参考图导入、安全清理、布局编译与持久化
│   ├── data/                     # 风格模板和投放方案（Git 忽略）
│   ├── tests/                    # 后端回归测试
│   ├── uploads/                  # 本地上传图片和 AI 重构结果
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # 主页面和业务状态
│   │   ├── api.js                # 前后端请求封装
│   │   ├── components/           # 模型配置、风格模板和投放策划界面
│   │   └── styles.css
│   ├── dist/                     # 生产构建产物（Git 忽略）
│   └── package.json
├── deploy/                       # Nginx、systemd 和一键部署脚本
├── .gitignore
└── README.md
```

## 环境要求

- Conda
- Python 3.10 以上，推荐 Python 3.12
- Node.js `^20.19.0` 或 `>=22.12.0`
- npm

## 本地启动

以下命令均从项目根目录执行。

### 1. 创建 Python 环境并安装后端依赖

```bash
conda create -n adcreate python=3.12 -y
conda activate adcreate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

所有 Python 包都通过 `python -m pip` 安装到当前激活的 `adcreate` 环境中。

### 2. 启动后端

```bash
conda activate adcreate
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

- API 地址：<http://localhost:8000>
- Swagger 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/api/health>

### 3. 安装前端依赖并启动

打开另一个终端：

```bash
cd frontend
npm ci
npm run dev
```

页面地址：<http://localhost:5173>

前端默认请求 `http://localhost:8000`。如果后端部署在其他地址，可以在启动前端时设置：

```bash
VITE_API_BASE_URL=https://your-api.example.com npm run dev
```

## 使用流程

### 规则模式

1. 上传商品图片。
2. 填写商品名称及其他商品信息。
3. 选择视觉风格。
4. 点击“生成广告页面”。
5. 后端使用本地规则生成文案，右侧立即展示广告预览。

该模式不需要 API Key，也不会调用外部模型。

### AI 文案模式

1. 点击商品信息区域右上方的 AI 模型按钮。
2. 选择服务商，填写模型名称、Base URL 和 API Key。
3. 点击“测试连接”，成功后保存配置。
4. 填写商品信息并选择风格。
5. 点击“AI 润色”，按钮下方会显示处理状态。
6. 完成后，大标题、英文眉题、广告描述、广告卖点和行动文案会同时更新到左侧输入框与右侧预览。
7. 可以继续在左侧手动修改润色结果，右侧预览会实时同步。

常用配置：

| 服务商 | 模型示例 | Base URL |
| --- | --- | --- |
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com` |
| 通义千问 | `qwen-plus` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| OpenAI | `gpt-5-mini` | `https://api.openai.com/v1` |
| Ollama | `qwen3:8b` | `http://127.0.0.1:11434/v1` |

自定义服务需要兼容 OpenAI Chat Completions 接口。后端会在 Base URL 后自动追加 `/chat/completions`，如果填写的是完整接口地址则不会重复追加。

#### 阿里云百炼 Token Plan + DeepSeek 配置

在前端服务商中选择“自定义兼容接口”，然后填写：

| 配置项 | 值 |
| --- | --- |
| 模型 | `deepseek-v4-pro` |
| Base URL | `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1` |
| API Key | 百炼 Token Plan API Key |

连接测试会自动为 DeepSeek 关闭思考输出，避免测试请求的输出额度全部消耗在思考内容上，最终被误判为“模型返回了空文案”。文案润色和投放策略的最大输出额度均为 4096 tokens。

### AI 重构模式

1. 上传商品图片并生成或完善当前广告文案。
2. 点击“重构 AI 模型配置”。
3. 选择图片服务商，填写模型、Base URL、API Key、生成尺寸和质量。
4. 测试并保存配置。
5. 按需填写“AI 重构创意要求”；该字段可留空，最多 1000 个字符。
6. 点击提示词文本框下方的“开始 AI 重构”。
7. 生成完成后，通过广告预览上方的切换按钮查看原版或 AI 成图。

桌面端左侧控制面板可以独立上下滚动，右侧预览会保持可见；移动端使用自然页面滚动。

接近高端卫浴场景主视觉的横版广告时，建议选择 `1536×1024`；用于手机海报时可选择 `1024×1536`。

#### OpenAI Images 配置示例

| 配置项 | 值 |
| --- | --- |
| 服务商 | OpenAI Images |
| 模型 | `gpt-image-2` |
| Base URL | `https://api.openai.com/v1` |
| API Key | OpenAI API Key |

#### 阿里云百炼 Wan2.7 配置示例

在前端服务商中选择“自定义 OpenAI 图片接口”，然后填写：

| 配置项 | 值 |
| --- | --- |
| 模型 | `wan2.7-image` |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| API Key | 阿里云百炼 API Key |

后端会识别阿里云域名和 `wan2.7-image`，自动把兼容模式地址转换为万相原生多模态图片生成接口，前端无需填写原生接口全路径。

如果使用百炼 Token Plan，可以改用下列 Base URL，其他配置不变：

```text
https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
```

请确保百炼 API Key 与服务地域一致。连接测试只检查鉴权，不会生成图片；真正执行 AI 重构时会调用图片模型，并可能产生费用。

### AI 投放策划模式

1. 先填写商品信息，并点击“生成广告页面”或完成一次 AI 重构。
2. 在右侧广告预览顶部点击“基于当前广告生成投放方案”。
3. 确认投放目标、平台、周期、总预算、目标 CPA、毛利率、转化落点和可服务地区。
4. 按需开启“联网检索公开资料”。
5. 投放策略模型可选；如需 AI 分析，点击“配置 AI”并使用文案模型配置。
6. 点击“开始生成投放方案”，页面会展示创意分析、资料研究、策略生成和预算保存进度。
7. 任务完成后会自动跳转到 `/media-plans/{plan_id}`。
8. 可编辑计划、广告单元、城市、人群和预算，点击“保存并重新计算”后更新本地方案。
9. 页面右上角可导出 Markdown 简报或 JSON 数据。

> 投放方案中的人群、预算、CPA 和转化量均为待验证建议，不是平台实时预测或效果承诺。当前实现不会向 DeepSeek 发送投放策划图片，只发送商品、文案、业务约束和研究证据。

## API 概览

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/health` | 后端健康检查 |
| GET | `/api/styles` | 获取广告风格 |
| POST | `/api/style-templates/drafts/html` | 上传 HTML 并创建安全模板草稿 |
| POST | `/api/style-templates/drafts/reference` | 使用视觉模型从参考图生成草稿 |
| GET | `/api/style-templates/drafts/{draft_id}` | 读取风格模板草稿 |
| PATCH | `/api/style-templates/drafts/{draft_id}` | 更新草稿字段映射和风格设定 |
| POST | `/api/style-templates/drafts/{draft_id}/publish` | 发布可复用风格 |
| GET | `/api/style-templates/{style_id}/render-source` | 读取已清理的模板渲染源 |
| POST | `/api/ads/generate` | 使用规则生成广告数据并上传商品图 |
| GET | `/api/ai/providers` | 获取文案模型服务商 |
| POST | `/api/ai/test-connection` | 测试文案模型连接 |
| POST | `/api/ai/polish` | AI 润色广告文案 |
| GET | `/api/reconstruction/providers` | 获取图片模型服务商 |
| POST | `/api/reconstruction/test-connection` | 测试图片模型鉴权 |
| POST | `/api/reconstruction/generate` | 根据页面快照和商品图生成完整广告图 |
| POST | `/api/media-plans/jobs` | 创建异步投放策划任务 |
| GET | `/api/media-plans/jobs/{job_id}` | 查询任务进度与生成结果 |
| POST | `/api/media-plans/jobs/{job_id}/cancel` | 把未完成任务标记为已取消 |
| GET | `/api/media-plans/{plan_id}` | 读取已保存投放方案 |
| PATCH | `/api/media-plans/{plan_id}` | 保存编辑后的投放方案 |
| POST | `/api/media-plans/{plan_id}/recalculate` | 重新计算方案预算和派生数据 |
| GET | `/api/media-plans/{plan_id}/export?format={markdown,json}` | 导出 Markdown 或 JSON 方案 |

具体请求字段和返回结构以 Swagger 文档为准。

## 服务器部署

仓库提供以下生产环境配置：

- `deploy/nginx.conf`：在 `8080` 端口托管 `frontend/dist/`，并把 `/api/` 和 `/uploads/` 反向代理到 `127.0.0.1:8000`。
- `deploy/ad-api.service`：使用 systemd 运行 FastAPI，默认启动 2 个 Uvicorn worker。
- `deploy/deploy.sh`：拉取代码、安装依赖、构建前端、安装配置并重启服务。

默认配置假设：

- 项目目录：`/root/projects/ad-auto-create`
- Conda 环境：`adcreate`
- Python：`/root/miniconda3/envs/adcreate/bin/python`
- 对外端口：`8080`
- 后端内部端口：`8000`

如果服务器路径、Python 路径或端口不同，先修改 `deploy/deploy.sh`、`deploy/ad-api.service` 和 `deploy/nginx.conf`。

### 首次部署

首次执行脚本前，需要确认 Nginx、Node.js/npm、Miniconda 和 `adcreate` 环境已安装，且 `/etc/nginx/conf.d/` 已存在。然后以 root 用户进入项目目录执行：

```bash
cd /root/projects/ad-auto-create
VITE_API_BASE_URL= bash deploy/deploy.sh
```

`VITE_API_BASE_URL=` 表示生产前端使用同源的 `/api`，由 Nginx 转发到后端。不要把生产前端构建为 `http://localhost:8000`，否则浏览器会请求访问者自己电脑上的 `8000` 端口。

部署后访问：

```text
http://<服务器 IP>:8080/
```

同时需要在云服务器安全组或防火墙中放行 TCP `8080` 端口。

### 拉取代码后更新

先在项目根目录拉取代码：

```bash
cd /root/projects/ad-auto-create
git pull
```

如果只修改了 `frontend/`：

```bash
cd frontend
VITE_API_BASE_URL= npm run build
chmod -R o+rX dist
cd ..
nginx -t
systemctl reload nginx
```

构建成功后，浏览器按 `Ctrl + F5` 或 `Ctrl + Shift + R` 强制刷新。前端代码变更不需要重启 `ad-api`。

如果修改了 `backend/` 或 `backend/requirements.txt`：

```bash
/root/miniconda3/envs/adcreate/bin/python -m pip install -r backend/requirements.txt
systemctl restart ad-api
systemctl status ad-api --no-pager
```

如果修改了 Nginx 配置：

```bash
cp deploy/nginx.conf /etc/nginx/conf.d/ad-auto-create.conf
nginx -t
systemctl reload nginx
```

### 服务检查与日志

```bash
curl http://127.0.0.1:8000/api/health
curl -I http://127.0.0.1:8080/
systemctl status ad-api --no-pager
journalctl -u ad-api -n 100 --no-pager
systemctl status nginx --no-pager
tail -n 100 /var/log/nginx/error.log
```

Nginx 已设置 `client_max_body_size 12m`，覆盖后端最大 10 MB 的投放素材上传并为 multipart 请求预留开销；AI 接口的反向代理读取超时为 180 秒。

## API Key 与数据安全

- API Key 只保存在当前浏览器页面的 React 内存状态中，不写入源码、本地文件、数据库或 `localStorage`。
- 刷新或关闭页面后，当前模型配置和 API Key 会丢失。
- 调用 AI 功能时，API Key 会随请求发送给本项目后端，再由后端用于访问所选模型服务商。
- AI 重构会把商品图片和广告文案发送给所选图片模型服务商；敏感或未公开商品图请先确认服务商的数据政策。
- 投放策划任务会把商品、文案、业务约束和公开研究摘要发送给所选文本模型；DeepSeek 不会接收投放策划中的广告图片。
- 不要把 API Key 写入 README、前端源码、截图或 Git 提交。
- 生产环境应改用服务端密钥管理、用户鉴权、访问限流和 HTTPS，不应继续让公共用户直接提交长期有效的管理型密钥。

上传的商品图片和生成结果会保存在 `backend/uploads/`。该目录内容已经被 Git 忽略，但当前版本不会自动定期清理，本机或服务器维护者需要自行管理存储和隐私。

上传 HTML 不会在主页直接执行。后端会删除脚本、交互标签、事件属性、外链和高风险 CSS，前端再通过 CSP 与不授予脚本权限的沙箱 iframe 渲染。风格源文件和已发布资产保存在 `backend/data/`，使用者需要确保对上传的 HTML、图片、字体和品牌资产拥有使用权。

投放任务和方案保存在 `backend/data/media_plans/`。任务快照不保存 AI 模型配置或 API Key，但会保存商品资料、业务约束和策划结果，服务器维护者需要按业务需求备份或清理。

## 构建与检查

后端导入检查：

```bash
conda run -n adcreate python -m compileall -q backend/app
```

后端回归测试（包含风格模板、百炼 DeepSeek 连接和投放策划）：

```bash
cd backend
conda run -n adcreate python -m unittest discover -s tests -v
```

前端生产构建：

```bash
cd frontend
npm run build
```

构建结果输出到 `frontend/dist/`，该目录不会提交到 Git。

## 常见问题

### 模型测试返回“模型返回了空文案”

- 确认 DeepSeek Token Plan 的模型名称和 Base URL 与账号地域一致。
- 确认服务器已拉取最新后端代码并执行 `systemctl restart ad-api`。
- 当前代码会为 `deepseek-*` 模型的连接测试设置 `enable_thinking=false`，正常情况下不应再因思考输出占满额度而误报空文案。

### 投放进度显示 100%，但没有进入方案页

- 重新构建最新前端，不要只执行 `git pull`。
- 确认任务轮询和方案读取均返回 `200`。
- 构建后使用浏览器强制刷新，避免继续运行旧的 JavaScript 资源。

### 服务器拉取后页面没有变化

`git pull` 只会更新源码，Nginx 读取的是 `frontend/dist/`。请再执行：

```bash
cd frontend
VITE_API_BASE_URL= npm run build
chmod -R o+rX dist
```

然后强制刷新浏览器。

### 上传返回 413

确认当前生效的 Nginx `server` 块包含 `client_max_body_size 12m;`，再执行 `nginx -t` 和 `systemctl reload nginx`。

### AI 重构成功但图片无法显示

- 确认 Nginx 已把 `/uploads/` 反向代理到 `127.0.0.1:8000`。
- 直接访问后端返回的 `/uploads/reconstructions/<filename>.png` 检查是否为 `200`。
- 检查 `journalctl -u ad-api -n 100 --no-pager` 和 `/var/log/nginx/error.log`。

## 当前限制

- 没有账号、权限、数据库和历史项目列表；已生成投放方案只能通过方案 ID 路由重新打开。
- 上传文件、成图、风格模板和投放方案只保存在当前后端的本地磁盘。
- AI 图片请求目前采用同步等待，复杂生成可能耗时较长。
- 图片模型可能改变商品细节，也可能生成错误或不可读的中文。
- 自定义图片接口需要兼容当前支持的 OpenAI Images 返回格式；百炼 Wan2.7 由后端单独适配。
- 投放任务使用单机进程内的 asyncio 任务，不是 Redis/Celery 等可恢复队列；后端在任务执行期间重启时不会自动续跑。
- 公开资料研究依赖外网可用性，失败时会回退到内置官方参考资料，不代表广告平台实时数据。
- 当前不会把方案直接发布到 TikTok Ads、Google Ads 或国内广告平台。
- CORS 允许本地 Vite 前端和当前演示服务器地址；如果新前端需要跨域直连后端，需更新 `backend/app/main.py`。通过 Nginx 同源访问 `/api` 时不需要额外增加 CORS 来源。
- 默认部署使用 HTTP，未配置 HTTPS 证书。

## 后续可扩展方向

- 增加用户系统、项目保存、历史记录和生成版本管理。
- 使用数据库和对象存储替代本地文件。
- 将 API Key 改为服务端加密保存或密钥管理服务托管。
- 将投放策划的进程内任务迁移到可恢复队列，增加失败重试和额度控制。
- 增加投放方案列表、版本管理、多项目管理和广告平台发布集成。
- 增加商品分割、遮罩和局部重绘，提高商品真实性。
- 将 AI 视觉设计与确定性文字排版结合，提高中文文案准确率。
- 增加更多卫浴品类、风格模板、画幅和批量生成能力。
- 增加自动化测试、内容审核、生成记录和生产部署配置。
