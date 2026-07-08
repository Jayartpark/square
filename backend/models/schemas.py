"""
Pydantic 数据模型定义模块

包含所有 API 请求和响应的数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 请求模型 ====================

class GenerateRequest(BaseModel):
    """图片生成请求模型"""
    prompt: str = Field(..., description="生成图片的描述文本", min_length=1, max_length=2000)
    negative_prompt: Optional[str] = Field("", description="负面提示词", max_length=2000)
    style: Optional[str] = Field("photorealistic", description="风格类型")
    aspect_ratio: Optional[str] = Field("1:1", description="宽高比")
    width: Optional[int] = Field(None, description="图片宽度", ge=64, le=2048)
    height: Optional[int] = Field(None, description="图片高度", ge=64, le=2048)
    num_inference_steps: Optional[int] = Field(None, description="推理步数", ge=1, le=150)
    guidance_scale: Optional[float] = Field(None, description="引导系数", ge=0.1, le=30.0)
    seed: Optional[int] = Field(None, description="随机种子", ge=0)
    num_images: Optional[int] = Field(None, description="生成数量", ge=1, le=4)

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "一个现代简约风格的客厅设计，大面积落地窗，自然光线充足",
                "style": "photorealistic",
                "aspect_ratio": "16:9",
                "num_images": 2
            }
        }


class EditRequest(BaseModel):
    """图片编辑请求模型"""
    image_id: str = Field(..., description="原图 ID", min_length=1)
    instruction: str = Field(..., description="编辑指令", min_length=1, max_length=1000)
    mask: Optional[str] = Field(None, description="编辑区域的 mask (base64)")
    strength: Optional[float] = Field(None, description="编辑强度", ge=0.1, le=1.0)
    num_inference_steps: Optional[int] = Field(None, description="推理步数", ge=1, le=150)

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "img_123",
                "instruction": "将沙发换成深蓝色的皮质沙发",
                "strength": 0.75
            }
        }


class RedesignRequest(BaseModel):
    """图片重设计请求模型"""
    image_id: str = Field(..., description="原图 ID", min_length=1)
    style_description: str = Field(..., description="目标风格描述", min_length=1, max_length=1000)
    preserve_elements: Optional[List[str]] = Field([], description="需要保留的元素")
    num_variants: Optional[int] = Field(None, description="生成变体数量", ge=1, le=5)

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "img_123",
                "style_description": "赛博朋克风格，霓虹灯色彩",
                "preserve_elements": ["建筑轮廓", "窗户布局"],
                "num_variants": 3
            }
        }


class AestheticEvaluateRequest(BaseModel):
    """审美评估请求模型"""
    image_id: str = Field(..., description="图片 ID", min_length=1)


class BatchGenerateRequest(BaseModel):
    """批量生成请求模型"""
    prompts: List[str] = Field(..., description="提示词列表", min_length=1, max_length=10)
    style: Optional[str] = Field("photorealistic", description="风格类型")
    width: Optional[int] = Field(None, description="图片宽度", ge=64, le=2048)
    height: Optional[int] = Field(None, description="图片高度", ge=64, le=2048)
    num_inference_steps: Optional[int] = Field(None, description="推理步数", ge=1, le=150)


# ==================== 响应模型 ====================

class ImageResponse(BaseModel):
    """图片响应模型"""
    success: bool = True
    image_id: Optional[str] = None
    image_ids: Optional[List[str]] = None
    image_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    message: str = "操作成功"
    metadata: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: str
    detail: str
    error_code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StyleListResponse(BaseModel):
    """样式列表响应模型"""
    success: bool = True
    styles: Dict[str, str]
    count: int


class AestheticEvaluationResponse(BaseModel):
    """审美评估响应模型"""
    success: bool = True
    image_id: str
    evaluation: Dict[str, Any]
    overall_score: float
    suggestions: List[str]


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    service: str
    version: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_loaded: bool = False
    device: str = "unknown"
    gpu_available: bool = False


class UploadResponse(BaseModel):
    """上传响应模型"""
    success: bool = True
    image_id: str
    image_url: str
    message: str = "上传成功"
    file_info: Optional[Dict[str, Any]] = None


class DeleteResponse(BaseModel):
    """删除响应模型"""
    success: bool = True
    message: str = "删除成功"
    image_id: str


# ==================== 任务状态模型 ====================

class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== 元数据模型 ====================

class ImageMetadata(BaseModel):
    """图片元数据模型"""
    image_id: str
    width: int
    height: int
    format: str
    size_bytes: int
    created_at: datetime
    prompt: Optional[str] = None
    style: Optional[str] = None
    seed: Optional[int] = None
    model_id: Optional[str] = None
