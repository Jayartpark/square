"""
自定义异常模块
"""
from fastapi import HTTPException, status


class VisionCraftException(HTTPException):
    """VisionCraft 基础异常类"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "操作失败",
        error_code: str = "UNKNOWN_ERROR"
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class ImageNotFoundException(VisionCraftException):
    """图片未找到异常"""
    
    def __init__(self, image_id: str = ""):
        detail = f"图片不存在" + (f": {image_id}" if image_id else "")
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="IMAGE_NOT_FOUND"
        )


class InvalidImageFormatException(VisionCraftException):
    """无效图片格式异常"""
    
    def __init__(self, message: str = "不支持的图片格式"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="INVALID_IMAGE_FORMAT"
        )


class GenerationFailedException(VisionCraftException):
    """图片生成失败异常"""
    
    def __init__(self, message: str = "图片生成失败"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="GENERATION_FAILED"
        )


class EditFailedException(VisionCraftException):
    """图片编辑失败异常"""
    
    def __init__(self, message: str = "图片编辑失败"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="EDIT_FAILED"
        )


class ModelLoadException(VisionCraftException):
    """模型加载失败异常"""
    
    def __init__(self, message: str = "AI 模型加载失败"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
            error_code="MODEL_LOAD_FAILED"
        )


class FileUploadException(VisionCraftException):
    """文件上传失败异常"""
    
    def __init__(self, message: str = "文件上传失败"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="FILE_UPLOAD_FAILED"
        )


class EvaluationFailedException(VisionCraftException):
    """审美评估失败异常"""
    
    def __init__(self, message: str = "审美评估失败"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="EVALUATION_FAILED"
        )
