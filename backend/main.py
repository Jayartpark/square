"""
VisionCraft - AI 驱动的智能设计软件后端服务

重构版本主要改进:
1. 模块化路由设计 - API 端点分离到独立的路由文件
2. 统一的依赖注入 - 服务实例集中管理
3. 增强的健康检查 - 包含模型状态和设备信息
4. 请求/响应中间件 - 记录请求日志和性能监控
5. 结构化数据模型 - 使用 Pydantic 模型定义请求和响应
6. 完善的异常处理 - 统一的异常处理器
7. 生命周期管理 - 应用启动和关闭事件处理
8. 支持批量操作 - 新增批量生成接口
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
import torch
from typing import AsyncGenerator

from backend.config.settings import settings
from backend.api.routes import (
    generation_router,
    edit_router,
    image_router,
    aesthetic_router
)
from backend.exceptions import VisionCraftException
from backend.models.schemas import HealthCheckResponse, ErrorResponse


# ==================== 日志配置 ====================

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("visioncraft.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


# ==================== 服务生命周期管理 ====================

class ServiceManager:
    """服务管理器 - 统一管理所有服务的生命周期"""
    
    def __init__(self):
        self.generator_service = None
        self.editor_service = None
        self.evaluator_service = None
        self._initialized = False
    
    def initialize_services(self):
        """懒加载初始化服务"""
        if self._initialized:
            return
        
        logger.info("Initializing services...")
        
        try:
            from backend.services.image_generator import ImageGeneratorService
            from backend.services.image_editor import ImageEditorService
            from backend.services.aesthetic_evaluator import AestheticEvaluatorService
            
            # 懒加载服务实例（不立即加载模型）
            self.generator_service = ImageGeneratorService()
            self.editor_service = ImageEditorService()
            self.evaluator_service = AestheticEvaluatorService()
            
            self._initialized = True
            logger.info("Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def preload_models(self):
        """预加载 AI 模型到内存"""
        if not self._initialized:
            self.initialize_services()
        
        logger.info("Preloading AI models...")
        
        try:
            # 根据配置决定是否预加载模型
            if settings.DEBUG:
                logger.info("Debug mode: skipping model preloading")
                return
            
            # 可以选择性地预加载模型
            # self.generator_service.load_model()
            # self.editor_service.load_inpaint_model()
            # self.editor_service.load_img2img_model()
            
            logger.info("Model preloading completed")
        except Exception as e:
            logger.warning(f"Model preloading failed: {e}")
    
    def shutdown_services(self):
        """清理服务资源"""
        logger.info("Shutting down services...")
        
        # 释放 GPU 内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU cache cleared")
        
        self._initialized = False
        logger.info("Services shutdown completed")


# 全局服务管理器实例
service_manager = ServiceManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理
    
    处理应用启动和关闭事件
    """
    # 启动事件
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    try:
        # 确保存储目录存在
        settings.UPLOAD_DIR.mkdir(exist_ok=True)
        settings.OUTPUT_DIR.mkdir(exist_ok=True)
        logger.info(f"Upload directory: {settings.UPLOAD_DIR.absolute()}")
        logger.info(f"Output directory: {settings.OUTPUT_DIR.absolute()}")
        
        # 初始化服务
        service_manager.initialize_services()
        
        # 可选：预加载模型
        # service_manager.preload_models()
        
        logger.info(f"Server running on http://{settings.HOST}:{settings.PORT}")
        logger.info(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
        
        yield
        
    finally:
        # 关闭事件
        service_manager.shutdown_services()
        logger.info(f"{settings.APP_NAME} shutdown completed")


# ==================== FastAPI 应用初始化 ====================

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# ==================== 中间件 ====================

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:
    """
    请求日志中间件
    
    记录每个请求的详细信息和执行时间
    """
    start_time = time.time()
    
    # 记录请求信息
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    # 处理请求
    response = await call_next(request)
    
    # 计算执行时间
    process_time = time.time() - start_time
    
    # 添加执行时间到响应头
    response.headers["X-Process-Time"] = str(round(process_time, 3))
    
    # 记录响应信息
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next) -> Response:
    """
    安全头中间件
    
    添加常用的安全 HTTP 头
    """
    response = await call_next(request)
    
    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


# ==================== 注册路由 ====================

# 注册各个功能模块的路由
app.include_router(generation_router)
app.include_router(edit_router)
app.include_router(image_router)
app.include_router(aesthetic_router)


# ==================== 全局异常处理 ====================

@app.exception_handler(VisionCraftException)
async def visioncraft_exception_handler(request: Request, exc: VisionCraftException):
    """
    VisionCraft 自定义异常处理器
    
    统一处理所有业务异常，返回标准化的错误响应
    """
    logger.error(
        f"VisionCraft error: {exc.detail}, "
        f"code: {exc.error_code}, "
        f"path: {request.url.path}"
    )
    
    return ErrorResponse(
        success=False,
        error=exc.error_code,
        detail=exc.detail,
        status_code=exc.status_code
    ).model_dump()


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    通用异常处理器
    
    捕获所有未处理的异常，防止敏感信息泄露
    """
    logger.error(
        f"Unhandled exception: {str(exc)}, "
        f"path: {request.url.path}",
        exc_info=settings.DEBUG
    )
    
    return ErrorResponse(
        success=False,
        error="INTERNAL_SERVER_ERROR",
        detail="服务器内部错误" if not settings.DEBUG else str(exc),
        status_code=500
    ).model_dump()


# ==================== 根路由和健康检查 ====================

@app.get("/", response_model=HealthCheckResponse, tags=["系统"])
async def root():
    """
    根路径 - 健康检查
    
    返回服务基本信息和运行状态
    """
    return HealthCheckResponse(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="running",
        model_loaded=service_manager.generator_service is not None,
        device=service_manager.generator_service.device if service_manager.generator_service else "unknown",
        gpu_available=torch.cuda.is_available()
    )


@app.get("/health", response_model=HealthCheckResponse, tags=["系统"])
async def health_check():
    """
    详细健康检查
    
    返回服务、模型和设备的详细状态信息
    """
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "gpu_count": torch.cuda.device_count(),
            "current_gpu": torch.cuda.current_device(),
            "gpu_name": torch.cuda.get_device_name(0),
            "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**2:.2f} MB",
            "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**2:.2f} MB"
        }
    
    return HealthCheckResponse(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="healthy",
        model_loaded=(
            service_manager.generator_service is not None and 
            service_manager.generator_service.pipe is not None
        ),
        device=service_manager.generator_service.device if service_manager.generator_service else "unknown",
        gpu_available=torch.cuda.is_available()
    )


@app.get("/api/v1/system/info", tags=["系统"])
async def system_info():
    """
    系统信息接口
    
    返回详细的系统和配置信息
    """
    return {
        "success": True,
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": settings.APP_DESCRIPTION,
            "debug_mode": settings.DEBUG
        },
        "server": {
            "host": settings.HOST,
            "port": settings.PORT
        },
        "storage": {
            "upload_dir": str(settings.UPLOAD_DIR.absolute()),
            "output_dir": str(settings.OUTPUT_DIR.absolute()),
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE // 1024 // 1024
        },
        "ai_config": {
            "default_model": settings.DEFAULT_MODEL_ID,
            "device": settings.DEVICE,
            "default_dimensions": f"{settings.DEFAULT_WIDTH}x{settings.DEFAULT_HEIGHT}",
            "default_steps": settings.DEFAULT_INFERENCE_STEPS,
            "default_guidance_scale": settings.DEFAULT_GUIDANCE_SCALE
        },
        "hardware": {
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
            "pytorch_version": torch.__version__,
            **gpu_info
        }
    }


# ==================== 应用入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.APP_NAME} development server...")
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=settings.DEBUG
    )
