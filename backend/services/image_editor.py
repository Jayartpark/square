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


class ImageEditorService:
    """图片编辑服务类"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.inpaint_pipe = None
        self.img2img_pipe = None
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
    
    def load_inpaint_model(self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"):
        """加载用于 inpainting 的模型"""
        from diffusers import StableDiffusionInpaintPipeline
        
        print(f"Loading inpainting model: {model_id}")
        
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
            except:
                pass
        
        print("Inpainting model loaded")
    
    def load_img2img_model(self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"):
        """加载用于 img2img 的模型"""
        from diffusers import StableDiffusionImg2ImgPipeline
        
        print(f"Loading img2img model: {model_id}")
        
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
            except:
                pass
        
        print("Img2Img model loaded")
    
    async def edit(
        self,
        image_path: Path,
        instruction: str,
        mask: Optional[str] = None,
        strength: float = 0.75,
        num_inference_steps: int = 30
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
        """
        # 懒加载模型
        if mask and self.inpaint_pipe is None:
            self.load_inpaint_model()
        elif self.img2img_pipe is None:
            self.load_img2img_model()
        
        # 加载原图
        original_image = Image.open(image_path).convert("RGB")
        
        # 处理 mask
        mask_image = None
        if mask:
            # 解码 base64 mask
            mask_bytes = base64.b64decode(mask)
            mask_image = Image.open(io.BytesIO(mask_bytes)).convert("L")
            # 调整大小以匹配原图
            mask_image = mask_image.resize(original_image.size)
        
        # 异步执行编辑
        loop = asyncio.get_event_loop()
        
        if mask_image:
            # 使用 inpainting
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
            # 使用 img2img (全局编辑)
            def _img2img():
                return self.img2img_pipe(
                    prompt=instruction,
                    image=original_image,
                    strength=strength,
                    num_inference_steps=num_inference_steps
                ).images[0]
            
            edited_image = await loop.run_in_executor(None, _img2img)
        
        # 保存编辑后的图片
        image_id = str(uuid.uuid4())
        output_path = self.output_dir / f"{image_id}.png"
        edited_image.save(output_path, format="PNG")
        
        return image_id
    
    async def redesign(
        self,
        image_path: Path,
        style_description: str,
        preserve_elements: Optional[List[str]] = None,
        num_variants: int = 3
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
        """
        if self.img2img_pipe is None:
            self.load_img2img_model()
        
        # 加载原图
        original_image = Image.open(image_path).convert("RGB")
        
        # 构建重设计提示词
        preserve_text = ""
        if preserve_elements:
            preserve_text = f", keep these elements: {', '.join(preserve_elements)}"
        
        prompt = f"redesign in this style: {style_description}{preserve_text}"
        
        # 生成多个变体
        image_ids = []
        loop = asyncio.get_event_loop()
        
        for i in range(num_variants):
            def _generate_variant(seed=i):
                generator = torch.Generator(device=self.device).manual_seed(seed)
                result = self.img2img_pipe(
                    prompt=prompt,
                    image=original_image,
                    strength=0.8,  # 较强的重设计力度
                    num_inference_steps=30,
                    generator=generator
                ).images[0]
                return result
            
            redesigned_image = await loop.run_in_executor(None, _generate_variant, i)
            
            # 保存图片
            image_id = str(uuid.uuid4())
            output_path = self.output_dir / f"{image_id}.png"
            redesigned_image.save(output_path, format="PNG")
            image_ids.append(image_id)
        
        return image_ids
    
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
        # TODO: 实现 outpainting 功能
        # 这需要使用专门的 outpainting 模型或技术
        raise NotImplementedError("Outpainting 功能开发中")
