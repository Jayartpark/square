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


class ImageGeneratorService:
    """图片生成服务类"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
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
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
    
    def load_model(self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"):
        """加载 Stable Diffusion 模型"""
        print(f"Loading model: {model_id} on {self.device}")
        
        # 使用 DPM Solver 加速推理
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
            # 启用 xformers 优化内存 (如果可用)
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
            except:
                pass
            # 启用 VAE 切片以减少显存
            self.pipe.enable_vae_slicing()
        
        print("Model loaded successfully")
    
    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        style: str = "photorealistic",
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        num_images: int = 1
    ) -> List[str]:
        """
        生成图片
        
        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            style: 风格类型
            width: 图片宽度
            height: 图片高度
            num_inference_steps: 推理步数
            guidance_scale: 引导系数
            seed: 随机种子
            num_images: 生成数量
            
        Returns:
            生成的图片ID列表
        """
        # 懒加载模型
        if self.pipe is None:
            self.load_model()
        
        # 构建完整提示词
        style_prompt = self.style_prompts.get(style, "")
        full_prompt = f"{prompt}, {style_prompt}" if style_prompt else prompt
        
        # 设置随机种子
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # 异步执行生成任务
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
        
        # 保存图片并返回ID
        image_ids = []
        for img in images:
            image_id = str(uuid.uuid4())
            output_path = self.output_dir / f"{image_id}.png"
            img.save(output_path, format="PNG")
            image_ids.append(image_id)
        
        return image_ids
    
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
            每个变体的图片ID列表
        """
        all_results = []
        
        for i in range(num_variants):
            # 为每个变体使用不同的种子
            variant_kwargs = kwargs.copy()
            variant_kwargs['seed'] = i + 1
            variant_kwargs['num_images'] = variant_kwargs.get('num_images', 1)
            
            result = await self.generate(base_prompt, **variant_kwargs)
            all_results.append(result)
        
        return all_results
