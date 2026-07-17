from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ==============================================================================
# 1. Các Model API (Yêu cầu và phản hồi từ Client)
# ==============================================================================

class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Yêu cầu chỉnh sửa hoặc tạo video từ người dùng bằng ngôn ngữ tự nhiên")
    media_files: List[str] = Field(default=[], description="Danh sách URL hoặc đường dẫn file media thô đầu vào")
    aspect_ratio: str = Field("9:16", description="Tỉ lệ khung hình mong muốn (9:16, 16:9, 1:1)")
    voice_id: Optional[str] = Field("rachel", description="ID giọng đọc lồng tiếng AI mong muốn")

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, generating_blueprint, processing, rendering, completed, failed
    progress: int  # 0 đến 100
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

# ==============================================================================
# 2. Cấu trúc JSON Blueprint (Kịch bản biên tập do AI Agent tạo ra)
# ==============================================================================

class CanvasConfig(BaseModel):
    width: int = Field(1080, description="Chiều rộng video (pixel)")
    height: int = Field(1920, description="Chiều cao video (pixel)")
    fps: int = Field(30, description="Khung hình trên giây")

class VoiceoverConfig(BaseModel):
    enabled: bool = Field(False, description="Có tạo thuyết minh giọng nói AI không")
    text: Optional[str] = Field(None, description="Đoạn văn bản thuyết minh")
    voice_id: Optional[str] = Field("rachel", description="Mã giọng đọc")

class AudioConfig(BaseModel):
    background_music_url: Optional[str] = Field(None, description="Đường dẫn nhạc nền")
    bgm_volume: float = Field(0.15, description="Âm lượng nhạc nền (0.0 đến 1.0)")
    voiceover: Optional[VoiceoverConfig] = Field(None, description="Cấu hình thuyết minh")

class TextOverlayConfig(BaseModel):
    text: str = Field(..., description="Nội dung chữ chèn trên clip")
    font_size: int = Field(40, description="Kích thước chữ")
    color: str = Field("#FFFFFF", description="Mã màu chữ (HEX)")
    position: str = Field("center", description="Vị trí hiển thị (top, center, bottom)")
    start_time: Optional[float] = Field(None, description="Thời điểm hiển thị chữ trong clip (giây)")
    duration: Optional[float] = Field(None, description="Thời lượng hiển thị chữ (giây)")

class TimelineClip(BaseModel):
    type: str = Field(..., description="Loại clip: video, image, image_to_video, text_only")
    source_url: str = Field(..., description="Đường dẫn file gốc hoặc ảnh gốc")
    trim_start: Optional[float] = Field(0.0, description="Thời gian bắt đầu cắt (chỉ cho video)")
    trim_end: Optional[float] = Field(None, description="Thời gian kết thúc cắt (chỉ cho video)")
    duration: Optional[float] = Field(None, description="Thời lượng hiển thị của clip trong video (giây)")
    ai_prompt: Optional[str] = Field(None, description="Prompt yêu cầu sinh video AI từ ảnh này (nếu có)")
    text_overlay: Optional[TextOverlayConfig] = Field(None, description="Chữ chèn lên clip")
    transition_out: Optional[str] = Field("fade", description="Hiệu ứng chuyển cảnh ở cuối clip (fade, crossfade, none)")

class VideoBlueprint(BaseModel):
    project_name: str = Field(..., description="Tên dự án biên tập video")
    canvas: CanvasConfig = Field(default_factory=CanvasConfig, description="Cấu hình canvas video")
    audio: AudioConfig = Field(..., description="Cấu hình âm thanh & lồng tiếng")
    timeline: List[TimelineClip] = Field(..., description="Danh sách các phân đoạn video dựng trên dòng thời gian")
