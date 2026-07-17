import os
import uuid
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.config import settings
from app.models import VideoGenerationRequest, TaskStatusResponse
from app.services.task_manager import create_task, get_task, run_video_generation_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video", tags=["Video Automation"])

# Đảm bảo thư mục upload tồn tại
UPLOAD_DIR = os.path.join(settings.TEMP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/generate", response_model=dict)
async def generate_video_endpoint(
    request: VideoGenerationRequest, 
    background_tasks: BackgroundTasks
):
    """
    Tạo yêu cầu sinh video tự động. API sẽ trả về task_id ngay lập tức 
    và xử lý render bất đồng bộ dưới nền.
    """
    logger.info(f"Nhận yêu cầu tạo video mới. Prompt: '{request.prompt[:30]}...'")
    
    # Khởi tạo task trong hệ thống
    task_id = create_task(request)
    
    # Chạy pipeline bất đồng bộ
    background_tasks.add_task(run_video_generation_pipeline, task_id, request)
    
    return {"task_id": task_id, "message": "Yêu cầu đã được nhận và đang xử lý."}

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status_endpoint(task_id: str):
    """
    Lấy tiến độ render video hiện tại của một Task ID.
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy Task ID yêu cầu.")
    return task

@router.post("/upload", response_model=dict)
async def upload_media_endpoint(file: UploadFile = File(...)):
    """
    Tải file ảnh/video thô từ Client lên Server để AI xử lý.
    """
    # Lấy đuôi mở rộng của file
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".mp4", ".mov", ".avi", ".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav"]:
        raise HTTPException(
            status_code=400, 
            detail="Định dạng file không được hỗ trợ. Chỉ hỗ trợ video, ảnh và nhạc."
        )

    # Đặt tên file duy nhất tránh trùng lặp
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Trả về URL static để client có thể truy cập
        file_url = f"/static/uploads/{unique_filename}"
        logger.info(f"Đã upload thành công file: {file.filename} -> {file_url}")
        
        return {
            "url": file_url,
            "filename": unique_filename,
            "original_name": file.filename
        }
    except Exception as e:
        logger.error(f"Lỗi khi lưu file upload: {e}")
        raise HTTPException(status_code=500, detail="Không thể lưu trữ tệp tin tải lên.")
