# Hướng Dẫn Sử Dụng Challenge Templates

Tài liệu này cung cấp các hướng dẫn tiêu chuẩn về cách khai thác và phát triển các mẫu thử thách (Challenge Templates) trên hệ thống nền tảng CTF (được tích hợp giữa CTFd, ctfcli và CTFd-Whale).

## 1. Định nghĩa Challenge Template

Challenge Template là các nguyên mẫu lưu trữ (blueprint/repository) định nghĩa cấu trúc cơ sở của một bài thử thách. 
- **Template** không phải là một thử thách có thể được đưa vào vận hành ngay lập tức. Đây thuần túy là một bản thiết kế nền tảng.
- **Thử thách hoàn chỉnh** được hình thành thông qua việc nhân bản (clone/copy) thư mục template. Sau đó, người tạo đề (Challenge Author) sẽ tiến hành tùy biến (customize) mã nguồn, cấu hình và mô tả để tạo ra một bài thi mang tính đặc thù.

## 2. Cấu trúc chuẩn của một Template

Mặc dù cấu trúc có thể thay đổi tùy thuộc vào ngôn ngữ lập trình và framework được sử dụng, một template tiêu chuẩn thường bao gồm các thành phần sau:

```text
template-name/
├── challenge.yml    # Tệp siêu dữ liệu (Metadata) cấu hình cho ctfcli và CTFd
├── Dockerfile       # Khai báo môi trường đóng gói container
├── entrypoint.sh    # Kịch bản (Script) khởi động dịch vụ và Cơ sở dữ liệu
├── schema.sql       # Kịch bản khởi tạo lược đồ Cơ sở dữ liệu và xử lý cờ (flag)
├── README.md        # Tài liệu hướng dẫn cục bộ cho template
└── src/             # Thư mục chứa mã nguồn ứng dụng (PHP, Python, JS...)
```

## 3. Chức năng chi tiết của từng thành phần

- **`challenge.yml`**: Khai báo các thông tin siêu dữ liệu (tên bài, mô tả, điểm số, thẻ phân loại) nhằm phục vụ quá trình triển khai qua công cụ `ctfcli`. Tệp này bắt buộc phải định nghĩa loại thử thách là `dynamic_docker` nhằm cấp quyền cho plugin Whale thực hiện quản lý vòng đời container động (per-user).
- **`Dockerfile`**: Khai báo môi trường vận hành của ứng dụng. Tệp định nghĩa các gói phụ thuộc (như Python, PHP, MariaDB, các thư viện liên quan) và xác định cổng mạng được Expose ra bên ngoài (thông thường là cổng 80).
- **`entrypoint.sh`**: Kịch bản thực thi tự động khi container được khởi tạo. Các nhiệm vụ chính bao gồm: khởi động dịch vụ cơ sở dữ liệu, thực thi tệp `schema.sql`, tiếp nhận cờ từ biến môi trường `$FLAG` (do Whale tiêm vào) để lưu trữ an toàn, và cuối cùng là khởi động máy chủ Web.
- **`schema.sql`**: Chứa các tập lệnh SQL để thiết lập cấu trúc bảng và chèn dữ liệu khởi tạo.
- **`src/` (Mã nguồn)**: Mã nguồn của ứng dụng Web chứa lỗ hổng bảo mật (vulnerability). Đây là môi trường chính để người chơi thực hiện các thao tác khai thác.

## 4. Hướng dẫn Tùy biến (Customization)

Trong vai trò là người tạo đề, việc chỉnh sửa các tệp tin trong template sẽ dẫn đến các thay đổi tương ứng đối với ứng dụng:

- **Thay đổi `challenge.yml`**: Cập nhật thông tin hiển thị trên giao diện CTFd. Cần thực thi lệnh `ctfcli challenge sync` để đồng bộ các cập nhật này lên máy chủ. Việc thay đổi cấu hình Docker image tại đây cũng sẽ tác động trực tiếp đến tiến trình cấp phát của Whale.
- **Thay đổi `Dockerfile`, `entrypoint.sh` hoặc `schema.sql`**: Tác động đến môi trường hệ thống bên trong container. Bất kỳ thay đổi nào tại các tệp này đều bắt buộc phải đóng gói lại Docker Image (`docker build`).
- **Thay đổi mã nguồn ứng dụng (`src/`)**: Thay đổi logic nghiệp vụ và bản chất của lỗ hổng bảo mật. Yêu cầu đóng gói lại (rebuild) Docker Image.
- **Thay đổi cấu hình cổng dịch vụ**: Nếu cổng mạng trong `Dockerfile` thay đổi, quản trị viên phải cập nhật thông số `redirect_port` bên trong `challenge.yml` tương ứng để Whale có thể định tuyến (route) lưu lượng truy cập chính xác.

**Phân loại mức độ ảnh hưởng của tùy biến**:
- Sửa đổi Application/Docker: Yêu cầu thực thi lệnh rebuild image.
- Cập nhật thông tin thử thách: Yêu cầu đồng bộ CTFd (thực thi ctfcli sync).
- Cập nhật cờ (Flag): Người tạo đề **không** tiến hành hardcode cờ. Hệ thống Whale sẽ đảm nhiệm việc quản lý và cấp phát cờ động cho từng người dùng. Template đã tích hợp sẵn cơ chế đọc và lưu trữ biến môi trường `$FLAG` vào cơ sở dữ liệu.

## 5. Quy trình tạo mới thử thách (Workflow)

Để triển khai một thử thách mới, vui lòng tuân thủ quy trình sau:

1. **Lựa chọn và sao chép Template**: `cp -r challenge-templates/sqli-php-mysql challenges/my-new-sqli`
2. **Cập nhật Metadata**: Mở tệp `challenge.yml`, chỉnh sửa Tên bài, mô tả, điểm số, và cấu hình `docker_image: my-new-sqli:latest`.
3. **Tùy biến mã nguồn**: Mở thư mục `src/`, điều chỉnh giao diện (HTML/CSS) hoặc các khối logic (như câu truy vấn SQL) nhằm định hình kịch bản khai thác.
4. **Đóng gói Docker Image**: 
   ```bash
   cd challenges/my-new-sqli
   docker build -t my-new-sqli:latest .
   ```
5. **Kiểm thử cục bộ (Local Testing)**: 
   ```bash
   # Khởi chạy container thử nghiệm để kiểm tra tính năng với biến FLAG giả định
   docker run -d -p 8080:80 -e FLAG="flag{test_local_flag}" my-new-sqli:latest
   ```
   Truy cập `http://localhost:8080` để thực hiện kiểm thử quá trình khai thác.
6. **Triển khai qua ctfcli**:
   ```bash
   ctfcli challenge add .
   ctfcli challenge install .
   ```
7. **Khởi tạo thông qua Whale runtime**: Khi người dùng nhấn nút "Start Instance" trên CTFd, hệ thống Whale sẽ tự động phân bổ một container mới từ image `my-new-sqli:latest` và tiêm một biến `$FLAG` độc lập cho phiên làm việc đó.

## 6. Môi trường Docker và Runtime

- **Image và Container**: Docker image chỉ cần được đóng gói (build) một lần. Khi có yêu cầu từ phía người dùng, CTFd-Whale sẽ dựa vào image này để khởi tạo các Container (môi trường runtime) riêng biệt.
- **Xử lý Cổng mạng (Port)**: Tiêu chuẩn là mở (Expose) cổng `80` (hoặc cổng cố định đã định nghĩa). Whale sẽ thiết lập một cổng proxy ngẫu nhiên linh hoạt cho từng người chơi và chuyển tiếp lưu lượng vào cổng `80` của container đó.
- **Entrypoint**: Cần đảm bảo tiến trình trong container không bị đóng (exit) ngay sau khi khởi động. Kịch bản entrypoint phải chạy tiến trình web server dưới dạng process foreground (ví dụ: `apache2-foreground` hoặc `node app.js`).

## 7. Tích hợp ctfcli

Mọi template đều phải tương thích hoàn toàn với luồng công việc của `ctfcli`. Sự hiện diện của tệp `challenge.yml` là điều kiện bắt buộc.
- Ctfcli là công cụ tiêu chuẩn, không sử dụng script tự chế để thay thế.
- Lệnh `ctfcli challenge add`: Đăng ký thư mục thử thách với cấu hình sự kiện hiện tại.
- Lệnh `ctfcli challenge install`: Đồng bộ dữ liệu (Tên, cấu hình dynamic docker, điểm) lên hệ thống CTFd.

## 8. Tích hợp CTFd-Whale

CTFd-Whale đảm nhận nhiệm vụ quản lý vòng đời runtime của container.
- Whale tự động khởi tạo cờ động (Dynamic per-user flag) để loại trừ rủi ro gian lận. Template tiếp nhận cờ này từ biến môi trường `$FLAG` và xử lý.
- Mỗi người chơi hoạt động trong một môi trường cô lập. Thao tác của người chơi A (ví dụ: xóa dữ liệu) hoàn toàn không tác động đến môi trường của người chơi B.
- Người tạo đề không cần phải thực hiện cấp phát port, quản lý network hay vòng đời container. Hệ thống Whale sẽ xử lý tự động toàn bộ quy trình này.

## 9. Cấu hình Đa Dịch Vụ (Multi-Port Configuration)

CTFd-Whale hỗ trợ việc expose và định tuyến lưu lượng (routing) đến nhiều dịch vụ chạy trên nhiều port bên trong cùng một container. Một ví dụ tiêu biểu là thử thách **Web2SSH** (thư mục `challenges/web2ssh/`), trong đó container vận hành đồng thời HTTP Web Service (port 8080) và SSH Service (port 22).

Để thiết lập tính năng này, quản trị viên sử dụng cấu hình `redirect_rules` thay cho `redirect_type` và `redirect_port` trong tệp `challenge.yml`. Cú pháp như sau:

```yaml
extra:
  # Cấu hình redirect_rules cho đa cổng (Multi-port):
  redirect_rules: "8080/http,22/direct"
```

- `8080/http`: Chỉ định hệ thống xử lý cổng 8080 dưới dạng HTTP traffic. Whale sẽ tạo ra một HTTP Proxy (thường thông qua domain) để người chơi có thể truy cập qua liên kết trên giao diện.
- `22/direct`: Chỉ định hệ thống định tuyến TCP trực tiếp (direct routing) đối với cổng 22. Whale sẽ mở một cổng ngẫu nhiên trên host (ví dụ: `2221`) và forward trực tiếp vào cổng 22 của container. Người chơi có thể sử dụng công cụ dòng lệnh để kết nối (ví dụ: `ssh ctf@<host> -p 2221`).

Chi tiết về kiến trúc đa dịch vụ có thể được tham khảo thêm tại tài liệu `challenges/web2ssh/README.md`.

## 10. Tiêu chuẩn phát triển (Best practices)

Trong quá trình tùy biến hoặc thiết kế một template mới, cần tuân thủ các quy tắc sau:
- **Đề cao sự tối giản**: Lược bỏ các thiết kế dư thừa (over-engineer). Cấu trúc mã nguồn càng tinh gọn, việc bảo trì càng dễ dàng.
- **Nghiêm cấm Hardcode Flag**: Không lưu trữ cờ dưới định dạng plaintext (`flag{...}`) trong mã nguồn hoặc tệp SQL. Toàn bộ logic phải xử lý thông qua biến `$FLAG`.
- **Đảm bảo tính tái lập (Reproducibility)**: Cố định phiên bản base image (ví dụ `node:18-slim` thay vì `node:latest`) nhằm hạn chế lỗi phát sinh do các thay đổi của thư viện trong tương lai.
- **Khai báo thư viện đầy đủ**: Sử dụng `requirements.txt` đối với Python hoặc `package.json` đối với Node.js.
- **Kiểm thử cục bộ**: Cần đảm bảo container hoạt động trơn tru tại local trước khi sử dụng ctfcli để đẩy lên hệ thống thực tế.
- **Ghi chú (Documentation) nội tuyến**: Nên sử dụng các khối bình luận trong source code (ví dụ: `// VULNERABILITY: ...`) để làm nổi bật dòng mã chứa lỗ hổng.

## 11. Xử lý sự cố (Troubleshooting)

- **Lỗi biên dịch Docker (Build fail)**: Kiểm tra lại cú pháp tệp `Dockerfile` hoặc đối chiếu xem các dependency có bị lỗi phiên bản không. 
- **Container tự đóng ngay sau khi khởi tạo**: Nguyên nhân thường do web server lỗi khởi động, hoặc dịch vụ cơ sở dữ liệu chưa sẵn sàng. Kiểm tra log thông qua lệnh `docker logs <container_id>`.
- **Dịch vụ không tiếp nhận port**: Cần đảm bảo ứng dụng (Flask, Express, Apache) thực hiện bind vào địa chỉ `0.0.0.0:80` (chứ không phải `127.0.0.1:80`).
- **Database không phản hồi**: Tiến trình MariaDB/MySQL cần khoảng thời gian khởi động. Kịch bản `entrypoint.sh` cần triển khai lệnh `sleep` trước khi thực thi `mysql < schema.sql` để tránh lỗi "can't connect to local MySQL server".
- **Lỗi đồng bộ ctfcli**: Thường do cú pháp YAML bên trong tệp `challenge.yml` không hợp lệ. Vui lòng đối chiếu các thụt lề (indentation).
- **Thử thách chạy được cục bộ nhưng lỗi trên Whale**: Đảm bảo cấu hình `redirect_port` bên trong tệp `challenge.yml` đồng nhất với cổng được khai báo `EXPOSE` bên trong `Dockerfile`. 

## 12. Hướng dẫn tạo Template mới (Development Guideline)

Quy trình chuẩn khi triển khai một Template mới cho một loại lỗ hổng khác (ví dụ: Command Injection):

1. **Lỗ hổng trọng tâm**: Bài thử thách cần tập trung vào 1 nhóm lỗ hổng duy nhất ở cấp độ cơ sở.
2. **Độ khó tiêu chuẩn**: Template chỉ nên dừng ở mức độ Dễ/Trung bình. Người tạo đề có thể tự nâng cấp độ khó thông qua các cơ chế WAF hoặc Regex Filter sau này.
3. **Tối thiểu hóa Dependencies**: Chỉ tiến hành cài đặt các công cụ thực sự cần thiết.
4. **Mã nguồn tường minh**: Logic mã nguồn cần được viết gọn gàng, có kèm bình luận ở các phân đoạn xử lý dữ liệu đầu vào.
5. **Tuân thủ cấu trúc**: Bắt buộc phải tích hợp đầy đủ tệp `challenge.yml`, `Dockerfile` và nghiêm cấm việc lập trình cứng giá trị cờ.
6. **Kiểm duyệt độc lập**: Mọi template phát triển mới phải được lưu trữ trong thư mục `challenge-templates/` và phải đảm bảo chạy độc lập thành công thông qua lệnh `docker build` và `docker run`.

## 13. Danh sách Template có sẵn (Python/Flask)

Hệ thống hiện tại tích hợp sẵn 5 mẫu cơ sở phục vụ cho các lỗ hổng Web tiêu chuẩn:

1. **SQL Injection**: `sqli-flask-sqlite` (Tham khảo [Tài liệu SQLi](sqli-flask-sqlite/README.md))
2. **Reflected XSS**: `xss-flask` (Tham khảo [Tài liệu XSS](xss-flask/README.md))
3. **IDOR / Broken Access Control**: `idor-flask` (Tham khảo [Tài liệu IDOR](idor-flask/README.md))
4. **SSTI (Server-Side Template Injection)**: `ssti-flask` (Tham khảo [Tài liệu SSTI](ssti-flask/README.md))
5. **File Upload (Path Traversal)**: `file-upload-flask` (Tham khảo [Tài liệu File Upload](file-upload-flask/README.md))

(Đi kèm với mỗi template đều có một thư mục minh họa trong hệ thống `challenges/` để người tạo đề tham khảo kiến trúc thực tế).
