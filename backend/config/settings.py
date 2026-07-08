"""
应用配置管理模块
"""
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "VisionCraft"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI 驱动的智能设计软件 API"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # 文件存储配置
    UPLOAD_DIR: Path = Field(default_factory=lambda: Path("uploads"))
    OUTPUT_DIR: Path = Field(default_factory=lambda: Path("outputs"))
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    
    # AI 模型配置
    DEFAULT_MODEL_ID: str = "stabilityai/stable-diffusion-xl-base-1.0"
    AESTHETIC_MODEL_ID: str = "christophschuhmann/improved-aesthetic-predictor"
    DEVICE: str = "auto"
    
    # 生成参数默认值
    DEFAULT_WIDTH: int = 1024
    DEFAULT_HEIGHT: int = 1024
    DEFAULT_INFERENCE_STEPS: int = 30
    DEFAULT_GUIDANCE_SCALE: float = 7.5
    DEFAULT_NUM_IMAGES: int = 1
    MAX_NUM_IMAGES: int = 4
    
    # 编辑参数默认值
    DEFAULT_EDIT_STRENGTH: float = 0.75
    DEFAULT_NUM_VARIANTS: int = 3
    MAX_NUM_VARIANTS: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
