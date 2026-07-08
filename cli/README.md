# VisionCraft CLI

> 🤖 **本项目由 AI 自主开发完成**  
> 从架构设计、代码实现到文档编写，全流程由 AI 驱动生成。

## 项目目标

VisionCraft CLI 致力于打造一个真正懂视觉审美创造的 AI 设计工具，让设计师和普通用户都能通过简单的自然语言指令，完成从创意构思到视觉呈现的完整设计流程。

### 核心能力

- 🎨 **文生图** - 将自然语言描述转化为高质量视觉图像
- ✏️ **智能编辑** - 理解编辑意图，精准修改图片内容或风格
- 🔄 **视觉重设计** - 基于现有设计生成多个创新方案
- ⭐ **审美评估** - AI 专业评分，提供构图、色彩分析和改进建议
- 📋 **风格探索** - 支持 10 种艺术风格，快速切换不同视觉表现

---

## 快速使用

### 1. 查看帮助
```bash
python cli/visioncraft.py --help
```

### 2. 生成图片
```bash
python cli/visioncraft.py generate -p "一只在星空下的猫" -s anime
```

### 3. 编辑图片
```bash
python cli/visioncraft.py edit -i input.png --instruction "把天空变成日落"
```

### 4. 重设计方案
```bash
python cli/visioncraft.py redesign -i input.png -t "赛博朋克风格" -n 3
```

### 5. 评估图片质量
```bash
python cli/visioncraft.py evaluate -i input.png
```

### 6. 查看支持的风格
```bash
python cli/visioncraft.py styles
```

---

## 详细说明

完整文档请查看各命令的 `--help` 参数，或参考：
- 命令详解：`python cli/visioncraft.py [command] --help`
- 批量处理：`python cli/batch_processor.py --help`
- 配置管理：`python cli/config_manager.py --help`
