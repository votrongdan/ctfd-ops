# CTFd Account Provisioning Plugin

Automate player account creation for offline CTF competitions. Upload a CSV file with player IDs and names → the plugin generates usernames, passwords, imports accounts into CTFd, and produces a printable Word document with login credentials.

## Features

- **Single-upload workflow**: Upload a CSV list of players → preview → confirm → download credentials
- **Automatic username generation**: Converts Unicode/Vietnamese names to ASCII usernames combined with player ID (e.g., `Nguyễn Văn An` + `P001` → `nguyen_van_an_p001`)
- **Secure password generation**: Cryptographically secure, human-typeable passwords using Python `secrets`
- **Duplicate handling**: Automatic numbering for duplicate names (`nguyen_van_an_p001`, `nguyen_van_an_p001_1`)
- **CTFd-native import**: Uses CTFd's own `UserSchema` validation and database operations
- **Printable credential cards**: Generates a Word document with bordered cards containing name, username, and password
- **Bilingual support**: Full Vietnamese and English interface and document generation
- **Admin-only access**: Secured with CTFd's `@admins_only` decorator and CSRF protection

## Requirements

- CTFd 3.x (tested with 3.8.6)
- Python 3.11+
- Additional Python packages: `python-docx>=1.1.0`

## Installation

1. Copy the `ctfd-account-provisioning` directory into `CTFd/CTFd/plugins/`:

```bash
cp -r ctfd-account-provisioning /path/to/CTFd/CTFd/plugins/
```

2. Install dependencies:

```bash
pip install python-docx
```

3. Restart CTFd. The plugin will be loaded automatically.

4. Access the plugin at **Admin Panel → Plugins → Account Provisioning** (or directly at `/plugins/ctfd-account-provisioning/admin`).

## Input CSV Format

The input file must be a `.csv` file with two columns: **`Player ID`** and **`Name`** (case-insensitive headers):

| Player ID | Name |
|---|---|
| P001 | Nguyễn Văn An |
| P002 | Trần Thị Bình |
| P003 | Lê Quốc Việt |
| P004 | John Smith |
| P005 | Alice Johnson |

A sample file can be generated using:

```bash
cd CTFd/plugins/ctfd-account-provisioning
python create_sample.py
```

### Validation Rules
- File must be a valid `.csv` file (UTF-8 encoding, BOM supported)
- Must contain both `Player ID` and `Name` columns
- Empty rows are ignored
- Leading/trailing whitespace is trimmed
- Rows with empty Name or Player ID produce errors
- Duplicate Player IDs within the file produce errors

## Username Generation

| Player ID | Display Name | Generated Username |
|---|---|---|
| P001 | Nguyễn Văn An | `nguyen_van_an_p001` |
| P002 | Đặng Thị Hương | `dang_thi_huong_p002` |
| P003 | Trần Quốc Việt | `tran_quoc_viet_p003` |
| P004 | John Smith | `john_smith_p004` |

**Algorithm:**
1. Replace Vietnamese `đ`/`Đ` → `d`/`D`
2. Unicode NFKD normalization + remove combining marks
3. Convert to lowercase
4. Replace spaces, hyphens, dots → underscores
5. Remove all non-`[a-z0-9_]` characters
6. Collapse consecutive underscores
7. Strip leading/trailing underscores
8. Append `_{safe_player_id}` (player ID sanitized with same rules)

**Duplicate handling:** If `nguyen_van_an_p001` already exists (in DB or current batch), the plugin appends a counter: `nguyen_van_an_p001_1`, `nguyen_van_an_p001_2`, etc.

## Password Generation

- 10 characters, cryptographically secure (`secrets` module)
- Contains uppercase, lowercase, and digits
- Excludes ambiguous characters (`0`, `O`, `1`, `l`, `I`) for easy manual entry
- Each password in a batch is unique

## How It Uses CTFd's Import Mechanism

This plugin reuses the **exact same logic** as CTFd's built-in CSV user import (`CTFd/utils/csv/load_users_csv()`):

1. For each user, creates a dict with `name`, `email`, `password`
2. Passes it to `UserSchema().load()` for validation
3. On success, calls `db.session.add()` + `db.session.commit()`

The `Users` model automatically hashes passwords via its `@validates('password')` decorator using `bcrypt_sha256`.

**Why not call `load_users_csv()` directly?** Because that function doesn't provide per-user success/failure tracking with user IDs, which the plugin needs to know exactly which accounts were created for the credential document.

## Email Handling

CTFd's `UserSchema` requires a valid email. Since offline competitions typically don't use real emails, the plugin auto-generates placeholder emails:

- Format: `{username}@{domain}` (e.g., `nguyen_van_an_p001@ctf.local`)
- Domain is configurable in the settings panel (default: `ctf.local`)
- No real emails are sent

## Credential Word Document

After account creation, a `.docx` file is generated with printable credential cards:

- Each card contains: player name (Unicode preserved), username, password
- Cards have borders and clear visual separation
- Uses Calibri font for Vietnamese diacritics support
- Usernames shown in green monospace, passwords in red monospace
- Available in Vietnamese or English

## Vietnamese & English Support

- Admin interface labels, buttons, and messages support both languages
- Credential document labels support both languages
- Language is selectable in the settings panel
- Translation files: `i18n/en.py` and `i18n/vi.py`

## Security

| Measure | Implementation |
|---|---|
| Authorization | `@admins_only` on all routes |
| CSRF | Nonce in forms, `CSRF-Token` header for AJAX |
| File validation | Extension check + CSV format validation |
| Password storage | Hashed via bcrypt_sha256 (CTFd's mechanism) |
| No password logging | Passwords never written to logs |
| No DB plaintext | Passwords only in memory during request lifecycle |
| Temp data | Encrypted database storage (Fernet) with TTL expiration; auto-cleanup |
| File size | 5MB upload limit |

## Testing

Run tests with pytest from the CTFd root directory:

```bash
# Username generator and password generator tests (no CTFd context needed)
pytest CTFd/plugins/ctfd-account-provisioning/tests/test_username_generator.py -v
pytest CTFd/plugins/ctfd-account-provisioning/tests/test_password_generator.py -v

# CSV parser tests
pytest CTFd/plugins/ctfd-account-provisioning/tests/test_csv_parser.py -v

# Document generator tests
pytest CTFd/plugins/ctfd-account-provisioning/tests/test_document_generator.py -v

# Import adapter tests (uses mocking)
pytest CTFd/plugins/ctfd-account-provisioning/tests/test_ctfd_import_adapter.py -v

# All tests
pytest CTFd/plugins/ctfd-account-provisioning/tests/ -v
```

## Directory Structure

```
ctfd-account-provisioning/
├── __init__.py                  # Plugin entry point
├── config.py                    # Default settings
├── models.py                    # ProvisioningJob DB model (encrypted storage)
├── routes.py                    # Admin routes (upload/preview/provision/download)
├── create_sample.py             # Generate sample CSV
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── services/
│   ├── __init__.py
│   ├── csv_parser.py            # Parse .csv input (Player ID + Name)
│   ├── username_generator.py    # Unicode → ASCII username
│   ├── password_generator.py    # Secure random passwords
│   ├── participant_validator.py # Combine and validate data
│   ├── ctfd_import_adapter.py   # CTFd UserSchema-based import
│   ├── provisioning_service.py  # Orchestrate workflow
│   ├── document_generator.py    # Generate .docx credentials
│   └── storage.py               # Encrypted DB persistence (Fernet + TTL)
├── i18n/
│   ├── __init__.py              # Translation service
│   ├── en.py                    # English strings
│   └── vi.py                    # Vietnamese strings
├── templates/
│   └── account_provisioning.html
├── assets/
│   └── provisioning.js
├── sample/
│   └── sample_players.csv       # Generated by create_sample.py
└── tests/
    ├── __init__.py
    ├── test_csv_parser.py
    ├── test_username_generator.py
    ├── test_password_generator.py
    ├── test_ctfd_import_adapter.py
    └── test_document_generator.py
```

## License

Same as CTFd.
