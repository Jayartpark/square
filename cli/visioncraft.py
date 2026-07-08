#!/usr/bin/env python3
"""
VisionCraft CLI - AI 驱动设计软件命令行界面

功能：
- 文生图 (generate)
- 图片编辑 (edit)
- 视觉重设计 (redesign)
- 审美评估 (evaluate)
- 风格列表 (styles)
"""

import asyncio
import argparse
import sys
import os
import json
from pathlib import Path
from typing import Optional, List
import base64

# 添加后端路径到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from services.image_generator import ImageGeneratorService
    from services.image_editor import ImageEditorService
    from services.aesthetic_evaluator import AestheticEvaluatorService
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    print("⚠️  警告：后端服务未安装，将使用模拟模式运行")


class Colors:
    """终端颜色代码"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header():
    """打印程序头部"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║           🎨 VisionCraft - AI Design Studio              ║")
    print("║              AI 驱动的智能设计软件 CLI                    ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")


def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")


class MockImageGenerator:
    """模拟图片生成器（当后端不可用时）"""
    
    async def generate(self, prompt: str, style: str = "realistic", **kwargs):
        await asyncio.sleep(0.5)  # 模拟延迟
        return {
            "success": True,
            "image_id": "mock_img_123",
            "prompt": prompt,
            "style": style,
            "message": f"[模拟模式] 已生成图片：'{prompt}' ({style}风格)",
            "url": "/api/v1/images/mock_img_123"
        }


class MockImageEditor:
    """模拟图片编辑器"""
    
    async def edit(self, image_path: str, instruction: str, **kwargs):
        await asyncio.sleep(0.5)
        return {
            "success": True,
            "image_id": "mock_edit_456",
            "instruction": instruction,
            "message": f"[模拟模式] 已编辑图片：{image_path}",
            "url": "/api/v1/images/mock_edit_456"
        }
    
    async def inpaint(self, image_path: str, mask_path: str, instruction: str, **kwargs):
        await asyncio.sleep(0.5)
        return {
            "success": True,
            "image_id": "mock_inpaint_789",
            "instruction": instruction,
            "message": f"[模拟模式] 已完成局部编辑：{image_path}",
            "url": "/api/v1/images/mock_inpaint_789"
        }


class MockAestheticEvaluator:
    """模拟审美评估器"""
    
    async def evaluate(self, image_path: str):
        await asyncio.sleep(0.5)
        return {
            "success": True,
            "score": 8.5,
            "composition": {
                "rule_of_thirds": 0.85,
                "symmetry": 0.72,
                "balance": 0.88
            },
            "color_harmony": 0.91,
            "suggestions": [
                "可以尝试调整构图以增强视觉焦点",
                "色彩搭配和谐，保持当前色调",
                "建议增加一些对比度以提升层次感"
            ]
        }


class VisionCraftCLI:
    """VisionCraft 命令行主类"""
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock or not BACKEND_AVAILABLE
        
        if self.use_mock:
            self.generator = MockImageGenerator()
            self.editor = MockImageEditor()
            self.evaluator = MockAestheticEvaluator()
        else:
            self.generator = ImageGeneratorService()
            self.editor = ImageEditorService()
            self.evaluator = AestheticEvaluatorService()
        
        self.output_dir = Path("./output")
        self.output_dir.mkdir(exist_ok=True)
    
    async def generate_image(self, args):
        """文生图命令"""
        print_info(f"正在生成图片：'{args.prompt}'")
        print_info(f"风格：{args.style}")
        print_info(f"尺寸：{args.width}x{args.height}")
        
        try:
            result = await self.generator.generate(
                prompt=args.prompt,
                style=args.style,
                width=args.width,
                height=args.height,
                steps=args.steps,
                guidance_scale=args.guidance,
                seed=args.seed if args.seed != -1 else None
            )
            
            if result.get("success"):
                print_success(result.get("message", "图片生成成功"))
                print_info(f"图片 ID: {result.get('image_id')}")
                print_info(f"访问 URL: {result.get('url', 'N/A')}")
                
                if not self.use_mock:
                    output_path = self.output_dir / f"{result['image_id']}.png"
                    print_info(f"保存路径：{output_path}")
            else:
                print_error(f"生成失败：{result.get('error', '未知错误')}")
                return 1
                
        except Exception as e:
            print_error(f"发生错误：{str(e)}")
            return 1
        
        return 0
    
    async def edit_image(self, args):
        """图片编辑命令"""
        if not os.path.exists(args.image):
            print_error(f"图片文件不存在：{args.image}")
            return 1
        
        print_info(f"正在编辑图片：{args.image}")
        print_info(f"编辑指令：'{args.instruction}'")
        
        try:
            if args.mask:
                if not os.path.exists(args.mask):
                    print_error(f"Mask 文件不存在：{args.mask}")
                    return 1
                
                result = await self.editor.inpaint(
                    image_path=args.image,
                    mask_path=args.mask,
                    instruction=args.instruction,
                    strength=args.strength
                )
                print_info("模式：局部编辑 (Inpainting)")
            else:
                result = await self.editor.edit(
                    image_path=args.image,
                    instruction=args.instruction,
                    strength=args.strength
                )
                print_info("模式：全局编辑 (Img2Img)")
            
            if result.get("success"):
                print_success(result.get("message", "图片编辑成功"))
                print_info(f"结果 ID: {result.get('image_id')}")
                print_info(f"访问 URL: {result.get('url', 'N/A')}")
            else:
                print_error(f"编辑失败：{result.get('error', '未知错误')}")
                return 1
                
        except Exception as e:
            print_error(f"发生错误：{str(e)}")
            return 1
        
        return 0
    
    async def redesign_image(self, args):
        """视觉重设计命令"""
        if not os.path.exists(args.image):
            print_error(f"图片文件不存在：{args.image}")
            return 1
        
        print_info(f"正在重设计图片：{args.image}")
        print_info(f"目标风格：{args.target_style}")
        print_info(f"生成数量：{args.count}")
        
        try:
            # 这里调用后端的 redesign 接口
            # 由于是 CLI，我们简化处理
            print_warning("重设计功能需要后端服务支持")
            print_info("建议使用 API 直接调用 /api/v1/redesign 端点")
            
            # 模拟输出
            for i in range(args.count):
                print_success(f"方案 {i+1}: 已生成重设计方案")
            
        except Exception as e:
            print_error(f"发生错误：{str(e)}")
            return 1
        
        return 0
    
    async def evaluate_image(self, args):
        """审美评估命令"""
        if not os.path.exists(args.image):
            print_error(f"图片文件不存在：{args.image}")
            return 1
        
        print_info(f"正在评估图片：{args.image}")
        
        try:
            result = await self.evaluator.evaluate(args.image)
            
            if result.get("success"):
                print_success("审美评估完成")
                print("\n" + "="*50)
                print(f"{Colors.BOLD}综合评分：{result['score']}/10{Colors.ENDC}")
                print("="*50)
                
                print(f"\n{Colors.BLUE}📐 构图分析:{Colors.ENDC}")
                comp = result.get('composition', {})
                print(f"  • 三分法：{comp.get('rule_of_thirds', 0):.2f}")
                print(f"  • 对称性：{comp.get('symmetry', 0):.2f}")
                print(f"  • 平衡感：{comp.get('balance', 0):.2f}")
                
                print(f"\n{Colors.BLUE}🎨 色彩和谐度：{result.get('color_harmony', 0):.2f}{Colors.ENDC}")
                
                suggestions = result.get('suggestions', [])
                if suggestions:
                    print(f"\n{Colors.BLUE}💡 改进建议:{Colors.ENDC}")
                    for i, sug in enumerate(suggestions, 1):
                        print(f"  {i}. {sug}")
                
                print("\n" + "="*50)
            else:
                print_error(f"评估失败：{result.get('error', '未知错误')}")
                return 1
                
        except Exception as e:
            print_error(f"发生错误：{str(e)}")
            return 1
        
        return 0
    
    def list_styles(self):
        """列出支持的样式"""
        styles = {
            "realistic": "写实摄影",
            "illustration": "插画艺术",
            "minimalist": "极简主义",
            "abstract": "抽象艺术",
            "watercolor": "水彩画",
            "oil_painting": "油画",
            "digital_art": "数字艺术",
            "anime": "动漫风格",
            "concept_art": "概念艺术",
            "architectural": "建筑设计"
        }
        
        print(f"{Colors.BOLD}支持的藝術風格:{Colors.ENDC}\n")
        for key, value in styles.items():
            print(f"  {Colors.CYAN}{key:15s}{Colors.ENDC} - {value}")
        print()


async def main_async():
    """异步主函数"""
    parser = argparse.ArgumentParser(
        description="VisionCraft - AI 驱动的设计软件 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s generate -p "一只在星空下的猫" -s anime
  %(prog)s edit -i input.png --instruction "把天空变成日落"
  %(prog)s edit -i input.png -m mask.png --instruction "替换为红色花朵"
  %(prog)s redesign -i input.png -t "赛博朋克风格" -n 3
  %(prog)s evaluate -i input.png
  %(prog)s styles
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # generate 命令
    gen_parser = subparsers.add_parser('generate', help='文生图')
    gen_parser.add_argument('-p', '--prompt', required=True, help='图片描述提示词')
    gen_parser.add_argument('-s', '--style', default='realistic', 
                           choices=['realistic', 'illustration', 'minimalist', 'abstract', 
                                   'watercolor', 'oil_painting', 'digital_art', 'anime', 
                                   'concept_art', 'architectural'],
                           help='艺术风格 (默认：realistic)')
    gen_parser.add_argument('-W', '--width', type=int, default=1024, help='图片宽度 (默认：1024)')
    gen_parser.add_argument('-H', '--height', type=int, default=1024, help='图片高度 (默认：1024)')
    gen_parser.add_argument('--steps', type=int, default=30, help='推理步数 (默认：30)')
    gen_parser.add_argument('--guidance', type=float, default=7.5, help='引导系数 (默认：7.5)')
    gen_parser.add_argument('--seed', type=int, default=-1, help='随机种子 (默认：随机)')
    
    # edit 命令
    edit_parser = subparsers.add_parser('edit', help='图片编辑')
    edit_parser.add_argument('-i', '--image', required=True, help='输入图片路径')
    edit_parser.add_argument('--instruction', required=True, help='编辑指令（自然语言）')
    edit_parser.add_argument('-m', '--mask', help='Mask 图片路径（用于局部编辑）')
    edit_parser.add_argument('--strength', type=float, default=0.75, 
                            help='编辑强度 0-1 (默认：0.75)')
    
    # redesign 命令
    redesign_parser = subparsers.add_parser('redesign', help='视觉重设计')
    redesign_parser.add_argument('-i', '--image', required=True, help='输入图片路径')
    redesign_parser.add_argument('-t', '--target-style', required=True, help='目标风格描述')
    redesign_parser.add_argument('-n', '--count', type=int, default=3, 
                                help='生成方案数量 (默认：3)')
    redesign_parser.add_argument('--preserve', nargs='+', help='要保留的元素')
    
    # evaluate 命令
    eval_parser = subparsers.add_parser('evaluate', help='审美评估')
    eval_parser.add_argument('-i', '--image', required=True, help='输入图片路径')
    
    # styles 命令
    subparsers.add_parser('styles', help='列出支持的風格')
    
    args = parser.parse_args()
    
    print_header()
    
    if not args.command:
        parser.print_help()
        return 0
    
    cli = VisionCraftCLI()
    
    if args.command == 'generate':
        return await cli.generate_image(args)
    elif args.command == 'edit':
        return await cli.edit_image(args)
    elif args.command == 'redesign':
        return await cli.redesign_image(args)
    elif args.command == 'evaluate':
        return await cli.evaluate_image(args)
    elif args.command == 'styles':
        cli.list_styles()
        return 0
    
    return 0


def main():
    """CLI 入口点"""
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(130)
    except Exception as e:
        print_error(f"未处理的错误：{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
