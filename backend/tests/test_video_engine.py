import os
import pytest
from PIL import Image
from unittest.mock import MagicMock, patch, AsyncMock
from app.models import TextOverlayConfig, VideoBlueprint, CanvasConfig, AudioConfig, VoiceoverConfig, TimelineClip
from app.services.video_engine import download_file, generate_voiceover, create_text_overlay_image, render_video

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_download_file_remote(mock_async_client, tmp_path):
    """Kiểm tra tải file từ URL về thư mục tạm."""
    mock_client = MagicMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.content = b"fake binary data"
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    
    url = "https://example.com/assets/bg_music.mp3"
    dest_dir = str(tmp_path / "temp_download")
    
    # Thực hiện gọi hàm
    file_path = await download_file(url, dest_dir)
    
    assert os.path.exists(file_path)
    assert file_path.endswith("bg_music.mp3")
    with open(file_path, "rb") as f:
        assert f.read() == b"fake binary data"
    
    mock_client.get.assert_called_once_with(url)

@pytest.mark.asyncio
async def test_download_file_local():
    """Kiểm tra nếu là file cục bộ thì trả về ngay đường dẫn đó."""
    local_path = "uploads/my_video.mp4"
    result = await download_file(local_path, "some_dir")
    assert result == local_path

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_generate_voiceover_openai(mock_async_client, tmp_path):
    """Kiểm tra sinh giọng nói thuyết minh dùng OpenAI TTS thành công."""
    mock_client = MagicMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.content = b"fake audio voice"
    mock_response.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    
    dest_path = str(tmp_path / "voice.mp3")
    
    # Mock settings.OPENAI_API_KEY
    with patch("app.services.video_engine.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test_key"
        result = await generate_voiceover("Xin chào", "rachel", dest_path)
        
        assert result == dest_path
        assert os.path.exists(dest_path)
        with open(dest_path, "rb") as f:
            assert f.read() == b"fake audio voice"
        
        mock_client.post.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.video_engine.gTTS")
async def test_generate_voiceover_gtts_fallback(mock_gtts, tmp_path):
    """Kiểm tra fallback sang gTTS khi không có OpenAI Key hoặc OpenAI bị lỗi."""
    dest_path = str(tmp_path / "voice_gtts.mp3")
    
    # Mock gTTS instance
    mock_gtts_instance = MagicMock()
    mock_gtts.return_value = mock_gtts_instance
    
    # Ghi đè settings.OPENAI_API_KEY = ""
    with patch("app.services.video_engine.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = ""
        result = await generate_voiceover("Xin chào tiếng Việt", "rachel", dest_path)
        
        assert result == dest_path
        mock_gtts.assert_called_once_with(text="Xin chào tiếng Việt", lang="vi", slow=False)
        mock_gtts_instance.save.assert_called_once_with(dest_path)

def test_create_text_overlay_image(tmp_path):
    """Kiểm tra việc tạo ảnh chữ bằng Pillow."""
    config = TextOverlayConfig(
        text="TÍNH NĂNG MỚI",
        font_size=50,
        color="#FF0000",
        position="center"
    )
    dest_path = str(tmp_path / "overlay.png")
    
    result = create_text_overlay_image(config, 1080, 1920, dest_path)
    
    assert result == dest_path
    assert os.path.exists(dest_path)
    
    # Mở ảnh kiểm tra kích thước và định dạng
    with Image.open(dest_path) as img:
        assert img.size == (1080, 1920)
        assert img.format == "PNG"
        assert img.mode == "RGBA"

@pytest.mark.asyncio
@patch("app.services.video_engine.download_file")
@patch("app.services.video_engine.generate_voiceover")
@patch("app.services.video_engine.VideoFileClip")
@patch("app.services.video_engine.ImageClip")
@patch("app.services.video_engine.AudioFileClip")
@patch("app.services.video_engine.CompositeVideoClip")
@patch("app.services.video_engine.CompositeAudioClip")
@patch("app.services.video_engine.concatenate_videoclips")
async def test_render_video_flow(
    mock_concat, mock_composite_audio, mock_composite_video,
    mock_audio_clip, mock_image_clip, mock_video_clip, 
    mock_gen_voiceover, mock_download, tmp_path
):
    """Kiểm tra toàn bộ luồng render video với MoviePy được mock hoàn toàn."""
    # Thiết lập mock composite video và audio
    mock_composite_video.side_effect = lambda clips: clips[0]
    mock_composite_audio.return_value = MagicMock()
    
    # Thiết lập mock download
    mock_download.side_effect = lambda url, dest: url # Trả về chính URL/Path
    
    # Thiết lập mock voiceover
    mock_gen_voiceover.return_value = "voiceover.mp3"
    
    # Cấu hình mock cho clips
    mock_v_instance = MagicMock()
    mock_v_instance.w = 1920
    mock_v_instance.h = 1080
    mock_v_instance.duration = 10.0
    mock_v_instance.subclip.return_value = mock_v_instance
    mock_v_instance.resize.return_value = mock_v_instance
    mock_v_instance.crop.return_value = mock_v_instance
    mock_v_instance.fadeout.return_value = mock_v_instance
    mock_video_clip.return_value = mock_v_instance
    
    mock_img_instance = MagicMock()
    mock_img_instance.w = 500
    mock_img_instance.h = 500
    mock_img_instance.duration = 4.0
    mock_img_instance.set_duration.return_value = mock_img_instance
    mock_img_instance.resize.return_value = mock_img_instance
    mock_img_instance.crop.return_value = mock_img_instance
    mock_img_instance.fadeout.return_value = mock_img_instance
    mock_image_clip.return_value = mock_img_instance
    
    # Mock audio clip
    mock_a_instance = MagicMock()
    mock_a_instance.volumex.return_value = mock_a_instance
    mock_a_instance.set_duration.return_value = mock_a_instance
    mock_a_instance.set_start.return_value = mock_a_instance
    mock_audio_clip.return_value = mock_a_instance
    
    # Mock concatenate_videoclips
    mock_final_video = MagicMock()
    mock_final_video.duration = 14.0
    mock_final_video.audio = MagicMock()
    mock_final_video.set_audio.return_value = mock_final_video
    mock_concat.return_value = mock_final_video
    
    # Thiết lập blueprint
    blueprint = VideoBlueprint(
        project_name="render_test",
        canvas=CanvasConfig(width=1080, height=1920, fps=30),
        audio=AudioConfig(
            background_music_url="bgm.mp3",
            bgm_volume=0.2,
            voiceover=VoiceoverConfig(enabled=True, text="Chào bạn", voice_id="alloy")
        ),
        timeline=[
            TimelineClip(
                type="video",
                source_url="video.mp4",
                trim_start=1.0,
                trim_end=6.0,
                text_overlay=TextOverlayConfig(text="Test", font_size=20, color="#FFFFFF", position="top"),
                transition_out="fade"
            ),
            TimelineClip(
                type="image",
                source_url="image.jpg",
                duration=4.0,
                transition_out="fade"
            )
        ]
    )
    
    progress_updates = []
    def progress_callback(val):
        progress_updates.append(val)
        
    task_id = "test_render_task"
    
    # Chạy render
    output_path = await render_video(blueprint, task_id, progress_callback)
    
    # Kiểm tra xem file đầu ra có được sinh ra (do mock write_videofile nên ta chỉ kiểm tra logic gọi và callback)
    assert output_path.endswith(f"output_{task_id}.mp4")
    assert 10 in progress_updates
    assert 100 in progress_updates
    
    # Kiểm tra xem có đóng các clip giải phóng bộ nhớ không
    mock_final_video.close.assert_called_once()
    mock_a_instance.close.assert_called()
