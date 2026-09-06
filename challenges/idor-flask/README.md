# Challenge Template: IDOR

## 1. Mục đích
Template mô phỏng lỗ hổng Insecure Direct Object Reference (IDOR) - Broken Access Control. Người dùng có thể truy cập tài nguyên của người khác chỉ bằng cách thay đổi identifier (ở đây là tham số `id`).

## 2. Vulnerability
Lỗ hổng nằm ở hàm `view_note` trong `app.py`. Mặc dù query DB lấy `note` dựa vào `id`, ứng dụng không kiểm tra xem `note` đó có thuộc quyền sở hữu của người dùng hiện tại (vd: `current_user_id`) hay không.
Đoạn mã:
`cursor.execute("SELECT title, content FROM notes WHERE id = ?", (note_id,))`

## 3. Structure
- `challenge.yml`: Metadata.
- `Dockerfile`: Môi trường Python.
- `src/app.py`: Logic ứng dụng và query.
- `src/templates/`: Giao diện hiển thị danh sách note và chi tiết note.
- `solution/`: Solve script và writeup.

## 4. Các file
- **`app.py`**: Điểm tạo ra lỗi authorization. 
- **`index.html`**: Liệt kê các note của current user.
- **`note.html`**: Hiển thị note detail (chứa cờ nếu là note của admin).

## 5. Customization impact (Mức độ ảnh hưởng khi thay đổi)

### UI / presentation
- Có thể thay đổi màu sắc, font, text trong `index.html` và `note.html`.

### Challenge content
- Sửa lại nội dung dữ liệu (thay note thành hóa đơn, profile nhân viên).
- Trong `init_db()`, có thể tùy chỉnh các dòng `INSERT INTO`.

### Vulnerability code
- **Cẩn thận**: Nếu bạn thêm đoạn kiểm tra `WHERE id = ? AND user_id = ?`, lỗ hổng IDOR sẽ biến mất và bài lab không thể giải.

### Routes / parameters
- Tham số `?id=X` được dùng để khai thác. Nếu đổi thành mã hash UUID ngẫu nhiên thì đây sẽ trở thành IDOR nhưng khó đoán (Insecure Object Reference nhưng không Direct đoán được), có thể yêu cầu rò rỉ ID từ nơi khác. 

### FLAG
- Đọc từ `$FLAG` ở lúc khởi tạo db và gán cho `user_id = 1` (Admin). Không thay thế bằng flag cứng.

### Deployment
- Port mặc định 80.
