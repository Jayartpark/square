# 🚀 VisionCraft 极简使用指南

## 一行命令启动

```bash
./run.sh
```

就这么简单！服务会自动在 `http://localhost:8000` 启动。

---

## 常用操作

### 1. 启动服务（默认端口 8000）
```bash
./run.sh
```

### 2. 指定端口启动
```bash
./run.sh 9000
```

### 3. 访问 API 文档
浏览器打开：`http://localhost:8000/docs`

### 4. 停止服务
按 `Ctrl + C`

---

## 快速测试 API

### 方式一：浏览器访问
打开 `http://localhost:8000/docs`，点击 "Try it out" 测试接口。

### 方式二：命令行测试

#### 生成图片
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "一只可爱的猫咪", "style": "anime"}'
```

#### 批量生成
```bash
curl -X POST http://localhost:8000/api/v1/batch/generate \
  -H "Content-Type: application/json" \
  -d '{"prompts": ["一只猫", "一只狗", "一只鸟"], "style": "realistic"}'
```

#### 查看系统信息
```bash
curl http://localhost:8000/api/v1/system/info
```

#### 健康检查
```bash
curl http://localhost:8000/health
```

---

## Python 代码调用

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 生成单张图片
response = requests.post(f"{BASE_URL}/generate", json={
    "prompt": "夕阳下的海滩",
    "style": "realistic",
    "width": 512,
    "height": 512
})
result = response.json()
print(f"图片 URL: {result['image_url']}")

# 批量生成
response = requests.post(f"{BASE_URL}/batch/generate", json={
    "prompts": ["春天", "夏天", "秋天", "冬天"],
    "style": "anime"
})
results = response.json()
for img in results['images']:
    print(f"生成成功：{img['image_url']}")
```

---

## 常见问题

### Q: 提示权限不足？
```bash
chmod +x run.sh
./run.sh
```

### Q: 端口被占用？
```bash
./run.sh 9000  # 换一个端口
```

### Q: 如何查看日志？
启动脚本会实时显示日志，直接看终端输出即可。

### Q: 依赖安装失败？
```bash
pip3 install -r requirements.txt
./run.sh
```

---

## 高级用法

### 开发模式（自动重载）
脚本默认已开启 `--reload`，修改代码后自动重启。

### 生产环境部署
```bash
# 关闭调试模式
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker 部署（可选）
```bash
docker build -t visioncraft .
docker run -p 8000:8000 visioncraft
```

---

## 功能速览

| 功能 | 端点 | 说明 |
|------|------|------|
| 🎨 图片生成 | `/api/v1/generate` | 根据文字描述生成图片 |
| 📦 批量生成 | `/api/v1/batch/generate` | 一次生成多张图片 |
| ✏️ 图片编辑 | `/api/v1/edit` | 编辑现有图片 |
| 🖼️ 图片上传 | `/api/v1/image/upload` | 上传图片文件 |
| 📊 系统信息 | `/api/v1/system/info` | 查看配置和状态 |
| ❤️ 健康检查 | `/health` | 服务健康状态 |

---

**享受简单的 AI 图像创作！** 🎉
