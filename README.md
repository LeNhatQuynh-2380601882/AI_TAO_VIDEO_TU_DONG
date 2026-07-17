# Hệ Thống Tự Động Hóa Biên Tập Video Bằng AI (AI Video Automator)

Dự án này là một bộ mã nguồn hoàn chỉnh (Monorepo) cho phép tự động hóa việc tạo và cắt ghép video bằng trí tuệ nhân tạo. 

Người dùng chỉ cần tải lên hình ảnh/video thô và nhập câu lệnh yêu cầu biên tập (Prompt) bằng ngôn ngữ tự nhiên (ví dụ: *"Cắt clip còn 5s đầu, ghép thêm ảnh sản phẩm, thuyết minh bằng giọng nói AI và thêm nhạc nền công nghệ..."*). AI Agent (Gemini) sẽ tự động phân tích và tạo kịch bản biên tập (JSON Blueprint) để công cụ render (MoviePy + FFmpeg) biên tập thành video hoàn chỉnh.

Sản phẩm được thiết kế dạng **White-label** để các lập trình viên có thể dễ dàng tùy biến thương hiệu và deploy/bán cho nhiều khách hàng khác nhau.

---

## 📁 Cấu Trúc Dự Án

```
/ai-video-automation
├── /backend           # API Gateway FastAPI (Python) & Task Manager
│   ├── /app
│   │   ├── /routes    # Các API endpoints (upload file, sinh video, status)
│   │   ├── /services  # AI Agent (Gemini) & Video Engine (MoviePy/Pillow)
│   │   ├── config.py  # Đọc cấu hình từ file .env
│   │   └── models.py  # Pydantic schemas cho API và Blueprint
│   └── Dockerfile     # Dockerfile tối ưu cho Python & FFmpeg
├── /frontend          # Dashboard UI Next.js (React) + Tailwind
│   ├── /src/app       # Các trang và giao diện
│   ├── /src/config    # brand.ts (Cấu hình White-label thương hiệu)
│   └── Dockerfile     # Dockerfile build multi-stage cho Next.js
├── docker-compose.yml # Khởi chạy toàn bộ hệ thống bằng Docker
├── .env.example       # Mẫu cấu hình biến môi trường
└── README.md          # Hướng dẫn này
```

---

## 🛠️ Thiết Lập Cục Bộ (Local Development)

### 1. Chuẩn bị biến môi trường
Sao chép file `.env.example` thành `.env` ở thư mục gốc:
```bash
cp .env.example .env
```
Mở `.env` ra và điền các API keys của bạn:
- `GEMINI_API_KEY`: Bắt buộc để chạy AI Agent biên tập video. (Lấy miễn phí hoặc trả phí tại Google AI Studio).
- `OPENAI_API_KEY` hoặc `ELEVENLABS_API_KEY`: Dùng để lồng tiếng AI cao cấp (Nếu không có, hệ thống sẽ tự động fallback sang công cụ lồng tiếng `gTTS` hoàn toàn miễn phí).

### 2. Chạy Backend (FastAPI)
1. Di chuyển vào thư mục backend và tạo môi trường ảo Python:
   ```bash
   cd backend
   python -m venv venv
   # Kích hoạt trên Windows:
   .\venv\Scripts\activate
   # Kích hoạt trên macOS/Linux:
   source venv/bin/activate
   ```
2. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
3. Khởi chạy API Server:
   ```bash
   python app/main.py
   ```
   Server backend sẽ chạy tại: `http://localhost:8000`. Bạn có thể truy cập `http://localhost:8000/docs` để xem tài liệu Swagger API.

### 3. Chạy Frontend (Next.js)
1. Di chuyển vào thư mục frontend:
   ```bash
   cd frontend
   ```
2. Cài đặt dependencies:
   ```bash
   npm install
   ```
3. Khởi chạy server phát triển:
   ```bash
   npm run dev
   ```
   Frontend Dashboard sẽ chạy tại: `http://localhost:3000`.

---

## 🏷️ Chiến Lược White-label & Bán Cho Khách Hàng

Dự án này giúp bạn dễ dàng đóng gói thương hiệu và bán cho nhiều khách hàng bằng Git:

### 1. Quản lý nhánh trên Git
- Nhánh `main` là nhánh cốt lõi (Core Product). Tất cả nâng cấp AI và vá lỗi hệ thống sẽ được thực hiện trên nhánh này.
- Nhánh `client/<ten-khach-hang>`: Mỗi khi bán cho một khách hàng mới, hãy checkout một nhánh mới từ `main`:
  ```bash
  git checkout -b client/khach-hang-a
  ```

### 2. Thay đổi nhận diện thương hiệu
Bạn chỉ cần thay đổi các thông số tại tệp cấu hình tập trung để đổi giao diện:
- Giao diện Frontend: Thay đổi trong tệp `frontend/src/config/brand.ts` để cập nhật tên ứng dụng, logo, slogan và email hỗ trợ.
- Tên dịch vụ Backend: Cập nhật biến môi trường `BRAND_NAME` trong file `.env`.
- Tùy biến mã màu thương hiệu: Sửa các biến màu CSS/Tailwind trong cấu hình của khách hàng.

### 3. Cập nhật mã nguồn lõi
Khi bạn phát triển tính năng mới ở nhánh `main`, bạn có thể cập nhật cho các khách hàng cũ bằng cách merge code:
```bash
git checkout client/khach-hang-a
git merge main
# Xử lý các conflict nhỏ nếu có (thường chỉ ở phần cấu hình brand)
```

---

## 🐳 Triển Khai Bằng Docker (Dành Cho Máy Chủ/VPS Khách Hàng)

Khi bàn giao dự án hoặc deploy lên VPS Ubuntu của khách hàng:

1. Đảm bảo máy chủ đã cài đặt `Docker` và `Docker Compose`.
2. Tạo file `.env` chứa API keys và cấu hình của khách hàng trên VPS.
3. Chạy lệnh khởi tạo và xây dựng toàn bộ container dưới nền:
   ```bash
   docker-compose up -d --build
   ```
4. Kiểm tra xem các cổng `3000` (Frontend) và `8000` (Backend) đã mở trên firewall của VPS. Khách hàng của bạn có thể truy cập trực tiếp qua IP của VPS hoặc cấu hình tên miền qua Nginx Reverse Proxy.
