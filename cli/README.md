# VisionCraft CLI 使用文档

## 🚀 快速开始

### 安装依赖

```bash
# 如果使用完整后端功能
pip install -r requirements.txt

# 如果只使用 CLI（模拟模式）
python cli/visioncraft.py --help
```

### 基本用法

```bash
# 查看帮助
python cli/visioncraft.py --help

# 查看支持的命令
python cli/visioncraft.py -h
```

---

## 📋 可用命令

### 1. 文生图 (generate)

根据自然语言描述生成图片。

```bash
python cli/visioncraft.py generate -p "一只在星空下的猫" -s anime
```

**参数：**
- `-p, --prompt` (必需): 图片描述提示词
- `-s, --style`: 艺术风格 (默认：realistic)
  - `realistic` - 写实摄影
  - `illustration` - 插画艺术
  - `minimalist` - 极简主义
  - `abstract` - 抽象艺术
  - `watercolor` - 水彩画
  - `oil_painting` - 油画
  - `digital_art` - 数字艺术
  - `anime` - 动漫风格
  - `concept_art` - 概念艺术
  - `architectural` - 建筑设计
- `-W, --width`: 图片宽度 (默认：1024)
- `-H, --height`: 图片高度 (默认：1024)
- `--steps`: 推理步数 (默认：30)
- `--guidance`: 引导系数 (默认：7.5)
- `--seed`: 随机种子 (默认：随机)

**示例：**
```bash
# 生成动漫风格的风景
python cli/visioncraft.py generate -p "美丽的樱花树，春天，日落" -s anime -W 1024 -H 768

# 生成写实摄影，指定种子以保证可重复性
python cli/visioncraft.py generate -p "雪山湖泊倒影" -s realistic --seed 42

# 生成高细节的数字艺术作品
python cli/visioncraft.py generate -p "未来城市，霓虹灯，赛博朋克" -s digital_art --steps 50
```

---

### 2. 图片编辑 (edit)

使用自然语言指令编辑现有图片。

#### 全局编辑 (Img2Img)

```bash
python cli/visioncraft.py edit -i input.png --instruction "把天空变成日落"
```

#### 局部编辑 (Inpainting)

```bash
python cli/visioncraft.py edit -i input.png -m mask.png --instruction "替换为红色花朵"
```

**参数：**
- `-i, --image` (必需): 输入图片路径
- `--instruction` (必需): 编辑指令（自然语言）
- `-m, --mask`: Mask 图片路径（用于局部编辑，白色区域会被编辑）
- `--strength`: 编辑强度 0-1 (默认：0.75)
  - 值越大，编辑幅度越大
  - 值越小，越保留原图

**示例：**
```bash
# 改变整体风格
python cli/visioncraft.py edit -i photo.png --instruction "转换成油画风格"

# 调整季节
python cli/visioncraft.py edit -i landscape.png --instruction "把夏天变成冬天，添加雪景"

# 局部修改（需要 mask）
python cli/visioncraft.py edit -i portrait.png -m face_mask.png --instruction "改变发色为金色" --strength 0.8

# 轻微调整
python cli/visioncraft.py edit -i product.png --instruction "增强光线，使产品更突出" --strength 0.4
```

---

### 3. 视觉重设计 (redesign)

基于现有图片生成多个设计方案。

```bash
python cli/visioncraft.py redesign -i input.png -t "赛博朋克风格" -n 3
```

**参数：**
- `-i, --image` (必需): 输入图片路径
- `-t, --target-style` (必需): 目标风格描述
- `-n, --count`: 生成方案数量 (默认：3)
- `--preserve`: 要保留的元素列表

**示例：**
```bash
# 生成 3 个赛博朋克风格方案
python cli/visioncraft.py redesign -i logo.png -t "赛博朋克风格，霓虹色彩" -n 3

# 生成 5 个方案，保留特定元素
python cli/visioncraft.py redesign -i design.png -t "极简现代风格" -n 5 --preserve "主体形状 品牌色彩"

# 转换为不同艺术风格
python cli/visioncraft.py redesign -i sketch.png -t "水彩画风格，柔和色调" -n 4
```

---

### 4. 审美评估 (evaluate)

对图片进行 AI 审美质量评估。

```bash
python cli/visioncraft.py evaluate -i input.png
```

**参数：**
- `-i, --image` (必需): 输入图片路径

**输出内容：**
- 综合评分 (1-10 分)
- 构图分析（三分法、对称性、平衡感）
- 色彩和谐度
- 智能改进建议

**示例：**
```bash
# 评估摄影作品
python cli/visioncraft.py evaluate -i photo.jpg

# 评估设计稿
python cli/visioncraft.py evaluate -i design.png

# 批量评估（使用循环）
for img in designs/*.png; do
    python cli/visioncraft.py evaluate -i "$img"
done
```

---

### 5. 风格列表 (styles)

查看所有支持的艺术风格。

```bash
python cli/visioncraft.py styles
```

---

## 💡 高级用法

### 组合工作流

#### 工作流 1：从概念到成品
```bash
# 1. 生成初始概念
python cli/visioncraft.py generate -p "现代建筑外观" -s architectural -o concept.png

# 2. 编辑优化
python cli/visioncraft.py edit -i concept.png --instruction "增加玻璃幕墙，使更现代化"

# 3. 评估质量
python cli/visioncraft.py evaluate -i concept.png
```

#### 工作流 2：多方案探索
```bash
# 1. 生成基础设计
python cli/visioncraft.py generate -p "产品包装设计" -s minimalist

# 2. 生成多个变体
python cli/visioncraft.py redesign -i base_design.png -t "不同配色方案" -n 5

# 3. 评估所有方案
for i in {1..5}; do
    python cli/visioncraft.py evaluate -i variant_$i.png
done
```

#### 工作流 3：精细编辑
```bash
# 1. 创建 mask（使用图像编辑软件）
# 2. 局部编辑
python cli/visioncraft.py edit -i original.png -m object_mask.png \
    --instruction "替换为陶瓷材质" --strength 0.9

# 3. 全局调色
python cli/visioncraft.py edit -i edited.png --instruction \
    "调整为暖色调，增强对比度" --strength 0.3
```

---

## 🔧 配置选项

### 环境变量

```bash
# 设置后端 API 地址（如果后端运行在不同端口）
export VISIONCRAFT_API_URL=http://localhost:8000

# 设置输出目录
export VISIONCRAFT_OUTPUT_DIR=./my_outputs

# 启用调试模式
export VISIONCRAFT_DEBUG=1
```

---

## ⚠️ 注意事项

1. **模拟模式**: 如果后端服务未启动，CLI 将自动进入模拟模式，仅演示功能流程。

2. **图片格式**: 支持 PNG、JPG、JPEG、WEBP 等常见格式。

3. **Mask 制作**: 
   - Mask 图片应为黑白图
   - 白色区域 (255) 表示要编辑的区域
   - 黑色区域 (0) 表示保持不变

4. **性能优化**:
   - 大尺寸图片会消耗更多显存
   - 建议使用 `--steps 20-30` 平衡质量和速度
   - GPU 加速可显著提升生成速度

5. **文件管理**:
   - 生成的图片保存在 `./output/` 目录
   - 建议定期清理临时文件

---

## 🆘 故障排除

### 问题：提示 "后端服务未安装"
**解决**: 这是正常现象，CLI 会自动切换到模拟模式。如需完整功能，请安装后端依赖并启动服务。

### 问题：图片生成失败
**解决**: 
- 检查图片路径是否正确
- 确保有足够的磁盘空间
- 检查 GPU 显存是否充足

### 问题：中文乱码
**解决**: 确保终端支持 UTF-8 编码。
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

---

## 📞 技术支持

如遇问题，请查看：
- 完整文档：`docs/DEVELOPMENT.md`
- API 文档：启动后端后访问 `http://localhost:8000/docs`
