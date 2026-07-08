# VisionCraft 开发文档

## 项目简介

VisionCraft 是一个真正懂视觉审美创造的 AI 驱动设计软件，支持：
- 自然语言到图片生成 (Text-to-Image)
- 智能图片编辑和修改 (Inpainting/Img2Img)
- 视觉重设计和风格转换
- AI 审美评估和建议

## 技术架构

### 后端技术栈
- **框架**: FastAPI (Python)
- **AI 模型**: 
  - Stable Diffusion XL / SD 3.5
  - ControlNet (姿态/边缘/深度控制)
  - CLIP (语义理解)
- **图像处理**: Pillow, OpenCV
- **异步处理**: asyncio

### 前端技术栈
- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **样式**: TailwindCSS 3
- **状态管理**: Zustand
- **UI 组件**: Radix UI, Lucide Icons

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- GPU (推荐，用于加速 AI 推理)
- CUDA 11.8+ (如果使用 GPU)

### 后端安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000 使用应用。

## API 文档

### 核心端点

#### 1. 生成图片
```
POST /api/v1/generate
Content-Type: application/json

{
    "prompt": "描述文本",
    "negative_prompt": "负面描述 (可选)",
    "style": "风格类型",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 30,
    "guidance_scale": 7.5,
    "seed": null,
    "num_images": 1
}
```

#### 2. 编辑图片
```
POST /api/v1/edit
Content-Type: application/json

{
    "image_id": "图片 ID",
    "instruction": "编辑指令",
    "mask": "base64 编码的 mask (可选)",
    "strength": 0.75
}
```

#### 3. 视觉重设计
```
POST /api/v1/redesign
Content-Type: application/json

{
    "image_id": "图片 ID",
    "style_description": "目标风格描述",
    "preserve_elements": ["需要保留的元素"],
    "num_variants": 3
}
```

#### 4. 审美评估
```
POST /api/v1/aesthetic/evaluate
Content-Type: application/json

{
    "image_id": "图片 ID"
}
```

#### 5. 上传图片
```
POST /api/v1/upload
Content-Type: multipart/form-data

file: [图片文件]
```

#### 6. 获取图片
```
GET /api/v1/images/{image_id}
```

### 支持的样式
- photorealistic (写实风格)
- illustration (插画风格)
- minimalist (极简主义)
- abstract (抽象艺术)
- watercolor (水彩画)
- oil_painting (油画)
- digital_art (数字艺术)
- anime (动漫风格)
- concept_art (概念艺术)
- architectural (建筑设计)

## 项目结构

```
visioncraft/
├── backend/                 # 后端服务
│   ├── main.py             # FastAPI 主应用
│   ├── api/                # API 路由
│   ├── models/             # 数据模型
│   ├── services/           # 业务逻辑
│   │   ├── image_generator.py    # 图片生成服务
│   │   ├── image_editor.py       # 图片编辑服务
│   │   └── aesthetic_evaluator.py # 审美评估服务
│   └── utils/              # 工具函数
│       └── file_handler.py # 文件处理
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── App.tsx        # 主应用组件
│   │   ├── main.tsx       # 入口文件
│   │   └── index.css      # 全局样式
│   ├── package.json
│   └── vite.config.ts
├── requirements.txt        # Python 依赖
└── README.md              # 项目说明
```

## 高级功能

### 自定义模型
可以在服务类中指定不同的模型 ID：

```python
# backend/services/image_generator.py
def load_model(self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"):
    # 可以替换为其他 SD 模型
    pass
```

### GPU 优化
- 启用 xformers 进行内存优化
- 使用 DPM Solver 加速推理
- VAE 切片减少显存占用

### 批量处理
支持一次生成多张图片：
```json
{
    "num_images": 4
}
```

## 性能优化建议

1. **GPU 显存优化**
   - 使用 `--precision fp16`
   - 启用 xformers: `pipe.enable_xformers_memory_efficient_attention()`
   - 启用 VAE 切片：`pipe.enable_vae_slicing()`

2. **推理速度优化**
   - 使用 DPM Solver scheduler
   - 减少 inference steps (20-30 通常足够)
   - 适当降低分辨率

3. **并发处理**
   - 使用 asyncio 处理多个请求
   - 考虑使用任务队列 (Celery/RQ)

## 常见问题

### Q: 显存不足怎么办？
A: 
- 降低生成分辨率
- 减少 batch size
- 使用 `--medvram` 或 `--lowvram` 模式
- 考虑使用 CPU 推理 (速度慢)

### Q: 如何添加新的风格？
A: 在 `ImageGeneratorService.style_prompts` 中添加新的风格映射。

### Q: 如何提高生成质量？
A:
- 增加 inference steps (30-50)
- 调整 guidance scale (7-9)
- 使用更详细的 prompt
- 尝试 negative prompt

## 开发计划

- [ ] ControlNet 集成 (姿态/边缘控制)
- [ ] 批量处理支持
- [ ] 用户系统和作品收藏
- [ ] 实时预览功能
- [ ] 更多 AI 模型支持
- [ ] 插件系统
- [ ] API 速率限制
- [ ] Docker 部署支持

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
