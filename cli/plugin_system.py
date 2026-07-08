#!/usr/bin/env python3
"""
VisionCraft Plugin System - 插件系统

支持自定义插件扩展 CLI 功能
"""

import importlib
import json
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod


class VisionCraftPlugin(ABC):
    """插件基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @abstractmethod
    def register_commands(self) -> Dict[str, Callable]:
        """注册命令，返回命令名和处理函数的字典"""
        pass
    
    def on_init(self, cli_instance):
        """插件初始化回调"""
        pass
    
    def on_shutdown(self):
        """插件关闭回调"""
        pass


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dirs: Optional[list] = None):
        self.plugins: Dict[str, VisionCraftPlugin] = {}
        self.plugin_dirs = plugin_dirs or [
            Path.home() / ".visioncraft" / "plugins",
            Path(__file__).parent / "plugins"
        ]
    
    def discover_plugins(self):
        """发现并加载所有插件"""
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
            
            # 查找插件文件
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue
                
                try:
                    self.load_plugin(plugin_file)
                except Exception as e:
                    print(f"⚠️  加载插件失败 {plugin_file.name}: {e}")
    
    def load_plugin(self, plugin_path: Path):
        """加载单个插件"""
        module_name = plugin_path.stem
        
        # 动态导入模块
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 查找插件类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, VisionCraftPlugin) and 
                attr is not VisionCraftPlugin):
                
                plugin_instance = attr()
                self.register_plugin(plugin_instance)
                print(f"✓ 已加载插件：{plugin_instance.name} v{plugin_instance.version}")
    
    def register_plugin(self, plugin: VisionCraftPlugin):
        """注册插件"""
        if plugin.name in self.plugins:
            print(f"⚠️  插件已存在：{plugin.name}")
            return
        
        self.plugins[plugin.name] = plugin
        print(f"🔌 插件 '{plugin.name}' 已注册")
        print(f"   描述：{plugin.description}")
    
    def get_plugin(self, name: str) -> Optional[VisionCraftPlugin]:
        """获取插件"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> list:
        """列出所有已加载的插件"""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description
            }
            for p in self.plugins.values()
        ]
    
    def get_all_commands(self) -> Dict[str, Callable]:
        """获取所有插件注册的命令"""
        all_commands = {}
        
        for plugin in self.plugins.values():
            commands = plugin.register_commands()
            for cmd_name, handler in commands.items():
                if cmd_name in all_commands:
                    print(f"⚠️  命令冲突：{cmd_name}")
                else:
                    all_commands[cmd_name] = handler
        
        return all_commands
    
    def initialize_plugins(self, cli_instance):
        """初始化所有插件"""
        for plugin in self.plugins.values():
            plugin.on_init(cli_instance)
    
    def shutdown_plugins(self):
        """关闭所有插件"""
        for plugin in self.plugins.values():
            plugin.on_shutdown()


# ============ 示例插件 ============

class StyleTransferPlugin(VisionCraftPlugin):
    """风格迁移插件示例"""
    
    @property
    def name(self) -> str:
        return "style_transfer"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "图片风格迁移功能"
    
    def register_commands(self) -> Dict[str, Callable]:
        return {
            "transfer": self.handle_transfer
        }
    
    async def handle_transfer(self, args):
        """处理风格迁移命令"""
        print(f"🎨 风格迁移：{args.image} -> {args.style_image}")
        # 实际实现应调用风格迁移模型
        print("✓ 风格迁移完成（模拟）")


class UpscalePlugin(VisionCraftPlugin):
    """图片超分插件示例"""
    
    @property
    def name(self) -> str:
        return "upscale"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "图片超分辨率放大"
    
    def register_commands(self) -> Dict[str, Callable]:
        return {
            "upscale": self.handle_upscale
        }
    
    async def handle_upscale(self, args):
        """处理超分命令"""
        print(f"🔍 超分处理：{args.image}")
        print(f"   放大倍数：{getattr(args, 'scale', 2)}x")
        # 实际实现应调用超分模型（如 ESRGAN）
        print("✓ 超分完成（模拟）")


class WatermarkPlugin(VisionCraftPlugin):
    """水印插件示例"""
    
    @property
    def name(self) -> str:
        return "watermark"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "添加水印到图片"
    
    def register_commands(self) -> Dict[str, Callable]:
        return {
            "watermark": self.handle_watermark
        }
    
    async def handle_watermark(self, args):
        """处理水印命令"""
        print(f"💧 添加水印：{args.image}")
        print(f"   水印文本：{getattr(args, 'text', 'VisionCraft')}")
        # 实际实现应使用 PIL/Pillow 添加水印
        print("✓ 水印添加完成（模拟）")


def main():
    """测试插件系统"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionCraft 插件系统测试")
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # plugins 命令
    subparsers.add_parser('list', help='列出已加载的插件')
    
    args = parser.parse_args()
    
    manager = PluginManager()
    manager.discover_plugins()
    
    if args.command == 'list':
        plugins = manager.list_plugins()
        if plugins:
            print("\n已加载的插件：")
            for p in plugins:
                print(f"\n  📦 {p['name']} v{p['version']}")
                print(f"     {p['description']}")
        else:
            print("未加载任何插件")
    
    # 获取所有命令
    commands = manager.get_all_commands()
    if commands:
        print(f"\n可用的插件命令：{list(commands.keys())}")


if __name__ == "__main__":
    main()
