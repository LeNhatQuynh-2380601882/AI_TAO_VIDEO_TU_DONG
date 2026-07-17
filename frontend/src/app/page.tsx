"use client";

import React, { useState, useEffect, useRef } from "react";
import { BRAND_CONFIG } from "../config/brand";

interface MediaFile {
  url: string;
  filename: string;
  original_name: string;
}

interface TaskStatus {
  task_id: string;
  status: string;
  progress: number;
  output_url: Optional<string>;
  error_message: Optional<string>;
  created_at: string;
  updated_at: string;
}

type Optional<T> = T | null;

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [voiceId, setVoiceId] = useState("rachel");
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [uploading, setUploading] = useState(false);
  
  // Trạng thái Render Video
  const [generating, setGenerating] = useState(false);
  const [taskId, setTaskId] = useState<Optional<string>>(null);
  const [taskStatus, setTaskStatus] = useState<Optional<TaskStatus>>(null);
  const [errorMsg, setErrorMsg] = useState<Optional<string>>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<any>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Dọn dẹp polling khi unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Xử lý tải file lên server
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setErrorMsg(null);

    try {
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append("file", files[i]);

        const response = await fetch(`${API_BASE_URL}/api/video/upload`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Không thể tải tệp lên server. Vui lòng kiểm tra định dạng.");
        }

        const data = await response.json();
        setMediaFiles((prev) => [...prev, data]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Đã xảy ra lỗi khi tải file lên.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Xóa file khỏi danh sách đã tải
  const removeMediaFile = (index: number) => {
    setMediaFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Kích hoạt sinh video
  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setErrorMsg("Vui lòng nhập câu lệnh yêu cầu biên tập video.");
      return;
    }
    if (mediaFiles.length === 0) {
      setErrorMsg("Vui lòng tải lên ít nhất một hình ảnh hoặc video thô.");
      return;
    }

    setGenerating(true);
    setTaskId(null);
    setTaskStatus(null);
    setErrorMsg(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/video/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          media_files: mediaFiles.map((f) => f.url),
          aspect_ratio: aspectRatio,
          voice_id: voiceId,
        }),
      });

      if (!response.ok) {
        throw new Error("Không thể gửi yêu cầu tạo video.");
      }

      const data = await response.json();
      setTaskId(data.task_id);
      
      // Bắt đầu Polling trạng thái
      startPolling(data.task_id);
    } catch (err: any) {
      setErrorMsg(err.message || "Không thể khởi chạy tiến trình sinh video.");
      setGenerating(false);
    }
  };

  // Khởi động vòng lặp kiểm tra tiến trình
  const startPolling = (tid: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/video/status/${tid}`);
        if (!response.ok) {
          throw new Error("Lỗi khi kết nối lấy tiến độ.");
        }
        
        const data: TaskStatus = await response.json();
        setTaskStatus(data);

        if (data.status === "completed" || data.status === "failed") {
          clearInterval(pollIntervalRef.current);
          setGenerating(false);
          if (data.status === "failed") {
            setErrorMsg(data.error_message || "Quá trình biên tập video bị lỗi.");
          }
        }
      } catch (err: any) {
        console.error("Lỗi polling:", err);
      }
    }, 2000);
  };

  // Lấy text trạng thái thân thiện cho người dùng
  const getStatusText = (status: string) => {
    switch (status) {
      case "pending":
        return "Đang chờ xếp hàng xử lý...";
      case "generating_blueprint":
        return "AI Agent đang lập kịch bản dựng video (JSON Blueprint)...";
      case "rendering":
        return "Đang thực thi MoviePy: Cắt ghép phân cảnh, trộn nhạc & render...";
      case "completed":
        return "Hoàn thành dựng video!";
      case "failed":
        return "Biên tập thất bại.";
      default:
        return "Đang xử lý...";
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              AI
            </div>
            <div>
              <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                {BRAND_CONFIG.name}
              </span>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">White-label Edition</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-400 flex items-center gap-1.5 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Core API: Ready
            </span>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
        
        {/* Left Column: Input Form */}
        <div className="flex-1 flex flex-col gap-6">
          <div className="bg-slate-900/40 border border-slate-950/60 rounded-3xl p-6 backdrop-blur-xl shadow-xl flex flex-col gap-5">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-white">Yêu Cầu Biên Tập Video</h2>
              <p className="text-slate-400 text-sm mt-1">{BRAND_CONFIG.tagline}</p>
            </div>

            {/* Prompt Input */}
            <div className="flex flex-col gap-2">
              <label htmlFor="prompt-input" className="text-sm font-semibold text-slate-300">Nhập mô tả yêu cầu của bạn:</label>
              <textarea
                id="prompt-input"
                className="w-full h-28 bg-slate-950/80 border border-slate-850 rounded-2xl p-4 text-slate-100 placeholder-slate-650 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm resize-none transition-all"
                placeholder="Ví dụ: Cắt video gốc còn 5 giây đầu, chèn ảnh sản phẩm, lồng giọng đọc thuyết minh giới thiệu sản phẩm thật lôi cuốn và ghép nhạc nền công nghệ..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </div>

            {/* Grid options */}
            <div className="grid grid-cols-2 gap-4">
              {/* Aspect Ratio */}
              <div className="flex flex-col gap-2">
                <label htmlFor="aspect-ratio-select" className="text-sm font-semibold text-slate-300">Tỉ lệ khung hình (Canvas):</label>
                <select
                  id="aspect-ratio-select"
                  className="bg-slate-950/80 border border-slate-850 rounded-xl p-3 text-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(e.target.value)}
                >
                  <option value="9:16">Dọc (9:16) - TikTok/Reels</option>
                  <option value="16:9">Ngang (16:9) - YouTube</option>
                  <option value="1:1">Vuông (1:1) - Instagram</option>
                </select>
              </div>

              {/* Voice ID */}
              <div className="flex flex-col gap-2">
                <label htmlFor="voice-select" className="text-sm font-semibold text-slate-300">Giọng đọc lồng tiếng AI:</label>
                <select
                  id="voice-select"
                  className="bg-slate-950/80 border border-slate-850 rounded-xl p-3 text-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                >
                  <option value="rachel">Rachel (Nữ ấm áp)</option>
                  <option value="alloy">Alloy (Nam năng động)</option>
                  <option value="echo">Echo (Trung tính nhẹ nhàng)</option>
                  <option value="onyx">Onyx (Nam trầm ấm)</option>
                </select>
              </div>
            </div>

            {/* Media Upload Area */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-slate-300">Tải lên hình ảnh hoặc video thô:</label>
              
              <div 
                className="border-2 border-dashed border-slate-800 hover:border-indigo-500/50 bg-slate-950/40 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all gap-2"
                onClick={() => fileInputRef.current?.click()}
              >
                <svg className="w-8 h-8 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path>
                </svg>
                <span className="text-xs text-slate-400 font-medium">Bấm vào để tải lên ảnh hoặc video</span>
                <span className="text-[10px] text-slate-650">Hỗ trợ MP4, MOV, JPG, PNG, WEBP</span>
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  multiple
                  onChange={handleFileUpload}
                  accept="video/*,image/*"
                />
              </div>

              {/* Upload progress or files display */}
              {uploading && (
                <div className="text-xs text-indigo-400 flex items-center gap-2 mt-2">
                  <span className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></span>
                  Đang tải file lên máy chủ...
                </div>
              )}

              {/* List of uploaded files */}
              {mediaFiles.length > 0 && (
                <div className="flex flex-col gap-2 mt-3">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">File đã chuẩn bị ({mediaFiles.length}):</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
                    {mediaFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-slate-950/80 border border-slate-850 rounded-xl p-2.5 text-xs">
                        <div className="flex items-center gap-2 truncate pr-2">
                          <span className="text-indigo-400 font-semibold">#{idx + 1}</span>
                          <span className="truncate text-slate-300 font-medium" title={file.original_name}>
                            {file.original_name}
                          </span>
                        </div>
                        <button 
                          onClick={() => removeMediaFile(idx)}
                          className="text-slate-500 hover:text-red-400 p-1 rounded-lg hover:bg-slate-900 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Error Message */}
            {errorMsg && (
              <div className="bg-red-950/40 border border-red-900/60 rounded-xl p-4 text-xs text-red-300 flex items-start gap-2.5">
                <svg className="w-4 h-4 text-red-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              onClick={handleGenerate}
              disabled={generating || uploading}
              className={`w-full py-4 rounded-2xl text-sm font-semibold flex items-center justify-center gap-2.5 transition-all shadow-lg ${
                generating || uploading
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-indigo-500 to-pink-500 hover:from-indigo-600 hover:to-pink-600 text-white shadow-indigo-500/10 hover:shadow-indigo-500/20 active:scale-[0.98]"
              }`}
            >
              {generating ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Đang Tạo Video...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  Bắt Đầu Biên Tập Video AI
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Processing Screen / Video Output Preview */}
        <div className="w-full lg:w-[450px] flex flex-col gap-6">
          <div className="bg-slate-900/40 border border-slate-950/60 rounded-3xl p-6 backdrop-blur-xl shadow-xl flex-1 flex flex-col justify-center min-h-[400px]">
            
            {/* 1. Screen: IDLE State */}
            {!taskId && !generating && (
              <div className="text-center py-10 flex flex-col items-center justify-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-slate-950 flex items-center justify-center text-slate-500 border border-slate-850">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Xem Trước Thành Phẩm</h3>
                  <p className="text-xs text-slate-500 mt-1 max-w-[280px] mx-auto">Tải lên media và yêu cầu AI biên tập để xem trước video xuất ra tại đây.</p>
                </div>
              </div>
            )}

            {/* 2. Screen: PROCESSING State */}
            {generating && taskStatus && (
              <div className="flex flex-col gap-6 py-6">
                <div>
                  <h3 className="font-bold text-white text-base">Trạng Thái Xử Lý</h3>
                  <p className="text-xs text-indigo-400 mt-1 flex items-center gap-1.5 font-medium animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                    Hệ thống đang làm việc
                  </p>
                </div>

                {/* Main Progress Indicator */}
                <div className="flex flex-col items-center justify-center py-6 gap-3">
                  <div className="relative w-28 h-28 flex items-center justify-center">
                    {/* Ring background */}
                    <svg className="absolute w-full h-full transform -rotate-90">
                      <circle cx="56" cy="56" r="48" stroke="#1e293b" strokeWidth="6" fill="transparent" />
                      <circle 
                        cx="56" 
                        cy="56" 
                        r="48" 
                        stroke="url(#progressGradient)" 
                        strokeWidth="6" 
                        fill="transparent" 
                        strokeDasharray={2 * Math.PI * 48}
                        strokeDashoffset={2 * Math.PI * 48 * (1 - taskStatus.progress / 100)}
                        strokeLinecap="round"
                        className="transition-all duration-300"
                      />
                      <defs>
                        <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#6366f1" />
                          <stop offset="100%" stopColor="#ec4899" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <span className="text-2xl font-black text-white">{taskStatus.progress}%</span>
                  </div>
                  <span className="text-xs font-semibold text-slate-400 tracking-wider">TIẾN ĐỘ RENDER</span>
                </div>

                {/* Sub status info */}
                <div className="bg-slate-950/60 border border-slate-850 rounded-2xl p-4 flex flex-col gap-3">
                  <div className="flex items-center justify-between text-xs border-b border-slate-900 pb-2">
                    <span className="text-slate-500 font-medium">Task ID:</span>
                    <span className="text-slate-300 font-mono select-all bg-slate-900 px-2 py-0.5 rounded">{taskStatus.task_id.substring(0, 8)}...</span>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Giai đoạn hiện tại</span>
                    <span className="text-xs text-indigo-300 font-medium leading-relaxed">
                      {getStatusText(taskStatus.status)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* 3. Screen: COMPLETED Output Preview State */}
            {taskStatus && taskStatus.status === "completed" && taskStatus.output_url && (
              <div className="flex flex-col gap-5 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-white text-base">Video Thành Phẩm</h3>
                    <p className="text-[10px] text-emerald-400 mt-0.5 flex items-center gap-1 font-semibold">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      Render hoàn tất
                    </p>
                  </div>
                  <a
                    href={`${API_BASE_URL}${taskStatus.output_url}`}
                    download={`video_${taskStatus.task_id}.mp4`}
                    className="p-2 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 rounded-xl text-indigo-400 transition-colors text-xs font-semibold flex items-center gap-1.5"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                    </svg>
                    Tải về
                  </a>
                </div>

                {/* Responsive Video container based on ratio */}
                <div className="bg-slate-950 rounded-2xl overflow-hidden border border-slate-850 flex items-center justify-center bg-black/60 shadow-inner">
                  <video
                    src={`${API_BASE_URL}${taskStatus.output_url}`}
                    controls
                    className={`max-w-full max-h-[450px] object-contain ${
                      aspectRatio === "9:16" 
                        ? "aspect-[9/16] w-[253px]" 
                        : aspectRatio === "1:1" 
                        ? "aspect-square w-[350px]" 
                        : "aspect-[16/9] w-full"
                    }`}
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => {
                      setTaskId(null);
                      setTaskStatus(null);
                    }}
                    className="w-full py-3 bg-slate-950 border border-slate-850 hover:bg-slate-900 rounded-xl text-xs font-semibold text-slate-400 transition-colors"
                  >
                    Tạo Video Mới
                  </button>
                </div>
              </div>
            )}

            {/* 4. Screen: FAILED Output State */}
            {taskStatus && taskStatus.status === "failed" && (
              <div className="text-center py-8 flex flex-col items-center justify-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-red-950/40 border border-red-900/40 flex items-center justify-center text-red-400">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Lỗi Biên Tập Video</h3>
                  <p className="text-xs text-slate-500 mt-2.5 max-w-[280px] leading-relaxed">
                    {taskStatus.error_message || "Đã xảy ra sự cố trong quá trình render video."}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setTaskId(null);
                    setTaskStatus(null);
                  }}
                  className="mt-2 px-6 py-2.5 bg-slate-950 hover:bg-slate-900 border border-slate-850 rounded-xl text-xs font-semibold text-slate-400 transition-colors"
                >
                  Quay Lại
                </button>
              </div>
            )}

          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900/60 bg-slate-950/40 py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-slate-550 font-medium">
          <span>&copy; 2026 {BRAND_CONFIG.name}. Tất cả quyền lợi được bảo lưu.</span>
          <div className="flex gap-4">
            <a href={`mailto:${BRAND_CONFIG.supportEmail}`} className="hover:text-indigo-400 transition-colors">
              Liên hệ hỗ trợ: {BRAND_CONFIG.supportEmail}
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
