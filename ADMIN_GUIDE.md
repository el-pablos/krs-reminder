# 👨‍💼 Admin Guide - KRS Reminder Bot V3

**Version:** 3.0 Multi-User  
**Last Updated:** 2025-10-07

---

## 📋 Table of Contents

1. [Admin Overview](#admin-overview)
2. [Admin Commands](#admin-commands)
3. [User Management](#user-management)
4. [Schedule Management](#schedule-management)
5. [Database Management](#database-management)
6. [Troubleshooting](#troubleshooting)

---

## 👑 Admin Overview

### What is an Admin?

Admin adalah user dengan privilege khusus yang dapat:
- ✅ Menambah dan menghapus user
- ✅ Mengatur Google Calendar token untuk user
- ✅ Import jadwal dari Google Calendar ke database
- ✅ Melihat daftar semua user
- ✅ Mengelola sistem secara keseluruhan

### Admin Telegram ID

Admin ditentukan berdasarkan **Telegram Chat ID** yang terdaftar di database.

**Default Admin:**
- Telegram Chat ID: `5476148500`
- Username: `admin`
- Secret Key: `admin_krs_2025`

---

## 🎮 Admin Commands

### 1. `/admin_add_user` - Tambah User Baru

**Format:**
```
/admin_add_user <username> [secret_key]
```

**Contoh:**
```
/admin_add_user tama
/admin_add_user tama rahasia123
```

**Output:**
```
✅ User Berhasil Dibuat!

👤 Username: tama
🔑 Secret Key: rahasia123
🆔 User ID: 550e8400-e29b-41d4-a716-446655440000

⚠️  PENTING: Simpan secret key ini!
Berikan ke user untuk login.
```

**Notes:**
- Jika `secret_key` tidak diberikan, sistem akan generate otomatis
- Secret key di-hash dengan bcrypt sebelum disimpan
- Berikan secret key ke user untuk login

---

### 2. `/admin_list_users` - Lihat Daftar User

**Format:**
```
/admin_list_users
```

**Output:**
```
👥 Daftar User (3)

━━━━━━━━━━━━━━━━━━━

1. admin
   🆔 550e8400-e29b-41d4-a716-446655440000
   📅 Calendar: ✅

2. tama
   🆔 660e8400-e29b-41d4-a716-446655440001
   📅 Calendar: ❌

3. budi
   🆔 770e8400-e29b-41d4-a716-446655440002
   📅 Calendar: ✅
```

**Legend:**
- ✅ Calendar: User sudah setup Google Calendar token
- ❌ Calendar: User belum setup Google Calendar token

---

### 3. `/admin_import_schedule` - Import Jadwal User

**Format:**
```
/admin_import_schedule <user_id>
```

**Contoh:**
```
/admin_import_schedule 550e8400-e29b-41d4-a716-446655440000
```

**Output:**
```
✅ Import Berhasil!

📅 Total jadwal: 44
📆 Range: 30 hari ke depan

Jadwal berhasil diimport dari Google Calendar
```

**Prerequisites:**
- User harus sudah setup Google Calendar token
- Google Calendar harus memiliki events

**Notes:**
- Import jadwal 30 hari ke depan
- Jadwal lama akan dihapus dan diganti dengan yang baru
- Parsing otomatis: course name, facilitator, location, class type

---

### 4. `/admin_delete_user` - Hapus User

**Format:**
```
/admin_delete_user <user_id>
```

**Contoh:**
```
/admin_delete_user 660e8400-e29b-41d4-a716-446655440001
```

**Output:**
```
✅ User berhasil dihapus
```

**⚠️  WARNING:**
- Menghapus user akan menghapus SEMUA data user:
  - User account
  - Semua schedules
  - Semua sessions
  - Semua reminders
- **Tidak bisa di-undo!**
- Pastikan user_id benar sebelum menghapus

---

## 👥 User Management

### Workflow: Menambah User Baru

1. **Admin menambah user:**
   ```
   /admin_add_user tama
   ```

2. **Sistem generate secret key:**
   ```
   Secret Key: xK9mP2nQ5rT8wY
   ```

3. **Admin memberikan credentials ke user:**
   - Username: `tama`
   - Secret Key: `xK9mP2nQ5rT8wY`

4. **User login via Telegram:**
   ```
   /login xK9mP2nQ5rT8wY
   ```

5. **User bisa menggunakan bot:**
   ```
   /jadwal
   ```

---

## 📅 Schedule Management

### Import Jadwal dari Google Calendar

**Step 1: Setup Google Calendar Token**

Untuk sekarang, Google Calendar token harus di-setup manual via database atau script.

**Step 2: Import Schedule**

```
/admin_import_schedule <user_id>
```

**Step 3: Verify**

User bisa cek jadwal dengan:
```
/jadwal
```

### Format Event di Google Calendar

Bot akan parsing event dengan format:

**Event Title:**
```
📚 Kecerdasan Artifisial
```

**Event Description:**
```
📚 Mata Kuliah: Kecerdasan Artifisial
👨‍🏫 Dosen: Dr. John Doe
🔢 Kode: CS401
📍 Lokasi: Lab Komputer 1
📖 Tipe: Kuliah Teori
```

**Event Location:**
```
Lab Komputer 1
```

---

## 🗄️ Database Management

### Database Schema

**Tables:**
- `users` - User accounts
- `schedules` - User schedules
- `sessions` - Active sessions
- `admins` - Admin list
- `reminders` - Reminder tracking

### Manual Database Access

**Via Supabase Dashboard:**
1. Login ke https://supabase.com
2. Pilih project: `qdklwiuazobrmyjrofdq`
3. Go to Table Editor
4. Select table

**Via SQL:**
```sql
-- List all users
SELECT * FROM users;

-- List all admins
SELECT * FROM admins;

-- List schedules for user
SELECT * FROM schedules WHERE user_id = '<user_id>';
```

---

## 🔧 Troubleshooting

### User tidak bisa login

**Problem:** User mendapat error "Secret key tidak valid"

**Solution:**
1. Cek apakah user sudah dibuat: `/admin_list_users`
2. Jika belum, buat user baru: `/admin_add_user <username>`
3. Berikan secret key yang benar ke user

---

### Import schedule gagal

**Problem:** `/admin_import_schedule` error

**Possible Causes:**
1. User belum setup Google Calendar token
2. Google Calendar tidak memiliki events
3. Network error

**Solution:**
1. Verify user has calendar token: `/admin_list_users`
2. Check Google Calendar has events
3. Try again later

---

### User tidak menerima reminder

**Problem:** User sudah login dan ada jadwal, tapi tidak dapat reminder

**Possible Causes:**
1. User tidak memiliki active session
2. Reminder system belum running
3. Schedule belum di-import

**Solution:**
1. User harus login ulang: `/login <secret_key>`
2. Verify bot running: `./botctl.sh status`
3. Import schedule: `/admin_import_schedule <user_id>`

---

## 📞 Support

**Admin Contact:**
- Telegram: @admin_username
- Email: admin@example.com

**Documentation:**
- README.md - General documentation
- USER_GUIDE.md - User guide
- ADMIN_GUIDE.md - This file

---

**Last Updated:** 2025-10-07  
**Version:** 3.0 Multi-User

