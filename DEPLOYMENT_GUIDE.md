# 🚀 Deployment Guide - KRS Reminder Bot V3

**Version:** 3.0 Multi-User  
**Date:** 2025-10-07

---

## 📋 Pre-Deployment Checklist

- ✅ Code committed to git
- ✅ All tests passing (5/5)
- ✅ Documentation complete
- ✅ Supabase account ready
- ✅ Telegram bot token configured
- ✅ Google Calendar credentials ready

---

## 🗄️ Step 1: Setup Database Tables

### Option A: Via Supabase Dashboard (Recommended)

1. **Login to Supabase:**
   ```
   https://supabase.com/dashboard
   ```

2. **Select Project:**
   - Project: `qdklwiuazobrmyjrofdq`
   - URL: `https://qdklwiuazobrmyjrofdq.supabase.co`

3. **Open SQL Editor:**
   - Click "SQL Editor" in left sidebar
   - Click "New query"

4. **Copy Migration SQL:**
   ```bash
   cat migrations/001_initial_schema.sql
   ```

5. **Paste and Execute:**
   - Paste SQL into editor
   - Click "Run" button
   - Wait for success message

6. **Verify Tables Created:**
   - Go to "Table Editor"
   - Should see tables: `users`, `schedules`, `sessions`, `admins`, `reminders`

### Option B: Via Script (If network allows)

```bash
python3 scripts/create_tables_direct.py
```

**Note:** May fail due to IPv6 network issues. Use Option A if this fails.

---

## 👤 Step 2: Create Admin User & Import Data

### 2.1: Run Migration Script

```bash
python3 scripts/migrate_admin_data.py
```

**Expected Output:**
```
============================================================
📦 PHASE 4: Data Migration - Admin Schedule
============================================================

👤 Admin: admin
📱 Telegram ID: 5476148500

📝 Step 1: Create admin user...
✅ Admin user created: <user_id>

📝 Step 2: Ensure admin in admins table...
✅ Admin added to admins table

📝 Step 3: Load backup data...
✅ Loaded 44 events from backup

📝 Step 4: Parse and insert schedules...
✅ Parsed 44 schedules

📝 Step 5: Delete old schedules...
✅ Old schedules deleted

📝 Step 6: Bulk insert schedules...
✅ Inserted 44 schedules

📝 Step 7: Verify...
✅ Verified: 44 schedules in database

============================================================
✅ PHASE 4 COMPLETE: Data Migration Success!
============================================================

📊 Summary:
  • Admin User ID: <uuid>
  • Admin Username: admin
  • Admin Secret Key: admin_krs_2025
  • Total Schedules: 44

💡 Admin can now login with:
   /login admin_krs_2025
```

### 2.2: Verify Migration

```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from krs_reminder.database import SupabaseClient

db = SupabaseClient()
users = db.list_all_users()
print(f'✅ Total users: {len(users)}')

for user in users:
    print(f'  - {user[\"username\"]} (ID: {user[\"user_id\"]})')
"
```

---

## 🤖 Step 3: Test Bot Functionality

### 3.1: Test Bot Initialization

```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from krs_reminder.bot import KRSReminderBotV2

bot = KRSReminderBotV2()
print(f'✅ Bot initialized')
print(f'   Multi-user: {bot.multi_user_enabled}')
print(f'   Database: {\"Connected\" if bot.db else \"Not connected\"}')
print(f'   Auth: {\"Ready\" if bot.auth else \"Not ready\"}')
print(f'   Admin: {\"Ready\" if bot.admin else \"Not ready\"}')
"
```

### 3.2: Run Multi-User Tests

```bash
python3 tests/test_multiuser.py
```

**Expected:** All 5 tests should pass

### 3.3: Test Admin Login (Manual)

1. Open Telegram
2. Search: `@krs_reminderbot`
3. Send: `/start`
4. Send: `/login admin_krs_2025`

**Expected Response:**
```
✅ Login Berhasil!

👤 Username: admin
🔑 Session aktif selama 24 jam

Gunakan /jadwal untuk melihat jadwal Anda
```

### 3.4: Test Admin Schedule View

Send: `/jadwal`

**Expected:** Should show 44 events with VA/VB status

### 3.5: Test Admin Commands

```
/admin_list_users
```

**Expected:** Should show admin user

---

## 🚀 Step 4: Deploy Bot

### 4.1: Stop Old Bot (if running)

```bash
./botctl.sh stop
```

### 4.2: Start New Bot

```bash
./botctl.sh start
```

### 4.3: Check Status

```bash
./botctl.sh status
```

**Expected Output:**
```
✅ Bot is running (PID: xxxxx)
```

### 4.4: Monitor Logs

```bash
./botctl.sh logs
```

**Look for:**
- ✅ "Multi-user support enabled"
- ✅ "Bot started successfully"
- ✅ No errors in initialization

---

## ✅ Step 5: Final Verification

### 5.1: Verify Multi-User Features

**Test Checklist:**
- [ ] Admin can login with `/login admin_krs_2025`
- [ ] Admin can see 44 events with `/jadwal`
- [ ] VA/VB status shows correctly (Week 2 = VB = Onsite)
- [ ] Interactive buttons work (Today, Tomorrow, Week, etc.)
- [ ] Admin commands work (`/admin_list_users`)
- [ ] Reminders are scheduled (check logs)

### 5.2: Verify VA/VB System

Current date: **October 7, 2025**
- Week: **2** (VB - Onsite)
- Expected: All events should show "🏫 VB (ONSITE)"

### 5.3: Verify Reminder System

Check logs for:
```
⏰ Scheduling reminders from 2025-10-07...
👥 Checking 1 users...
  👤 admin: X events
✅ Processed X events
```

---

## 🔧 Troubleshooting

### Issue: Tables not created

**Solution:**
1. Manually create via Supabase Dashboard (Step 1, Option A)
2. Verify with: `python3 scripts/setup_tables_via_api.py`

### Issue: Migration fails

**Possible Causes:**
- Tables don't exist → Create tables first
- Network error → Check internet connection
- Invalid backup file → Verify `var/backup_admin_schedule.json` exists

**Solution:**
```bash
# Verify backup exists
ls -lh var/backup_admin_schedule.json

# Re-run migration
python3 scripts/migrate_admin_data.py
```

### Issue: Admin can't login

**Possible Causes:**
- User not created → Run migration script
- Wrong secret key → Use `admin_krs_2025`
- Session expired → Login again

**Solution:**
```bash
# Verify admin user exists
python3 -c "
import sys
sys.path.insert(0, 'src')
from krs_reminder.database import SupabaseClient
db = SupabaseClient()
user = db.get_user_by_username('admin')
print(f'Admin exists: {user is not None}')
"
```

### Issue: No reminders sent

**Possible Causes:**
- Bot not running → Start bot
- No active session → Login first
- No upcoming events → Check schedule

**Solution:**
```bash
# Check bot status
./botctl.sh status

# Check logs
./botctl.sh logs | grep -i reminder
```

---

## 📊 Post-Deployment Checklist

- [ ] Database tables created
- [ ] Admin user created (username: admin)
- [ ] 44 events imported to database
- [ ] Admin can login via Telegram
- [ ] Admin can view schedule
- [ ] VA/VB system working
- [ ] Interactive buttons working
- [ ] Reminders being scheduled
- [ ] Bot running without errors
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Code committed to git
- [ ] Code pushed to GitHub

---

## 🎉 Success Criteria

✅ **Bot is production-ready when:**
1. Admin (telegram_id: 5476148500) can login
2. Admin can see all 44 events
3. VA/VB status shows correctly
4. Reminders are being sent
5. No errors in logs
6. All tests passing

---

## 📞 Support

**Issues?**
- Check logs: `./botctl.sh logs`
- Run tests: `python3 tests/test_multiuser.py`
- Review documentation: README.md, ADMIN_GUIDE.md, USER_GUIDE.md

---

**Last Updated:** 2025-10-07  
**Version:** 3.0 Multi-User  
**Status:** Ready for Deployment

