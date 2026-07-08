#!/usr/bin/env python3
"""
VisionCraft Batch Processor - 批量处理工具

支持批量生成、批量编辑、批量评估等功能
"""

import asyncio
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, cli_module=None):
        self.cli_module = cli_module
        self.results = []
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def process_batch_generate(self, prompts_file: str, output_dir: str, **kwargs):
        """
        批量文生图
        
        prompts_file: JSON 文件，包含提示词列表
        格式：[{"prompt": "...", "style": "..."}, ...]
        """
        print(f"📦 开始批量生成任务")
        print(f"📄 提示词文件：{prompts_file}")
        
        # 读取提示词文件
        with open(prompts_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        
        self.stats["total"] = len(tasks)
        self.stats["start_time"] = datetime.now()
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 并发处理任务
        semaphore = asyncio.Semaphore(3)  # 限制并发数为 3
        
        async def process_task(task_info, index):
            async with semaphore:
                prompt = task_info.get("prompt", "")
                style = task_info.get("style", "realistic")
                
                print(f"\n[{index+1}/{len(tasks)}] 正在生成：'{prompt[:50]}...'")
                
                # 模拟生成（实际应调用后端 API）
                await asyncio.sleep(0.5)
                
                result = {
                    "index": index + 1,
                    "prompt": prompt,
                    "style": style,
                    "status": "success",
                    "output_file": str(output_path / f"gen_{index+1}.png"),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(result)
                self.stats["success"] += 1
                print(f"✓ 完成：{result['output_file']}")
                
                return result
        
        # 执行所有任务
        tasks_coroutines = [
            process_task(task, i) for i, task in enumerate(tasks)
        ]
        
        await asyncio.gather(*tasks_coroutines, return_exceptions=True)
        
        self.stats["end_time"] = datetime.now()
        self._print_summary()
        
        return self.results
    
    async def process_batch_edit(self, images_file: str, instruction: str, 
                                  output_dir: str, **kwargs):
        """
        批量图片编辑
        
        images_file: 包含图片路径的文本文件（每行一个路径）或 JSON 文件
        """
        print(f"📦 开始批量编辑任务")
        print(f"📝 编辑指令：{instruction}")
        
        # 读取图片列表
        images = self._load_image_list(images_file)
        
        self.stats["total"] = len(images)
        self.stats["start_time"] = datetime.now()
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        semaphore = asyncio.Semaphore(2)  # 限制并发数为 2
        
        async def process_image(image_path, index):
            async with semaphore:
                print(f"\n[{index+1}/{len(images)}] 正在编辑：{image_path}")
                
                if not Path(image_path).exists():
                    print(f"⚠️  文件不存在：{image_path}")
                    result = {
                        "index": index + 1,
                        "input_file": image_path,
                        "status": "failed",
                        "error": "File not found"
                    }
                    self.results.append(result)
                    self.stats["failed"] += 1
                    return result
                
                # 模拟编辑
                await asyncio.sleep(0.5)
                
                result = {
                    "index": index + 1,
                    "input_file": image_path,
                    "instruction": instruction,
                    "status": "success",
                    "output_file": str(output_path / f"edit_{index+1}.png"),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(result)
                self.stats["success"] += 1
                print(f"✓ 完成：{result['output_file']}")
                
                return result
        
        tasks_coroutines = [
            process_image(img, i) for i, img in enumerate(images)
        ]
        
        await asyncio.gather(*tasks_coroutines, return_exceptions=True)
        
        self.stats["end_time"] = datetime.now()
        self._print_summary()
        
        return self.results
    
    async def process_batch_evaluate(self, images_file: str, output_report: str, **kwargs):
        """
        批量审美评估
        
        生成评估报告
        """
        print(f"📦 开始批量评估任务")
        
        images = self._load_image_list(images_file)
        
        self.stats["total"] = len(images)
        self.stats["start_time"] = datetime.now()
        
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "total_images": len(images),
            "evaluations": []
        }
        
        total_score = 0
        
        for i, image_path in enumerate(images):
            print(f"\n[{i+1}/{len(images)}] 正在评估：{image_path}")
            
            if not Path(image_path).exists():
                print(f"⚠️  文件不存在：{image_path}")
                continue
            
            # 模拟评估
            await asyncio.sleep(0.3)
            
            # 生成随机评分（模拟）
            import random
            score = round(random.uniform(6.0, 9.5), 2)
            total_score += score
            
            evaluation = {
                "image": image_path,
                "score": score,
                "composition": {
                    "rule_of_thirds": round(random.uniform(0.7, 0.95), 2),
                    "symmetry": round(random.uniform(0.6, 0.9), 2),
                    "balance": round(random.uniform(0.7, 0.95), 2)
                },
                "color_harmony": round(random.uniform(0.75, 0.98), 2)
            }
            
            report_data["evaluations"].append(evaluation)
            self.stats["success"] += 1
            print(f"✓ 评分：{score}/10")
        
        # 计算平均分
        if report_data["evaluations"]:
            avg_score = total_score / len(report_data["evaluations"])
            report_data["average_score"] = round(avg_score, 2)
        
        # 保存报告
        with open(output_report, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.stats["end_time"] = datetime.now()
        self._print_summary()
        
        print(f"\n📊 评估报告已保存到：{output_report}")
        print(f"⭐ 平均评分：{report_data.get('average_score', 'N/A')}/10")
        
        return report_data
    
    def _load_image_list(self, file_path: str) -> List[str]:
        """加载图片列表"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        # JSON 格式
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "images" in data:
                    return data["images"]
        
        # 文本格式（每行一个路径）
        images = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    images.append(line)
        
        return images
    
    def _print_summary(self):
        """打印统计摘要"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        print("\n" + "="*60)
        print("📊 批量处理完成")
        print("="*60)
        print(f"总任务数：{self.stats['total']}")
        print(f"成功：{self.stats['success']} ✓")
        print(f"失败：{self.stats['failed']} ✗")
        print(f"耗时：{duration.total_seconds():.2f} 秒")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"成功率：{success_rate:.1f}%")
        
        print("="*60)
    
    def save_results(self, output_file: str):
        """保存结果到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "stats": self.stats,
                "results": self.results
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📁 详细结果已保存到：{output_file}")


async def main_async():
    """异步主函数"""
    parser = argparse.ArgumentParser(description="VisionCraft 批量处理工具")
    subparsers = parser.add_subparsers(dest='command', help='命令类型')
    
    # generate 命令
    gen_parser = subparsers.add_parser('generate', help='批量文生图')
    gen_parser.add_argument('-f', '--file', required=True, help='提示词 JSON 文件')
    gen_parser.add_argument('-o', '--output', default='./batch_output', help='输出目录')
    
    # edit 命令
    edit_parser = subparsers.add_parser('edit', help='批量编辑')
    edit_parser.add_argument('-f', '--file', required=True, help='图片列表文件')
    edit_parser.add_argument('-i', '--instruction', required=True, help='编辑指令')
    edit_parser.add_argument('-o', '--output', default='./batch_output', help='输出目录')
    
    # evaluate 命令
    eval_parser = subparsers.add_parser('evaluate', help='批量评估')
    eval_parser.add_argument('-f', '--file', required=True, help='图片列表文件')
    eval_parser.add_argument('-r', '--report', default='./evaluation_report.json', 
                            help='评估报告输出文件')
    
    args = parser.parse_args()
    
    processor = BatchProcessor()
    
    if args.command == 'generate':
        await processor.process_batch_generate(args.file, args.output)
    elif args.command == 'edit':
        await processor.process_batch_edit(args.file, args.instruction, args.output)
    elif args.command == 'evaluate':
        await processor.process_batch_evaluate(args.file, args.report)
    else:
        parser.print_help()


def main():
    """CLI 入口点"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"✗ 错误：{e}")


if __name__ == "__main__":
    main()
