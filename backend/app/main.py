import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import video

# Thiết lập log cơ bản
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.BRAND_NAME,
    description="Hệ thống tự động hóa biên tập video bằng AI Agent",
    version="1.0.0"
)

# Cấu hình CORS để cho phép Frontend (ví dụ chạy ở cổng 3000) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong môi trường production nên cấu hình domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount thư mục lưu trữ tạm thời thành thư mục tĩnh
# Điều này giúp Client truy cập trực tiếp các video đã render hoặc file đã upload qua URL
# Ví dụ: http://localhost:8000/static/output_123.mp4
app.mount("/static", StaticFiles(directory=settings.TEMP_DIR), name="static")

# Đăng ký các router API
app.include_router(video.router)

@app.get("/")
async def root_endpoint():
    """Endpoint kiểm tra tình trạng hoạt động của server."""
    return {
        "status": "online",
        "service": settings.BRAND_NAME,
        "brand_color": settings.BRAND_PRIMARY_COLOR,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    logger.info(f"Đang khởi động server tại http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )
