# 🎓 KRS REMINDER BOT V3

> **Multi-User Telegram Bot untuk Reminder Jadwal Kuliah dengan Google Calendar Integration, VA/VB System & Database Backend**

Bot otomatis yang mengirim notifikasi Telegram untuk jadwal kuliah dengan format premium, terintegrasi dengan Google Calendar dan Supabase Database, dilengkapi dengan sistem multi-user, authentication, session management, dan VA/VB (Virtual Attendance / Virtual Blended) untuk menentukan mode perkuliahan (online/onsite).

**Bot Telegram:** [@krs_reminderbot](https://t.me/krs_reminderbot)  
**GitHub:** [el-pablos/krs-reminder](https://github.com/el-pablos/krs-reminder)  
**Status:** ✅ Production Ready | **Version:** V3 Multi-User | **Tests:** 5/5 PASSED

---

## 🆕 What's New in V3

- ✅ **Multi-User Support** - Multiple users can use the bot simultaneously
- ✅ **User Authentication** - Secure login with secret key (bcrypt hashing)
- ✅ **Session Management** - 24-hour sessions with auto-expiry
- ✅ **Database Backend** - Supabase PostgreSQL for data persistence
- ✅ **Admin Panel** - User management, schedule import, and more
- ✅ **Role-Based Access** - Admin and user roles with different permissions
- ✅ **Privacy Isolation** - Each user only sees their own schedules
- ✅ **Token Encryption** - Google Calendar tokens encrypted with AES-256

---

## 📑 Table of Contents

1. [System Architecture](#-system-architecture)
2. [Quick Start](#-quick-start)
3. [Installation & Setup](#-installation--setup)
4. [User Guide](#-user-guide)
5. [Admin Guide](#-admin-guide)
6. [Deployment](#-deployment)
7. [VA/VB Schedule System](#-vavb-schedule-system)
8. [Features](#-features)
9. [Commands Reference](#-commands-reference)
10. [Technical Implementation](#-technical-implementation)
11. [Testing](#-testing)
12. [Troubleshooting](#-troubleshooting)
13. [Development](#-development)

---

## 🏗️ System Architecture

### Architecture Diagram

\`\`\`mermaid
graph TB
    subgraph "User Interface"
        TG[Telegram Bot API]
    end
    
    subgraph "Application Layer"
        BOT[KRS Reminder Bot V3]
        AUTH[Auth Manager]
        ADMIN[Admin Manager]
        CMD[Command Handler]
    end
    
    subgraph "Data Layer"
        DB[(Supabase PostgreSQL)]
        GC[Google Calendar API]
    end
    
    subgraph "Background Services"
        SCHED[APScheduler]
        REM[Reminder System]
    end
    
    TG <-->|Messages| BOT
    BOT --> AUTH
    BOT --> ADMIN
    BOT --> CMD
    BOT <--> DB
    BOT <--> GC
    BOT --> SCHED
    SCHED --> REM
    REM -->|Send Reminders| TG
    
    style BOT fill:#4CAF50
    style DB fill:#FF9800
    style TG fill:#2196F3
\`\`\`

### Database Schema (ERD)

\`\`\`mermaid
erDiagram
    USERS ||--o{ SCHEDULES : has
    USERS ||--o{ SESSIONS : has
    USERS ||--o{ REMINDERS : receives
    SCHEDULES ||--o{ REMINDERS : triggers
    ADMINS ||--|| USERS : is
    
    USERS {
        uuid user_id PK
        string username UK
        string secret_key_hash
        text google_calendar_token_encrypted
        timestamp created_at
    }
    
    SCHEDULES {
        uuid schedule_id PK
        uuid user_id FK
        string course_name
        string course_code
        int day_of_week
        timestamp start_time
        timestamp end_time
        string location
        string facilitator
        string class_type
        string google_event_id
    }
    
    SESSIONS {
        uuid session_id PK
        uuid user_id FK
        bigint telegram_chat_id
        string session_token
        boolean is_active
        timestamp expires_at
        timestamp last_activity
    }
    
    ADMINS {
        uuid admin_id PK
        bigint telegram_chat_id UK
        jsonb permissions
        timestamp created_at
    }
    
    REMINDERS {
        uuid reminder_id PK
        uuid user_id FK
        uuid schedule_id FK
        string reminder_type
        timestamp scheduled_time
        timestamp sent_at
        string status
    }
\`\`\`

### User Authentication Flow

\`\`\`mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram
    participant B as Bot
    participant A as Auth Manager
    participant D as Database
    
    U->>T: /login <secret_key>
    T->>B: Forward command
    B->>A: Validate credentials
    A->>D: Query user by secret_key
    D-->>A: User data
    A->>A: Verify bcrypt hash
    A->>D: Create session
    D-->>A: Session created
    A-->>B: Login successful
    B-->>T: Success message
    T-->>U: "✅ Login Berhasil!"
\`\`\`

### Admin Workflow

\`\`\`mermaid
flowchart TD
    A[Admin Login] --> B{Authenticated?}
    B -->|Yes| C[Admin Dashboard]
    B -->|No| A
    
    C --> D[Add User]
    C --> E[List Users]
    C --> F[Import Schedule]
    C --> G[Delete User]
    
    D --> H[Generate Secret Key]
    H --> I[Create User in DB]
    I --> J[Give Secret Key to User]
    
    F --> K[Fetch from Google Calendar]
    K --> L[Parse Events]
    L --> M[Save to Database]
    M --> N[Schedule Reminders]
    
    style C fill:#4CAF50
    style D fill:#2196F3
    style F fill:#FF9800
\`\`\`

### Reminder Scheduling Flow

\`\`\`mermaid
sequenceDiagram
    participant S as Scheduler
    participant B as Bot
    participant D as Database
    participant T as Telegram
    
    S->>B: Check events (every 30 min)
    B->>D: Get all users
    D-->>B: User list
    
    loop For each user
        B->>D: Get user schedules
        D-->>B: Schedule list
        B->>B: Calculate reminder times
        B->>S: Schedule reminders (5h, 3h, 2h, 1h, exact)
    end
    
    S->>B: Trigger reminder
    B->>D: Get user session
    D-->>B: Telegram chat_id
    B->>T: Send reminder message
    T-->>User: 🔔 Reminder notification
\`\`\`

---

## ⚡ Quick Start

### For Users

1. **Get Credentials from Admin**
2. **Open Bot:** https://t.me/krs_reminderbot
3. **Login:** `/login <your_secret_key>`
4. **View Schedule:** `/jadwal`

### For Admin

1. **Login:** `/login admin_krs_2025`
2. **Add User:** `/admin_add_user tama`
3. **Import Schedule:** `/admin_import_schedule <user_id>`

---

## 🔧 Installation & Setup

### Prerequisites

- Python 3.10+
- Supabase account
- Telegram Bot Token
- Google Calendar API credentials

### Step 1: Clone Repository

\`\`\`bash
git clone https://github.com/el-pablos/krs-reminder.git
cd krs-reminder
\`\`\`

### Step 2: Install Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

**Dependencies:**
- `google-api-python-client` - Google Calendar integration
- `supabase` - Database client
- `bcrypt` - Password hashing
- `cryptography` - Token encryption
- `APScheduler` - Background job scheduling
- `pytz` - Timezone handling
- `requests` - HTTP client

### Step 3: Configure Credentials

1. **Telegram Bot Token**
   \`\`\`bash
   # Edit src/krs_reminder/config.py
   BOT_TOKEN = "your_telegram_bot_token"
   CHAT_ID = your_telegram_chat_id
   \`\`\`

2. **Supabase Configuration**
   \`\`\`bash
   # Create configs/supabase/config.json
   {
     "url": "https://your-project.supabase.co",
     "anon_key": "your_anon_key",
     "service_role_key": "your_service_role_key",
     "jwt_secret": "your_jwt_secret",
     "db_url": "postgresql://..."
   }
   \`\`\`

3. **Google Calendar**
   \`\`\`bash
   python3 scripts/auth/auth_final.py
   # Follow instructions to generate token
   \`\`\`

### Step 4: Setup Database

1. **Login to Supabase Dashboard**
   \`\`\`
   https://supabase.com/dashboard
   \`\`\`

2. **Run Migration SQL**
   - Go to SQL Editor
   - Copy content from `migrations/001_initial_schema.sql`
   - Paste and execute

3. **Verify Tables Created**
   - Check Table Editor
   - Should see: `users`, `schedules`, `sessions`, `admins`, `reminders`

### Step 5: Import Admin Data

\`\`\`bash
python3 scripts/migrate_admin_data.py
\`\`\`

**Expected Output:**
\`\`\`
✅ Admin user created
✅ 44 schedules imported
✅ Admin can login with: admin_krs_2025
\`\`\`

### Step 6: Start Bot

\`\`\`bash
./botctl.sh start
\`\`\`

**Verify:**
\`\`\`bash
./botctl.sh status
./botctl.sh logs
\`\`\`

---

## 👤 User Guide

### Getting Started

#### Step 1: Get Your Credentials

Contact admin to get:
- ✅ **Secret Key** - For login

#### Step 2: Start Bot

1. Open Telegram
2. Search: `@krs_reminderbot`
3. Click **START**

#### Step 3: Login

\`\`\`
/login <secret_key>
\`\`\`

**Example:**
\`\`\`
/login xK9mP2nQ5rT8wY
\`\`\`

**Success Response:**
\`\`\`
✅ Login Berhasil!

👤 Username: tama
🔑 Session aktif selama 24 jam

Gunakan /jadwal untuk melihat jadwal Anda
\`\`\`

### User Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start bot & show welcome | `/start` |
| `/login <key>` | Login to bot | `/login abc123` |
| `/logout` | Logout from bot | `/logout` |
| `/jadwal` | View schedule (7 days) | `/jadwal` |
| `/stats` | View bot statistics | `/stats` |

### View Schedule

\`\`\`
/jadwal
\`\`\`

**Response:**
\`\`\`
📅 JADWAL KULIAH MINGGU INI

🗓️ Periode: 7 - 13 Oktober 2025
📍 Minggu ke-2 (VB - Onsite)

━━━━━━━━━━━━━━━━━━━

📆 SENIN, 7 OKTOBER 2025

🏫 VB (ONSITE) - Hadir ke kampus

━━━━━━━━━━━━━━━━━━━

📚 Kecerdasan Artifisial
⏰ 08:00 - 10:00 WIB
👨‍🏫 Dr. John Doe
📍 Lab Komputer 1
📖 Kuliah Teori
\`\`\`

### Automatic Reminders

Bot automatically sends reminders:
- ⏰ **5 hours before** - Early warning
- ⏰ **3 hours before** - Preparation time
- ⏰ **2 hours before** - Get ready
- ⏰ **1 hour before** - Final reminder
- ⏰ **Exact time** - Class starting now!

### Interactive Buttons

After viewing schedule, use buttons:
- 📅 **Hari Ini** - Today's classes
- 📅 **Besok** - Tomorrow's classes
- 📅 **Minggu Ini** - This week's classes

### FAQ

**Q: Session expired, what to do?**  
A: Login again with `/login <secret_key>`. Sessions last 24 hours.

**Q: Schedule not showing?**  
A: Make sure you're logged in and admin has imported your schedule.

**Q: Forgot secret key?**  
A: Contact admin for reset or new key.

**Q: Can I login from multiple devices?**  
A: Yes, each login creates a new session.

**Q: How to change my schedule?**  
A: Contact admin to re-import from Google Calendar.

---

## 👨‍💼 Admin Guide

### Admin Overview

Admin adalah user dengan privilege khusus yang dapat:
- ✅ Menambah dan menghapus user
- ✅ Mengatur Google Calendar token untuk user
- ✅ Import jadwal dari Google Calendar ke database
- ✅ Melihat daftar semua user
- ✅ Mengelola sistem secara keseluruhan

**Default Admin:**
- Telegram Chat ID: `5476148500`
- Username: `admin`
- Secret Key: `admin_krs_2025`

### Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/admin_add_user <username> [key]` | Add new user | `/admin_add_user tama` |
| `/admin_list_users` | List all users | `/admin_list_users` |
| `/admin_import_schedule <user_id>` | Import schedule | `/admin_import_schedule abc123` |
| `/admin_delete_user <user_id>` | Delete user | `/admin_delete_user abc123` |

### 1. Add New User

**Command:**
\`\`\`
/admin_add_user <username> [secret_key]
\`\`\`

**Example:**
\`\`\`
/admin_add_user tama
\`\`\`

**Response:**
\`\`\`
✅ User berhasil ditambahkan!

👤 Username: tama
🆔 User ID: f68515aa-0e61-45db-aea7-ac1c3af0360d
🔑 Secret Key: xK9mP2nQ5rT8wY

⚠️ PENTING: Simpan secret key ini!
Berikan kepada user untuk login.
\`\`\`

**With Custom Secret Key:**
\`\`\`
/admin_add_user budi my_custom_key_123
\`\`\`

### 2. List All Users

**Command:**
\`\`\`
/admin_list_users
\`\`\`

**Response:**
\`\`\`
👥 Daftar User (3)
━━━━━━━━━━━━━━━━━━━
1. admin
   🆔 f68515aa...
   📅 Created: 2025-10-07
   
2. tama
   🆔 a1b2c3d4...
   📅 Created: 2025-10-07
   
3. budi
   🆔 e5f6g7h8...
   📅 Created: 2025-10-07
\`\`\`

### 3. Import Schedule

**Command:**
\`\`\`
/admin_import_schedule <user_id>
\`\`\`

**Example:**
\`\`\`
/admin_import_schedule f68515aa-0e61-45db-aea7-ac1c3af0360d
\`\`\`

**Response:**
\`\`\`
📥 Importing schedule...

✅ Import berhasil!
📊 Total events: 44
📅 Date range: 7 Okt - 31 Des 2025

User dapat melihat jadwal dengan /jadwal
\`\`\`

### 4. Delete User

**Command:**
\`\`\`
/admin_delete_user <user_id>
\`\`\`

**Example:**
\`\`\`
/admin_delete_user a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6
\`\`\`

**Response:**
\`\`\`
✅ User berhasil dihapus!

👤 Username: tama
🗑️ Deleted: schedules, sessions, reminders
\`\`\`

### Admin Workflows

#### Workflow 1: Onboard New User

1. **Add User**
   \`\`\`
   /admin_add_user tama
   \`\`\`

2. **Save Secret Key**
   - Copy secret key from response
   - Send to user via secure channel

3. **Setup Google Calendar** (if needed)
   - User generates token: `python3 scripts/auth/auth_final.py`
   - Admin imports schedule: `/admin_import_schedule <user_id>`

4. **Verify**
   - User logs in: `/login <secret_key>`
   - User views schedule: `/jadwal`

#### Workflow 2: Update User Schedule

1. **Get User ID**
   \`\`\`
   /admin_list_users
   \`\`\`

2. **Re-import Schedule**
   \`\`\`
   /admin_import_schedule <user_id>
   \`\`\`

3. **Verify**
   - User views updated schedule: `/jadwal`

---

## 🚀 Deployment

### Pre-Deployment Checklist

- ✅ Code committed to git
- ✅ All tests passing (5/5)
- ✅ Documentation complete
- ✅ Supabase account ready
- ✅ Telegram bot token configured
- ✅ Google Calendar credentials ready

### Step 1: Setup Database Tables

#### Option A: Via Supabase Dashboard (Recommended)

1. **Login to Supabase:**
   \`\`\`
   https://supabase.com/dashboard
   \`\`\`

2. **Select Project**

3. **Open SQL Editor:**
   - Click "SQL Editor" in left sidebar
   - Click "New query"

4. **Copy Migration SQL:**
   \`\`\`bash
   cat migrations/001_initial_schema.sql
   \`\`\`

5. **Paste and Execute:**
   - Paste SQL into editor
   - Click "Run" button
   - Wait for success message

6. **Verify Tables Created:**
   - Go to "Table Editor"
   - Should see tables: `users`, `schedules`, `sessions`, `admins`, `reminders`

### Step 2: Run Data Migration

\`\`\`bash
python3 scripts/migrate_admin_data.py
\`\`\`

**Expected Output:**
\`\`\`
✅ Admin user created: f68515aa-0e61-45db-aea7-ac1c3af0360d
✅ Admin in admins table
✅ Loaded 44 events from backup
✅ Inserted 44 schedules
✅ Verified: 44 schedules in database

Admin can now login with: /login admin_krs_2025
\`\`\`

### Step 3: Test Bot Functionality

\`\`\`bash
python3 tests/test_multiuser.py
\`\`\`

**Expected:**
\`\`\`
✅ PASS: Database Module
✅ PASS: Auth Module
✅ PASS: Admin Module
✅ PASS: Commands Module
✅ PASS: Bot Multi-User Init

Results: 5/5 tests passed
\`\`\`

### Step 4: Start Bot

\`\`\`bash
./botctl.sh start
\`\`\`

**Verify:**
\`\`\`bash
./botctl.sh status
./botctl.sh logs
\`\`\`

### Step 5: Test Admin Login

1. Open Telegram: @krs_reminderbot
2. Send: `/start`
3. Send: `/login admin_krs_2025`
4. Send: `/jadwal`

**Expected:** 44 events with VA/VB status

---

## 📅 VA/VB Schedule System

### Apa itu VA dan VB?

KRS Reminder Bot menggunakan sistem **VA/VB rotation** untuk menentukan mode perkuliahan berdasarkan minggu akademik:

#### 🏠 VA (Virtual Attendance) = Minggu Ganjil

- **Semua kelas ONLINE** (tidak ada tatap muka)
- Minggu 1, 3, 5, 7, 9, 11, 13, 15
- 💻 Kuliah dari rumah
- ⚠️ TIDAK ADA tatap muka di kampus

#### 🏫 VB (Virtual Blended) = Minggu Genap

- **Semua kelas ONSITE** (tatap muka)
- Minggu 2, 4, 6, 8, 10, 12, 14, 16
- 🏫 Hadir ke kampus sesuai jadwal
- 📍 Cek lokasi ruangan di jadwal

### Semester Start Date

**Semester dimulai:** 29 September 2025

| Minggu | Tanggal | Mode | Status |
|--------|---------|------|--------|
| Minggu 1 | 29 Sep - 5 Okt 2025 | VA | 🏠 Online |
| Minggu 2 | 6 Okt - 12 Okt 2025 | VB | 🏫 Onsite |
| Minggu 3 | 13 Okt - 19 Okt 2025 | VA | �� Online |
| Minggu 4 | 20 Okt - 26 Okt 2025 | VB | 🏫 Onsite |

### How It Works

Bot automatically calculates:
1. **Current week number** from semester start
2. **VA/VB status** based on week parity
3. **Display mode** in schedule messages

**Example:**
\`\`\`
📍 Minggu ke-2 (VB - Onsite)
🏫 VB (ONSITE) - Hadir ke kampus
\`\`\`

---

## ✨ Features

### Core Features

- ✅ **Multi-User Support** - Multiple users with isolated schedules
- ✅ **User Authentication** - Secure login with bcrypt
- ✅ **Session Management** - 24-hour auto-expiring sessions
- ✅ **Database Backend** - Supabase PostgreSQL
- ✅ **Admin Panel** - Complete user management
- ✅ **Role-Based Access** - Admin vs user permissions
- ✅ **Privacy Isolation** - Users only see their own data

### Schedule Features

- ✅ **Google Calendar Integration** - Import from Google Calendar
- ✅ **VA/VB System** - Automatic online/onsite detection
- ✅ **Multi-Stage Reminders** - 5h, 3h, 2h, 1h, exact time
- ✅ **Interactive Buttons** - Easy navigation
- ✅ **Premium Formatting** - Beautiful message layout
- ✅ **Timezone Support** - Asia/Jakarta (WIB)

### Security Features

- ✅ **Password Hashing** - bcrypt with salt
- ✅ **Token Encryption** - AES-256 for Google tokens
- ✅ **Session Tokens** - Secure random tokens
- ✅ **Auto-Expiry** - Sessions expire after 24 hours
- ✅ **Input Validation** - Prevent SQL injection

### Technical Features

- ✅ **Background Scheduling** - APScheduler
- ✅ **Auto-Refresh** - Check events every 30 minutes
- ✅ **Error Handling** - Comprehensive error messages
- ✅ **Logging** - Detailed logs for debugging
- ✅ **Testing** - 5/5 tests passing

---

## �� Commands Reference

### User Commands

| Command | Description | Auth Required | Example |
|---------|-------------|---------------|---------|
| `/start` | Start bot & show welcome | No | `/start` |
| `/login <key>` | Login to bot | No | `/login abc123` |
| `/logout` | Logout from bot | Yes | `/logout` |
| `/jadwal` | View schedule (7 days) | Yes | `/jadwal` |
| `/stats` | View bot statistics | No | `/stats` |

### Admin Commands

| Command | Description | Admin Only | Example |
|---------|-------------|------------|---------|
| `/admin_add_user <username> [key]` | Add new user | Yes | `/admin_add_user tama` |
| `/admin_list_users` | List all users | Yes | `/admin_list_users` |
| `/admin_import_schedule <user_id>` | Import schedule | Yes | `/admin_import_schedule abc123` |
| `/admin_delete_user <user_id>` | Delete user | Yes | `/admin_delete_user abc123` |

### Interactive Buttons

| Button | Description | Action |
|--------|-------------|--------|
| 📅 Hari Ini | Show today's classes | Filter by today |
| 📅 Besok | Show tomorrow's classes | Filter by tomorrow |
| 📅 Minggu Ini | Show this week's classes | Filter by 7 days |

---

## 🔬 Technical Implementation

### Technology Stack

**Backend:**
- Python 3.10+
- Supabase PostgreSQL
- REST API (direct HTTP requests)

**Authentication:**
- bcrypt (password hashing)
- Fernet/AES-256 (token encryption)
- Session tokens (24-hour expiry)

**Bot Framework:**
- Telegram Bot API
- APScheduler (background jobs)
- Google Calendar API
- pytz (timezone handling)

### Project Structure

\`\`\`
krs-reminder/
├── src/
│   └── krs_reminder/
│       ├── bot.py              # Main bot class
│       ├── database.py         # Database operations
│       ├── auth.py             # Authentication
│       ├── admin.py            # Admin operations
│       ├── commands.py         # Command handlers
│       └── config.py           # Configuration
├── scripts/
│   ├── migrate_admin_data.py  # Data migration
│   └── auth/
│       └── auth_final.py      # Google Calendar auth
├── migrations/
│   └── 001_initial_schema.sql # Database schema
├── tests/
│   └── test_multiuser.py      # Multi-user tests
├── configs/
│   └── supabase/
│       └── config.json        # Supabase config
├── var/
│   └── backup_admin_schedule.json
├── requirements.txt
├── botctl.sh
└── README.md
\`\`\`

### Database Schema

**Tables:**
1. `users` - User accounts
2. `schedules` - Class schedules
3. `sessions` - Active sessions
4. `admins` - Admin privileges
5. `reminders` - Scheduled reminders

**Relationships:**
- User → Schedules (1:N)
- User → Sessions (1:N)
- User → Reminders (1:N)
- Schedule → Reminders (1:N)
- Admin → User (1:1)

### Security Implementation

**Password Hashing:**
\`\`\`python
import bcrypt

# Hash password
hashed = bcrypt.hashpw(secret_key.encode(), bcrypt.gensalt())

# Verify password
bcrypt.checkpw(input_key.encode(), stored_hash)
\`\`\`

**Token Encryption:**
\`\`\`python
from cryptography.fernet import Fernet

# Encrypt token
cipher = Fernet(encryption_key)
encrypted = cipher.encrypt(token.encode())

# Decrypt token
decrypted = cipher.decrypt(encrypted).decode()
\`\`\`

### Reminder Scheduling

**Algorithm:**
1. Fetch all users from database
2. For each user:
   - Get schedules for next 7 days
   - Calculate reminder times (5h, 3h, 2h, 1h, exact)
   - Schedule reminders with APScheduler
3. When reminder triggers:
   - Get user session (telegram_chat_id)
   - Format message with VA/VB status
   - Send via Telegram API

**Code:**
\`\`\`python
def check_and_schedule_multiuser(self):
    users = self.db.list_all_users()
    for user in users:
        schedules = self.db.get_user_schedules(user['user_id'])
        self.schedule_reminders_for_user(user, schedules)
\`\`\`

---

## 🧪 Testing

### Run All Tests

\`\`\`bash
python3 tests/test_multiuser.py
\`\`\`

### Test Coverage

| Test | Description | Status |
|------|-------------|--------|
| Database Module | Test database connection | ✅ PASS |
| Auth Module | Test authentication | ✅ PASS |
| Admin Module | Test admin operations | ✅ PASS |
| Commands Module | Test command handlers | ✅ PASS |
| Bot Multi-User Init | Test bot initialization | ✅ PASS |

**Results:** 5/5 tests passed (100%)

### Manual Testing

**Test Admin Login:**
\`\`\`bash
# 1. Start bot
./botctl.sh start

# 2. Open Telegram
# 3. Send: /login admin_krs_2025
# 4. Send: /jadwal
# 5. Verify: 44 events displayed
\`\`\`

**Test User Creation:**
\`\`\`bash
# 1. Admin: /admin_add_user tama
# 2. Copy secret key
# 3. User: /login <secret_key>
# 4. User: /jadwal
# 5. Verify: User's schedule displayed
\`\`\`

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Bot Not Starting

**Symptoms:**
- Bot doesn't respond
- No logs generated

**Solutions:**
\`\`\`bash
# Check bot status
./botctl.sh status

# Check logs
./botctl.sh logs

# Restart bot
./botctl.sh restart

# Check Python errors
python3 -m krs_reminder.cli.run_bot
\`\`\`

#### 2. Database Connection Failed

**Symptoms:**
- "Database connection error"
- "Failed to fetch data"

**Solutions:**
\`\`\`bash
# Verify Supabase config
cat configs/supabase/config.json

# Test database connection
python3 << 'EOF'
from krs_reminder.database import SupabaseClient
db = SupabaseClient()
print("✅ Database connected")
EOF

# Check network connectivity
ping qdklwiuazobrmyjrofdq.supabase.co
\`\`\`

#### 3. Login Failed

**Symptoms:**
- "Invalid secret key"
- "User not found"

**Solutions:**
\`\`\`bash
# Verify user exists
# Admin: /admin_list_users

# Reset secret key
# Admin: /admin_delete_user <user_id>
# Admin: /admin_add_user <username>

# Check session expiry
# User: /logout
# User: /login <secret_key>
\`\`\`

#### 4. Schedule Not Showing

**Symptoms:**
- Empty schedule
- "No events found"

**Solutions:**
\`\`\`bash
# Verify user logged in
# User: /login <secret_key>

# Check database
python3 << 'EOF'
from krs_reminder.database import SupabaseClient
db = SupabaseClient()
schedules = db.get_user_schedules('<user_id>')
print(f"Found {len(schedules)} schedules")
EOF

# Re-import schedule
# Admin: /admin_import_schedule <user_id>
\`\`\`

#### 5. Reminders Not Sending

**Symptoms:**
- No reminder notifications
- Reminders delayed

**Solutions:**
\`\`\`bash
# Check scheduler running
./botctl.sh logs | grep "Scheduler"

# Verify session active
# User: /login <secret_key>

# Check reminder times
# Reminders sent: 5h, 3h, 2h, 1h before class

# Restart bot
./botctl.sh restart
\`\`\`

### Debug Mode

**Enable Debug Logging:**
\`\`\`python
# Edit src/krs_reminder/bot.py
import logging
logging.basicConfig(level=logging.DEBUG)
\`\`\`

**Check Logs:**
\`\`\`bash
tail -f var/bot.log
\`\`\`

### Get Help

**Contact:**
- Email: yeteprem.end23juni@gmail.com
- GitHub Issues: https://github.com/el-pablos/krs-reminder/issues

---

## 💻 Development

### Setup Development Environment

\`\`\`bash
# Clone repository
git clone https://github.com/el-pablos/krs-reminder.git
cd krs-reminder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install
\`\`\`

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Add comments for complex logic

### Testing

\`\`\`bash
# Run all tests
python3 tests/test_multiuser.py

# Run specific test
python3 -c "from tests.test_multiuser import *; test_database_module()"
\`\`\`

### Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "feat: add my feature"`
4. Push to branch: `git push origin feature/my-feature`
5. Create Pull Request

### Commit Message Format

\`\`\`
<type>: <description>

[optional body]

[optional footer]
\`\`\`

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style
- `refactor` - Code refactoring
- `test` - Testing
- `chore` - Maintenance

---

## 📄 License

This project is licensed under the MIT License.

---

## ��‍💻 Author

**Developer:** el-pablos  
**Email:** yeteprem.end23juni@gmail.com  
**GitHub:** https://github.com/el-pablos

---

## 🙏 Acknowledgments

- Telegram Bot API
- Google Calendar API
- Supabase
- Python Community

---

**Last Updated:** 2025-10-07  
**Version:** V3 Multi-User  
**Status:** ✅ Production Ready
