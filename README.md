# Ultimate CTF Platform

## Giới thiệu

Ultimate CTF Platform là một nền tảng tổ chức cuộc thi Capture The Flag (CTF) hoàn chỉnh, được xây dựng dựa trên [CTFd](https://github.com/CTFd/CTFd) và plugin [CTFd-Whale](https://github.com/frankli0324/ctfd-whale).

### Vấn đề cần giải quyết

Khi tổ chức một cuộc thi CTF ở quy mô lớn (ví dụ: trong trường đại học hoặc sự kiện nội bộ), organizer gặp phải nhiều vấn đề mà CTFd và Whale gốc chưa giải quyết đầy đủ:

- **Tạo tài khoản hàng loạt**: CTFd không có workflow tự động để tạo hàng chục/hàng trăm tài khoản người chơi từ danh sách sinh viên, đồng thời phát credential cho từng người.
- **Giám sát session**: Không có cơ chế phát hiện hoặc chặn việc chia sẻ tài khoản (nhiều người dùng cùng một account).
- **Challenge multi-port**: CTFd-Whale gốc chỉ hỗ trợ một port duy nhất cho mỗi challenge container. Các challenge phức tạp (ví dụ: web + SSH cùng container) không thể triển khai.
- **Challenge templates**: Không có bộ mẫu chuẩn để challenge author nhanh chóng tạo challenge mới theo các loại lỗ hổng web phổ biến.

Project này mở rộng CTFd + Whale bằng cách thêm các plugin tùy chỉnh và sửa đổi Whale để giải quyết các vấn đề trên.

---

## Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (:80)                          │
│                     Reverse Proxy                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      CTFd (:8000)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐ │
│  │  CTFd-Whale  │  │  Account     │  │  Single Session   │ │
│  │  (modified)  │  │  Provisioning│  │  Monitor          │ │
│  └──────┬───────┘  └──────────────┘  └───────────────────┘ │
└─────────┼───────────────────────────────────────────────────┘
          │
   ┌──────▼──────┐     ┌──────────┐     ┌──────────────────┐
   │   Docker    │     │  FRP     │     │   Challenge      │
   │   Swarm     │◄───►│  (frps + │◄───►│   Containers     │
   │   Engine    │     │   frpc)  │     │   (per-user)     │
   └─────────────┘     └──────────┘     └──────────────────┘
          │
   ┌──────▼──────┐     ┌──────────┐
   │  MariaDB    │     │  Redis   │
   │  (database) │     │  (cache) │
   └─────────────┘     └──────────┘
```

---

## Technology Stack

| Thành phần | Công nghệ |
|---|---|
| Core Platform | CTFd (Python 3.11, Flask, Gunicorn) |
| Database | MariaDB 10.11 |
| Cache | Redis 4 |
| Container Orchestration | Docker Swarm |
| Reverse Proxy (CTFd) | Nginx |
| Reverse Proxy (Challenge containers) | FRP (frps + frpc) |
| Challenge Deployment | ctfcli |
| Containerization | Docker (multi-stage build) |

---

## Tính năng mở rộng

### 1. Multi-Port / Multi-Service Challenge *(Modification của Whale)*

**Vấn đề**: CTFd-Whale gốc chỉ hỗ trợ expose một port duy nhất cho mỗi challenge container (thông qua `redirect_type` + `redirect_port`). Điều này ngăn việc triển khai các challenge phức tạp có nhiều dịch vụ (ví dụ: HTTP trên port 8080 và SSH trên port 22 trong cùng một container).

**Giải pháp của project**: Mở rộng Whale bằng cách thêm field `redirect_rules` vào model `DynamicDockerChallenge` và field `ports` (JSON) vào model `WhaleContainer`. Khi `redirect_rules` được cấu hình, Whale sẽ:
- Parse danh sách rules (ví dụ: `"8080/http,22/direct"`)
- Allocate host port riêng cho mỗi direct rule
- Tạo FRP rule riêng cho từng port
- Render nhiều access URL/command cho người chơi

Backward compatibility được giữ nguyên: nếu `redirect_rules` trống, flow cũ (`redirect_type` + `redirect_port`) vẫn hoạt động bình thường.

**Lợi ích**: Challenge author có thể thiết kế challenge chạy nhiều dịch vụ trong cùng một container. Admin không cần cấu hình thủ công. Người chơi thấy nhiều access point trên giao diện.

**Files liên quan**: `models.py` (WhaleContainer.ports, redirect_rules), `utils/routers/frp.py` (FrpRouter.register/unregister/reload/access)

---

### 2. Account Provisioning *(Custom plugin — do project tự phát triển)*

**Vấn đề**: Khi tổ chức CTF nội bộ (ví dụ: cho lớp học hoặc sự kiện với danh sách người chơi cố định), admin phải tạo tay từng tài khoản. CTFd có chức năng import CSV nhưng không sinh username/password tự động và không xuất credential để phát cho người chơi.

**Giải pháp của project**: Plugin `ctfd-account-provisioning` cung cấp workflow hoàn chỉnh:

1. Admin upload file CSV chứa 2 cột: **Player ID** và **Name**
2. Plugin tự động sinh username (chuẩn hóa tên Unicode/tiếng Việt sang ASCII, kết hợp Player ID), password (10 ký tự, cryptographically secure), và email placeholder
3. Admin xem preview và xác nhận
4. Plugin tạo tài khoản trong CTFd (sử dụng cùng `UserSchema` mà CTFd dùng)
5. Admin tải về file `.docx` chứa credential cards để in và phát cho người chơi

**Lợi ích**: Giảm thời gian chuẩn bị từ hàng giờ xuống vài phút. Hỗ trợ tên tiếng Việt. Output credential dạng Word sẵn sàng in. Hỗ trợ 2 ngôn ngữ (EN/VI).

**Files liên quan**: `CTFd/CTFd/plugins/ctfd-account-provisioning/`

---

### 3. Session Monitoring *(Custom plugin — do project tự phát triển)*

**Vấn đề**: Trong CTF nội bộ, việc chia sẻ tài khoản (nhiều người dùng cùng 1 account) là hành vi gian lận phổ biến. CTFd không có cơ chế phát hiện hoặc ngăn chặn điều này.

**Giải pháp của project**: Plugin `ctfd-single-session` giám sát session đăng nhập với 2 chế độ:

- **Monitoring mode**: Cho phép nhiều session đồng thời nhưng tạo security event khi phát hiện. Admin thấy cảnh báo trên dashboard.
- **Block mode**: Chỉ cho phép 1 session active tại một thời điểm. Login mới bị từ chối khi đã có session đang hoạt động.

Plugin hoạt động bằng cách monkey-patch `login_user`/`logout_user` của CTFd để theo dõi session mà không cần sửa CTFd core. Dữ liệu session được lưu trong database riêng (bảng `ssm_sessions`, `ssm_events`) và được reconcile với cache để xác định session thực sự active.

**Lợi ích**: Admin phát hiện gian lận chia sẻ tài khoản. Có thể force logout session hoặc toàn bộ session của một user. Security events có cooldown tránh flood.

**Files liên quan**: `CTFd/CTFd/plugins/ctfd-single-session/`

---

### 4. Challenge Templates *(Custom — do project tự phát triển)*

**Vấn đề**: Tạo challenge web containerized từ đầu tốn nhiều thời gian. Challenge author phải tự thiết lập Dockerfile, cấu hình flag injection, tương thích với Whale và ctfcli.

**Giải pháp của project**: Cung cấp 5 template sẵn sàng (Python/Flask) cho các loại lỗ hổng web phổ biến:

| Template | Loại lỗ hổng |
|---|---|
| `sqli-flask-sqlite` | SQL Injection |
| `xss-flask` | Reflected XSS |
| `idor-flask` | IDOR / Broken Access Control |
| `ssti-flask` | Server-Side Template Injection |
| `file-upload-flask` | File Upload / Path Traversal |

Mỗi template bao gồm: `challenge.yml` (metadata cho ctfcli), `Dockerfile`, `src/` (source code ứng dụng), `README.md`, và `solution/` (writeup + solve script).

Template là blueprint — challenge author copy thư mục, sửa source code, build Docker image, rồi deploy qua ctfcli. Flag không được hardcode; template đọc flag từ biến môi trường `$FLAG` do Whale inject.

**Lợi ích**: Giảm thời gian tạo challenge mới. Đảm bảo cấu trúc chuẩn và tương thích với Whale + ctfcli. Có solution/writeup đi kèm.

**Files liên quan**: `challenge-templates/`

---

### 5. Flag Validation Security Fix *(Modification của Whale)*

**Vấn đề**: Trong Whale gốc, logic validation flag không kiểm tra container có thuộc đúng challenge đang submit hay không. Một user có thể submit flag của container từ challenge khác.

**Giải pháp**: Thêm kiểm tra `WhaleContainer.challenge_id == challenge.id` trong `challenge_type.py` (method `attempt`). Nếu user không có container đang chạy cho challenge hiện tại, submission bị từ chối.

---

### 6. Per-User Challenge Environment *(Tính năng có sẵn của CTFd-Whale)*

> Đây là tính năng **có sẵn** của CTFd-Whale, không phải do project tự phát triển.

Khi người chơi nhấn "Start Instance", Whale tạo một Docker Swarm service riêng cho user đó. Mỗi user có môi trường cô lập, không ảnh hưởng lẫn nhau. Container tự động bị xóa sau khi hết thời gian (mặc định 1 giờ). Mỗi user chỉ có tối đa 1 container tại một thời điểm.

### 7. Per-User Flag *(Tính năng có sẵn của CTFd-Whale)*

> Đây là tính năng **có sẵn** của CTFd-Whale, không phải do project tự phát triển.

Mỗi container được inject một flag ngẫu nhiên duy nhất qua biến môi trường `FLAG`. Flag được sinh bằng Jinja2 template (mặc định: `flag{<uuid4>}`), lưu trong database, và validate khi user submit.

---

## Cấu trúc Repository

```
Ultimate-CTF-Platform/
├── README.md                          # File này
├── docs/
│   ├── installation.md                # Hướng dẫn cài đặt
│   └── architecture.md                # Tài liệu kiến trúc
├── CTFd/                              # CTFd core (fork)
│   ├── docker-compose.yml             # Docker Compose config (7 services)
│   ├── Dockerfile                     # Multi-stage build cho CTFd
│   ├── docker-entrypoint.sh           # Entrypoint: DB migration + Gunicorn
│   ├── conf/
│   │   ├── frp/                       # FRP config (frpc.ini, frps.ini)
│   │   └── nginx/                     # Nginx reverse proxy config
│   ├── CTFd/
│   │   └── plugins/
│   │       ├── ctfd-whale/            # Whale plugin (modified)
│   │       ├── ctfd-account-provisioning/  # Account provisioning (custom)
│   │       └── ctfd-single-session/   # Session monitor (custom)
│   ├── requirements.txt
│   └── ...                            # CTFd source files
├── challenge-templates/               # Challenge template blueprints
│   ├── README.md                      # Hướng dẫn sử dụng templates
│   ├── sqli-flask-sqlite/
│   ├── xss-flask/
│   ├── idor-flask/
│   ├── ssti-flask/
│   └── file-upload-flask/
└── challenges/                        # Challenge instances (deployed)
    ├── .ctf/                          # ctfcli event config
    └── example-*/                     # Các challenge đã tạo từ templates
```

---

## Quick Start

### Yêu cầu
- Linux (Ubuntu/Debian khuyến nghị)
- Docker và Docker Compose
- Git

### Khởi động nhanh

```bash
# Clone repository
git clone <repository-url>
cd Ultimate-CTF-Platform

# Khởi tạo Docker Swarm
docker swarm init
docker node update --label-add "name=linux-1" $(docker node ls -q)

# Khởi động hệ thống
cd CTFd
docker compose up -d

# Truy cập CTFd tại http://localhost (qua Nginx) hoặc http://localhost:8000
```

Xem hướng dẫn chi tiết tại [docs/installation.md](docs/installation.md).

---

## Tài liệu

- **[Hướng dẫn cài đặt](docs/installation.md)** — Cài đặt, cấu hình, và triển khai hoàn chỉnh
- **[Kiến trúc kỹ thuật](docs/architecture.md)** — Kiến trúc hệ thống, workflows, và chi tiết implementation
- **[Hướng dẫn Challenge Templates](challenge-templates/README.md)** — Cách sử dụng và tạo challenge templates
