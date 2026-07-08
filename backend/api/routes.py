"""
API 路由模块

将 API 端点按功能分离到不同的路由器中
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
import uuid
import logging
from pathlib import Path
from typing import List

from backend.config.settings import settings
from backend.services.image_generator import ImageGeneratorService
from backend.services.image_editor import ImageEditorService
from backend.services.aesthetic_evaluator import AestheticEvaluatorService
from backend.utils.file_handler import save_uploaded_file, get_image_path, validate_image_file, get_image_info
from backend.exceptions import (
    VisionCraftException,
    ImageNotFoundException,
    InvalidImageFormatException,
    GenerationFailedException,
    EditFailedException,
    EvaluationFailedException
)
from backend.models.schemas import (
    GenerateRequest,
    EditRequest,
    RedesignRequest,
    AestheticEvaluateRequest,
    BatchGenerateRequest,
    ImageResponse,
    StyleListResponse,
    HealthCheckResponse,
    UploadResponse,
    DeleteResponse,
    AestheticEvaluationResponse
)

logger = logging.getLogger(__name__)

# 创建路由器
generation_router = APIRouter(prefix="/api/v1", tags=["图片生成"])
edit_router = APIRouter(prefix="/api/v1", tags=["图片编辑"])
image_router = APIRouter(prefix="/api/v1", tags=["图片管理"])
aesthetic_router = APIRouter(prefix="/api/v1/aesthetic", tags=["审美评估"])


# ==================== 图片生成接口 ====================

@generation_router.post("/generate", response_model=ImageResponse)
async def generate_image(request: GenerateRequest, generator: ImageGeneratorService = Depends()):
    """
    根据文本描述生成图片
    
    - **prompt**: 生成图片的描述文本
    - **negative_prompt**: 负面提示词
    - **style**: 风格类型
    - **aspect_ratio**: 宽高比
    - **width/height**: 图片尺寸
    - **num_inference_steps**: 推理步数
    - **guidance_scale**: 引导系数
    - **seed**: 随机种子
    - **num_images**: 生成数量 (1-4)
    """
    try:
        image_ids = await generator.generate(
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

        return ImageResponse(
            success=True,
            image_ids=image_ids,
            image_urls=[f"/api/v1/images/{img_id}" for img_id in image_ids],
            message=f"成功生成 {len(image_ids)} 张图片",
            metadata={
                "prompt": request.prompt,
                "style": request.style,
                "num_images": len(image_ids)
            }
        )
    except ValueError as e:
        logger.warning(f"Invalid generation parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except GenerationFailedException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_image: {e}")
        raise GenerationFailedException(f"生成失败：{str(e)}")


@generation_router.post("/batch/generate", response_model=ImageResponse)
async def batch_generate(request: BatchGenerateRequest, generator: ImageGeneratorService = Depends()):
    """
    批量生成图片
    
    一次性提交多个提示词，批量生成图片
    """
    try:
        all_image_ids = []
        
        for prompt in request.prompts:
            image_ids = await generator.generate(
                prompt=prompt,
                style=request.style,
                width=request.width,
                height=request.height,
                num_inference_steps=request.num_inference_steps,
                num_images=1
            )
            all_image_ids.extend(image_ids)

        logger.info(f"Batch generated {len(all_image_ids)} images")

        return ImageResponse(
            success=True,
            image_ids=all_image_ids,
            image_urls=[f"/api/v1/images/{img_id}" for img_id in all_image_ids],
            message=f"批量生成 {len(all_image_ids)} 张图片成功",
            metadata={
                "total_prompts": len(request.prompts),
                "total_images": len(all_image_ids)
            }
        )
    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
        raise GenerationFailedException(f"批量生成失败：{str(e)}")


# ==================== 图片编辑接口 ====================

@edit_router.post("/edit", response_model=ImageResponse)
async def edit_image(request: EditRequest, editor: ImageEditorService = Depends()):
    """
    智能编辑图片
    
    - **image_id**: 原图 ID
    - **instruction**: 编辑指令（自然语言）
    - **mask**: 可选的编辑区域 mask (base64)
    - **strength**: 编辑强度 (0.1-1.0)
    """
    try:
        original_path = get_image_path(request.image_id, settings.OUTPUT_DIR)
        if not original_path.exists():
            raise ImageNotFoundException(request.image_id)

        edited_id = await editor.edit(
            image_path=original_path,
            instruction=request.instruction,
            mask=request.mask,
            strength=request.strength,
            num_inference_steps=request.num_inference_steps
        )

        logger.info(f"Edited image {request.image_id} -> {edited_id}")

        return ImageResponse(
            success=True,
            image_id=edited_id,
            image_url=f"/api/v1/images/{edited_id}",
            message="编辑成功",
            metadata={
                "original_image_id": request.image_id,
                "instruction": request.instruction
            }
        )
    except ImageNotFoundException:
        raise
    except EditFailedException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in edit_image: {e}")
        raise EditFailedException(f"编辑失败：{str(e)}")


@edit_router.post("/redesign", response_model=ImageResponse)
async def redesign_image(request: RedesignRequest, editor: ImageEditorService = Depends()):
    """
    对图片进行视觉重设计
    
    - **image_id**: 原图 ID
    - **style_description**: 目标风格描述
    - **preserve_elements**: 需要保留的元素列表
    - **num_variants**: 生成变体数量 (1-5)
    """
    try:
        original_path = get_image_path(request.image_id, settings.OUTPUT_DIR)
        if not original_path.exists():
            raise ImageNotFoundException(request.image_id)

        image_ids = await editor.redesign(
            image_path=original_path,
            style_description=request.style_description,
            preserve_elements=request.preserve_elements,
            num_variants=request.num_variants
        )

        logger.info(f"Redesigned image {request.image_id} into {len(image_ids)} variants")

        return ImageResponse(
            success=True,
            image_ids=image_ids,
            image_urls=[f"/api/v1/images/{img_id}" for img_id in image_ids],
            message=f"成功生成 {len(image_ids)} 个设计方案",
            metadata={
                "original_image_id": request.image_id,
                "style": request.style_description,
                "variants_count": len(image_ids)
            }
        )
    except ImageNotFoundException:
        raise
    except EditFailedException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in redesign_image: {e}")
        raise EditFailedException(f"重设计失败：{str(e)}")


# ==================== 图片管理接口 ====================

@image_router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片
    
    支持 PNG, JPG, JPEG, WEBP 格式
    """
    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise InvalidImageFormatException("只支持图片文件")

        # 检查文件大小
        file_content = await file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise InvalidImageFormatException(f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB)")

        image_id = str(uuid.uuid4())
        file_path = settings.UPLOAD_DIR / f"{image_id}.png"

        # 重新写入文件
        from io import BytesIO
        from PIL import Image
        
        img = Image.open(BytesIO(file_content))
        img.save(file_path, format="PNG")

        # 获取图片信息
        file_info = get_image_info(file_path)

        logger.info(f"Uploaded image: {image_id}, size: {file_info['width']}x{file_info['height']}")

        return UploadResponse(
            success=True,
            image_id=image_id,
            image_url=f"/api/v1/images/{image_id}",
            message="上传成功",
            file_info=file_info
        )
    except InvalidImageFormatException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败：{str(e)}")


@image_router.get("/images/{image_id}")
async def get_image(image_id: str):
    """
    获取图片文件
    
    自动在 output 和 upload 目录中查找
    """
    image_path = get_image_path(image_id, settings.OUTPUT_DIR)
    if not image_path.exists():
        image_path = get_image_path(image_id, settings.UPLOAD_DIR)

    if not image_path.exists():
        raise ImageNotFoundException(image_id)

    return FileResponse(image_path, media_type="image/png")


@image_router.delete("/images/{image_id}", response_model=DeleteResponse)
async def delete_image(image_id: str):
    """
    删除图片
    
    从 output 或 upload 目录中删除
    """
    for dir_path in [settings.OUTPUT_DIR, settings.UPLOAD_DIR]:
        image_path = get_image_path(image_id, dir_path)
        if image_path.exists():
            image_path.unlink()
            logger.info(f"Deleted image: {image_id}")
            return DeleteResponse(
                success=True,
                message="删除成功",
                image_id=image_id
            )

    raise ImageNotFoundException(image_id)


@image_router.get("/styles", response_model=StyleListResponse)
async def list_styles():
    """
    获取支持的样式列表
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

    return StyleListResponse(
        success=True,
        styles=styles,
        count=len(styles)
    )


# ==================== 审美评估接口 ====================

@aesthetic_router.post("/evaluate", response_model=AestheticEvaluationResponse)
async def evaluate_aesthetic(request: AestheticEvaluateRequest, evaluator: AestheticEvaluatorService = Depends()):
    """
    评估图片的审美质量
    
    返回综合评分、构图分析、色彩分析和改进建议
    """
    try:
        image_path = get_image_path(request.image_id, settings.OUTPUT_DIR)
        if not image_path.exists():
            raise ImageNotFoundException(request.image_id)

        evaluation = await evaluator.evaluate(image_path)

        return AestheticEvaluationResponse(
            success=True,
            image_id=request.image_id,
            evaluation=evaluation,
            overall_score=evaluation.get("overall_score", 0),
            suggestions=evaluation.get("suggestions", [])
        )
    except ImageNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error in aesthetic evaluation: {e}")
        raise EvaluationFailedException(f"评估失败：{str(e)}")


def get_generator_service() -> ImageGeneratorService:
    """依赖注入：图片生成服务"""
    return ImageGeneratorService()


def get_editor_service() -> ImageEditorService:
    """依赖注入：图片编辑服务"""
    return ImageEditorService()


def get_evaluator_service() -> AestheticEvaluatorService:
    """依赖注入：审美评估服务"""
    return AestheticEvaluatorService()
