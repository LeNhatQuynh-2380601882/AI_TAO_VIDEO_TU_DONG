import uuid
import datetime
import logging
import asyncio
from typing import Dict, Optional
from fastapi import BackgroundTasks
from app.models import VideoGenerationRequest, TaskStatusResponse
from app.services.ai_agent import generate_blueprint
from app.services.video_engine import render_video

logger = logging.getLogger(__name__)

# Lưu trữ các tác vụ trong bộ nhớ tạm (In-Memory Database) cho bản đơn giản dễ deploy
tasks_db: Dict[str, dict] = {}

def get_current_time_str() -> str:
    return datetime.datetime.now().isoformat()

def create_task(request: VideoGenerationRequest) -> str:
    """Tạo một task mới và lưu vào DB tạm."""
    task_id = str(uuid.uuid4())
    now = get_current_time_str()
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "output_url": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now
    }
    return task_id

def update_task(task_id: str, **kwargs) -> None:
    """Cập nhật trạng thái của task."""
    if task_id in tasks_db:
        tasks_db[task_id].update(kwargs)
        tasks_db[task_id]["updated_at"] = get_current_time_str()

def get_task(task_id: str) -> Optional[TaskStatusResponse]:
    """Lấy thông tin chi tiết của task."""
    task_data = tasks_db.get(task_id)
    if task_data:
        return TaskStatusResponse(**task_data)
    return None

async def run_video_generation_pipeline(task_id: str, request: VideoGenerationRequest):
    """Pipeline chính chạy xử lý bất đồng bộ sinh video."""
    logger.info(f"Bắt đầu pipeline cho Task ID: {task_id}")
    
    try:
        # 1. Bước tạo Blueprint bằng AI Agent (Gemini)
        update_task(task_id, status="generating_blueprint", progress=15)
        logger.info(f"[{task_id}] Đang gọi AI Agent để sinh Blueprint...")
        
        blueprint = await generate_blueprint(
            prompt=request.prompt,
            media_files=request.media_files,
            aspect_ratio=request.aspect_ratio,
            voice_id=request.voice_id
        )
        
        logger.info(f"[{task_id}] AI Agent đã sinh Blueprint thành công.")
        
        # 2. Định nghĩa hàm callback cập nhật tiến trình render
        def progress_callback(progress_percent: int):
            # Map tiến trình của engine (10-100) sang tiến trình tổng thể (30-95)
            overall_progress = 30 + int(progress_percent * 0.65)
            update_task(task_id, status="rendering", progress=min(95, overall_progress))

        # 3. Thực thi Render video bằng Engine
        update_task(task_id, status="rendering", progress=30)
        logger.info(f"[{task_id}] Đang tiến hành biên tập & render video...")
        
        output_path = await render_video(
            blueprint=blueprint,
            task_id=task_id,
            progress_callback=progress_callback
        )
        
        # Ở môi trường thực tế, bạn sẽ upload file này lên S3/Supabase Storage.
        # Với bản chạy thử này, ta sẽ trả về đường dẫn cục bộ (hoặc URL static của backend)
        output_url = f"/static/{os.path.basename(output_path)}"
        
        update_task(
            task_id, 
            status="completed", 
            progress=100, 
            output_url=output_url
        )
        logger.info(f"[{task_id}] Đã hoàn thành sinh video thành công: {output_path}")
        
    except Exception as e:
        logger.error(f"[{task_id}] Lỗi trong quá trình xử lý pipeline: {e}", exc_info=True)
        update_task(
            task_id, 
            status="failed", 
            progress=100, 
            error_message=str(e)
        )

# Import os ở đây để tránh lỗi circular import hoặc undefined name trong hàm pipeline
import os
