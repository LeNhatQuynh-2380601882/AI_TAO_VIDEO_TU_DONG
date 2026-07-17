import pytest
from unittest.mock import patch
from app.services.task_manager import tasks_db

def test_root_endpoint(client):
    """Kiểm tra API root hoạt động bình thường."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "service" in data
    assert data["docs_url"] == "/docs"

def test_upload_media_success(client):
    """Kiểm tra upload file thành công với định dạng hỗ trợ."""
    file_content = b"fake image content"
    files = {"file": ("test_image.jpg", file_content, "image/jpeg")}
    
    response = client.post("/api/video/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "filename" in data
    assert data["original_name"] == "test_image.jpg"
    assert data["url"].startswith("/static/uploads/")

def test_upload_media_invalid_extension(client):
    """Kiểm tra upload file thất bại khi sai định dạng file."""
    file_content = b"fake executable content"
    files = {"file": ("malicious.exe", file_content, "application/octet-stream")}
    
    response = client.post("/api/video/upload", files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "không được hỗ trợ" in data["detail"]

def test_generate_video_endpoint(client):
    """Kiểm tra gửi yêu cầu tạo video thành công."""
    payload = {
        "prompt": "Cắt video này 3 giây và thêm nhạc",
        "media_files": ["/static/uploads/test.jpg"],
        "aspect_ratio": "16:9",
        "voice_id": "rachel"
    }
    
    # Mock hàm run_video_generation_pipeline để không chạy ngầm thực tế trong test này
    with patch("app.routes.video.run_video_generation_pipeline") as mock_pipeline:
        response = client.post("/api/video/generate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "message" in data
        assert data["message"] == "Yêu cầu đã được nhận và đang xử lý."
        
        # Đảm bảo task được khởi tạo trong DB và pipeline được gọi bất đồng bộ
        task_id = data["task_id"]
        assert task_id in tasks_db
        mock_pipeline.assert_called_once()

def test_get_task_status_success(client):
    """Kiểm tra truy vấn trạng thái của task ID hợp lệ."""
    # Khởi tạo một task giả trong DB
    task_id = "test-query-id"
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "rendering",
        "progress": 45,
        "output_url": None,
        "error_message": None,
        "created_at": "2026-07-17T20:00:00",
        "updated_at": "2026-07-17T20:01:00"
    }
    
    response = client.get(f"/api/video/status/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "rendering"
    assert data["progress"] == 45

def test_get_task_status_not_found(client):
    """Kiểm tra truy vấn task ID không tồn tại trả về lỗi 404."""
    response = client.get("/api/video/status/non-existent-task-id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Không tìm thấy Task ID" in data["detail"]
