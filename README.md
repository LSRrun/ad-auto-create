# 沐境 · 卫浴广告自动生成器

一个前后端分离的卫浴广告生成工具。用户上传商品图片、填写商品信息并选择视觉风格后，可以使用本地规则快速生成广告页面，也可以接入大模型润色文案或生成完整的 AI 场景广告图。

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
│   │   └── style_templates/      # HTML/参考图导入、安全清理、布局编译与持久化
│   ├── data/                     # 风格草稿与已发布模板（Git 忽略）
│   ├── uploads/                  # 本地上传图片和 AI 重构结果
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # 主页面和业务状态
│   │   ├── api.js                # 前后端请求封装
│   │   ├── components/           # 模型配置与预览切换组件
│   │   └── styles.css
│   └── package.json
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

请确保百炼 API Key 与服务地域一致。连接测试只检查鉴权，不会生成图片；真正执行 AI 重构时会调用图片模型，并可能产生费用。

## API 概览

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/health` | 后端健康检查 |
| GET | `/api/styles` | 获取广告风格 |
| POST | `/api/style-templates/drafts/html` | 上传 HTML 并创建安全模板草稿 |
| POST | `/api/style-templates/drafts/reference` | 使用视觉模型从参考图生成草稿 |
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

具体请求字段和返回结构以 Swagger 文档为准。

## API Key 与数据安全

- API Key 只保存在当前浏览器页面的 React 内存状态中，不写入源码、本地文件、数据库或 `localStorage`。
- 刷新或关闭页面后，当前模型配置和 API Key 会丢失。
- 调用 AI 功能时，API Key 会随请求发送给本项目后端，再由后端用于访问所选模型服务商。
- AI 重构会把商品图片和广告文案发送给所选图片模型服务商；敏感或未公开商品图请先确认服务商的数据政策。
- 不要把 API Key 写入 README、前端源码、截图或 Git 提交。
- 生产环境应改用服务端密钥管理、用户鉴权、访问限流和 HTTPS，不应继续让公共用户直接提交长期有效的管理型密钥。

上传的商品图片和生成结果会保存在 `backend/uploads/`。该目录内容已经被 Git 忽略，但当前版本不会自动定期清理，本机或服务器维护者需要自行管理存储和隐私。

上传 HTML 不会在主页直接执行。后端会删除脚本、交互标签、事件属性、外链和高风险 CSS，前端再通过 CSP 与不授予脚本权限的沙箱 iframe 渲染。风格源文件和已发布资产保存在 `backend/data/`，使用者需要确保对上传的 HTML、图片、字体和品牌资产拥有使用权。

## 构建与检查

后端导入检查：

```bash
conda run -n adcreate python -m compileall -q backend/app
```

风格模板回归测试：

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

## 当前限制

- 没有账号、权限、数据库和历史项目管理。
- 上传文件与生成结果只保存在当前后端的本地磁盘。
- AI 图片请求目前采用同步等待，复杂生成可能耗时较长。
- 图片模型可能改变商品细节，也可能生成错误或不可读的中文。
- 自定义图片接口需要兼容当前支持的 OpenAI Images 返回格式；百炼 Wan2.7 由后端单独适配。
- CORS 当前只允许本地前端的 `localhost:5173` 和 `127.0.0.1:5173`。

## 后续可扩展方向

- 增加用户系统、项目保存、历史记录和生成版本管理。
- 使用数据库和对象存储替代本地文件。
- 将 API Key 改为服务端加密保存或密钥管理服务托管。
- 增加异步任务队列、进度查询、失败重试和额度控制。
- 增加商品分割、遮罩和局部重绘，提高商品真实性。
- 将 AI 视觉设计与确定性文字排版结合，提高中文文案准确率。
- 增加更多卫浴品类、风格模板、画幅和批量生成能力。
- 增加自动化测试、内容审核、生成记录和生产部署配置。
