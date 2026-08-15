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

`backend/app/generator.py` 是后续接入大模型的替换点；只要保持返回结构不变，前端无需修改。
