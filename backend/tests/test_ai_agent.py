import pytest
from unittest.mock import MagicMock, patch
from app.services.ai_agent import generate_blueprint, create_fallback_blueprint
from app.models import VideoBlueprint

def test_create_fallback_blueprint():
    """Kiểm tra xem fallback blueprint có được sinh ra chính xác không."""
    prompt = "Cắt clip ngắn 5s"
    media_files = ["test_image.jpg", "test_video.mp4"]
    width = 1080
    height = 1920
    voice_id = "alloy"
    
    blueprint = create_fallback_blueprint(prompt, media_files, width, height, voice_id)
    
    assert isinstance(blueprint, VideoBlueprint)
    assert blueprint.project_name == "fallback_project"
    assert blueprint.canvas.width == width
    assert blueprint.canvas.height == height
    assert len(blueprint.timeline) == 2
    assert blueprint.timeline[0].type == "image"
    assert blueprint.timeline[0].source_url == "test_image.jpg"
    assert blueprint.timeline[1].type == "video"
    assert blueprint.timeline[1].source_url == "test_video.mp4"
    assert blueprint.audio.voiceover.enabled is True
    assert voice_id in blueprint.audio.voiceover.voice_id
    assert prompt in blueprint.audio.voiceover.text

@pytest.mark.asyncio
@patch("google.generativeai.GenerativeModel")
async def test_generate_blueprint_success(mock_model_class):
    """Kiểm tra gọi API Gemini thành công và parse ra đúng blueprint."""
    # Định nghĩa mock response
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    
    mock_response = MagicMock()
    # Chuỗi JSON hợp lệ khớp với VideoBlueprint schema
    mock_response.text = """
    {
      "project_name": "ai_video_test",
      "canvas": { "width": 1080, "height": 1920, "fps": 30 },
      "audio": {
        "background_music_url": "https://pixabay.com/music/technology.mp3",
        "bgm_volume": 0.15,
        "voiceover": {
          "enabled": true,
          "text": "Xin chào thế giới!",
          "voice_id": "rachel"
        }
      },
      "timeline": [
        {
          "type": "video",
          "source_url": "uploads/raw_video.mp4",
          "trim_start": 0.0,
          "trim_end": 5.0,
          "transition_out": "fade"
        }
      ]
    }
    """
    mock_model_instance.generate_content.return_value = mock_response
    
    prompt = "Biên tập video công nghệ"
    media_files = ["uploads/raw_video.mp4"]
    
    blueprint = await generate_blueprint(prompt, media_files, aspect_ratio="9:16", voice_id="rachel")
    
    assert isinstance(blueprint, VideoBlueprint)
    assert blueprint.project_name == "ai_video_test"
    assert blueprint.canvas.width == 1080
    assert blueprint.canvas.height == 1920
    assert len(blueprint.timeline) == 1
    assert blueprint.timeline[0].type == "video"
    assert blueprint.timeline[0].source_url == "uploads/raw_video.mp4"
    assert blueprint.audio.voiceover.text == "Xin chào thế giới!"
    
    # Kiểm tra xem API Gemini có được gọi đúng
    mock_model_instance.generate_content.assert_called_once()

@pytest.mark.asyncio
@patch("google.generativeai.GenerativeModel")
async def test_generate_blueprint_failure_fallback(mock_model_class):
    """Kiểm tra xem khi Gemini bị lỗi, hệ thống có tự động fallback về blueprint cơ bản không."""
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    # Giả lập lỗi API
    mock_model_instance.generate_content.side_effect = Exception("API Quota Exceeded")
    
    prompt = "Cắt clip ngắn"
    media_files = ["uploads/raw_video.mp4"]
    
    blueprint = await generate_blueprint(prompt, media_files, aspect_ratio="9:16", voice_id="rachel")
    
    assert isinstance(blueprint, VideoBlueprint)
    # Xác nhận là fallback blueprint
    assert blueprint.project_name == "fallback_project"
    assert len(blueprint.timeline) == 1
    assert blueprint.timeline[0].source_url == "uploads/raw_video.mp4"
    assert "Cắt clip ngắn" in blueprint.audio.voiceover.text
