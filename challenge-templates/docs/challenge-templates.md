# Challenge Templates Documentation

Tài liệu này hướng dẫn cách sử dụng và tạo các Challenge Template trong hệ thống CTF platform (dựa trên CTFd + ctfcli + Whale).

## 1. Challenge Template là gì?

Challenge Template là một blueprint/repository mẫu chứa cấu trúc chuẩn của một thử thách. 
- **Template** không phải là một challenge thực tế có thể chơi ngay. Nó là một bản thiết kế cơ bản.
- **Challenge cụ thể** được tạo ra bằng cách clone hoặc copy thư mục template này, sau đó người ra đề (challenge author) sẽ sửa đổi (customize) source code, mô tả và cấu hình để biến nó thành một bài thi hoàn chỉnh mang đặc trưng riêng.

## 2. Cấu trúc chuẩn của một template

Mặc dù có thể thay đổi tùy thuộc vào ngôn ngữ và framework, một template chuẩn thường có cấu trúc như sau:

```text
template-name/
├── challenge.yml    # Metadata cho ctfcli và CTFd
├── Dockerfile       # Cấu hình container environment
├── entrypoint.sh    # Script khởi động service và DB (nếu cần)
├── schema.sql       # Script khởi tạo database schema và inject flag
├── README.md        # Hướng dẫn dành riêng cho template
└── src/             # Mã nguồn ứng dụng (PHP, Python, JS...)
```

## 3. Giải thích chức năng từng thành phần

- **`challenge.yml`**: Khai báo các thông tin metadata (tên, mô tả, điểm số, tags) để `ctfcli` sử dụng khi deploy lên CTFd. Đồng thời khai báo loại challenge là `dynamic_docker` để báo cho plugin Whale biết đây là một container được quản lý linh hoạt (per-user).
- **`Dockerfile`**: Khai báo môi trường chạy ứng dụng. Nó định nghĩa các dependencies (như cài đặt Python, PHP, MariaDB, thư viện) và chỉ định port nào được Expose (thường là 80).
- **`entrypoint.sh`**: (Thường dùng cho PHP/Node.js + MySQL). Script khởi động khi container bắt đầu chạy. Nhiệm vụ chính: khởi động service cơ sở dữ liệu, chạy script `schema.sql`, đọc biến môi trường `$FLAG` (do Whale cấp) và ghi vào DB, cuối cùng khởi động web server.
- **`schema.sql`**: Script chứa các câu lệnh SQL để tạo table và nhập dữ liệu mẫu.
- **`src/` (Source Code)**: Mã nguồn của web app chứa lỗ hổng (vulnerability). Đây là phần người chơi sẽ tương tác và khai thác.

## 4. Giải thích Customization (Tùy biến)

Là người tạo đề, bạn sẽ chỉnh sửa các file trong template để tạo challenge của riêng mình. Mỗi thay đổi sẽ có tác động khác nhau:

- **Sửa `challenge.yml`**: Thay đổi thông tin hiển thị trên giao diện CTFd (Tên, mô tả, điểm). Nó yêu cầu bạn phải chạy lại lệnh `ctfcli challenge sync` để cập nhật lên server CTFd. Thay đổi cấu hình image Docker ở đây cũng ảnh hưởng tới Whale deployment.
- **Sửa `Dockerfile` hoặc `entrypoint.sh` / `schema.sql`**: Thay đổi môi trường hệ thống (ví dụ cài thêm thư viện, đổi schema DB). Bất cứ thay đổi nào ở đây cũng yêu cầu **phải rebuild lại Docker image** (`docker build`).
- **Sửa application source code (`src/`)**: Thay đổi logic web app và thay đổi bản chất của lỗ hổng. Bạn cần **rebuild Docker image** để code mới được đóng gói vào image.
- **Sửa port/service configuration**: Nếu bạn đổi port trong Dockerfile, bạn phải nhớ cập nhật tương ứng mục `redirect_port` bên trong `challenge.yml` để Whale route traffic đúng port.

**Phân biệt mức độ ảnh hưởng**:
- Chỉ sửa application / Docker: Cần rebuild image.
- Cập nhật thông tin challenge: Sẽ ảnh hưởng trực tiếp tới CTFd (cần ctfcli sync).
- Cập nhật flag: Bạn **không** tự quản lý hoặc hardcode flag. Whale quản lý hệ thống flag (per-user). Template đã có sẵn logic nhận flag từ biến môi trường `$FLAG` và giấu vào nơi cần thiết (ví dụ: database).

## 5. Workflow tạo challenge từ template

Để tạo một challenge mới, thực hiện các bước sau:

1. **Chọn và copy template**: `cp -r challenge-templates/sqli-php-mysql challenges/my-new-sqli`
2. **Đổi metadata**: Mở `challenge.yml`, đổi Tên, mô tả, điểm số, và đặc biệt là `docker_image: my-new-sqli:latest`.
3. **Customize source code**: Mở thư mục `src/`, thay đổi giao diện (HTML/CSS), thay đổi câu lệnh truy vấn SQL (nếu cần thay đổi cách khai thác).
4. **Build Docker Image**: 
   ```bash
   cd challenges/my-new-sqli
   docker build -t my-new-sqli:latest .
   ```
5. **Test Container Locally**: 
   ```bash
   # Chạy thử container để đảm bảo code hoạt động với biến FLAG giả lập
   docker run -d -p 8080:80 -e FLAG="flag{test_local_flag}" my-new-sqli:latest
   ```
   Truy cập `http://localhost:8080` để test khai thác thử nghiệm.
6. **Deploy bằng ctfcli**:
   ```bash
   ctfcli challenge add .
   ctfcli challenge install .
   ```
7. **Whale runtime**: Khi người chơi ấn nút "Start Instance" trên CTFd, Whale sẽ tự động tạo một container mới từ image `my-new-sqli:latest` và tiêm một biến `$FLAG` riêng biệt cho user đó.

## 6. Customization hiện tại (Source-level)

Phiên bản template hiện tại **chỉ hỗ trợ tùy biến ở mức mã nguồn (Source-level Customization)**.
Điều này có nghĩa là chúng ta không sử dụng parameterization (như khai báo YAML: `table_name: users`, `vulnerable_column: id`). Thay vào đó, nếu bạn muốn đổi table `users` thành `employees`, bạn sẽ mở file mã nguồn (`app.py`, `index.php`) và file SQL (`schema.sql`) để tìm và thay thế trực tiếp chữ `users` thành `employees`.

Cơ chế này giúp giữ template ở mức đơn giản, minh bạch và linh hoạt tối đa cho người viết đề.

## 7. Docker và Runtime

- **Image vs Container**: Bạn xây dựng (build) image một lần. CTFd-Whale sẽ khởi tạo nhiều Container (runtime environment) từ image này khi người chơi yêu cầu.
- **Port**: Quy chuẩn là Expose port `80` ra ngoài (hoặc một port cố định). Whale sẽ dùng một port proxy linh hoạt gán cho người dùng, và route traffic đó về cổng `80` của container.
- **Entrypoint**: Đảm bảo container không bị "chết" (exit) ngay sau khi start. Entrypoint phải chạy web server dưới dạng process foreground (ví dụ: `apache2-foreground` hoặc `node app.js`).

## 8. ctfcli Integration

Template phải tương thích với workflow của `ctfcli`. Do đó, sự tồn tại của file `challenge.yml` là bắt buộc.
- Chúng ta không thay thế ctfcli bằng script riêng.
- Lệnh `ctfcli challenge add` dùng để đăng ký thư mục với event hiện tại.
- Lệnh `ctfcli challenge install` dùng để đẩy thông tin (Tên, điểm, cấu hình dynamic docker) lên CTFd.

## 9. Whale Integration

CTFd-Whale có nhiệm vụ quản lý runtime của container. 
- Whale tự sinh flag động (Dynamic per-user flag) để ngăn gian lận. Template lấy flag này qua biến môi trường `$FLAG` và lưu vào DB.
- Mỗi người chơi sẽ có môi trường riêng biệt. Nếu người chơi A xóa database, nó chỉ ảnh hưởng tới session của người chơi A. 
- Template tác giả không cần quan tâm đến cấp phát port, cấp phát network hay quản lý container lifecycle. Whale sẽ lo việc đó.

## 10. Best practices

Khi bạn tùy biến hoặc tạo một template mới, hãy tuân theo các quy tắc sau:
- **Giữ template đơn giản**: Đừng làm mọi thứ phức tạp (over-engineer). Code càng dễ hiểu, người tạo đề càng dễ sửa.
- **Tránh hardcode secret/flag**: Tuyệt đối không lưu cờ dưới dạng plaintext kiểu `flag{...}` trong source hay SQL. Luôn đọc từ `$FLAG`.
- **Docker build phải reproducible**: Cố định version của base image (ví dụ `node:18-slim` thay vì `node:latest`) để tránh lỗi sau này khi package update.
- **Khai báo dependency rõ ràng**: Dùng `requirements.txt` (Python) hoặc `package.json` (Node.js).
- **Challenge phải chạy được local trước khi deploy**: Luôn test local trước khi dùng ctfcli đẩy lên production.
- **Document các phần cần sửa**: Trong source code, nên dùng comment (ví dụ: `// VULNERABILITY: ...`) để chỉ ra dòng code có lỗ hổng để challenge author dễ tìm.

## 11. Troubleshooting (Xử lý sự cố)

- **Docker build fail**: Kiểm tra lại cú pháp Dockerfile hoặc xem các dependency có đổi tên/bỏ phiên bản hay không. 
- **Container exit ngay sau khi start (không start)**: Có thể do web server gặp lỗi code, hoặc database chưa kịp khởi động. Xem log bằng `docker logs <container_id>`.
- **Application không listen đúng port**: Đảm bảo application (Flask, Express, Apache) bind vào `0.0.0.0:80` (chứ không phải `127.0.0.1:80`) để nhận traffic từ ngoài container.
- **Database không ready**: Các process như MySQL mất thời gian vài giây để khởi động. Trong `entrypoint.sh` cần có lệnh `sleep` trước khi gọi `mysql < schema.sql` để tránh lỗi "can't connect to local MySQL server".
- **ctfcli deploy fail**: Cú pháp `challenge.yml` bị sai YAML. Kiểm tra lại thụt lề (indentation).
- **Challenge chạy local nhưng không chạy trong Whale**: Có thể thiết lập `redirect_port` trong `challenge.yml` sai so với port đang `EXPOSE` trong Dockerfile. 

## 12. Template Development Guideline

Nếu bạn muốn tạo thêm một Template mới cho loại lỗ hổng khác (ví dụ: XSS, SSRF, Command Injection), hãy tuân thủ guideline sau:

1. **Vulnerability rõ ràng**: Tập trung vào 1 lỗ hổng. Đừng trộn lẫn quá nhiều kỹ thuật phức tạp nếu đó chỉ là template cơ sở.
2. **Mức độ Dễ/Trung bình**: Template là điểm bắt đầu. Tác giả sau này sẽ tự làm khó nó thêm bằng cách implement WAF hoặc filter.
3. **Dependency tối thiểu**: Chỉ cài những gì thực sự cần (ví dụ curl cho SSRF, database cho SQLi).
4. **Source code dễ đọc**: Viết code sạch, kèm comment chú thích rõ phần nhận input và phần thực thi gây ra lỗ hổng.
5. **Đầy đủ cấu phần**: Luôn phải có `challenge.yml`, `Dockerfile`, cấu trúc source rõ ràng, và KHÔNG hardcode flag.
6. **Kiểm tra độc lập**: Template phải chạy được chỉ bằng `docker build` và `docker run`. Mọi template mới nên được tạo thư mục riêng trong `challenge-templates/` và bổ sung README hướng dẫn ngắn gọn.
