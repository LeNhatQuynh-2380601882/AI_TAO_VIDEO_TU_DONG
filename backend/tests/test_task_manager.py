import pytest
from unittest.mock import patch, AsyncMock
from app.models import VideoGenerationRequest, VideoBlueprint, CanvasConfig, AudioConfig
from app.services.task_manager import (
    tasks_db, 
    create_task, 
    update_task, 
    get_task, 
    run_video_generation_pipeline
)

@pytest.fixture(autouse=True)
def clear_tasks_db():
    """Tự động làm sạch database in-memory trước mỗi test case."""
    tasks_db.clear()
    yield

def test_create_task_flow():
    """Kiểm tra tạo task mới lưu vào DB."""
    req = VideoGenerationRequest(
        prompt="Tạo video",
        media_files=["image.jpg"],
        aspect_ratio="1:1",
        voice_id="alloy"
    )
    
    task_id = create_task(req)
    
    assert task_id in tasks_db
    task = tasks_db[task_id]
    assert task["status"] == "pending"
    assert task["progress"] == 0
    assert task["output_url"] is None
    assert task["error_message"] is None

def test_update_and_get_task():
    """Kiểm tra cập nhật thông tin task và lấy thông tin task."""
    req = VideoGenerationRequest(prompt="Test", media_files=[])
    task_id = create_task(req)
    
    update_task(task_id, status="rendering", progress=50)
    
    task_res = get_task(task_id)
    assert task_res is not None
    assert task_res.status == "rendering"
    assert task_res.progress == 50
    
    # Lấy task không tồn tại
    assert get_task("invalid-id") is None

@pytest.mark.asyncio
@patch("app.services.task_manager.generate_blueprint")
@patch("app.services.task_manager.render_video")
async def test_run_video_generation_pipeline_success(mock_render, mock_gen_blueprint):
    """Kiểm tra luồng chạy pipeline thành công."""
    req = VideoGenerationRequest(prompt="Test", media_files=["video.mp4"])
    task_id = create_task(req)
    
    # Thiết lập mock sinh blueprint
    mock_blueprint = VideoBlueprint(
        project_name="test_proj",
        canvas=CanvasConfig(width=1080, height=1920, fps=30),
        audio=AudioConfig(bgm_volume=0.2),
        timeline=[]
    )
    mock_gen_blueprint.return_value = mock_blueprint
    
    # Thiết lập mock render video
    mock_render.return_value = "temp/output_test_task.mp4"
    
    # Chạy pipeline
    await run_video_generation_pipeline(task_id, req)
    
    # Kiểm tra trạng thái cuối cùng của task trong DB
    task = get_task(task_id)
    assert task.status == "completed"
    assert task.progress == 100
    assert task.output_url == "/static/output_test_task.mp4"
    assert task.error_message is None
    
    # Kiểm tra các hàm được gọi đúng
    mock_gen_blueprint.assert_called_once_with(
        prompt=req.prompt,
        media_files=req.media_files,
        aspect_ratio=req.aspect_ratio,
        voice_id=req.voice_id
    )
    mock_render.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.task_manager.generate_blueprint")
async def test_run_video_generation_pipeline_failure(mock_gen_blueprint):
    """Kiểm tra luồng chạy pipeline thất bại khi gặp ngoại lệ."""
    req = VideoGenerationRequest(prompt="Test Error", media_files=["video.mp4"])
    task_id = create_task(req)
    
    # Giả lập lỗi khi sinh blueprint
    mock_gen_blueprint.side_effect = ValueError("Gemini API Error")
    
    # Chạy pipeline
    await run_video_generation_pipeline(task_id, req)
    
    # Kiểm tra trạng thái cuối cùng của task trong DB
    task = get_task(task_id)
    assert task.status == "failed"
    assert task.progress == 100
    assert "Gemini API Error" in task.error_message
