# 使用官方Python完整镜像（非slim版）
FROM python:3.10

# 设置工作目录
WORKDIR /app

# 1. 复制依赖文件并安装Python包（完整镜像通常已包含gcc等编译工具）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple \
    --extra-index-url https://download.pytorch.org/whl/cpu

# ===== 核心步骤：构建时预下载模型 =====
# 2. 设置环境变量，使用国内镜像源加速下载
ENV HF_ENDPOINT=https://hf-mirror.com

# 3. 执行Python命令，触发模型下载与缓存（使用HEREDOC语法，最可靠）
RUN python <<EOF
try:
    from sentence_transformers import SentenceTransformer
    print('开始下载并缓存模型: sentence-transformers/all-MiniLM-L6-v2')
    # 这行代码会下载并缓存模型
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print('✅ 模型下载与缓存成功。')
except Exception as e:
    print('❌ 模型下载失败，错误信息:', e)
    import traceback
    traceback.print_exc()
    exit(1)
EOF

# ===== 后续步骤 =====
# 4. 复制你的应用代码（此时模型已就绪）
COPY . .

# 5. 声明暴露端口
EXPOSE 80

# 6. 启动命令
CMD ["uvicorn", "backend_demo:app", "--host", "0.0.0.0", "--port", "80"]