# Challenge Template: Reflected XSS

## 1. Mục đích
Template này mô phỏng lỗ hổng Reflected Cross-Site Scripting (XSS). Để challenge hoạt động được trong môi trường per-user container, template tích hợp sẵn một Admin Bot (headless browser bằng Selenium) dùng để giả lập admin truy cập vào link độc hại và bị đánh cắp cookie.

## 2. Vulnerability
Lỗ hổng nằm ở endpoint `/` khi tham số `name` được render ra template mà không có cơ chế escaping an toàn (sử dụng filter `| safe` trong Jinja2). Người chơi có thể chèn thẻ `<script>` để thực thi mã Javascript. 

## 3. Structure
- `challenge.yml`: Metadata của challenge.
- `Dockerfile`: Môi trường Python cài sẵn `chromium` và `chromium-driver`.
- `src/app.py`: Web app Flask chứa lỗ hổng.
- `src/bot.py`: Script Selenium đóng vai trò là Admin Bot.
- `src/templates/`: Giao diện HTML.
- `solution/`: Solve script và writeup.

## 4. Các file
- **`app.py`**: Xử lý request từ người chơi, hiển thị XSS và nhận URL báo cáo. Gọi `bot.py` khi nhận URL.
- **`bot.py`**: Chạy ngầm trong container, thiết lập cookie chứa FLAG và truy cập URL mà người chơi cung cấp.
- **`Dockerfile`**: Phải đảm bảo có Chromium. Script bot.py chạy bằng non-root user.

## 5. Customization impact (Mức độ ảnh hưởng khi thay đổi)

### UI / presentation (`index.html`, `report.html`)
- **Có thể sửa thoải mái**. Không ảnh hưởng vulnerability miễn là bạn vẫn giữ form truyền tham số bị lỗi.

### Challenge content
- Thay đổi câu chào, form input name để phù hợp với ngữ cảnh.

### Vulnerability code (`app.py` và `index.html`)
- **Cẩn thận**: Trong `index.html`, mã Jinja2 `{{ name | safe }}` tạo ra lỗi. Nếu bỏ `| safe`, Flask sẽ tự động encode HTML, lỗ hổng biến mất.

### Routes / parameters
- Nếu đổi tên tham số `name`, update file `solve.py` và Writeup.
- Đừng đổi cơ chế `/report` trừ khi bạn tự viết lại form gửi URL.

### FLAG (`bot.py` và `app.py`)
- Lấy từ `os.environ.get("FLAG")`. Admin Bot đặt cookie tên là `flag`. Không sửa tên cookie này nếu không có lý do cụ thể, vì player thường viết script tìm cookie.

### Docker / runtime
- Image khá nặng do cài Chromium. Không nên bỏ các argument của webdriver như `--no-sandbox` hay `--disable-dev-shm-usage`, bot sẽ không chạy được trong Docker.
