# VisionCraft CLI 示例文件

## 批量生成示例 - prompts.json

```json
[
  {
    "prompt": "一只在星空下仰望的猫，梦幻氛围",
    "style": "anime"
  },
  {
    "prompt": "未来赛博朋克城市，霓虹灯闪烁",
    "style": "digital_art"
  },
  {
    "prompt": "宁静的山水画，中国传统风格",
    "style": "watercolor"
  },
  {
    "prompt": "极简主义几何抽象图案",
    "style": "minimalist"
  },
  {
    "prompt": "森林中的魔法小屋，童话风格",
    "style": "illustration"
  }
]
```

**使用方法：**
```bash
python cli/batch_processor.py generate -f examples/prompts.json -o ./my_generations
```

---

## 批量编辑示例 - images.txt

```txt
# 每行一个图片路径
./images/photo1.png
./images/photo2.png
./images/photo3.png
./images/product_shot.png
./images/logo_design.png
```

**使用方法：**
```bash
# 批量应用相同的编辑指令
python cli/batch_processor.py edit -f examples/images.txt -i "转换成油画风格" -o ./edited_images
```

---

## 批量评估示例 - portfolio.txt

```txt
./portfolio/design_01.png
./portfolio/design_02.png
./portfolio/design_03.png
./portfolio/design_04.png
./portfolio/design_05.png
```

**使用方法：**
```bash
# 批量评估并生成报告
python cli/batch_processor.py evaluate -f examples/portfolio.txt -r ./evaluation_report.json
```

---

## 配置管理示例

```bash
# 查看当前配置
python cli/config_manager.py show

# 获取特定配置项
python cli/config_manager.py get api.base_url
python cli/config_manager.py get generation.default_style

# 设置配置项
python cli/config_manager.py set api.base_url http://api.example.com:8000
python cli/config_manager.py set generation.default_steps 50
python cli/config_manager.py set output.directory ./my_output
python cli/config_manager.py set display.verbose true

# 重置为默认配置
python cli/config_manager.py reset
```

---

## 完整工作流示例

### 1. 创建项目配置文件
```bash
# 设置 API 地址
python cli/config_manager.py set api.base_url http://localhost:8000

# 设置默认输出目录
python cli/config_manager.py set output.directory ./projects/my_campaign
```

### 2. 批量生成营销素材
```bash
python cli/batch_processor.py generate -f marketing_prompts.json -o ./projects/my_campaign/generated
```

### 3. 批量优化生成的图片
```bash
# 创建图片列表
ls ./projects/my_campaign/generated/*.png > image_list.txt

# 批量增强质量
python cli/batch_processor.py edit -f image_list.txt -i "提高清晰度，增强色彩饱和度" -o ./projects/my_campaign/enhanced
```

### 4. 评估所有设计
```bash
python cli/batch_processor.py evaluate -f image_list.txt -r ./projects/my_campaign/evaluation.json
```

### 5. 查看评估报告
```bash
cat ./projects/my_campaign/evaluation.json | python -m json.tool
```

---

## 提示词模板示例

### 产品摄影
```json
{
  "prompt": "专业的产品摄影，{product} 放置在 {background} 上，柔和的影棚灯光，高分辨率，商业广告风格",
  "style": "realistic"
}
```

### 角色设计
```json
{
  "prompt": "{character} 角色设计，{style_description}，完整的身体，正面和侧面视图，概念艺术",
  "style": "concept_art"
}
```

### 建筑可视化
```json
{
  "prompt": "现代建筑设计，{building_type}，{architectural_style} 风格，黄昏时分，温暖的灯光，超写实渲染",
  "style": "architectural"
}
```

### Logo 设计
```json
{
  "prompt": "简洁的 logo 设计，{industry} 行业，{brand_personality} 品牌个性，矢量风格，白色背景",
  "style": "minimalist"
}
```
