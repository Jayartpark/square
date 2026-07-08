"""
VisionCraft - AI驱动的智能设计软件后端服务
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import os
from pathlib import Path

from backend.services.image_generator import ImageGeneratorService
from backend.services.image_editor import ImageEditorService
from backend.services.aesthetic_evaluator import AestheticEvaluatorService
from backend.utils.file_handler import save_uploaded_file, get_image_path

app = FastAPI(
    title="VisionCraft API",
    description="AI驱动的智能设计软件API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
image_generator = ImageGeneratorService()
image_editor = ImageEditorService()
aesthetic_evaluator = AestheticEvaluatorService()

# 存储目录
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ==================== 数据模型 ====================

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="生成图片的描述文本")
    negative_prompt: Optional[str] = Field("", description="负面提示词")
    style: Optional[str] = Field("photorealistic", description="风格类型")
    aspect_ratio: Optional[str] = Field("1:1", description="宽高比")
    width: Optional[int] = Field(1024, description="图片宽度")
    height: Optional[int] = Field(1024, description="图片高度")
    num_inference_steps: Optional[int] = Field(30, description="推理步数")
    guidance_scale: Optional[float] = Field(7.5, description="引导系数")
    seed: Optional[int] = Field(None, description="随机种子")
    num_images: Optional[int] = Field(1, description="生成数量", ge=1, le=4)


class EditRequest(BaseModel):
    image_id: str = Field(..., description="原图ID")
    instruction: str = Field(..., description="编辑指令")
    mask: Optional[str] = Field(None, description="编辑区域的mask (base64)")
    strength: Optional[float] = Field(0.75, description="编辑强度", ge=0.1, le=1.0)
    num_inference_steps: Optional[int] = Field(30, description="推理步数")


class RedesignRequest(BaseModel):
    image_id: str = Field(..., description="原图ID")
    style_description: str = Field(..., description="目标风格描述")
    preserve_elements: Optional[List[str]] = Field([], description="需要保留的元素")
    num_variants: Optional[int] = Field(3, description="生成变体数量", ge=1, le=5)


class AestheticEvaluateRequest(BaseModel):
    image_id: str = Field(..., description="图片ID")


# ==================== API端点 ====================

@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "VisionCraft API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/v1/generate")
async def generate_image(request: GenerateRequest):
    """
    根据文本描述生成图片
    
    Args:
        request: 生成请求，包含prompt、风格等参数
        
    Returns:
        生成的图片ID和URL列表
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
        
        return {
            "success": True,
            "image_ids": image_ids,
            "image_urls": [f"/api/v1/images/{img_id}" for img_id in image_ids],
            "message": f"成功生成 {len(image_ids)} 张图片"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败：{str(e)}")


@app.post("/api/v1/edit")
async def edit_image(request: EditRequest):
    """
    智能编辑图片
    
    Args:
        request: 编辑请求，包含原图ID、编辑指令、可选mask
        
    Returns:
        编辑后的图片ID和URL
    """
    try:
        # 验证原图存在
        original_path = get_image_path(request.image_id, OUTPUT_DIR)
        if not original_path.exists():
            raise HTTPException(status_code=404, detail="原图不存在")
        
        edited_id = await image_editor.edit(
            image_path=original_path,
            instruction=request.instruction,
            mask=request.mask,
            strength=request.strength,
            num_inference_steps=request.num_inference_steps
        )
        
        return {
            "success": True,
            "image_id": edited_id,
            "image_url": f"/api/v1/images/{edited_id}",
            "message": "编辑成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编辑失败：{str(e)}")


@app.post("/api/v1/redesign")
async def redesign_image(request: RedesignRequest):
    """
    对图片进行视觉重设计
    
    Args:
        request: 重设计请求，包含原图ID、目标风格等
        
    Returns:
        重设计后的图片ID列表和URL列表
    """
    try:
        original_path = get_image_path(request.image_id, OUTPUT_DIR)
        if not original_path.exists():
            raise HTTPException(status_code=404, detail="原图不存在")
        
        image_ids = await image_editor.redesign(
            image_path=original_path,
            style_description=request.style_description,
            preserve_elements=request.preserve_elements,
            num_variants=request.num_variants
        )
        
        return {
            "success": True,
            "image_ids": image_ids,
            "image_urls": [f"/api/v1/images/{img_id}" for img_id in image_ids],
            "message": f"成功生成 {len(image_ids)} 个设计方案"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重设计失败：{str(e)}")


@app.post("/api/v1/aesthetic/evaluate")
async def evaluate_aesthetic(request: AestheticEvaluateRequest):
    """
    评估图片的审美质量
    
    Args:
        request: 评估请求，包含图片ID
        
    Returns:
        审美评分和详细分析
    """
    try:
        image_path = get_image_path(request.image_id, OUTPUT_DIR)
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="图片不存在")
        
        evaluation = await aesthetic_evaluator.evaluate(image_path)
        
        return {
            "success": True,
            "image_id": request.image_id,
            "evaluation": evaluation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败：{str(e)}")


@app.post("/api/v1/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片
    
    Args:
        file: 图片文件
        
    Returns:
        上传后的图片ID和URL
    """
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只支持图片文件")
        
        image_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{image_id}.png"
        
        await save_uploaded_file(file, file_path)
        
        return {
            "success": True,
            "image_id": image_id,
            "image_url": f"/api/v1/images/{image_id}",
            "message": "上传成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败：{str(e)}")


@app.get("/api/v1/images/{image_id}")
async def get_image(image_id: str):
    """
    获取图片文件
    
    Args:
        image_id: 图片ID
        
    Returns:
        图片文件
    """
    # 优先在outputs中查找，然后在uploads中查找
    image_path = get_image_path(image_id, OUTPUT_DIR)
    if not image_path.exists():
        image_path = get_image_path(image_id, UPLOAD_DIR)
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    
    return FileResponse(image_path, media_type="image/png")


@app.delete("/api/v1/images/{image_id}")
async def delete_image(image_id: str):
    """
    删除图片
    
    Args:
        image_id: 图片ID
        
    Returns:
        删除结果
    """
    # 尝试从两个目录删除
    for dir_path in [OUTPUT_DIR, UPLOAD_DIR]:
        image_path = get_image_path(image_id, dir_path)
        if image_path.exists():
            image_path.unlink()
            return {
                "success": True,
                "message": "删除成功"
            }
    
    raise HTTPException(status_code=404, detail="图片不存在")


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
    uvicorn.run(app, host="0.0.0.0", port=8000)
