"""
文件处理工具函数
"""
from fastapi import UploadFile
from pathlib import Path
import aiofiles


async def save_uploaded_file(file: UploadFile, destination: Path):
    """
    保存上传的文件
    
    Args:
        file: FastAPI UploadFile 对象
        destination: 目标路径
    """
    # 确保目录存在
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    # 异步写入文件
    async with aiofiles.open(destination, 'wb') as out_file:
        while content := await file.read(1024 * 1024):  # 每次读取 1MB
            await out_file.write(content)


def get_image_path(image_id: str, directory: Path) -> Path:
    """
    获取图片路径
    
    Args:
        image_id: 图片 ID
        directory: 搜索目录
        
    Returns:
        图片路径 (可能不存在)
    """
    # 尝试不同的扩展名
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        path = directory / f"{image_id}{ext}"
        if path.exists():
            return path
    
    # 默认返回 png 路径
    return directory / f"{image_id}.png"


def validate_image_file(file_path: Path) -> bool:
    """
    验证文件是否为有效的图片
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为有效图片
    """
    from PIL import Image
    
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def get_image_info(file_path: Path) -> dict:
    """
    获取图片信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        包含图片信息的字典
    """
    from PIL import Image
    
    with Image.open(file_path) as img:
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "size_bytes": file_path.stat().st_size
        }
