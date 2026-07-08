"""
审美评估服务
使用 AI 模型评估图片的审美质量并提供分析建议
"""
import torch
from PIL import Image
from pathlib import Path
from typing import Dict, Any
import asyncio


class AestheticEvaluatorService:
    """审美评估服务类"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
    
    def load_model(self, model_id: str = "christophschuhmann/improved-aesthetic-predictor"):
        """加载审美评估模型"""
        try:
            from transformers import AutoProcessor, AutoModelForImageClassification
            
            print(f"Loading aesthetic model: {model_id}")
            
            self.processor = AutoProcessor.from_pretrained(model_id)
            self.model = AutoModelForImageClassification.from_pretrained(model_id)
            
            if self.device == "cuda":
                self.model = self.model.to("cuda")
            
            print("Aesthetic model loaded")
        except Exception as e:
            print(f"Failed to load aesthetic model: {e}")
            print("Using fallback evaluation method")
            self.model = None
    
    async def evaluate(self, image_path: Path) -> Dict[str, Any]:
        """
        评估图片的审美质量
        
        Args:
            image_path: 图片路径
            
        Returns:
            包含评分和详细分析的字典
        """
        # 懒加载模型
        if self.model is None:
            self.load_model()
        
        # 加载图片
        image = Image.open(image_path).convert("RGB")
        
        if self.model is not None:
            # 使用 AI 模型评估
            loop = asyncio.get_event_loop()
            
            def _predict():
                inputs = self.processor(images=image, return_tensors="pt")
                if self.device == "cuda":
                    inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    scores = outputs.logits.softmax(dim=1)[0]
                
                # 假设分数范围是 1-10
                aesthetic_score = (scores[1].item() * 9 + 1)  # 映射到 1-10
                
                return {
                    "overall_score": round(aesthetic_score, 2),
                    "ai_confidence": round(scores.max().item(), 3)
                }
            
            result = await loop.run_in_executor(None, _predict)
        else:
            # 回退到基于规则的评估
            result = await self._rule_based_evaluation(image)
        
        # 添加详细分析
        detailed_analysis = await self._analyze_image(image)
        result.update(detailed_analysis)
        
        # 生成改进建议
        result["suggestions"] = self._generate_suggestions(result)
        
        return result
    
    async def _rule_based_evaluation(self, image: Image.Image) -> Dict[str, Any]:
        """基于规则的审美评估 (回退方案)"""
        import numpy as np
        
        img_array = np.array(image)
        
        # 计算基础指标
        brightness = np.mean(img_array)
        contrast = np.std(img_array)
        
        # 简单的色彩丰富度评估
        if len(img_array.shape) == 3:
            color_variance = np.var(img_array, axis=(0, 1)).mean()
        else:
            color_variance = 0
        
        # 综合评分 (简化版)
        score = min(10, max(1, 5 + (contrast - 50) / 50 + color_variance / 1000))
        
        return {
            "overall_score": round(score, 2),
            "brightness": round(brightness, 2),
            "contrast": round(contrast, 2),
            "color_richness": round(color_variance, 2)
        }
    
    async def _analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """分析图片的构图、色彩等特征"""
        import numpy as np
        
        img_array = np.array(image)
        width, height = image.size
        
        analysis = {
            "dimensions": {
                "width": width,
                "height": height,
                "aspect_ratio": f"{width}:{height}"
            },
            "composition": {
                "rule_of_thirds": self._check_rule_of_thirds(img_array),
                "symmetry": self._check_symmetry(img_array),
                "balance": self._assess_balance(img_array)
            },
            "color_analysis": self._analyze_colors(img_array)
        }
        
        return analysis
    
    def _check_rule_of_thirds(self, img_array: np.ndarray) -> float:
        """检查是否符合三分法构图 (简化版)"""
        # TODO: 实现更精确的三分法检测
        return 0.7  # 示例分数
    
    def _check_symmetry(self, img_array: np.ndarray) -> float:
        """检查对称性"""
        import numpy as np
        
        if len(img_array.shape) == 3:
            # 水平对称
            left_half = img_array[:, :img_array.shape[1]//2]
            right_half = img_array[:, img_array.shape[1]//2:]
            if left_half.shape == right_half.shape:
                symmetry_score = 1 - np.mean(np.abs(left_half.astype(float) - right_half[::-1].astype(float))) / 255
                return round(max(0, symmetry_score), 2)
        return 0.5
    
    def _assess_balance(self, img_array: np.ndarray) -> float:
        """评估画面平衡感"""
        # TODO: 实现更精确的平衡评估
        return 0.75
    
    def _analyze_colors(self, img_array: np.ndarray) -> Dict[str, Any]:
        """分析色彩特征"""
        import numpy as np
        
        if len(img_array.shape) < 3:
            return {
                "dominant_colors": [],
                "color_harmony": 0.5,
                "saturation_level": "medium"
            }
        
        # 计算平均颜色
        avg_color = np.mean(img_array, axis=(0, 1))
        
        # 简化的色彩和谐度评估
        color_std = np.std(img_array, axis=(0, 1)).mean()
        harmony_score = min(1.0, color_std / 50)
        
        # 饱和度评估
        saturation = np.std(img_array, axis=2).mean()
        if saturation > 80:
            saturation_level = "high"
        elif saturation > 40:
            saturation_level = "medium"
        else:
            saturation_level = "low"
        
        return {
            "dominant_colors": [int(c) for c in avg_color],
            "color_harmony": round(harmony_score, 2),
            "saturation_level": saturation_level
        }
    
    def _generate_suggestions(self, evaluation: Dict[str, Any]) -> list:
        """根据评估结果生成改进建议"""
        suggestions = []
        
        overall_score = evaluation.get("overall_score", 5)
        
        if overall_score < 5:
            suggestions.append("考虑调整构图以提升视觉吸引力")
            suggestions.append("尝试改善色彩搭配和对比度")
        
        composition = evaluation.get("composition", {})
        if composition.get("rule_of_thirds", 1) < 0.6:
            suggestions.append("尝试使用三分法构图，将主体放在交叉点上")
        
        color_analysis = evaluation.get("color_analysis", {})
        if color_analysis.get("color_harmony", 1) < 0.5:
            suggestions.append("选择更协调的色彩组合，参考色轮理论")
        
        if color_analysis.get("saturation_level") == "low":
            suggestions.append("适当提高色彩饱和度以增强视觉冲击力")
        elif color_analysis.get("saturation_level") == "high":
            suggestions.append("降低部分区域的饱和度以避免视觉疲劳")
        
        if not suggestions:
            suggestions.append("整体视觉效果良好，保持当前风格")
        
        return suggestions
