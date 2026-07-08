"""
图片生成服务
使用 Stable Diffusion 模型实现文生图功能
"""
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from pathlib import Path
import uuid
from typing import Optional, List
import asyncio
import logging

from backend.config.settings import settings
from backend.exceptions import GenerationFailedException, ModelLoadException


logger = logging.getLogger(__name__)


class ImageGeneratorService:
    """图片生成服务类"""
    
    def __init__(self):
        self.device = self._get_device()
        self.pipe = None
        self.style_prompts = {
            "photorealistic": "photorealistic, highly detailed, professional photography, 8k uhd",
            "illustration": "digital illustration, clean lines, vibrant colors",
            "minimalist": "minimalist, clean composition, simple shapes, limited color palette",
            "abstract": "abstract art, expressive, bold colors, artistic",
            "watercolor": "watercolor painting, soft edges, flowing colors, artistic",
            "oil_painting": "oil painting, textured brushstrokes, rich colors, classical art",
            "digital_art": "digital art, concept art, highly detailed, trending on artstation",
            "anime": "anime style, studio ghibli, vibrant, detailed",
            "concept_art": "concept art, matte painting, cinematic lighting, epic",
            "architectural": "architectural visualization, professional rendering, realistic lighting"
        }
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
    
    def load_model(self, model_id: Optional[str] = None):
        """加载 Stable Diffusion 模型"""
        model_id = model_id or settings.DEFAULT_MODEL_ID
        logger.info(f"Loading model: {model_id} on {self.device}")
        
        try:
            self.pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16" if self.device == "cuda" else None
            )
            
            self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipe.scheduler.config
            )
            
            if self.device == "cuda":
                self.pipe = self.pipe.to("cuda")
                try:
                    self.pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    pass
                self.pipe.enable_vae_slicing()
            
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise ModelLoadException(f"模型加载失败：{str(e)}")
    
    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "photorealistic",
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        num_images: Optional[int] = None
    ) -> List[str]:
        """
        生成图片
        
        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            style: 风格类型
            width: 图片宽度，默认使用配置值
            height: 图片高度，默认使用配置值
            num_inference_steps: 推理步数，默认使用配置值
            guidance_scale: 引导系数，默认使用配置值
            seed: 随机种子
            num_images: 生成数量，默认使用配置值
            
        Returns:
            生成的图片 ID 列表
            
        Raises:
            GenerationFailedException: 生成失败时抛出
        """
        width = width or settings.DEFAULT_WIDTH
        height = height or settings.DEFAULT_HEIGHT
        num_inference_steps = num_inference_steps or settings.DEFAULT_INFERENCE_STEPS
        guidance_scale = guidance_scale if guidance_scale is not None else settings.DEFAULT_GUIDANCE_SCALE
        num_images = num_images or settings.DEFAULT_NUM_IMAGES
        
        if num_images < 1 or num_images > settings.MAX_NUM_IMAGES:
            raise ValueError(f"图片数量必须在 1-{settings.MAX_NUM_IMAGES}之间")
        
        try:
            if self.pipe is None:
                self.load_model()
            
            style_prompt = self.style_prompts.get(style, "")
            full_prompt = f"{prompt}, {style_prompt}" if style_prompt else prompt
            
            generator = None
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
            
            loop = asyncio.get_event_loop()
            
            def _generate():
                return self.pipe(
                    prompt=full_prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                    num_images_per_prompt=num_images
                ).images
            
            images = await loop.run_in_executor(None, _generate)
            
            image_ids = []
            for img in images:
                image_id = str(uuid.uuid4())
                output_path = self.output_dir / f"{image_id}.png"
                img.save(output_path, format="PNG")
                image_ids.append(image_id)
            
            logger.info(f"Successfully generated {len(image_ids)} images")
            return image_ids
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise GenerationFailedException(f"图片生成失败：{str(e)}")
    
    async def generate_variants(
        self,
        base_prompt: str,
        num_variants: int = 3,
        **kwargs
    ) -> List[List[str]]:
        """
        生成多个变体方案
        
        Args:
            base_prompt: 基础提示词
            num_variants: 变体数量
            **kwargs: 其他参数传递给 generate
            
        Returns:
            每个变体的图片 ID 列表
        """
        all_results = []
        
        for i in range(num_variants):
            variant_kwargs = kwargs.copy()
            variant_kwargs['seed'] = i + 1
            variant_kwargs['num_images'] = variant_kwargs.get('num_images', 1)
            
            result = await self.generate(base_prompt, **variant_kwargs)
            all_results.append(result)
        
        return all_results
