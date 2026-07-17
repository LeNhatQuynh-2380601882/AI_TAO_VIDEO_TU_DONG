import json
import logging
from typing import List, Optional
import google.generativeai as genai
from app.config import settings
from app.models import VideoBlueprint, TimelineClip

logger = logging.getLogger(__name__)

# Cấu hình API Gemini nếu key tồn tại
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY chưa được cấu hình. Vui lòng thiết lập biến môi trường này.")

SYSTEM_INSTRUCTION = """
Bạn là một Biên tập viên Video AI chuyên nghiệp (AI Video Director). Nhiệm vụ của bạn là nhận:
1. Danh sách đường dẫn/URL của các file media đầu vào (ảnh, video) của người dùng.
2. Câu lệnh yêu cầu biên tập (Prompt) dạng ngôn ngữ tự nhiên của người dùng.
3. Tỉ lệ khung hình (Aspect Ratio) mong muốn.

Sau đó, bạn cần phân tích các thông tin trên và tạo ra một kịch bản biên tập video dạng JSON (JSON Blueprint) để chuyển cho Worker thực thi cắt ghép.

Các quy tắc biên tập bạn phải tuân thủ:
1. Tỉ lệ canvas:
   - "9:16": Rộng 1080, Cao 1920 (Thích hợp cho TikTok, Shorts, Reels)
   - "16:9": Rộng 1920, Cao 1080 (Thích hợp cho YouTube)
   - "1:1": Rộng 1080, Cao 1080 (Thích hợp cho Instagram)
2. Phân cảnh trên Timeline:
   - Sắp xếp các clip theo thứ tự logic hợp lý dựa trên ý đồ của người dùng.
   - Với ảnh: Đặt type là 'image'. Thời lượng mặc định cho ảnh là 3 đến 5 giây. Nếu người dùng muốn tạo chuyển động từ ảnh bằng AI, đặt type là 'image_to_video' và viết mô tả chuyển động trong 'ai_prompt' (Ví dụ: "slow zoom in on the product", "cinematic camera panning right").
   - Với video: Xác định 'trim_start' và 'trim_end' (giây) nếu người dùng yêu cầu cắt bớt hoặc để lấy phần hay nhất của video.
   - Thêm tiêu đề, phụ đề vào trường 'text_overlay' cho từng phân cảnh nếu người dùng yêu cầu chèn chữ. Đặt text ngắn gọn và chọn vị trí hợp lý ('top', 'center', 'bottom').
3. Âm thanh & Lồng tiếng:
   - Lựa chọn nhạc nền phù hợp với phong cách (Ví dụ: vui tươi, công nghệ, buồn, hùng tráng) và cung cấp URL nhạc nền. Bạn có thể chọn nhạc nền từ danh sách nhạc mẫu sau nếu phù hợp:
     * Nhạc công nghệ: https://pixabay.com/music/download/technology-corporate-143640/
     * Nhạc vui tươi: https://pixabay.com/music/download/happy-acoustic-guitar-158220/
     * Nhạc du lịch: https://pixabay.com/music/download/ambient-travel-vlog-12345/
   - Nếu người dùng muốn thuyết minh (lồng tiếng) hoặc nếu video cần một lời dẫn dắt, hãy kích hoạt 'voiceover.enabled = true' và viết nội dung kịch bản thuyết minh vào 'voiceover.text'. Kịch bản này phải được chia nhỏ khớp với thứ tự các cảnh trong timeline.
"""

async def generate_blueprint(
    prompt: str,
    media_files: List[str],
    aspect_ratio: str = "9:16",
    voice_id: str = "rachel"
) -> VideoBlueprint:
    """
    Sử dụng Gemini API để phân tích yêu cầu của người dùng và tạo ra JSON Blueprint
    chỉ định quy trình cắt ghép video.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("Chưa cấu hình GEMINI_API_KEY. Vui lòng cấu hình trong file .env.")

    # Xác định kích thước khung hình
    width, height = 1080, 1920
    if aspect_ratio == "16:9":
        width, height = 1920, 1080
    elif aspect_ratio == "1:1":
        width, height = 1080, 1080

    user_message = f"""
Hãy tạo kịch bản dựng video dựa trên các dữ liệu sau:
- Câu lệnh yêu cầu của người dùng: "{prompt}"
- Danh sách file media thô tải lên: {media_files}
- Tỉ lệ khung hình: {aspect_ratio} (đã định cấu hình Canvas {width}x{height})
- Giọng nói lồng tiếng AI mong muốn: {voice_id}

Hãy phân tích kỹ các file media đầu vào để sắp xếp chúng hợp lý nhất theo đúng prompt yêu cầu.
"""

    try:
        # Sử dụng model gemini-1.5-flash để phản hồi nhanh và hỗ trợ JSON Schema tốt
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Gọi API bắt buộc trả về kết quả tuân thủ schema của VideoBlueprint
        response = model.generate_content(
            user_message,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=VideoBlueprint,
                temperature=0.2, # Giảm sáng tạo để trả về JSON chuẩn xác hơn
            ),
        )
        
        # Parse kết quả dạng string sang Pydantic Model
        blueprint_json = json.loads(response.text)
        
        # Fix một số giá trị mặc định cho an toàn
        blueprint_json["canvas"]["width"] = width
        blueprint_json["canvas"]["height"] = height
        
        return VideoBlueprint(**blueprint_json)
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo blueprint từ Gemini: {e}")
        # Phương án dự phòng (fallback) tự động sinh một Blueprint tối giản nếu AI bị lỗi
        return create_fallback_blueprint(prompt, media_files, width, height, voice_id)

def create_fallback_blueprint(
    prompt: str,
    media_files: List[str],
    width: int,
    height: int,
    voice_id: str
) -> VideoBlueprint:
    """
    Tạo ra một kịch bản video dự phòng cơ bản trong trường hợp API AI gặp sự cố.
    """
    timeline = []
    for file in media_files:
        is_video = file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
        timeline.append(
            TimelineClip(
                type="video" if is_video else "image",
                source_url=file,
                duration=5.0 if not is_video else None,
                transition_out="fade"
            )
        )
    
    return VideoBlueprint(
        project_name="fallback_project",
        canvas={"width": width, "height": height, "fps": 30},
        audio={
            "background_music_url": "https://pixabay.com/music/download/happy-acoustic-guitar-158220/",
            "bgm_volume": 0.2,
            "voiceover": {
                "enabled": True,
                "text": f"Dưới đây là các hình ảnh bạn yêu cầu xử lý từ câu lệnh: {prompt}",
                "voice_id": voice_id
            }
        },
        timeline=timeline
    )
