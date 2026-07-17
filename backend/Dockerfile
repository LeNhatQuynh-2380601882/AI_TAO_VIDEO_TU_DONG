# Sử dụng Python base image chính thức
FROM python:3.10-slim

# Cài đặt FFmpeg và các thư viện hệ thống cần thiết cho MoviePy / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép và cài đặt các dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn backend
COPY . .

# Khởi tạo các thư mục lưu trữ tạm thời
RUN mkdir -p temp/uploads

# Expose cổng 8000
EXPOSE 8000

# Lệnh khởi chạy server FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
