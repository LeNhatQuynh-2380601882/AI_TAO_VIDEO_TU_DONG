# Sử dụng Node.js base image chính thức
FROM node:18-alpine AS builder

WORKDIR /app

# Sao chép package.json và lock files để cài đặt thư viện
COPY package.json package-lock.json* ./
RUN npm ci

# Sao chép toàn bộ mã nguồn
COPY . .

# Thiết lập biến môi trường ở thời điểm build
# Next.js sẽ nhúng cứng biến này vào frontend lúc compile
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build dự án Next.js
RUN npm run build

# Giai đoạn production chạy ứng dụng gọn nhẹ
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy các file build cần thiết từ builder
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/src ./src

EXPOSE 3000

# Khởi chạy Next.js Server
CMD ["npm", "start"]
