# VisionCraft - AI驱动的智能设计软件

## 项目概述
VisionCraft 是一个真正懂视觉审美创造的AI设计软件，能够理解自然语言指令，完成从创意到视觉呈现的全流程设计工作。

## 核心功能

### 1. 文生图 (Text-to-Image)
- 支持自然语言描述生成高质量图像
- 理解设计风格、色彩搭配、构图原则
- 多风格适配：写实、插画、抽象、极简等

### 2. 智能编辑 (Smart Editing)
- 局部修改 (Inpainting/Outpainting)
- 风格迁移 (Style Transfer)
- 智能扩图 (Image Extension)
- 元素替换与调整

### 3. 视觉重设计 (Visual Redesign)
- 基于现有图片进行创意重构
- 多方案自动生成
- 保持品牌一致性

### 4. 审美评估 (Aesthetic Scoring)
- AI审美质量评分
- 构图分析建议
- 色彩和谐度评估

## 技术栈

- **后端**: Python + FastAPI
- **AI模型**: 
  - Stable Diffusion XL / SD 3.5
  - ControlNet (姿态/边缘/深度控制)
  - CLIP (语义理解)
  - BLIP (图像描述)
- **前端**: React + TypeScript + TailwindCSS
- **部署**: Docker + Kubernetes

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python backend/main.py

# 启动前端开发服务器
cd frontend && npm install && npm run dev
```

## 项目结构

```
visioncraft/
├── backend/           # 后端API服务
│   ├── api/          # API路由
│   ├── models/       # AI模型封装
│   ├── services/     # 业务逻辑
│   └── utils/        # 工具函数
├── frontend/         # 前端应用
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
├── models/           # 预训练模型
├── tests/            # 测试用例
└── docs/             # 文档
```

## API示例

### 生成图片
```python
POST /api/v1/generate
{
    "prompt": "一个现代简约风格的客厅设计，大面积落地窗，自然光线充足",
    "style": "photorealistic",
    "aspect_ratio": "16:9"
}
```

### 编辑图片
```python
POST /api/v1/edit
{
    "image_id": "img_123",
    "mask": "base64_encoded_mask",
    "instruction": "将沙发换成深蓝色的皮质沙发",
    "strength": 0.75
}
```

### 审美评估
```python
POST /api/v1/aesthetic/evaluate
{
    "image_id": "img_123"
}
```

## 许可证
MIT License

## 贡献
欢迎提交Issue和Pull Request！