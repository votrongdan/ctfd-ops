# Challenge Template: SSTI

## 1. Mục đích
Template này mô phỏng Server-Side Template Injection (SSTI) bằng Jinja2 trên Flask. 

## 2. Vulnerability
Thay vì truyền tham số vào `render_template` như thông thường (`render_template("index.html", name=name)`), ứng dụng lấy input của người dùng và nối chuỗi trực tiếp vào một template string, sau đó gọi `render_template_string()`.
Jinja2 sẽ parse input này như một phần cấu trúc của template, cho phép người dùng truyền các biểu thức `{{ ... }}` để thực thi mã (RCE).

## 3. Structure
- `challenge.yml`: Metadata.
- `Dockerfile`: Môi trường Python.
- `src/app.py`: Logic ứng dụng chứa lỗi SSTI.
- `src/templates/`: HTML cơ bản.
- `solution/`: Solve script và writeup.

## 4. Customization impact (Mức độ ảnh hưởng khi thay đổi)

### UI / presentation
- Form submit trong `index.html` có thể được trang trí tuỳ ý.

### Vulnerability code
- **Cẩn thận**: Trong `app.py`, template string bắt buộc phải nối chuỗi `{name}` (f-string) để tạo ra SSTI.
- Nếu bạn sửa thành `render_template_string(template, name=name)` và sửa chuỗi thành `Hello, {{ name }}`, **lỗ hổng sẽ biến mất** vì Jinja2 sẽ escape biến một cách an toàn.

### Routes / parameters
- Nếu đổi phương thức từ POST sang GET, phải đảm bảo form truyền method GET và `request.args` được lấy đúng.
- Thay đổi tên tham số (ví dụ từ `name` sang `username`) yêu cầu cập nhật solve script.

### FLAG
- RCE thông qua SSTI cho phép người chơi chạy lệnh shell (như `env` hoặc `printenv`). Họ có thể lấy FLAG từ biến môi trường.
- Bạn có thể ghi FLAG ra file `.txt` thay vì biến môi trường nếu muốn player dùng `cat flag.txt`. Mặc định cứ để môi trường để tuân theo convention của Whale.
