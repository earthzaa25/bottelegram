# กบ.ทหาร Telegram Bot

Bot จัดซื้อจัดจ้าง กบ.ทหาร — ตอบโต้ได้ + ส่งรายงานอัตโนมัติทุกวัน

## คำสั่งที่ใช้ได้
- `/report` — รายงานสรุปประจำวัน
- `/dashboard` — Dashboard เป็นรูปภาพ
- `/urgent` — งานเร่งด่วน
- `/unit` — สรุปตามหน่วย
- `/budget` — สรุปวงเงิน

## วิธี Deploy บน Railway.app

### ขั้นตอนที่ 1 — สร้างบัญชี
1. ไปที่ **railway.app**
2. กด **Login with GitHub**
3. สมัคร GitHub ฟรีถ้ายังไม่มี

### ขั้นตอนที่ 2 — Upload ไฟล์
1. ไปที่ **github.com** → New Repository
2. ชื่อ `procurement-bot` → Create
3. Upload ไฟล์ทั้ง 3 ไฟล์: `bot.py`, `requirements.txt`, `Procfile`

### ขั้นตอนที่ 3 — Deploy บน Railway
1. ไปที่ **railway.app** → New Project
2. กด **Deploy from GitHub repo**
3. เลือก `procurement-bot`
4. กด **Add Variables** ใส่:
   - `BOT_TOKEN` = Token จาก BotFather
   - `CHAT_ID` = -1003777924772
5. กด **Deploy** รอ 2-3 นาที

### ขั้นตอนที่ 4 — เสร็จแล้ว!
Bot จะรันตลอด 24 ชั่วโมง ส่งรายงานทุกวัน 08:00 น. อัตโนมัติ
