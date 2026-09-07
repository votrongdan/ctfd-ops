# Xác minh 9 issue — 2026-09-07

## Kết quả cuối

- MariaDB + Redis + Docker Swarm + FRP: **82 passed, 1 skipped**, 87.85 giây. Test bị skip là migration MariaDB cần database riêng; đã chạy riêng và pass như dòng tiếp theo.
- Nâng cấp schema MariaDB cũ: **1 passed**, 13.34 giây. Bỏ các cột mới trong database dùng một lần, chạy startup hai lần, xác minh port, flag và dữ liệu cũ được giữ nguyên.
- SQLite mới + Redis: **70 passed**, 20.72 giây, gồm test plugin hiện có và regression lifecycle/provisioning.
- `git diff --check`: pass.
- JUnit: `mariadb.xml`, `upgrade.xml`, `sqlite.xml` trong thư mục này. Các lần chạy lặp trên hai database không phải các test độc lập để cộng thành số lượng case duy nhất.

## Cách xử lý từng issue

| Issue | Nguyên nhân và thay đổi |
| --- | --- |
| #3 | `create_all` không thêm cột vào bảng đã tồn tại. Thêm migration additive, kiểm tra cột trước khi thêm; hỗ trợ chạy lại và SQLite, giữ dữ liệu cũ. |
| #4 | Rebuild chỉ đọc `container.port`. Tính cả các giá trị trong `container.ports`, thay pool Redis bằng transaction, dùng cùng khóa với routing/allocation. |
| #5 | Đăng ký session diễn ra trước khi CTFd ghi cache. Giữ reservation có hạn 60 giây và khóa theo user qua database; hoàn tất tại session-save, hủy khi ghi cache lỗi, chặn save muộn sau khi reservation hết hạn. |
| #7 | Lỗi giữa quá trình reserve nhiều port thiếu rollback đầy đủ. Theo dõi và hoàn trả reservation; khi cleanup không hoàn tất, giữ record phục hồi và tiếp tục loại port đó khỏi pool. |
| #8 | Nhiều HTTP rule dùng chung subdomain. Dùng helper chung cho cấu hình FRP và access information; các HTTP rule tiếp theo có hậu tố port, giữ URL single-port cũ. |
| #11 | Parser/preview thiếu required fields, duplicate Player ID và constraint tài khoản thật. Kiểm tra Name/Player ID, duplicate không phân biệt hoa thường trong CSV; dùng UserSchema và kiểm tra email/collision; xác minh lại khi import để xử lý dữ liệu thay đổi sau preview. |
| #12 | Dictionary cục bộ không chia sẻ qua worker/restart. Lưu job trong DB, payload mã hóa, giới hạn theo admin sở hữu và TTL; lưu account cùng kết quả recovery trong transaction. Preview mặc định 1 giờ, credential recovery 24 giờ. |
| #13 | GET download consume dữ liệu quá sớm. Cho phép GET lại trong TTL, cache document đã tạo và trả stream mới mỗi lần; lỗi render hoặc download không làm mất credential recovery. Không thể suy ra browser đã lưu file thành công từ việc server gửi response. |
| #15 | Tuổi record không phản ánh CTFd cache/session-save. Xác minh dữ liệu cache, lifecycle và reservation; quan sát session-save thực tế thay vì tự áp TTL khác. |

Khóa lifecycle dùng chung nằm ngoài ba thư mục plugin vì cả Whale, provisioning và single-session cần đồng bộ nhiều process. Đây là thay đổi hỗ trợ trực tiếp các issue concurrency; không sửa core authentication hoặc bỏ feature.

## Test mới và regression đã thực hiện

- `test_lifecycle.py`: migration SQLite cũ/partial và idempotency; CSV required/duplicate; đăng ký đồng thời; pending, expired reservation và cache-save failure; login/logout/Block/monitoring; cache expiry/refresh/force logout; preview/import/retry/download; ownership, constraints, expiry, render failure, transaction rollback, partial success, cancel/recovery; pool rebuild cũ/multi và URL.
- `test_whale_integration.py`: Docker Swarm/Redis/FRP thật; single HTTP, single TCP, hai HTTP, hai TCP, HTTP+TCP; route truy cập được sau rebuild/reload; renew/destroy/release; per-user environment/flag và submit qua player API; hết port, FRP lỗi, cleanup failure/recovery, snapshot cleanup cũ và create/rebuild đồng thời. Một số lỗi được chủ động inject để kiểm tra nhánh rollback.
- `test_process_recovery.py`: Gunicorn 2 workers, request HTTP đồng thời; admin login, upload CSV, restart, confirm lặp không tạo trùng account, download lại sau restart; player Block mode chỉ một login được giữ auth, restart giữ session hợp lệ, logout/login.
- `test_upgrade.py`: nâng cấp MariaDB từ schema không có các cột mới, giữ dữ liệu và chạy startup lặp.
- Các test plugin hiện có đã chạy: toàn bộ `ctfd-account-provisioning/tests` và `ctfd-single-session/tests`. Test cũ được chỉnh khi fixture/import hoặc kỳ vọng cache giả không còn mô phỏng đúng behavior; test save failure mới đánh dấu session modified và kiểm tra trực tiếp reservation đã inactive, không còn pending.

## Lệnh chạy

Chạy trong `/opt/CTFd` của container test cô lập, với DATABASE_URL/REDIS_URL của stack test:

```sh
python -m tests.plugin_regression.run CTFd/plugins/ctfd-account-provisioning/tests CTFd/plugins/ctfd-single-session/tests tests/plugin_regression -q --tb=short --junitxml=/tmp/final-regression.xml
```

Migration chạy riêng cùng runner, chỉ `tests/plugin_regression/test_upgrade.py`, cấu hình `UPGRADE_DATABASE_URL` trỏ vào database dùng một lần `ctfd_regression_upgrade`.

SQLite dùng database mới `/tmp/ctfd_regression_final_sqlite.db`, Redis DB 3, chạy hai thư mục test plugin và `tests/plugin_regression/test_lifecycle.py`.

## Giới hạn và triển khai

- Không có test thất bại trong các lượt cuối. Có warning cookie domain localhost và API SQLAlchemy deprecated; không đổi dependency major version trong scope này.
- Xác minh qua Flask test client và HTTP request thật; chưa chạy lại UI thủ công bằng browser với bản cuối.
- Đã test restart worker, cache mất dữ liệu, routing reload/pool recovery và startup migration. Chưa test mất điện/reboot toàn host, kill giữa mọi instruction, hoặc tải production kéo dài.
- Chưa test PostgreSQL hoặc filesystem-cache multi-worker; stack thực tế đã test dùng MariaDB/Redis/Docker/FRP, và SQLite với Redis.
- Key mã hóa provisioning cần được giữ trong UPLOAD_FOLDER persistent/shared hoặc cấu hình ACCOUNT_PROVISIONING_KEY giống nhau giữa các instance. Mất key sẽ không giải mã được job đã lưu.
- Không triển khai hay restart stack chính. Stack test cô lập vẫn còn để tái kiểm tra.
- Chưa tạo commit: thao tác Git trước đó bị chặn vì `.git` chỉ đọc. Thay đổi đang ở workspace. Revert code không tự rollback database; migration chỉ thêm cột nên không cần xóa dữ liệu để quay về code cũ. Cần giữ backup DB trước khi triển khai thực tế.

## Danh sách file code/test thay đổi

Xem `changed-files.txt` trong thư mục này. Danh sách không bao gồm hai tài liệu review có sẵn trước lần sửa này.
