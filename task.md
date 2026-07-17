# Kế hoạch Thực hiện: Dự Án Tự Động Hóa Video AI

Dưới đây là danh sách các nhiệm vụ cụ thể để xây dựng hệ thống:

- [x] Khởi tạo thư mục dự án và thiết lập môi trường
    - [x] Tạo cấu trúc thư mục dự án tại `C:\Users\ASUS\.gemini\antigravity-ide\scratch\ai-video-automation`
    - [x] Tạo file `.gitignore` và khởi tạo Git repository
    - [x] Khởi tạo file cấu hình môi trường `.env.example`
- [x] Xây dựng Backend API (FastAPI)
    - [x] Thiết lập khung dự án FastAPI cơ bản
    - [x] Cấu hình API endpoints cho việc nhận prompt và file media
    - [x] Setup hàng đợi (Queue) giả lập hoặc Redis/Celery cho xử lý bất đồng bộ
- [x] Xây dựng AI Agent (Gemini API Integration)
    - [x] Cấu hình SDK Gemini
    - [x] Thiết kế Prompt System hướng dẫn Gemini xuất JSON Blueprint chuẩn
    - [x] Viết module chuyển đổi Prompt tự nhiên của user thành JSON Blueprint
- [x] Xây dựng Media Processing Engine (Python Worker)
    - [x] Viết module tải và quản lý file media tạm thời (Temporary Storage)
    - [x] Viết trình xử lý JSON Blueprint dùng MoviePy (cắt, ghép, chèn nhạc, lồng tiếng)
    - [x] Tích hợp API chuyển giọng nói (OpenAI TTS / ElevenLabs) và tạo phụ đề (Whisper)
- [x] Xây dựng Frontend UI (Next.js)
    - [x] Khởi tạo dự án Next.js bằng npx
    - [x] Xây dựng trang Dashboard quản lý dự án video
    - [x] Xây dựng trang Upload media & nhập prompt với giao diện premium
    - [x] Tích hợp cấu hình White-label dễ tùy biến thương hiệu
- [x] Đóng gói & Tài liệu hướng dẫn
    - [x] Viết Dockerfile cho backend và worker
    - [x] Viết docker-compose.yml kết nối các dịch vụ
    - [x] Hoàn thiện file README.md hướng dẫn triển khai chi tiết cho khách hàng
