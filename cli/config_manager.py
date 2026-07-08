#!/usr/bin/env python3
"""
VisionCraft Config Manager - CLI 配置管理工具

管理 VisionCraft CLI 的用户配置、API 设置和默认参数
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "api": {
            "base_url": "http://localhost:8000",
            "timeout": 120,
            "max_retries": 3
        },
        "generation": {
            "default_style": "realistic",
            "default_width": 1024,
            "default_height": 1024,
            "default_steps": 30,
            "default_guidance": 7.5
        },
        "editing": {
            "default_strength": 0.75,
            "auto_save": True
        },
        "output": {
            "directory": "./output",
            "format": "png",
            "quality": 95,
            "save_metadata": True
        },
        "display": {
            "use_colors": True,
            "show_progress": True,
            "verbose": False
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 默认配置文件路径
            home_dir = Path.home()
            visioncraft_dir = home_dir / ".visioncraft"
            visioncraft_dir.mkdir(exist_ok=True)
            self.config_path = visioncraft_dir / "config.json"
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并默认配置和用户配置
                    return self._merge_configs(self.DEFAULT_CONFIG, user_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  配置文件读取失败，使用默认配置：{e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # 创建默认配置文件
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """递归合并配置字典"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✓ 配置已保存到：{self.config_path}")
        except IOError as e:
            print(f"✗ 保存配置失败：{e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的路径
        
        示例：
            config.get("api.base_url")
            config.get("generation.default_style")
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        设置配置值，支持点号分隔的路径
        
        示例：
            config.set("api.base_url", "http://api.example.com")
            config.set("generation.default_steps", 50)
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def list_all(self) -> Dict[str, Any]:
        """返回所有配置"""
        return self.config.copy()
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
        print("✓ 配置已重置为默认值")


def main():
    """配置管理 CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionCraft 配置管理工具")
    subparsers = parser.add_subparsers(dest='action', help='操作类型')
    
    # show 命令
    subparsers.add_parser('show', help='显示当前配置')
    
    # get 命令
    get_parser = subparsers.add_parser('get', help='获取配置值')
    get_parser.add_argument('key', help='配置键（点号分隔）')
    
    # set 命令
    set_parser = subparsers.add_parser('set', help='设置配置值')
    set_parser.add_argument('key', help='配置键（点号分隔）')
    set_parser.add_argument('value', help='配置值')
    
    # reset 命令
    subparsers.add_parser('reset', help='重置为默认配置')
    
    # edit 命令
    subparsers.add_parser('edit', help='编辑配置文件（打开编辑器）')
    
    args = parser.parse_args()
    config = ConfigManager()
    
    if args.action == 'show':
        print("当前配置：\n")
        print(json.dumps(config.list_all(), indent=2, ensure_ascii=False))
    
    elif args.action == 'get':
        value = config.get(args.key)
        if value is not None:
            print(f"{args.key} = {json.dumps(value, ensure_ascii=False)}")
        else:
            print(f"✗ 配置项不存在：{args.key}")
    
    elif args.action == 'set':
        # 尝试转换类型
        value = args.value
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)
        else:
            try:
                value = float(value)
            except ValueError:
                pass
        
        config.set(args.key, value)
        config.save_config()
        print(f"✓ 已设置 {args.key} = {json.dumps(value, ensure_ascii=False)}")
    
    elif args.action == 'reset':
        config.reset_to_default()
    
    elif args.action == 'edit':
        print(f"请使用文本编辑器打开：{config.config_path}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
