# 使用Python官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有文件
COPY . .

# 暴露端口
EXPOSE 5000

# 启动Flask应用
CMD ["python", "app.py"]
