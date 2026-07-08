"""
VisionCraft - AI 驱动的智能设计软件后端服务
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import logging

from backend.config.settings import settings
from backend.services.image_generator import ImageGeneratorService
from backend.services.image_editor import ImageEditorService
from backend.services.aesthetic_evaluator import AestheticEvaluatorService
from backend.utils.file_handler import save_uploaded_file, get_image_path
from backend.exceptions import (
    VisionCraftException,
    ImageNotFoundException,
    InvalidImageFormatException,
    GenerationFailedException,
    EditFailedException,
    EvaluationFailedException
)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 初始化 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 初始化服务
image_generator = ImageGeneratorService()
image_editor = ImageEditorService()
aesthetic_evaluator = AestheticEvaluatorService()

# 确保存储目录存在
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.OUTPUT_DIR.mkdir(exist_ok=True)


# ==================== 数据模型 ====================

class GenerateRequest(BaseModel):
    """图片生成请求模型"""
    prompt: str = Field(..., description="生成图片的描述文本")
    negative_prompt: Optional[str] = Field("", description="负面提示词")
    style: Optional[str] = Field("photorealistic", description="风格类型")
    aspect_ratio: Optional[str] = Field("1:1", description="宽高比")
    width: Optional[int] = Field(None, description="图片宽度")
    height: Optional[int] = Field(None, description="图片高度")
    num_inference_steps: Optional[int] = Field(None, description="推理步数")
    guidance_scale: Optional[float] = Field(None, description="引导系数")
    seed: Optional[int] = Field(None, description="随机种子")
    num_images: Optional[int] = Field(None, description="生成数量", ge=1, le=4)


class EditRequest(BaseModel):
    """图片编辑请求模型"""
    image_id: str = Field(..., description="原图 ID")
    instruction: str = Field(..., description="编辑指令")
    mask: Optional[str] = Field(None, description="编辑区域的 mask (base64)")
    strength: Optional[float] = Field(None, description="编辑强度", ge=0.1, le=1.0)
    num_inference_steps: Optional[int] = Field(None, description="推理步数")


class RedesignRequest(BaseModel):
    """图片重设计请求模型"""
    image_id: str = Field(..., description="原图 ID")
    style_description: str = Field(..., description="目标风格描述")
    preserve_elements: Optional[List[str]] = Field([], description="需要保留的元素")
    num_variants: Optional[int] = Field(None, description="生成变体数量", ge=1, le=5)


class AestheticEvaluateRequest(BaseModel):
    """审美评估请求模型"""
    image_id: str = Field(..., description="图片 ID")


# ==================== 异常处理 ====================

@app.exception_handler(VisionCraftException)
async def visioncraft_exception_handler(request, exc: VisionCraftException):
    """自定义异常处理器"""
    logger.error(f"VisionCraft error: {exc.detail}, code: {exc.error_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.error_code,
            "detail": exc.detail
        }
    )


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.post("/api/v1/generate")
async def generate_image(request: GenerateRequest):
    """
    根据文本描述生成图片
    
    Args:
        request: 生成请求，包含 prompt、风格等参数
        
    Returns:
        生成的图片 ID 和 URL 列表
    """
    try:
        image_ids = await image_generator.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            style=request.style,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            num_images=request.num_images
        )
        
        logger.info(f"Generated {len(image_ids)} images for prompt: {request.prompt[:50]}...")
        
        return {
            "success": True,
            "image_ids": image_ids,
            "image_urls": [f"/api/v1/images/{img_id}" for img_id in image_ids],
            "message": f"成功生成 {len(image_ids)} 张图片"
        }
    except ValueError as e:
        logger.warning(f"Invalid generation parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except GenerationFailedException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in generate_image: {e}")
        raise GenerationFailedException(f"生成失败：{str(e)}")


@app.post("/api/v1/edit")
async def edit_image(request: EditRequest):
    """
    智能编辑图片
    
    Args:
        request: 编辑请求，包含原图 ID、编辑指令、可选 mask
        
    Returns:
        编辑后的图片 ID 和 URL
    """
    try:
        original_path = get_image_path(request.image_id, settings.OUTPUT_DIR)
        if not original_path.exists():
            raise ImageNotFoundException(request.image_id)
        
        edited_id = await image_editor.edit(
            image_path=original_path,
            instruction=request.instruction,
            mask=request.mask,
            strength=request.strength,
            num_inference_steps=request.num_inference_steps
        )
        
        logger.info(f"Edited image {request.image_id} -> {edited_id}")
        
        return {
            "success": True,
            "image_id": edited_id,
            "image_url": f"/api/v1/images/{edited_id}",
            "message": "编辑成功"
        }
    except ImageNotFoundException:
        raise
    except EditFailedException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in edit_image: {e}")
        raise EditFailedException(f"编辑失败：{str(e)}")


@app.post("/api/v1/redesign")
async def redesign_image(request: RedesignRequest):
    """
    对图片进行视觉重设计
    
    Args:
        request: 重设计请求，包含原图 ID、目标风格等
        
    Returns:
        重设计后的图片 ID 列表和 URL 列表
    """
    try:
        original_path = get_image_path(request.image_id, settings.OUTPUT_DIR)
        if not original_path.exists():
            raise ImageNotFoundException(request.image_id)
        
        image_ids = await image_editor.redesign(
            image_path=original_path,
            style_description=request.style_description,
            preserve_elements=request.preserve_elements,
            num_variants=request.num_variants
        )
        
        logger.info(f"Redesigned image {request.image_id} into {len(image_ids)} variants")
        
        return {
            "success": True,
            "image_ids": image_ids,
            "image_urls": [f"/api/v1/images/{img_id}" for img_id in image_ids],
            "message": f"成功生成 {len(image_ids)} 个设计方案"
        }
    except ImageNotFoundException:
        raise
    except EditFailedException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in redesign_image: {e}")
        raise EditFailedException(f"重设计失败：{str(e)}")


@app.post("/api/v1/aesthetic/evaluate")
async def evaluate_aesthetic(request: AestheticEvaluateRequest):
    """
    评估图片的审美质量
    
    Args:
        request: 评估请求，包含图片 ID
        
    Returns:
        审美评分和详细分析
    """
    try:
        image_path = get_image_path(request.image_id, settings.OUTPUT_DIR)
        if not image_path.exists():
            raise ImageNotFoundException(request.image_id)
        
        evaluation = await aesthetic_evaluator.evaluate(image_path)
        
        return {
            "success": True,
            "image_id": request.image_id,
            "evaluation": evaluation
        }
    except ImageNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error in aesthetic evaluation: {e}")
        raise EvaluationFailedException(f"评估失败：{str(e)}")


@app.post("/api/v1/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片
    
    Args:
        file: 图片文件
        
    Returns:
        上传后的图片 ID 和 URL
    """
    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise InvalidImageFormatException("只支持图片文件")
        
        image_id = str(uuid.uuid4())
        file_path = settings.UPLOAD_DIR / f"{image_id}.png"
        
        await save_uploaded_file(file, file_path)
        
        logger.info(f"Uploaded image: {image_id}")
        
        return {
            "success": True,
            "image_id": image_id,
            "image_url": f"/api/v1/images/{image_id}",
            "message": "上传成功"
        }
    except InvalidImageFormatException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败：{str(e)}")


@app.get("/api/v1/images/{image_id}")
async def get_image(image_id: str):
    """
    获取图片文件
    
    Args:
        image_id: 图片 ID
        
    Returns:
        图片文件
    """
    image_path = get_image_path(image_id, settings.OUTPUT_DIR)
    if not image_path.exists():
        image_path = get_image_path(image_id, settings.UPLOAD_DIR)
    
    if not image_path.exists():
        raise ImageNotFoundException(image_id)
    
    return FileResponse(image_path, media_type="image/png")


@app.delete("/api/v1/images/{image_id}")
async def delete_image(image_id: str):
    """
    删除图片
    
    Args:
        image_id: 图片 ID
        
    Returns:
        删除结果
    """
    for dir_path in [settings.OUTPUT_DIR, settings.UPLOAD_DIR]:
        image_path = get_image_path(image_id, dir_path)
        if image_path.exists():
            image_path.unlink()
            logger.info(f"Deleted image: {image_id}")
            return {
                "success": True,
                "message": "删除成功"
            }
    
    raise ImageNotFoundException(image_id)


@app.get("/api/v1/styles")
async def list_styles():
    """
    获取支持的样式列表
    
    Returns:
        样式列表
    """
    styles = {
        "photorealistic": "写实风格",
        "illustration": "插画风格",
        "minimalist": "极简主义",
        "abstract": "抽象艺术",
        "watercolor": "水彩画",
        "oil_painting": "油画",
        "digital_art": "数字艺术",
        "anime": "动漫风格",
        "concept_art": "概念艺术",
        "architectural": "建筑设计"
    }
    
    return {
        "success": True,
        "styles": styles
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT
    )
