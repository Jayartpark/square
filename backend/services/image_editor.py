"""
图片编辑服务
实现智能编辑、局部修改和视觉重设计功能
"""
import torch
from PIL import Image
from pathlib import Path
import uuid
import base64
import io
from typing import Optional, List
import asyncio
import logging

from backend.config.settings import settings
from backend.exceptions import EditFailedException, ImageNotFoundException, ModelLoadException


logger = logging.getLogger(__name__)


class ImageEditorService:
    """图片编辑服务类"""
    
    def __init__(self):
        self.device = self._get_device()
        self.inpaint_pipe = None
        self.img2img_pipe = None
        self.output_dir = settings.OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)
    
    def _get_device(self) -> str:
        """获取运行设备"""
        if settings.DEVICE == "cuda":
            return "cuda"
        elif settings.DEVICE == "cpu":
            return "cpu"
        else:
            return "cuda" if torch.cuda.is_available() else "cpu"
    
    def load_inpaint_model(self, model_id: Optional[str] = None):
        """加载用于 inpainting 的模型"""
        from diffusers import StableDiffusionInpaintPipeline
        
        model_id = model_id or settings.DEFAULT_MODEL_ID
        logger.info(f"Loading inpainting model: {model_id}")
        
        try:
            self.inpaint_pipe = StableDiffusionInpaintPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16" if self.device == "cuda" else None
            )
            
            if self.device == "cuda":
                self.inpaint_pipe = self.inpaint_pipe.to("cuda")
                try:
                    self.inpaint_pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    pass
            
            logger.info("Inpainting model loaded")
        except Exception as e:
            logger.error(f"Failed to load inpainting model: {e}")
            raise ModelLoadException(f"模型加载失败：{str(e)}")
    
    def load_img2img_model(self, model_id: Optional[str] = None):
        """加载用于 img2img 的模型"""
        from diffusers import StableDiffusionImg2ImgPipeline
        
        model_id = model_id or settings.DEFAULT_MODEL_ID
        logger.info(f"Loading img2img model: {model_id}")
        
        try:
            self.img2img_pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16" if self.device == "cuda" else None
            )
            
            if self.device == "cuda":
                self.img2img_pipe = self.img2img_pipe.to("cuda")
                try:
                    self.img2img_pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    pass
            
            logger.info("Img2Img model loaded")
        except Exception as e:
            logger.error(f"Failed to load img2img model: {e}")
            raise ModelLoadException(f"模型加载失败：{str(e)}")
    
    async def edit(
        self,
        image_path: Path,
        instruction: str,
        mask: Optional[str] = None,
        strength: Optional[float] = None,
        num_inference_steps: Optional[int] = None
    ) -> str:
        """
        智能编辑图片
        
        Args:
            image_path: 原图路径
            instruction: 编辑指令 (自然语言描述)
            mask: 可选的 mask (base64 编码的 PNG)
            strength: 编辑强度 (0.1-1.0)
            num_inference_steps: 推理步数
            
        Returns:
            编辑后的图片 ID
            
        Raises:
            EditFailedException: 编辑失败时抛出
        """
        strength = strength if strength is not None else settings.DEFAULT_EDIT_STRENGTH
        num_inference_steps = num_inference_steps or settings.DEFAULT_INFERENCE_STEPS
        
        try:
            if mask and self.inpaint_pipe is None:
                self.load_inpaint_model()
            elif self.img2img_pipe is None:
                self.load_img2img_model()
            
            original_image = Image.open(image_path).convert("RGB")
            
            mask_image = None
            if mask:
                mask_bytes = base64.b64decode(mask)
                mask_image = Image.open(io.BytesIO(mask_bytes)).convert("L")
                mask_image = mask_image.resize(original_image.size)
            
            loop = asyncio.get_event_loop()
            
            if mask_image:
                def _inpaint():
                    return self.inpaint_pipe(
                        prompt=instruction,
                        image=original_image,
                        mask_image=mask_image,
                        strength=strength,
                        num_inference_steps=num_inference_steps
                    ).images[0]
                
                edited_image = await loop.run_in_executor(None, _inpaint)
            else:
                def _img2img():
                    return self.img2img_pipe(
                        prompt=instruction,
                        image=original_image,
                        strength=strength,
                        num_inference_steps=num_inference_steps
                    ).images[0]
                
                edited_image = await loop.run_in_executor(None, _img2img)
            
            image_id = str(uuid.uuid4())
            output_path = self.output_dir / f"{image_id}.png"
            edited_image.save(output_path, format="PNG")
            
            logger.info(f"Successfully edited image: {image_id}")
            return image_id
            
        except Exception as e:
            logger.error(f"Image editing failed: {e}")
            raise EditFailedException(f"图片编辑失败：{str(e)}")
    
    async def redesign(
        self,
        image_path: Path,
        style_description: str,
        preserve_elements: Optional[List[str]] = None,
        num_variants: Optional[int] = None
    ) -> List[str]:
        """
        视觉重设计
        
        Args:
            image_path: 原图路径
            style_description: 目标风格描述
            preserve_elements: 需要保留的元素列表
            num_variants: 生成变体数量
            
        Returns:
            重设计后的图片 ID 列表
            
        Raises:
            EditFailedException: 重设计失败时抛出
        """
        num_variants = num_variants or settings.DEFAULT_NUM_VARIANTS
        if num_variants < 1 or num_variants > settings.MAX_NUM_VARIANTS:
            raise ValueError(f"变体数量必须在 1-{settings.MAX_NUM_VARIANTS}之间")
        
        try:
            if self.img2img_pipe is None:
                self.load_img2img_model()
            
            original_image = Image.open(image_path).convert("RGB")
            
            preserve_text = ""
            if preserve_elements:
                preserve_text = f", keep these elements: {', '.join(preserve_elements)}"
            
            prompt = f"redesign in this style: {style_description}{preserve_text}"
            
            image_ids = []
            loop = asyncio.get_event_loop()
            
            for i in range(num_variants):
                def _generate_variant(seed=i):
                    generator = torch.Generator(device=self.device).manual_seed(seed)
                    result = self.img2img_pipe(
                        prompt=prompt,
                        image=original_image,
                        strength=0.8,
                        num_inference_steps=30,
                        generator=generator
                    ).images[0]
                    return result
                
                redesigned_image = await loop.run_in_executor(None, _generate_variant, i)
                
                image_id = str(uuid.uuid4())
                output_path = self.output_dir / f"{image_id}.png"
                redesigned_image.save(output_path, format="PNG")
                image_ids.append(image_id)
            
            logger.info(f"Successfully redesigned {len(image_ids)} variants")
            return image_ids
            
        except Exception as e:
            logger.error(f"Image redesign failed: {e}")
            raise EditFailedException(f"图片重设计失败：{str(e)}")
    
    async def extend_canvas(
        self,
        image_path: Path,
        direction: str = "right",
        extension_pixels: int = 512
    ) -> str:
        """
        智能扩图 (Outpainting)
        
        Args:
            image_path: 原图路径
            direction: 扩展方向 (left/right/top/bottom)
            extension_pixels: 扩展像素数
            
        Returns:
            扩展后的图片 ID
        """
        raise NotImplementedError("Outpainting 功能开发中")
