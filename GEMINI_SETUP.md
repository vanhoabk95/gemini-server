# Hướng dẫn sử dụng Gemini API Proxy

## Tổng quan

Tính năng Gemini API Proxy cho phép các máy client không có internet truy cập Google Generative AI API thông qua proxy server. Server sẽ chứa API key và cấu hình model, trong khi client chỉ cần gửi request với dummy credentials.

### Lợi ích
- ✅ Bảo mật API key tập trung tại server
- ✅ Client không cần internet trực tiếp
- ✅ Tự động thay thế model name theo cấu hình server
- ✅ Chạy chung với HTTP/HTTPS proxy trên cùng port 80

## Cài đặt Server (Máy có internet)

### Bước 1: Cài đặt dependencies

```bash
# Sử dụng pip
pip install httpx

# Hoặc sử dụng uv (nếu đang dùng)
uv pip install httpx
```

### Bước 2: Lấy Google API Key

1. Truy cập [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Đăng nhập với tài khoản Google
3. Tạo API key mới
4. Copy API key

### Bước 3: Cấu hình Gemini Proxy

Có 2 cách cấu hình:

#### Cách 1: Sử dụng file config (Khuyến nghị)

```bash
# Copy file mẫu
copy gemini_config.json.example gemini_config.json

# Sửa file gemini_config.json
notepad gemini_config.json
```

Nội dung file `gemini_config.json`:

```json
{
  "enabled": true,
  "google_api_key": "AIzaSyD...",
  "model": "gemini-1.5-flash",
  "api_base": "https://generativelanguage.googleapis.com"
}
```

**Các tham số:**
- `enabled`: `true` để bật tính năng, `false` để tắt
- `google_api_key`: API key từ Google AI Studio
- `model`: Model sẽ được dùng (gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash-exp, v.v.)
- `api_base`: URL gốc của Google API (thường không cần thay đổi)

#### Cách 2: Sử dụng Environment Variables

```bash
# Windows CMD
set GOOGLE_API_KEY=AIzaSyD...
set GEMINI_MODEL=gemini-1.5-flash
set GEMINI_ENABLED=true

# Windows PowerShell
$env:GOOGLE_API_KEY="AIzaSyD..."
$env:GEMINI_MODEL="gemini-1.5-flash"
$env:GEMINI_ENABLED="true"
```

### Bước 4: Khởi động Server

Server sẽ tự động load cấu hình Gemini khi khởi động.

```bash
# Chạy thông thường
python main.py

# Hoặc sử dụng batch file
proxy_server_admin.bat

# Hoặc chạy như Windows Service (xem SERVICE_README.md)
```

Server sẽ lắng nghe trên port 80 và xử lý cả:
- HTTP/HTTPS proxy requests (các path thông thường)
- Gemini API requests (path bắt đầu với `/v1beta/`)

### Kiểm tra trạng thái

Khi server khởi động, kiểm tra log để xác nhận Gemini proxy đã được bật:

```
Gemini Proxy Config:
  Enabled: True
  Model: gemini-1.5-flash
  API Base: https://generativelanguage.googleapis.com
  API Key: ***xyz123
```

## Cài đặt Client (Máy không có internet)

### Bước 1: Cài đặt LangChain Google GenAI

```bash
pip install langchain-google-genai
```

### Bước 2: Cấu hình client để sử dụng proxy

```python
from langchain_google_genai import ChatGoogleGenerativeAI

# Cấu hình
PROXY_HOST = "192.168.1.100"  # IP của máy server
PROXY_PORT = 80               # Port của proxy server

# Khởi tạo LLM
llm = ChatGoogleGenerativeAI(
    model="any-name-works",  # Tên gì cũng được, server sẽ thay thế
    temperature=0,
    api_key="dummy-key",     # API key dummy, server có key thật
    client_options={"api_endpoint": f"http://{PROXY_HOST}:{PROXY_PORT}"}
)

# Sử dụng
response = llm.invoke("Xin chào! Bạn là ai?")
print(response.content)
```

### Bước 3: Chạy client code

```bash
python your_client_script.py
```

## Ví dụ sử dụng

### Example 1: Chat đơn giản

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="dummy",
    api_key="dummy",
    client_options={"api_endpoint": "http://192.168.1.100:80"}
)

response = llm.invoke("Giải thích về Python trong 2 câu")
print(response.content)
```

### Example 2: Streaming response

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="dummy",
    api_key="dummy",
    client_options={"api_endpoint": "http://192.168.1.100:80"}
)

for chunk in llm.stream("Kể một câu chuyện ngắn"):
    print(chunk.content, end="", flush=True)
```

### Example 3: Sử dụng với LangChain chains

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

llm = ChatGoogleGenerativeAI(
    model="dummy",
    api_key="dummy",
    client_options={"api_endpoint": "http://192.168.1.100:80"}
)

prompt = ChatPromptTemplate.from_template("Dịch sang tiếng Anh: {text}")
chain = prompt | llm | StrOutputParser()

result = chain.invoke({"text": "Xin chào thế giới"})
print(result)
```

## Troubleshooting

### Server không nhận Gemini requests

**Kiểm tra:**
1. File `gemini_config.json` có tồn tại không?
2. `enabled` có được set thành `true` không?
3. API key có đúng không?
4. Log có hiển thị "Gemini Proxy Config: Enabled: True" không?

### Client không kết nối được

**Kiểm tra:**
1. IP và port có đúng không?
2. Firewall có block port 80 không?
3. Client có thể ping được server không?
4. Thử test bằng curl:

```bash
curl http://192.168.1.100:80/v1beta/models
```

### Lỗi "httpx library not found"

```bash
pip install httpx
```

### Lỗi "503 Service Unavailable"

Gemini proxy chưa được bật. Kiểm tra config file hoặc environment variables.

### Lỗi "502 Bad Gateway"

Server không thể kết nối đến Google API. Kiểm tra:
1. Server có internet không?
2. API key có hợp lệ không?
3. Google API có bị block không?

## Thay đổi model

Để thay đổi model được sử dụng, chỉnh sửa `gemini_config.json`:

```json
{
  "model": "gemini-2.0-flash-exp"
}
```

Sau đó restart server. Client code không cần thay đổi gì.

## Bảo mật

- ⚠️ **KHÔNG** commit file `gemini_config.json` lên git (đã được thêm vào `.gitignore`)
- ⚠️ Chỉ sử dụng trong mạng LAN tin cậy
- ⚠️ Cân nhắc sử dụng HTTPS nếu triển khai qua internet
- ✅ Sử dụng environment variables cho production
- ✅ Rotate API key định kỳ

## Monitoring

Theo dõi log để xem các request:

```
INFO - Gemini API request from 192.168.1.50: POST /v1beta/models/gemini-1.5-flash:generateContent
```

## Tắt Gemini Proxy

Để tắt tính năng Gemini proxy mà vẫn giữ HTTP/HTTPS proxy:

```json
{
  "enabled": false
}
```

Hoặc xóa file `gemini_config.json` và unset environment variables.
