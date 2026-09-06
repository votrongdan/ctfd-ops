"""English translations for CTFd Account Provisioning plugin."""

TRANSLATIONS = {
    # Page titles
    "page_title": "Account Provisioning",
    "page_subtitle": "Bulk create player accounts from a CSV file",

    # Upload section
    "upload_title": "Upload Player List",
    "upload_description": "Upload a CSV file (.csv) containing 'Player ID' and 'Name' columns.",
    "upload_button": "Upload & Preview",
    "upload_select_file": "Select CSV File (.csv)",

    # Settings
    "settings_title": "Settings",
    "email_domain_label": "Email Domain",
    "email_domain_help": "Domain for auto-generated placeholder emails (e.g., ctf.local)",
    "language_label": "Language",

    # Preview section
    "preview_title": "Preview",
    "preview_summary": "Summary",
    "total_players": "Total Players",
    "valid_players": "Valid",
    "invalid_players": "Invalid",
    "col_number": "#",
    "col_name": "Name",
    "col_username": "Username",
    "col_email": "Email",
    "col_password": "Password",
    "col_status": "Status",
    "status_valid": "Valid",
    "status_invalid": "Invalid",
    "confirm_button": "Create Accounts",
    "confirm_message": "Are you sure you want to create {count} accounts?",
    "cancel_button": "Cancel",

    # Results section
    "results_title": "Results",
    "results_success": "Successfully created {count} accounts.",
    "results_partial": "Created {success} of {total} accounts. {failed} failed.",
    "results_failure": "Account creation failed.",
    "download_button": "Download Credentials (Word)",
    "col_result": "Result",
    "result_created": "Created",
    "result_failed": "Failed",

    # Credential document
    "doc_title": "Player Login Credentials",
    "doc_event_label": "CTF Competition",
    "card_name_label": "Name",
    "card_username_label": "Username",
    "card_password_label": "Password",
    "card_note": "Please keep your credentials safe. Do not share with others.",

    # Error messages
    "error_no_file": "No file was uploaded.",
    "error_invalid_file": "Invalid file format. Please upload a .csv file.",
    "error_unreadable_file": "Could not read the uploaded file. Please ensure it is a valid CSV file.",
    "error_no_name_column": "The CSV file must contain a column named 'Name'.",
    "error_no_player_id_column": "The uploaded CSV file is missing a 'Player ID' column.",
    "error_empty_name": "Player name is empty.",
    "error_no_valid_players": "No valid players found in the uploaded file.",
    "error_no_preview_data": "No preview data found. Please upload a file first.",
    "error_provision_failed": "Account provisioning failed: {error}",
    "error_file_too_large": "File is too large. Maximum size is 5MB.",
}
