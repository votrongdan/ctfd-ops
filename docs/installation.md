# Hướng dẫn Cài đặt và Triển khai

Tài liệu này hướng dẫn cài đặt và triển khai hoàn chỉnh hệ thống Ultimate CTF Platform. Mục tiêu là người có kiến thức Linux và Docker cơ bản có thể clone repository và dựng được hệ thống hoạt động.

---

## 1. Yêu cầu hệ thống

### Phần mềm bắt buộc

| Thành phần | Yêu cầu |
|---|---|
| Hệ điều hành | Linux (Ubuntu 20.04+ / Debian 11+ khuyến nghị) |
| Docker Engine | Phiên bản hỗ trợ Docker Swarm |
| Docker Compose | v2 (tích hợp sẵn trong Docker Engine mới) |
| Git | Để clone repository |

### Phần mềm tùy chọn (cho challenge deployment)

| Thành phần | Mục đích |
|---|---|
| Python 3.x | Chạy ctfcli |
| pip | Cài đặt ctfcli |
| ctfcli | Deploy challenge lên CTFd |

### Ports sử dụng

| Port | Service | Mô tả |
|---|---|---|
| 80 | Nginx | Reverse proxy cho CTFd (giao diện web) |
| 8000 | CTFd | Application server (có thể truy cập trực tiếp) |
| 8001 | FRP Server | HTTP vhost cho challenge containers (HTTP redirect) |
| 10000-10100 | FRP Server | Port range cho challenge containers (direct/TCP redirect) |

> **Lưu ý**: Các port trên được cấu hình trong `docker-compose.yml`. Port 80 và 8000 dành cho giao diện CTFd. Port 8001 và 10000-10100 dành cho traffic tới challenge containers qua FRP.

---

## 2. Chuẩn bị môi trường

### 2.1. Cài đặt Docker

Nếu chưa có Docker, cài đặt theo hướng dẫn chính thức: https://docs.docker.com/engine/install/

Kiểm tra Docker đã hoạt động:

```bash
docker --version
docker compose version
```

### 2.2. Khởi tạo Docker Swarm

CTFd-Whale sử dụng Docker Swarm để orchestrate challenge containers. Đây là bước **bắt buộc**.

```bash
# Khởi tạo Swarm (trên máy hiện tại làm manager node)
docker swarm init
```

Gắn label cho node (Whale sử dụng label để chọn node khi tạo container):

```bash
docker node update --label-add "name=linux-1" $(docker node ls -q)
```

> **Giải thích**: Whale cấu hình mặc định tìm node với label `name=linux-1`. Giá trị này phải khớp với config `whale:docker_swarm_nodes` trong CTFd (mặc định: `linux-1`).

### 2.3. Kiểm tra Docker socket

CTFd container cần truy cập Docker socket để quản lý challenge containers:

```bash
ls -la /var/run/docker.sock
```

Ghi nhận GID của group `docker`:

```bash
getent group docker | cut -d: -f3
```

> **Quan trọng**: `docker-compose.yml` cấu hình `group_add: ["973"]`. Nếu GID của group `docker` trên hệ thống khác `973`, bạn cần sửa giá trị này trong `docker-compose.yml` (dòng `group_add`). Đây là GID cần thiết để container CTFd có quyền đọc/ghi Docker socket.

---

## 3. Clone Repository

```bash
git clone <repository-url>
cd Ultimate-CTF-Platform
```

---

## 4. Cấu hình

### 4.1. Docker Compose

File: `CTFd/docker-compose.yml`

Các biến môi trường chính (service `ctfd`):

| Biến | Mặc định | Mô tả |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://ctfd:ctfd@db/ctfd` | Connection string tới MariaDB |
| `REDIS_URL` | `redis://cache:6379` | Connection string tới Redis |
| `WORKERS` | `1` | Số Gunicorn workers (khuyến nghị giữ 1 cho Whale) |
| `REVERSE_PROXY` | `true` | Cho CTFd biết đang chạy sau reverse proxy |
| `SECRET_KEY` | *(tự sinh)* | Secret key cho session. Nên set cố định cho production |

**Credentials MariaDB** (service `db`):

```yaml
environment:
  - MARIADB_ROOT_PASSWORD=ctfd
  - MARIADB_USER=ctfd
  - MARIADB_PASSWORD=ctfd
  - MARIADB_DATABASE=ctfd
```

> **Cảnh báo**: Mật khẩu mặc định là `ctfd`. Đối với production, **bắt buộc** thay đổi password trong cả service `db` và biến `DATABASE_URL` của service `ctfd`.

**Docker GID** (service `ctfd`):

```yaml
group_add:
  - "973"  # ← Thay bằng GID thực tế của group docker trên hệ thống
```

### 4.2. FRP (Fast Reverse Proxy)

FRP chịu trách nhiệm route traffic từ bên ngoài tới challenge containers.

**FRP Server** — File: `CTFd/conf/frp/frps.ini`

```ini
[common]
bind_port = 7987
vhost_http_port = 8001
token = your_token        # ← THAY ĐỔI token này
subdomain_host = 127.0.0.1.nip.io
```

| Tham số | Mô tả |
|---|---|
| `bind_port` | Port giao tiếp giữa frps và frpc |
| `vhost_http_port` | Port cho HTTP vhost (challenge HTTP redirect) |
| `token` | Token xác thực giữa frps và frpc. **Phải giống nhau** ở cả 2 file |
| `subdomain_host` | Domain suffix cho HTTP challenges. `127.0.0.1.nip.io` phù hợp cho development |

**FRP Client** — File: `CTFd/conf/frp/frpc.ini`

```ini
[common]
token = your_token        # ← THAY ĐỔI, phải giống frps.ini
server_addr = frps
server_port = 7987
admin_addr = 0.0.0.0
admin_port = 7400
```

| Tham số | Mô tả |
|---|---|
| `server_addr` | Hostname của frps (trong Docker Compose network, dùng service name `frps`) |
| `admin_addr` / `admin_port` | API endpoint để Whale quản lý FRP rules |

> **Quan trọng**: Token trong `frpc.ini` và `frps.ini` **phải giống nhau**. Giá trị mặc định `your_token` chỉ là placeholder — thay bằng một chuỗi bất kỳ.

### 4.3. Nginx

File: `CTFd/conf/nginx/http.conf`

Cấu hình mặc định proxy tất cả traffic từ port 80 tới CTFd (:8000). Thường không cần sửa đổi trừ khi cần thêm HTTPS.

---

## 5. Khởi động hệ thống

```bash
cd CTFd
docker compose up -d
```

Kiểm tra tất cả services đã chạy:

```bash
docker compose ps
```

Kết quả mong đợi: 6 services đều ở trạng thái `Up`:
- `ctfd`
- `nginx`
- `db`
- `cache`
- `frps`
- `frpc`

> **Lưu ý**: Lần đầu khởi động, service `permissions` sẽ chạy rồi exit (đây là hành vi bình thường — nó chỉ set quyền cho volumes). Service `ctfd` sẽ chạy database migration tự động qua `flask db upgrade`.

Kiểm tra logs nếu có lỗi:

```bash
docker compose logs ctfd
docker compose logs frpc
docker compose logs frps
```

---

## 6. Cấu hình CTFd (Setup Wizard)

### 6.1. Lần đầu truy cập

Mở trình duyệt tại `http://localhost` (hoặc `http://<server-ip>`).

CTFd sẽ hiển thị Setup Wizard. Điền thông tin:
- **Event Name**: Tên cuộc thi
- **Admin Username / Email / Password**: Tài khoản admin

Hoàn tất wizard để vào trang admin.

### 6.2. Cấu hình Whale

Truy cập **Admin Panel → Plugins → Whale** (hoặc URL: `/plugins/ctfd-whale/admin/settings`).

Các cấu hình quan trọng:

| Config | Giá trị mặc định | Mô tả |
|---|---|---|
| Docker API URL | `unix:///var/run/docker.sock` | Đường dẫn tới Docker socket |
| Swarm Nodes | `linux-1` | Tên label node (phải khớp với label đã gắn ở bước 2.2) |
| Auto Connect Network | `ctfd_frp-containers` | Tên Docker network cho challenge containers |
| FRP API URL | `http://frpc:7400` | URL tới FRP client admin API |
| FRP HTTP Domain Suffix | `127.0.0.1.nip.io` | Domain suffix cho HTTP challenges |
| FRP HTTP Port | `8001` | Port của FRP HTTP vhost |
| FRP Direct IP Address | `127.0.0.1` | IP hiển thị cho người chơi khi dùng direct/TCP redirect |
| Direct Port Minimum | `10000` | Port range bắt đầu |
| Direct Port Maximum | `10100` | Port range kết thúc |
| Docker Timeout | `3600` | Thời gian sống container (giây) |

> **Lưu ý về Auto Connect Network**: Tên network phụ thuộc vào tên thư mục chứa `docker-compose.yml`. Nếu thư mục tên `CTFd`, network sẽ là `ctfd_frp-containers`. Kiểm tra tên chính xác:
>
> ```bash
> docker network ls | grep containers
> ```
>
> Sửa giá trị "Auto Connect Network" cho khớp.

Sau khi cấu hình, trang Whale settings sẽ hiển thị trạng thái checks (Docker API, FRP connection). Tất cả phải pass.

---

## 7. Deploy Challenge thử nghiệm

### 7.1. Build Docker image

Chọn một template hoặc example challenge:

```bash
cd challenge-templates/sqli-flask-sqlite
docker build -t template-sqli-flask-sqlite:latest .
```

Kiểm tra image đã build:

```bash
docker image ls | grep sqli
```

### 7.2. Test cục bộ (tùy chọn)

```bash
docker run -d -p 8080:80 -e FLAG="flag{test_flag}" template-sqli-flask-sqlite:latest
```

Truy cập `http://localhost:8080` để kiểm tra challenge hoạt động. Dừng container sau khi test:

```bash
docker stop $(docker ps -q --filter ancestor=template-sqli-flask-sqlite:latest)
```

### 7.3. Deploy qua ctfcli

Cài ctfcli nếu chưa có:

```bash
pip install ctfcli
```

Khởi tạo event (chỉ cần làm 1 lần):

```bash
cd challenges
ctfcli init
# Nhập CTFd URL: http://localhost:8000
# Nhập Access Token: lấy từ Admin Panel → Settings → Access Tokens
```

Deploy challenge:

```bash
# Từ thư mục challenges/
ctfcli challenge install <tên-thư-mục-challenge>
```

Hoặc nếu challenge đã tồn tại, đồng bộ lại:

```bash
ctfcli challenge sync <tên-thư-mục-challenge>
```

### 7.4. Kiểm tra per-user container

1. Đăng nhập CTFd bằng tài khoản người chơi (không phải admin)
2. Mở challenge vừa deploy
3. Nhấn **"Start Instance"**
4. Chờ container khởi tạo — URL hoặc connection command sẽ xuất hiện
5. Truy cập challenge qua URL/command hiển thị

### 7.5. Kiểm tra flag

1. Khai thác lỗ hổng trong challenge để lấy flag
2. Submit flag trên CTFd
3. Flag là chuỗi ngẫu nhiên dạng `flag{<uuid>}` — khác nhau cho mỗi user

### 7.6. Kiểm tra port mapping

Kiểm tra port đã được allocate qua admin panel:

**Admin → Plugins → Whale → Containers** (hoặc `/plugins/ctfd-whale/admin/containers`)

Danh sách containers hiển thị user, challenge, thời gian, và port mapping.

---

## 8. Deploy Challenge Multi-Port

### 8.1. Cấu hình redirect_rules

Trong `challenge.yml`, thay `redirect_type` và `redirect_port` bằng `redirect_rules`:

```yaml
extra:
  initial: 500
  decay: 100
  minimum: 50
  docker_image: my-multiport-challenge:latest
  # Thay vì:
  #   redirect_type: http
  #   redirect_port: 80
  # Sử dụng:
  redirect_rules: "8080/http,22/direct"
```

Cú pháp: `<container_port>/<redirect_type>` phân cách bằng dấu phẩy.

- `8080/http`: Route HTTP traffic. Whale tạo HTTP proxy qua FRP vhost.
- `22/direct`: Route TCP traffic. Whale allocate host port ngẫu nhiên (trong range 10000-10100).

### 8.2. Kiểm tra multi-port

Sau khi user start instance, giao diện challenge sẽ hiển thị **nhiều access point**:
- HTTP link cho port 8080
- `nc <ip> <port>` command cho port 22

Kiểm tra port mapping trong admin panel: container sẽ có JSON `ports` chứa mapping `{"22": <allocated_host_port>}`.

---

## 9. Account Provisioning

### 9.1. Truy cập plugin

**Admin → Plugins → Account Provisioning** (hoặc `/plugins/ctfd-account-provisioning/admin`)

### 9.2. Chuẩn bị file CSV

Tạo file CSV với 2 cột bắt buộc (header case-insensitive):

```csv
Player ID,Name
P001,Nguyễn Văn An
P002,Trần Thị Bình
P003,John Smith
```

- **Player ID**: Mã định danh duy nhất cho mỗi người chơi (ví dụ: mã sinh viên)
- **Name**: Tên hiển thị (hỗ trợ Unicode/tiếng Việt)

Plugin có script tạo file CSV mẫu: `CTFd/CTFd/plugins/ctfd-account-provisioning/create_sample.py`

### 9.3. Upload và provision

1. Chọn file CSV và cấu hình email domain (mặc định: `ctf.local`)
2. Nhấn **Upload** — plugin hiển thị preview với username và password đã sinh
3. Kiểm tra preview — username có dạng `nguyen_van_an_p001`
4. Nhấn **Confirm** để tạo tài khoản

### 9.4. Download credentials

Sau khi tạo tài khoản thành công, nhấn **Download** để tải file `.docx` chứa credential cards. File này sẵn sàng in và phát cho người chơi.

---

## 10. Session Monitoring

### 10.1. Cấu hình

**Admin → Plugins → Single Session** → Settings (hoặc `/plugins/ctfd-single-session/admin/settings`)

| Config | Mô tả |
|---|---|
| Mode | `monitoring` (cho phép nhiều session, cảnh báo) hoặc `block` (chặn login khi đã có session) |
| Event Cooldown | Thời gian tối thiểu giữa 2 event cùng loại cho cùng user (giây, mặc định: 300) |
| Heartbeat Interval | Tần suất cập nhật last_seen (giây, mặc định: 30) |

### 10.2. Sử dụng

- **Sessions tab**: Xem danh sách session đang active. Có thể force logout từng session hoặc tất cả session của một user.
- **Events tab**: Xem security events (multiple_sessions, login_blocked). Có thể resolve event.

---

## 11. Troubleshooting

### Docker connection errors

**Triệu chứng**: Whale settings hiển thị lỗi "Unable to connect to Docker API".

**Giải pháp**:
- Kiểm tra Docker socket được mount: `docker compose exec ctfd ls -la /var/run/docker.sock`
- Kiểm tra GID trong `group_add` khớp với group docker trên host
- Kiểm tra Docker Swarm đã init: `docker info | grep Swarm`

### FRP connection errors

**Triệu chứng**: Whale settings hiển thị lỗi "Unable to access frpc admin api".

**Giải pháp**:
- Kiểm tra frpc đang chạy: `docker compose ps frpc`
- Kiểm tra token giống nhau trong `frpc.ini` và `frps.ini`
- Kiểm tra logs: `docker compose logs frpc`
- Kiểm tra FRP API URL trong Whale settings (mặc định: `http://frpc:7400`)

### Container creation failed

**Triệu chứng**: User nhấn "Start Instance" nhưng nhận lỗi "Container creation failed".

**Giải pháp**:
- Kiểm tra Docker image tồn tại: `docker image ls | grep <image-name>`
- Kiểm tra Swarm node có label đúng: `docker node inspect $(docker node ls -q) | grep -A2 Labels`
- Kiểm tra Auto Connect Network trong Whale settings khớp với tên network thực tế: `docker network ls | grep containers`
- Kiểm tra logs CTFd: `docker compose logs ctfd | tail -50`

### Port exhaustion

**Triệu chứng**: Lỗi "No available ports. Please wait for a few minutes."

**Giải pháp**:
- Mở rộng port range trong Whale settings (Direct Port Minimum / Maximum)
- Mở rộng port range trong `docker-compose.yml` (service `frps`, mục `ports`)
- Kiểm tra container cũ đã được cleanup: **Admin → Whale → Containers**

### Challenge không truy cập được

**Triệu chứng**: Container tạo thành công nhưng người chơi không truy cập được.

**Giải pháp**:
- **HTTP redirect**: Kiểm tra `subdomain_host` trong `frps.ini` và FRP HTTP Domain Suffix trong Whale settings
- **Direct redirect**: Kiểm tra port range được expose trong `docker-compose.yml` (service `frps`)
- Kiểm tra ứng dụng trong container bind vào `0.0.0.0` (không phải `127.0.0.1`)
- Kiểm tra `redirect_port` trong `challenge.yml` khớp với port `EXPOSE` trong Dockerfile
