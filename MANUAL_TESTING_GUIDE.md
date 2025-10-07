# 📝 Manual Testing Guide - Authorization Fixes

## Admin Information
- **Telegram ID:** 5476148500
- **Username:** @ImTamaa
- **Secret Key:** `jembotisme`

---

## Test Scenarios

### ✅ Test 1: Admin Login
**Steps:**
1. Open Telegram and go to @krs_reminderbot
2. Send command: `/login jembotisme`

**Expected Result:**
```
✅ Login Berhasil!

👤 Username: admin
🔑 Session aktif selama 24 jam

Gunakan /jadwal untuk melihat jadwal Anda
```

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 2: Admin Views Weekly Schedule (Inline Button)
**Steps:**
1. Make sure you're logged in (Test 1)
2. Send command: `/start`
3. Click the "📅 Jadwal Mingguan" button

**Expected Result:**
- Should display admin's schedule (10 events)
- Should NOT display any other user's schedule
- Schedule should be filtered by admin's user_id

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 3: Admin Views Daily Schedule (Inline Button)
**Steps:**
1. Make sure you're logged in (Test 1)
2. Send command: `/start`
3. Click the "📆 Jadwal Harian" button
4. Select a day (e.g., "Senin")

**Expected Result:**
- Should display admin's schedule for selected day
- Should NOT display any other user's schedule
- Schedule should be filtered by admin's user_id

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 4: Unauthenticated User Clicks Buttons
**Steps:**
1. Logout first: `/logout`
2. Send command: `/start`
3. Click any button (e.g., "📅 Jadwal Mingguan")

**Expected Result:**
```
❌ Anda belum login. Gunakan /login <secret_key>
```

**Admin should receive notification:**
```
🚨 Unauthorized Access Attempt

👤 User: [Name]
🆔 Username: @[username]
💬 Chat ID: [chat_id]
🔴 Action: Callback: jadwal_weekly

━━━━━━━━━━━━━━━━━━━

💡 Suggested command to add user:
/admin add_user [username] [secret_key]
```

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 5: /stats Command (No HTML Errors)
**Steps:**
1. Make sure you're logged in (Test 1)
2. Send command: `/stats`

**Expected Result:**
- Should display bot statistics
- Should NOT show any HTML parsing errors
- Should display properly formatted message with:
  - Uptime
  - Server time
  - Jobs aktif
  - Reminder terkirim
  - CPU & Memory usage
  - Configuration
  - Connections

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 6: /jadwal Command (Privacy Isolation)
**Steps:**
1. Make sure you're logged in (Test 1)
2. Send command: `/jadwal`

**Expected Result:**
- Should display admin's schedule (10 events)
- Should NOT display any other user's schedule
- Schedule should be filtered by admin's user_id

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 7: Login with Wrong Secret Key
**Steps:**
1. Logout first: `/logout`
2. Send command: `/login wrong_key_12345`

**Expected Result:**
```
❌ Secret key tidak valid

Pastikan Anda memasukkan secret key yang benar.
Hubungi admin jika Anda lupa secret key Anda.
```

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 8: Login with Missing Secret Key
**Steps:**
1. Logout first: `/logout`
2. Send command: `/login` (without secret key)

**Expected Result:**
```
❌ Format salah!

Gunakan: /login <secret_key>

Contoh: /login rahasia123
```

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 9: Already Logged In
**Steps:**
1. Make sure you're logged in (Test 1)
2. Send command: `/login jembotisme` again

**Expected Result:**
```
⚠️  Anda sudah login sebagai admin
```

**Status:** [ ] PASS / [ ] FAIL

---

### ✅ Test 10: Unauthenticated User Sends /jadwal
**Steps:**
1. Logout first: `/logout`
2. Send command: `/jadwal`

**Expected Result:**
```
❌ Anda belum terdaftar di sistem.

📋 Untuk menggunakan bot ini:

1️⃣ Kirim jadwal kuliah Anda ke admin: @ImTamaa
2️⃣ Admin akan menambahkan Anda ke database
3️⃣ Anda akan menerima secret key untuk login
4️⃣ Login dengan command:
     /login <secret_key>

━━━━━━━━━━━━━━━━━━━

📧 Hubungi admin untuk registrasi: @ImTamaa

ℹ️ Bot ini menggunakan sistem multi-user dengan autentikasi untuk menjaga privasi jadwal setiap user.
```

**Admin should receive notification:**
```
🚨 Unauthorized Access Attempt

👤 User: [Name]
🆔 Username: @[username]
💬 Chat ID: [chat_id]
🔴 Action: Command: /jadwal

━━━━━━━━━━━━━━━━━━━

💡 Suggested command to add user:
/admin add_user [username] [secret_key]
```

**Status:** [ ] PASS / [ ] FAIL

---

## Summary

| Test | Description | Status |
|------|-------------|--------|
| 1 | Admin Login | [ ] |
| 2 | Admin Views Weekly Schedule | [ ] |
| 3 | Admin Views Daily Schedule | [ ] |
| 4 | Unauthenticated User Clicks Buttons | [ ] |
| 5 | /stats Command (No HTML Errors) | [ ] |
| 6 | /jadwal Command (Privacy Isolation) | [ ] |
| 7 | Login with Wrong Secret Key | [ ] |
| 8 | Login with Missing Secret Key | [ ] |
| 9 | Already Logged In | [ ] |
| 10 | Unauthenticated User Sends /jadwal | [ ] |

**Total Tests:** 10  
**Passed:** ___  
**Failed:** ___  
**Success Rate:** ___%

---

## Notes

- All tests should be performed via Telegram (@krs_reminderbot)
- Make sure to test both authenticated and unauthenticated scenarios
- Verify that admin receives notifications for unauthorized access attempts
- Check that schedules are properly isolated (admin only sees admin's schedule)
- Verify that all error messages are clear and helpful
- Ensure no HTML parsing errors occur

---

## Expected Outcomes (All Tests)

After completing all tests:

- ✅ Inline keyboard buttons require authentication
- ✅ Schedules are completely isolated - users can only see their own schedules
- ✅ `/stats` command works without HTML parsing errors
- ✅ Admin check queries use correct data types
- ✅ Admin notifications work when unauthenticated users attempt access
- ✅ `/login jembotisme` works correctly for admin user
- ✅ Login errors show specific, helpful error messages
- ✅ Bot is running without errors in logs

---

## Troubleshooting

### If a test fails:

1. **Check bot status:**
   ```bash
   ./botctl.sh status
   ```

2. **Check bot logs:**
   ```bash
   ./botctl.sh logs
   ```

3. **Restart bot if needed:**
   ```bash
   ./botctl.sh restart
   ```

4. **Verify database connection:**
   - Check Supabase dashboard
   - Verify tables: users, sessions, admins, schedules

5. **Report issue with:**
   - Test number
   - Expected result
   - Actual result
   - Error message (if any)
   - Screenshot (if applicable)

---

## Contact

**Developer:** el-pablos  
**Telegram:** @ImTamaa  
**Date:** 2025-10-07  
**Version:** V3 Multi-User  
**Commit:** e17f6d3

