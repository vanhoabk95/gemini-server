# Hướng dẫn chạy Proxy Server như Windows Service

## Tổng quan
Thay vì sử dụng file `.bat` để chạy proxy server, bạn có thể cài đặt nó như một Windows Service để:
- Tự động khởi động khi Windows boot
- Chạy ngầm không cần cửa sổ console
- Quản lý dễ dàng qua Windows Services Manager
- Tự động restart khi có lỗi

## Yêu cầu
- Windows 7/8/10/11
- Python đã được cài đặt và có trong PATH
- Quyền Administrator để cài đặt service

## Các bước cài đặt (Đơn giản nhất)

### Bước 1: Cài đặt NSSM
Chạy file `install_nssm.bat` **với quyền Administrator**:
```
Clic phải vào install_nssm.bat → "Run as administrator"
```

File này sẽ:
- Tự động tải NSSM từ internet
- Cài đặt NSSM vào hệ thống
- Dọn dẹp các file tạm

### Bước 2: Cài đặt Service
Chạy file `install_service.bat` **với quyền Administrator**:
```
Clic phải vào install_service.bat → "Run as administrator"
```

File này sẽ:
- Tạo Windows Service tên "ProxyServer"
- Cấu hình tự động khởi động
- Thiết lập log files
- Khởi động service ngay lập tức

### Bước 3: Hoàn thành!
Service đã sẵn sàng sử dụng. Proxy server sẽ:
- Chạy trên port 80 (0.0.0.0:80)
- Tự động khởi động khi Windows boot
- Ghi log vào `service_output.log` và `service_error.log`

## Quản lý Service

### Sử dụng script quản lý
Chạy `manage_service.bat` để có menu quản lý đầy đủ:
- Khởi động/Dừng/Restart service
- Xem trạng thái và log files
- Mở Windows Services Manager
- Gỡ bỏ service

### Sử dụng Windows Services Manager
1. Nhấn `Win + R`, gõ `services.msc`
2. Tìm service "ProxyServer"
3. Clic phải để Start/Stop/Restart

### Sử dụng Command Line
```cmd
# Khởi động service
net start ProxyServer

# Dừng service
net stop ProxyServer

# Xem trạng thái
sc query ProxyServer
```

## Log Files
Service tạo ra 2 log files:
- `service_output.log`: Output bình thường của proxy server
- `service_error.log`: Các lỗi và exception

Log files được tự động rotate hàng ngày và khi đạt 10MB.

## Gỡ bỏ Service
Nếu muốn gỡ bỏ service, chạy `uninstall_service.bat` **với quyền Administrator**.

## Cấu hình Service

### Thay đổi cấu hình proxy
Để thay đổi host/port/max_connections, chỉnh sửa file `main.py`:
```python
class SimpleConfig:
    def __init__(self):
        self.host = '0.0.0.0'      # Thay đổi IP
        self.port = 80             # Thay đổi port
        self.max_connections = 150 # Thay đổi max connections
```

Sau khi chỉnh sửa, restart service:
```cmd
net stop ProxyServer
net start ProxyServer
```

### Thay đổi cấu hình service
Sử dụng NSSM để thay đổi cấu hình nâng cao:
```cmd
nssm edit ProxyServer
```

## Troubleshooting

### Service không khởi động được
1. Kiểm tra log file `service_error.log`
2. Đảm bảo Python có trong PATH
3. Kiểm tra port 80 có bị chiếm dụng không
4. Đảm bảo có quyền bind port 80 (cần admin)

### Port 80 bị chiếm dụng
Nếu port 80 đã được sử dụng bởi IIS hoặc ứng dụng khác:
1. Chỉnh sửa port trong `main.py` (ví dụ: 8080)
2. Restart service
3. Cập nhật cấu hình proxy trên client devices

### Service bị crash liên tục
Service được cấu hình tự động restart sau 5 giây khi gặp lỗi. Kiểm tra `service_error.log` để xem nguyên nhân.

## So sánh với file .bat

| Tính năng | File .bat | Windows Service |
|-----------|-----------|-----------------|
| Tự động khởi động | ❌ | ✅ |
| Chạy ngầm | ❌ | ✅ |
| Tự động restart | ❌ | ✅ |
| Quản lý dễ dàng | ❌ | ✅ |
| Log rotation | ❌ | ✅ |
| Chạy khi không login | ❌ | ✅ |

## Files được tạo
- `install_nssm.bat`: Cài đặt NSSM
- `install_service.bat`: Cài đặt Windows Service
- `uninstall_service.bat`: Gỡ bỏ Windows Service  
- `manage_service.bat`: Quản lý service
- `service_output.log`: Log output
- `service_error.log`: Log error
- `nssm/`: Thư mục chứa NSSM (có thể xóa sau khi cài đặt)