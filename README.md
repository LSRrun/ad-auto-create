# 沐境·卫浴广告生成器

一个前后端分离的最小可用原型：用户填写商品信息、上传图片并选择样式，系统生成可预览的卫浴广告页面。

## 技术栈

- 前端：React + Vite
- 后端：Python + FastAPI
- 存储：本地文件（初期不使用数据库）

## 启动

需要 Node.js 18+ 和 Python 3.10+。

### 1. 创建并启动后端环境

```bash
conda create -n adcreate python=3.12 -y
conda activate adcreate
python -m pip install -r backend/requirements.txt
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

接口文档：<http://localhost:8000/docs>

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

页面地址：<http://localhost:5173>

## 当前流程

1. 前端请求 `GET /api/styles` 获取可用广告样式。
2. 用户提交商品信息和图片到 `POST /api/ads/generate`。
3. 后端保存图片，使用简单规则生成标题、文案和卖点。
4. 前端按所选样式渲染广告预览。

## AI 文案润色

原有“生成广告页面”规则模式保持不变。如需 AI 文案：

1. 在“商品信息”右侧点击“选择 AI 模型”。
2. 选择 DeepSeek、通义千问、OpenAI、Ollama 或自定义 OpenAI 兼容接口。
3. 填写模型名称、Base URL 和 API Key，可先测试连接再保存。
4. 填写商品信息、选择风格，点击“AI 润色”即可更新右侧预览文案。

API Key 只保存在当前页面内存中，不写入项目文件，刷新页面后会清除。`backend/app/ai/` 是 AI 适配、风格提示词和输出校验模块；`backend/app/generator.py` 继续负责不依赖 AI 的规则生成。
