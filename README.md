# VisionCraft - AI 驱动的智能设计软件

> 🤖 **本项目由 AI 自主开发完成**  
> 从架构设计、代码实现到文档编写，全流程由 AI 驱动生成。

---

## 📦 CLI 工具使用

VisionCraft CLI 是一个命令行界面工具，支持通过简单的命令完成图片生成、编辑、评估等操作。

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本用法

#### 1. 查看帮助
```bash
python cli/visioncraft.py --help
```

#### 2. 生成图片（文生图）
```bash
# 基础用法
python cli/visioncraft.py generate -p "一只在星空下的猫" -s anime

# 指定尺寸和参数
python cli/visioncraft.py generate \
  -p "现代简约风格的客厅设计" \
  -s realistic \
  -W 1024 -H 1024 \
  --steps 30 \
  --guidance 7.5 \
  --seed 42
```

#### 3. 编辑图片
```bash
# 全局编辑 (Img2Img)
python cli/visioncraft.py edit \
  -i input.png \
  --instruction "把天空变成日落"

# 局部编辑 (Inpainting)
python cli/visioncraft.py edit \
  -i input.png \
  -m mask.png \
  --instruction "替换为红色花朵" \
  --strength 0.75
```

#### 4. 视觉重设计
```bash
python cli/visioncraft.py redesign \
  -i input.png \
  -t "赛博朋克风格" \
  -n 3
```

#### 5. 审美评估
```bash
python cli/visioncraft.py evaluate -i input.png
```

#### 6. 查看支持的風格
```bash
python cli/visioncraft.py styles
```

### 命令参数详解

#### generate 命令
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-p, --prompt` | 图片描述提示词（必填） | - |
| `-s, --style` | 艺术风格 | realistic |
| `-W, --width` | 图片宽度 | 1024 |
| `-H, --height` | 图片高度 | 1024 |
| `--steps` | 推理步数 | 30 |
| `--guidance` | 引导系数 | 7.5 |
| `--seed` | 随机种子 (-1 为随机) | -1 |

**支持的风格**: `realistic`, `illustration`, `minimalist`, `abstract`, `watercolor`, `oil_painting`, `digital_art`, `anime`, `concept_art`, `architectural`

#### edit 命令
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --image` | 输入图片路径（必填） | - |
| `--instruction` | 编辑指令（必填） | - |
| `-m, --mask` | Mask 图片路径（可选） | - |
| `--strength` | 编辑强度 0-1 | 0.75 |

#### redesign 命令
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --image` | 输入图片路径（必填） | - |
| `-t, --target-style` | 目标风格描述（必填） | - |
| `-n, --count` | 生成方案数量 | 3 |
| `--preserve` | 要保留的元素列表 | - |

#### evaluate 命令
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --image` | 输入图片路径（必填） | - |

### 批量处理

使用 `batch_processor.py` 进行批量操作：

```bash
# 查看帮助
python cli/batch_processor.py --help

# 批量生成
python cli/batch_processor.py generate \
  --prompts "prompt1,prompt2,prompt3" \
  -s anime \
  -o ./output
```

### 配置管理

使用 `config_manager.py` 管理配置：

```bash
# 查看帮助
python cli/config_manager.py --help

# 设置 API Key
python cli/config_manager.py set llm.api_key "your-api-key"

# 查看配置
python cli/config_manager.py show
```

---

## 🧠 大模型接入方法

VisionCraft 支持接入多种大语言模型来增强语义理解和提示词优化能力。

### 支持的模型提供商

- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Anthropic** (Claude 系列)
- **Google** (Gemini 系列)
- **本地部署** (Ollama, vLLM 等)

### 配置方式

#### 1. 环境变量配置

创建 `.env` 文件或在系统中设置环境变量：

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
export ANTHROPIC_MODEL="claude-3-opus-20240229"

# Google
export GOOGLE_API_KEY="..."
export GOOGLE_MODEL="gemini-pro"

# 本地模型
export LOCAL_LLM_ENDPOINT="http://localhost:11434"
export LOCAL_LLM_MODEL="llama2"
```

#### 2. 配置文件方式

编辑 `backend/config/settings.py` 或使用 CLI 配置：

```bash
python cli/config_manager.py set llm.provider "openai"
python cli/config_manager.py set llm.api_key "sk-..."
python cli/config_manager.py set llm.model "gpt-4"
```

### 代码集成示例

#### 在提示词优化中使用 LLM

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

def optimize_prompt(user_input: str) -> str:
    """使用 LLM 优化用户输入的提示词"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的 AI 绘画提示词工程师。请将用户的简单描述优化为详细、专业的 Stable Diffusion 提示词。"
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    )
    return response.choices[0].message.content

# 使用优化后的提示词生成图片
optimized_prompt = optimize_prompt("一只可爱的猫")
# 调用 image_generator.generate(prompt=optimized_prompt)
```

#### 使用本地模型 (Ollama)

```python
import requests

def query_local_llm(prompt: str, model: str = "llama2"):
    """查询本地 Ollama 模型"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# 使用
result = query_local_llm("优化这个提示词：海边的日落")
```

### 提示词工程最佳实践

1. **结构化提示词**:
   ```
   [主体描述], [环境/背景], [风格/艺术形式], [光照/氛围], [技术参数]
   ```

2. **负面提示词** (Negative Prompt):
   ```
   low quality, worst quality, blurry, deformed, watermark, text
   ```

3. **风格关键词示例**:
   - 写实：`photorealistic, 8k, highly detailed, professional photography`
   - 动漫：`anime style, studio ghibli, vibrant colors, cel shaded`
   - 概念艺术：`concept art, matte painting, cinematic lighting, epic composition`

---

## 📝 注意事项

1. **GPU 要求**: 运行完整功能需要 NVIDIA GPU (推荐 8GB+ 显存)
2. **模拟模式**: 当后端依赖未安装时，CLI 会自动进入模拟模式
3. **模型下载**: 首次运行时会自动下载 Stable Diffusion 模型 (约 4-7GB)

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
