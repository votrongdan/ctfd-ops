# Challenge Template: SQL Injection

## 1. Mục đích
Template này mô phỏng lỗ hổng SQL Injection cơ bản (UNION-based) sử dụng Flask và SQLite. Phù hợp cho các bài lab mức độ dễ (Beginner).

## 2. Vulnerability
Lỗ hổng xảy ra tại hàm tìm kiếm do sử dụng string formatting trực tiếp thay vì parameterized query (Prepared Statements).
Đoạn code lỗi:
`sql_query = f"SELECT name, description FROM products WHERE name LIKE '%{query}%'"`

Kẻ tấn công có thể chèn các ký tự đặc biệt (như `'`) để đóng chuỗi `LIKE`, sau đó sử dụng mệnh đề `UNION SELECT` để trích xuất dữ liệu từ các bảng khác.

## 3. Structure
- `challenge.yml`: Metadata của challenge.
- `Dockerfile`: Môi trường Python 3.10-slim chạy Gunicorn.
- `src/app.py`: Source code chính chứa lỗ hổng.
- `src/templates/index.html`: Giao diện người dùng.
- `solution/`: Chứa file script giải bài `solve.py` và `WRITEUP.md`.

## 4. Các file
- **`app.py`**: Chứa logic web và tương tác cơ sở dữ liệu.
- **`index.html`**: Form gửi request.
- **`Dockerfile` & `challenge.yml`**: Dùng để build và deploy.

## 5. Customization impact (Mức độ ảnh hưởng khi thay đổi)

### UI / presentation (`index.html`)
- **Có thể sửa thoải mái**.
- Ảnh hưởng chủ yếu tới giao diện.
- **Lưu ý**: Cần giữ lại form POST với thuộc tính `name="query"` (hoặc nếu đổi, phải đổi tương ứng trong `app.py`), nếu không player sẽ không thể truyền payload.

### Challenge content (Dữ liệu mẫu trong `init_db`)
- **Có thể thay đổi**.
- Thay đổi danh sách `products` giúp challenge có câu chuyện (story) riêng biệt (ví dụ: đổi thành danh sách nhân viên, kho sách...).
- Không ảnh hưởng tới lỗ hổng, nhưng có thể ảnh hưởng tới context của bài toán.

### Vulnerability code (`app.py`)
- **Có thể sửa nhưng phải cẩn thận**.
- Đoạn code tạo vulnerability: `sql_query = f"... '{query}'"`
- **Rủi ro**: Nếu bạn thay đổi thành `cursor.execute("... LIKE ?", (f"%{query}%",))`, lỗ hổng SQLi sẽ **biến mất**. Nếu bạn đổi logic query (ví dụ: `ORDER BY`), intended payload có thể bị lỗi, yêu cầu phải dùng kĩ thuật khác (như Error-based hoặc Blind SQLi).

### Data / database schema (`init_db`)
- Thay đổi tên bảng (ví dụ: `products` -> `items`) hoặc tên cột sẽ buộc người chơi phải dò lại tên bảng (qua `sqlite_master`), điều này không sao nhưng writeup cũ và solve script cũ sẽ không còn đúng.

### Routes / parameters
- Đổi `/` thành `/search` hoặc đổi biến `query` thành `q`: solve script cũ sẽ hỏng. Bạn phải update lại file `solution/solve.py`.

### FLAG
- Code đọc flag: `flag = os.environ.get("FLAG", "...")`
- **Rủi ro**: Tuyệt đối không hard-code flag (vd: `flag = "flag{my_flag}"`). Nếu sửa, Whale sẽ không thể tiêm flag động (per-user flag) vào bài lab, dẫn tới việc hệ thống không chấm điểm được.

### Docker / runtime
- Nếu đổi base image hoặc sửa thư viện, có thể ứng dụng sẽ không chạy được. Port mặc định là 80, nếu đổi trong `app.py`, bạn phải cập nhật `EXPOSE` trong Dockerfile và `redirect_port` trong `challenge.yml`.

### Deployment
- Đổi tên `docker_image` trong `challenge.yml` cần đảm bảo không bị trùng với các challenge khác.
