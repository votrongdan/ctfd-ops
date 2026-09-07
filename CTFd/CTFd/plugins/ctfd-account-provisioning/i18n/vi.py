"""Vietnamese translations for CTFd Account Provisioning plugin."""

TRANSLATIONS = {
    # Page titles
    "page_title": "Cấp Phát Tài Khoản",
    "page_subtitle": "Tạo hàng loạt tài khoản người chơi từ file CSV",

    # Upload section
    "upload_title": "Tải Lên Danh Sách Người Chơi",
    "upload_description": "Tải lên tệp CSV (.csv) chứa các cột 'Player ID' và 'Name'.",
    "upload_button": "Tải lên & Xem trước",
    "upload_select_file": "Chọn File CSV (.csv)",

    # Settings
    "settings_title": "Cài Đặt",
    "email_domain_label": "Tên Miền Email",
    "email_domain_help": "Tên miền cho email tự động tạo (ví dụ: ctf.local)",
    "language_label": "Ngôn Ngữ",

    # Preview section
    "preview_title": "Xem Trước",
    "preview_summary": "Tóm Tắt",
    "total_players": "Tổng Số Người Chơi",
    "valid_players": "Hợp Lệ",
    "invalid_players": "Không Hợp Lệ",
    "col_number": "STT",
    "col_name": "Tên",
    "col_username": "Tên Đăng Nhập",
    "col_email": "Email",
    "col_password": "Mật Khẩu",
    "col_status": "Trạng Thái",
    "status_valid": "Hợp lệ",
    "status_invalid": "Không hợp lệ",
    "confirm_button": "Tạo Tài Khoản",
    "confirm_message": "Bạn có chắc chắn muốn tạo {count} tài khoản?",
    "cancel_button": "Hủy",

    # Results section
    "results_title": "Kết Quả",
    "results_success": "Đã tạo thành công {count} tài khoản.",
    "results_partial": "Đã tạo {success} trên {total} tài khoản. {failed} thất bại.",
    "results_failure": "Tạo tài khoản thất bại.",
    "download_button": "Tải Về Thông Tin Đăng Nhập (Word)",
    "col_result": "Kết Quả",
    "result_created": "Đã tạo",
    "result_failed": "Thất bại",

    # Credential document
    "doc_title": "Thông Tin Đăng Nhập Người Chơi",
    "doc_event_label": "Cuộc Thi CTF",
    "card_name_label": "Họ Tên",
    "card_username_label": "Tên Đăng Nhập",
    "card_password_label": "Mật Khẩu",
    "card_note": "Vui lòng giữ thông tin đăng nhập an toàn. Không chia sẻ với người khác.",

    # Error messages
    "error_no_file": "Chưa có file nào được tải lên.",
    "error_invalid_file": "Định dạng file không hợp lệ. Vui lòng tải lên file .csv.",
    "error_unreadable_file": "Không thể đọc file đã tải lên. Vui lòng đảm bảo đây là file CSV hợp lệ.",
    "error_no_name_column": "Tệp CSV tải lên thiếu cột 'Name'.",
    "error_no_player_id_column": "Tệp CSV tải lên thiếu cột 'Player ID'.",
    "error_empty_fields": "Một hàng chứa giá trị trống cho Name hoặc Player ID.",
    "error_no_valid_players": "Không tìm thấy người chơi hợp lệ trong file đã tải lên.",
    "error_no_preview_data": "Không tìm thấy dữ liệu xem trước. Vui lòng tải lên file trước.",
    "error_provision_failed": "Cấp phát tài khoản thất bại: {error}",
    "error_file_too_large": "File quá lớn. Kích thước tối đa là 5MB.",
    "error_required_fields": 'Bắt buộc nhập Player ID và Name.',
    "error_duplicate_player_id": 'Player ID bị trùng trong CSV.',
    "error_account_constraints": 'Tài khoản không đáp ứng điều kiện username/email của CTFd.',
}
