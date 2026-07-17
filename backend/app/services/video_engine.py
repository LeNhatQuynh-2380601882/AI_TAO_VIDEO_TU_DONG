import os
import uuid
import logging
import httpx
from typing import Callable, List
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

# Cấu hình log của MoviePy
import sys
# Để tắt logs quá dài của moviepy
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

try:
    try:
        from moviepy.editor import (
            VideoFileClip, 
            ImageClip, 
            AudioFileClip, 
            CompositeVideoClip, 
            concatenate_videoclips, 
            CompositeAudioClip
        )
    except ImportError:
        from moviepy import (
            VideoFileClip, 
            ImageClip, 
            AudioFileClip, 
            CompositeVideoClip, 
            concatenate_videoclips, 
            CompositeAudioClip
        )
except ImportError:
    # Dự phòng nếu chưa cài đặt moviepy khi import chạy thử
    pass

from app.config import settings
from app.models import VideoBlueprint, TimelineClip, TextOverlayConfig

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. Các Hàm Helper Tải và Xử Lý File Tạm
# ==============================================================================

async def download_file(url: str, dest_dir: str) -> str:
    """Tải file từ URL về thư mục tạm."""
    if not url.startswith("http://") and not url.startswith("https://"):
        # Nếu đã là đường dẫn cục bộ
        return url

    os.makedirs(dest_dir, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0]
    if not filename:
        filename = f"{uuid.uuid4()}"
    
    # Đảm bảo có đuôi file phù hợp
    if "." not in filename:
        filename += ".mp4"

    dest_path = os.path.join(dest_dir, filename)
    
    # Tránh tải lại nếu file đã tồn tại
    if os.path.exists(dest_path):
        return dest_path

    logger.info(f"Đang tải: {url} -> {dest_path}")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(response.content)
            
    return dest_path

# ==============================================================================
# 2. Xử Lý Giọng Nói AI (TTS)
# ==============================================================================

async def generate_voiceover(text: str, voice_id: str, dest_path: str) -> str:
    """Sinh giọng nói thuyết minh bằng OpenAI TTS hoặc gTTS làm dự phòng."""
    if settings.OPENAI_API_KEY:
        logger.info(f"Đang tạo giọng đọc OpenAI TTS cho: '{text[:20]}...'")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                payload = {
                    "model": "tts-1",
                    "input": text,
                    "voice": "alloy" if voice_id == "rachel" else voice_id
                }
                response = await client.post("https://api.openai.com/v1/audio/speech", json=payload, headers=headers)
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    f.write(response.content)
                return dest_path
        except Exception as e:
            logger.error(f"Lỗi gọi OpenAI TTS: {e}. Chuyển sang dùng gTTS miễn phí.")
            
    # Dự phòng bằng gTTS (Google Text-to-Speech) miễn phí, hỗ trợ tiếng Việt cực tốt
    logger.info(f"Đang tạo giọng đọc gTTS (Vietnamese) cho: '{text[:20]}...'")
    # Tự động chọn ngôn ngữ tiếng Việt nếu phát hiện ký tự đặc trưng hoặc cài mặc định
    lang = 'vi'
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(dest_path)
    return dest_path

# ==============================================================================
# 3. Tạo Text Overlay dùng Pillow (Tránh phụ thuộc ImageMagick của MoviePy)
# ==============================================================================

def create_text_overlay_image(
    config: TextOverlayConfig, 
    canvas_width: int, 
    canvas_height: int, 
    dest_path: str
) -> str:
    """Tạo tệp ảnh PNG trong suốt chứa chữ, tránh lỗi ImageMagick của MoviePy."""
    img = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_size = config.font_size
    # Thử load một số font Unicode phổ biến trên Windows/Linux
    font = None
    fonts_to_try = ["arial.ttf", "tahoma.ttf", "DejaVuSans.ttf", "Helvetica.ttf"]
    for font_name in fonts_to_try:
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except IOError:
            continue
            
    if font is None:
        font = ImageFont.load_default()

    # Tính toán kích thước chữ để căn lề giữa
    # Pillow 10.0+ dùng textbbox
    bbox = draw.textbbox((0, 0), config.text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (canvas_width - text_w) // 2
    
    # Xác định vị trí dọc (top, center, bottom)
    if config.position == "top":
        y = int(canvas_height * 0.15)
    elif config.position == "center":
        y = (canvas_height - text_h) // 2
    else: # bottom
        y = int(canvas_height * 0.8)

    # Vẽ viền chữ màu đen (stroke/outline) giúp dễ đọc trên mọi nền video
    outline_color = (0, 0, 0, 255)
    stroke_w = max(2, int(font_size * 0.05))
    
    for dx in range(-stroke_w, stroke_w + 1):
        for dy in range(-stroke_w, stroke_w + 1):
            if dx*dx + dy*dy <= stroke_w*stroke_w:
                draw.text((x + dx, y + dy), config.text, font=font, fill=outline_color)

    # Vẽ chữ chính
    # Chuyển đổi mã màu hex sang tuple RGBA
    hex_color = config.color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    fill_color = rgb + (255,)
    
    draw.text((x, y), config.text, font=font, fill=fill_color)
    
    img.save(dest_path)
    return dest_path

# ==============================================================================
# 4. Trình Biên Tập Chính (Render Video Engine)
# ==============================================================================

class RenderProgressLogger:
    """Logger để theo dõi tiến độ render của MoviePy."""
    def __init__(self, callback: Callable[[int], None]):
        self.callback = callback
        self.total_frames = 1
        
    def __call__(self, **kwargs):
        # Trích xuất tiến độ từ thư viện moviepy/proglog
        pass
        
    def callback_wrapper(self, current_frame, total_frames):
        if total_frames > 0:
            progress = int((current_frame / total_frames) * 100)
            self.callback(progress)

async def render_video(
    blueprint: VideoBlueprint, 
    task_id: str, 
    progress_callback: Callable[[int], None]
) -> str:
    """Đọc VideoBlueprint và thực thi render video hoàn chỉnh."""
    project_temp_dir = os.path.join(settings.TEMP_DIR, task_id)
    os.makedirs(project_temp_dir, exist_ok=True)
    
    progress_callback(10) # Bắt đầu tiến trình
    
    # 1. Tải và chuẩn bị nhạc nền
    bgm_clip = None
    if blueprint.audio.background_music_url:
        try:
            logger.info("Đang tải nhạc nền...")
            bgm_path = await download_file(blueprint.audio.background_music_url, project_temp_dir)
            bgm_clip = AudioFileClip(bgm_path).volumex(blueprint.audio.bgm_volume)
        except Exception as e:
            logger.error(f"Không thể tải nhạc nền: {e}")

    progress_callback(20)

    # 2. Tạo giọng lồng tiếng AI (Voiceover)
    voiceover_clip = None
    if blueprint.audio.voiceover and blueprint.audio.voiceover.enabled and blueprint.audio.voiceover.text:
        try:
            logger.info("Đang tạo thuyết minh AI...")
            vo_filename = f"voiceover_{task_id}.mp3"
            vo_path = os.path.join(project_temp_dir, vo_filename)
            await generate_voiceover(
                text=blueprint.audio.voiceover.text,
                voice_id=blueprint.audio.voiceover.voice_id,
                dest_path=vo_path
            )
            voiceover_clip = AudioFileClip(vo_path)
        except Exception as e:
            logger.error(f"Không thể tạo giọng đọc thuyết minh: {e}")

    progress_callback(30)

    # 3. Tạo các phân cảnh (Timeline Clips)
    video_clips = []
    current_time = 0.0
    canvas_w = blueprint.canvas.width
    canvas_h = blueprint.canvas.height
    
    for i, item in enumerate(blueprint.timeline):
        logger.info(f"Đang xử lý phân cảnh {i+1}/{len(blueprint.timeline)}: {item.type}")
        
        # Tải tài nguyên
        local_path = await download_file(item.source_url, project_temp_dir)
        clip = None
        
        if item.type == "video":
            clip = VideoFileClip(local_path)
            
            # Cắt ngắn (trim)
            start = item.trim_start or 0.0
            end = item.trim_end or clip.duration
            clip = clip.subclip(start, end)
            
        elif item.type in ["image", "image_to_video"]:
            # Nếu là image_to_video và có API Runway thì gọi ở đây.
            # Với bản MVP hiện tại, ta fallback render ảnh tĩnh có thời lượng duration
            dur = item.duration or 4.0
            clip = ImageClip(local_path).set_duration(dur)
            
        if clip is None:
            continue
            
        # Resize và crop vừa vặn canvas (Thao tác Box-fit)
        # Giữ tỉ lệ khung hình (Aspect Ratio)
        clip_aspect = clip.w / clip.h
        canvas_aspect = canvas_w / canvas_h
        
        if clip_aspect > canvas_aspect:
            # Clip rộng hơn canvas -> scale theo chiều cao rồi crop chiều rộng
            new_h = canvas_h
            new_w = int(new_h * clip_aspect)
            clip = clip.resize(height=new_h)
            x_center = new_w / 2
            clip = clip.crop(x1=x_center - canvas_w/2, x2=x_center + canvas_w/2, y1=0, y2=canvas_h)
        else:
            # Clip cao hơn canvas -> scale theo chiều rộng rồi crop chiều cao
            new_w = canvas_w
            new_h = int(new_w / clip_aspect)
            clip = clip.resize(width=new_w)
            y_center = new_h / 2
            clip = clip.crop(x1=0, x2=canvas_w, y1=y_center - canvas_h/2, y2=y_center + canvas_h/2)

        # Áp dụng chuyển cảnh mượt mà
        if item.transition_out == "fade" and clip.duration:
            clip = clip.fadeout(0.5)

        # Chèn chữ (Text Overlay)
        if item.text_overlay and item.text_overlay.text:
            text_img_name = f"text_{i}_{uuid.uuid4().hex[:6]}.png"
            text_img_path = os.path.join(project_temp_dir, text_img_name)
            create_text_overlay_image(item.text_overlay, canvas_w, canvas_h, text_img_path)
            
            # Load tệp ảnh chữ vừa tạo thành clip overlay
            text_clip = ImageClip(text_img_path).set_duration(clip.duration)
            if item.text_overlay.start_time is not None:
                text_clip = text_clip.set_start(item.text_overlay.start_time)
            if item.text_overlay.duration is not None:
                text_clip = text_clip.set_duration(item.text_overlay.duration)
                
            # Trộn đè chữ lên video
            clip = CompositeVideoClip([clip, text_clip])

        video_clips.append(clip)
        current_time += clip.duration if clip.duration else 0

    progress_callback(50)

    if not video_clips:
        raise ValueError("Không có phân cảnh video hợp lệ nào được tạo ra.")

    # 4. Ghép nối các phân cảnh thành video duy nhất
    final_video = concatenate_videoclips(video_clips, method="compose")
    
    # 5. Phối âm thanh (BGM + Voiceover)
    audio_tracks = []
    
    if voiceover_clip:
        # Lồng thuyết minh bắt đầu từ đầu video
        audio_tracks.append(voiceover_clip.set_start(0))
        
    if bgm_clip:
        # Cắt nhạc nền khớp với thời lượng video
        bgm_clip = bgm_clip.set_duration(final_video.duration)
        audio_tracks.append(bgm_clip)
        
    if audio_tracks:
        final_audio = CompositeAudioClip(audio_tracks)
        # Giữ lại âm thanh gốc của các clip (nếu có) bằng cách trộn thêm
        if final_video.audio:
            final_audio = CompositeAudioClip([final_video.audio.volumex(0.6), final_audio])
        final_video = final_video.set_audio(final_audio)

    progress_callback(70)

    # 6. Render xuất bản file MP4
    output_filename = f"output_{task_id}.mp4"
    output_path = os.path.join(settings.TEMP_DIR, output_filename)
    
    logger.info(f"Đang render xuất video thành phẩm: {output_path}")
    
    # Thực hiện render thực tế
    final_video.write_videofile(
        output_path,
        fps=blueprint.canvas.fps,
        codec="libx264",
        audio_codec="aac",
        logger=None # Ẩn output rác của moviepy
    )
    
    # Giải phóng bộ nhớ tài nguyên
    final_video.close()
    for c in video_clips:
        c.close()
    if voiceover_clip:
        voiceover_clip.close()
    if bgm_clip:
        bgm_clip.close()

    progress_callback(100)
    
    return output_path
