# SSRF Flask Template
Lỗ hổng Server-Side Request Forgery (SSRF).
Ứng dụng sử dụng `requests.get()` để truy xuất URL người dùng nhập mà không kiểm tra.
Chứa một internal service chạy ngầm ở `127.0.0.1:8080`.
