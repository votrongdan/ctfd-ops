# Challenge Template: File Upload

## 1. Mục đích
Template này mô phỏng lỗi tải tệp tin (File Upload Vulnerability). Cụ thể là lỗi Path Traversal trong quá trình xử lý tên tệp, dẫn tới Arbitrary File Write và kéo theo Remote Code Execution (RCE) qua việc ghi đè template.

## 2. Vulnerability
Lỗ hổng nằm ở việc sử dụng trực tiếp `file.filename` do người dùng gửi lên để lưu tệp tin, mà không đi qua hàm lọc (như `secure_filename`).
Đoạn code lỗi:
`file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))`

Nếu `filename` là `../templates/index.html`, tệp tin gốc của ứng dụng sẽ bị ghi đè. Kẻ tấn công có thể chèn mã SSTI độc hại vào tệp tải lên để đọc biến `$FLAG`.

## 3. Structure
- `challenge.yml`: Metadata.
- `Dockerfile`: Môi trường Python. Cấu hình gunicorn có `--reload` và cấp quyền ghi cho thư mục `templates/`.
- `src/app.py`: Logic ứng dụng, config `TEMPLATES_AUTO_RELOAD = True`.
- `src/templates/`: HTML cơ bản.
- `src/uploads/`: Thư mục lưu tệp tải lên.
- `solution/`: Solve script và writeup.

## 4. Customization impact (Mức độ ảnh hưởng khi thay đổi)

### UI / presentation
- Có thể thay đổi giao diện `index.html`. Tuy nhiên hãy nhớ rằng kẻ tấn công sẽ ghi đè file này, nên nếu bạn đổi tên file template gốc, exploit script của người chơi cũng phải trỏ tới đúng tên đó.

### Vulnerability code
- **Cẩn thận**: Nếu bạn thêm `from werkzeug.utils import secure_filename` và bọc `filename = secure_filename(file.filename)`, lỗ hổng File Upload sẽ bị **vá hoàn toàn**, người chơi không thể RCE.
- Không xoá `app.config['TEMPLATES_AUTO_RELOAD'] = True` và `--reload` trong Dockerfile. Nếu xoá, khi file template bị ghi đè, Gunicorn vẫn dùng bản cache cũ trong memory và payload sẽ không bao giờ chạy.

### Routes / parameters
- Đổi trường `name="file"` thành cái khác thì nhớ update script.

### FLAG
- Đọc từ `$FLAG` bằng biến môi trường. Sau khi ghi đè thành công, payload sẽ lấy biến này in ra màn hình.
