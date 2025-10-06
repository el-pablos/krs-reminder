# 👤 User Guide - KRS Reminder Bot V3

**Version:** 3.0 Multi-User  
**Bot:** [@krs_reminderbot](https://t.me/krs_reminderbot)

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Login & Logout](#login--logout)
3. [View Schedule](#view-schedule)
4. [Understanding VA/VB](#understanding-vavb)
5. [Reminders](#reminders)
6. [FAQ](#faq)

---

## 🚀 Getting Started

### Step 1: Get Your Credentials

Hubungi admin untuk mendapatkan:
- ✅ **Secret Key** - Untuk login ke bot

### Step 2: Start Bot

1. Buka Telegram
2. Search: `@krs_reminderbot`
3. Klik **START**

### Step 3: Login

```
/login <secret_key>
```

**Contoh:**
```
/login xK9mP2nQ5rT8wY
```

**Success Response:**
```
✅ Login Berhasil!

👤 Username: tama
🔑 Session aktif selama 24 jam

Gunakan /jadwal untuk melihat jadwal Anda
```

---

## 🔐 Login & Logout

### Login

**Command:**
```
/login <secret_key>
```

**Example:**
```
/login rahasia123
```

**Notes:**
- Session aktif selama **24 jam**
- Setelah 24 jam, harus login ulang
- Satu user bisa login dari multiple devices

---

### Logout

**Command:**
```
/logout
```

**Response:**
```
✅ Logout Berhasil!

Gunakan /login untuk login kembali
```

**Notes:**
- Logout akan menghapus semua session aktif
- Harus login ulang untuk menggunakan bot

---

## 📅 View Schedule

### Command: `/jadwal`

Melihat jadwal kuliah untuk 7 hari ke depan.

**Example:**
```
/jadwal
```

**Response:**
```
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

━━━━━━━━━━━━━━━━━━━

📚 Simulasi Pemodelan
⏰ 13:00 - 15:00 WIB
👨‍🏫 Prof. Jane Smith
📍 Ruang 301
📖 Praktikum
```

---

## 🔄 Understanding VA/VB

### What is VA/VB?

**VA (Virtual Attendance)** dan **VB (Virtual Blended)** adalah sistem rotasi mingguan untuk menentukan mode perkuliahan.

### VA = Minggu Ganjil = ONLINE 🏠

- **Semua kelas ONLINE**
- Minggu 1, 3, 5, 7, 9, 11, 13, 15
- 💻 Kuliah dari rumah
- ⚠️ TIDAK perlu ke kampus

### VB = Minggu Genap = ONSITE 🏫

- **Semua kelas ONSITE**
- Minggu 2, 4, 6, 8, 10, 12, 14, 16
- 🏫 Hadir ke kampus
- 📍 Cek lokasi ruangan di jadwal

### Semester Start

**Semester dimulai:** 29 September 2025 = Minggu 1 = VA (Online)

### Quick Reference

| Minggu | Tanggal | Mode | Keterangan |
|--------|---------|------|------------|
| 1 | 29 Sep - 5 Okt | VA | 🏠 Online |
| 2 | 6 Okt - 12 Okt | VB | 🏫 Onsite |
| 3 | 13 Okt - 19 Okt | VA | 🏠 Online |
| 4 | 20 Okt - 26 Okt | VB | 🏫 Onsite |

---

## 🔔 Reminders

### Automatic Reminders

Bot akan otomatis mengirim reminder untuk setiap jadwal kuliah:

**Reminder Schedule:**
- ⏰ **5 jam sebelum** - Early warning
- ⏰ **3 jam sebelum** - Preparation time
- ⏰ **2 jam sebelum** - Get ready
- ⏰ **1 jam sebelum** - Final reminder
- ⏰ **Tepat waktu** - Class starting now!

### Reminder Format

```
🔔 REMINDER: 1 JAM LAGI

📚 Kecerdasan Artifisial
⏰ 08:00 - 10:00 WIB
👨‍🏫 Dr. John Doe
📍 Lab Komputer 1

🏫 VB (ONSITE) - Hadir ke kampus

⏱️ Dimulai dalam: 1 jam
```

### Notes

- ✅ Reminder otomatis untuk semua jadwal
- ✅ Tidak perlu setting manual
- ✅ Reminder dikirim via Telegram
- ✅ Tidak akan spam (hanya 5 reminder per event)

---

## ❓ FAQ

### Q: Bagaimana cara mendapatkan secret key?

**A:** Hubungi admin untuk mendapatkan secret key. Admin akan create account untuk Anda dan memberikan secret key.

---

### Q: Session expired, apa yang harus dilakukan?

**A:** Login ulang dengan command:
```
/login <secret_key>
```

Session aktif selama 24 jam. Setelah itu harus login ulang.

---

### Q: Jadwal tidak muncul saat `/jadwal`

**A:** Kemungkinan:
1. Belum login - Login dulu dengan `/login`
2. Jadwal belum di-import - Hubungi admin untuk import jadwal
3. Tidak ada jadwal untuk 7 hari ke depan

---

### Q: Tidak menerima reminder

**A:** Pastikan:
1. Sudah login (session aktif)
2. Jadwal sudah di-import oleh admin
3. Bot sedang running

Jika masih tidak menerima, hubungi admin.

---

### Q: Lupa secret key

**A:** Hubungi admin untuk reset atau generate secret key baru.

---

### Q: Bisa login dari multiple devices?

**A:** Ya, bisa. Satu user bisa login dari multiple Telegram accounts. Setiap login akan create session baru.

---

### Q: Bagaimana cara update jadwal?

**A:** Jadwal di-update otomatis oleh admin. Jika ada perubahan jadwal di Google Calendar, admin perlu run import ulang:
```
/admin_import_schedule <user_id>
```

---

### Q: Apakah data saya aman?

**A:** Ya, data Anda aman:
- ✅ Secret key di-hash dengan bcrypt
- ✅ Google Calendar token di-encrypt dengan AES-256
- ✅ Privacy isolation - user lain tidak bisa lihat jadwal Anda
- ✅ Session auto-expire setelah 24 jam

---

## 📞 Support

**Need Help?**
- Hubungi admin via Telegram
- Check documentation: README.md
- Report bugs: GitHub Issues

---

## 🎯 Quick Commands Reference

| Command | Description |
|---------|-------------|
| `/start` | Start bot & show welcome message |
| `/login <secret_key>` | Login to bot |
| `/logout` | Logout from bot |
| `/jadwal` | View schedule (7 days) |
| `/stats` | View bot statistics |

---

**Last Updated:** 2025-10-07  
**Version:** 3.0 Multi-User  
**Bot:** [@krs_reminderbot](https://t.me/krs_reminderbot)

