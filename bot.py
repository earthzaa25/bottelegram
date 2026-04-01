import os, logging, io, json, hashlib
from datetime import datetime, time
from collections import Counter
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import urllib.request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN      = os.environ.get("BOT_TOKEN", "")
CHAT_ID        = os.environ.get("CHAT_ID", "-1003777924772")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
XLS_FILE       = os.path.join(os.path.dirname(__file__), "data.xls")
HASH_FILE      = os.path.join(os.path.dirname(__file__), ".data_hash")

# ==============================
# ฟอนต์ภาษาไทย
# ==============================
FONT_PATH = os.path.join(os.path.dirname(__file__), "Sarabun-Regular.ttf")

def get_thai_font(size=10):
    if os.path.exists(FONT_PATH):
        return fm.FontProperties(fname=FONT_PATH, size=size)
    return fm.FontProperties(size=size)

def setup_font():
    if os.path.exists(FONT_PATH):
        fm.fontManager.addfont(FONT_PATH)
        prop = fm.FontProperties(fname=FONT_PATH)
        matplotlib.rcParams['font.family'] = prop.get_name()
        logger.info(f"Thai font loaded: {prop.get_name()}")

setup_font()

# ==============================
# ตรวจจับการเปลี่ยนแปลงไฟล์
# ==============================
def get_file_hash():
    if not os.path.exists(XLS_FILE):
        return None
    with open(XLS_FILE, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def save_hash(h):
    with open(HASH_FILE, 'w') as f:
        f.write(h)

def load_hash():
    if not os.path.exists(HASH_FILE):
        return None
    with open(HASH_FILE, 'r') as f:
        return f.read().strip()

# ==============================
# โหลดข้อมูลจากไฟล์ XLS
# ==============================
def load_data():
    try:
        import pandas as pd
        from io import StringIO

        if not os.path.exists(XLS_FILE):
            logger.error(f"File not found: {XLS_FILE}")
            return []

        with open(XLS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        tables = pd.read_html(StringIO(content))
        if not tables:
            return []

        df = tables[0]
        rows = []

        for _, r in df.iterrows():
            try:
                no     = str(r.iloc[0])
                year   = str(r.iloc[1])
                unit   = str(r.iloc[2])
                name   = str(r.iloc[3])
                typ    = str(r.iloc[4])
                method = str(r.iloc[5])
                auth   = str(r.iloc[6])
                budget = float(r.iloc[7])
                status = str(r.iloc[27]) if len(r) > 27 else ""
            except:
                continue

            if no in ['nan', 'ลำดับ', ''] or name in ['nan', 'ชื่อโครงการ', '']:
                continue

            rows.append({
                'no'    : no,
                'year'  : year,
                'unit'  : unit,
                'name'  : name,
                'type'  : typ,
                'method': method,
                'auth'  : auth,
                'budget': budget,
                'status': status,
                'days'  : '',
            })

        logger.info(f"Loaded {len(rows)} rows from XLS")
        return rows

    except Exception as e:
        logger.error(f"XLS load error: {e}")
        return []

def get_summary(data=None):
    if data is None:
        data = load_data()
    total   = len(data)
    budget  = sum(r["budget"] for r in data)
    units   = Counter(r["unit"] for r in data)
    pending = [r for r in data if not any(
        w in r["status"] for w in ["บริหารสัญญา", "ตรวจรับ", "ลงนาม"]
    )]
    return total, budget, units, pending

def data_to_text(data):
    lines = []
    total, budget, units, pending = get_summary(data)
    lines.append(f"ข้อมูลจัดซื้อจัดจ้าง กบ.ทหาร ณ {datetime.now().strftime('%d/%m/%Y')}")
    lines.append(f"งานทั้งหมด: {total} รายการ | วงเงินรวม: {budget/1e6:,.1f} ล้านบาท")
    lines.append("")
    for r in data[:60]:
        lines.append(
            f"[{r['no']}] {r['unit']} | {r['name'][:60]} | "
            f"วงเงิน {r['budget']/1e6:,.1f} ลบ. | สถานะ: {r['status']}"
        )
    return "\n".join(lines)

# ==============================
# Gemini AI
# ==============================
def ask_gemini(prompt, data=None):
    if not GEMINI_API_KEY:
        return "ไม่พบ GEMINI_API_KEY ครับ"
    try:
        context = ""
        if data:
            context = f"\n\nข้อมูลจัดซื้อจัดจ้าง กบ.ทหาร:\n{data_to_text(data)}\n\n"
        full_prompt = (
            "คุณเป็น AI ผู้ช่วยวิเคราะห์งานจัดซื้อจัดจ้างของ กบ.ทหาร "
            "ตอบเป็นภาษาไทย กระชับ ชัดเจน เหมาะสำหรับผู้บริหารระดับสูง"
            f"{context}"
            f"คำถาม: {prompt}"
        )
        payload = json.dumps({
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}
        }).encode("utf-8")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        )
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return f"Gemini ตอบไม่ได้ตอนนี้ครับ ({e})"

# ==============================
# Dashboard Image
# ==============================
def build_dashboard_image(data=None):
    if data is None:
        data = load_data()
    total, budget, units, pending = get_summary(data)

    fig = plt.figure(figsize=(16, 10), facecolor="#0a1628")
    fig.text(0.5, 0.97, "Dashboard จัดซื้อจัดจ้าง กบ.ทหาร",
             ha="center", va="top", color="white", fontsize=18,
             fontweight="bold", fontproperties=get_thai_font(18))
    fig.text(0.5, 0.93, f"ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}  |  กบ.ทหาร",
             ha="center", va="top", color="#8a9bb8", fontsize=10,
             fontproperties=get_thai_font(10))

    auth_count  = Counter(r["auth"] for r in data)
    auth_budget = {}
    for r in data:
        auth_budget[r["auth"]] = auth_budget.get(r["auth"], 0) + r["budget"]

    kpi_data = [
        ("งานทั้งหมด",  f"{total}",                 "#00d4ff"),
        ("วงเงินรวม",   f"{budget/1e6:,.0f} ลบ.",   "#f5a623"),
        ("รอดำเนินการ", f"{len(pending)}",           "#ff4d6d"),
        ("หน่วยงาน",    f"{len(units)}",             "#00c896"),
    ]
    for i, (label, val, color) in enumerate(kpi_data):
        ax = fig.add_axes([0.04 + i*0.245, 0.78, 0.22, 0.12])
        ax.set_facecolor("#0f2044")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.axhline(y=1, color=color, linewidth=4)
        ax.text(0.5, 0.58, val, ha="center", va="center",
                color=color, fontsize=18, fontweight="bold",
                fontproperties=get_thai_font(18))
        ax.text(0.5, 0.18, label, ha="center", va="center",
                color="#8a9bb8", fontproperties=get_thai_font(9))
        ax.axis("off")

    ax1 = fig.add_axes([0.03, 0.30, 0.28, 0.44])
    ax1.set_facecolor("#0a1628")
    unit_names = [u for u, c in units.most_common()[:6]]
    unit_vals  = [c for u, c in units.most_common()[:6]]
    colors6 = ["#00d4ff", "#00c896", "#f5a623", "#ff4d6d", "#a78bfa", "#34d399"]
    ax1.pie(unit_vals, colors=colors6[:len(unit_vals)], startangle=90,
            wedgeprops=dict(width=0.5))
    ax1.set_title("สัดส่วนตามหน่วย", color="#8a9bb8", fontsize=11, pad=8,
                  fontproperties=get_thai_font(11))
    leg1 = ax1.legend(
        handles=[mpatches.Patch(color=colors6[i], label=f"{unit_names[i]} ({unit_vals[i]})")
                 for i in range(len(unit_names))],
        loc="lower center", bbox_to_anchor=(0.5, -0.30), ncol=2, fontsize=8,
        labelcolor="white", facecolor="#0f2044", edgecolor="none"
    )
    for t in leg1.get_texts():
        t.set_fontproperties(get_thai_font(8))

    ax2 = fig.add_axes([0.36, 0.30, 0.38, 0.44])
    ax2.set_facecolor("#0f2044")
    unit_budget = {}
    for r in data:
        unit_budget[r["unit"]] = unit_budget.get(r["unit"], 0) + r["budget"]
    sorted_u = sorted(unit_budget.items(), key=lambda x: x[1], reverse=True)[:8]
    names = [x[0] for x in sorted_u]
    vals  = [x[1]/1e6 for x in sorted_u]
    bars  = ax2.barh(names, vals, color="#00d4ff", alpha=0.85)
    for bar, val in zip(bars, vals):
        ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                 f"{val:,.0f}", va="center", color="#8a9bb8", fontsize=8)
    ax2.set_facecolor("#0f2044")
    ax2.tick_params(colors="#8a9bb8", labelsize=8)
    for lbl in ax2.get_yticklabels():
        lbl.set_fontproperties(get_thai_font(8))
    ax2.spines[:].set_visible(False)
    ax2.set_title("วงเงินตามหน่วย (ลบ.)", color="#8a9bb8", fontsize=10, pad=8,
                  fontproperties=get_thai_font(10))
    if vals:
        ax2.set_xlim(0, max(vals) * 1.28)

    ax3 = fig.add_axes([0.78, 0.30, 0.20, 0.44])
    ax3.set_facecolor("#0f2044")
    auth_items = sorted(auth_budget.items(), key=lambda x: x[1], reverse=True)
    a_names = [x[0] for x in auth_items]
    a_vals  = [x[1]/1e6 for x in auth_items]
    a_colors = ["#f5a623", "#00c896", "#00d4ff", "#ff4d6d"]
    ax3.barh(a_names, a_vals, color=a_colors[:len(a_names)], alpha=0.85)
    for i, (val, name) in enumerate(zip(a_vals, a_names)):
        cnt = auth_count.get(name, 0)
        ax3.text(val + 1, i, f"{val:,.0f}\n({cnt} งาน)",
                 va="center", color="#8a9bb8", fontsize=7)
    ax3.set_facecolor("#0f2044")
    ax3.tick_params(colors="#8a9bb8", labelsize=8)
    for lbl in ax3.get_yticklabels():
        lbl.set_fontproperties(get_thai_font(8))
    ax3.spines[:].set_visible(False)
    ax3.set_title("แยกอำนาจอนุมัติ", color="#8a9bb8", fontsize=10, pad=8,
                  fontproperties=get_thai_font(10))
    if a_vals:
        ax3.set_xlim(0, max(a_vals) * 1.4)

    ax4 = fig.add_axes([0.03, 0.03, 0.94, 0.22])
    ax4.set_facecolor("#0f2044")
    ax4.set_xlim(0, 1); ax4.set_ylim(0, 1); ax4.axis("off")
    ax4.text(0.01, 0.92, "งานที่รอดำเนินการ (ตัวอย่าง)",
             color="#ff4d6d", fontsize=11, fontweight="bold", va="top",
             fontproperties=get_thai_font(11))
    for i, r in enumerate(pending[:4]):
        color = "#ff4d6d" if i < 2 else "#f5a623"
        ax4.text(0.01, 0.70 - i*0.17,
                 f"  [{r['no']}] {r['unit']} — {r['name'][:55]}  |  {r['status']}",
                 color=color, fontsize=9, va="top",
                 fontproperties=get_thai_font(9))

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#0a1628")
    buf.seek(0)
    plt.close()
    return buf

def build_report(data=None):
    if data is None:
        data = load_data()
    total, budget, units, pending = get_summary(data)
    today = datetime.now().strftime("%d/%m/%Y %H:%M น.")
    unit_lines = "\n".join([f"  - {u}: {c} รายการ" for u, c in units.most_common()])
    return (
        f"รายงานจัดซื้อจัดจ้าง กบ.ทหาร\n"
        f"ข้อมูล ณ {today}\n"
        f"--------------------\n\n"
        f"งานทั้งหมด: {total} รายการ\n"
        f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n"
        f"รอดำเนินการ: {len(pending)} รายการ\n\n"
        f"สรุปตามหน่วย:\n{unit_lines}\n\n"
        f"#กบทหาร #จัดซื้อจัดจ้าง"
    )

# ==============================
# Handlers
# ==============================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "สวัสดีครับ Bot จัดซื้อจัดจ้าง กบ.ทหาร + Gemini AI\n\n"
        "คำสั่งทั้งหมด:\n"
        "/report      - รายงานสรุปประจำวัน\n"
        "/dashboard   - ภาพ Dashboard\n"
        "/ai          - AI วิเคราะห์ภาพรวม\n"
        "/authority   - สรุปตามอำนาจอนุมัติ + รายการงาน\n"
        "/progress    - Pipeline ความคืบหน้าตามขั้นตอน\n"
        "/overdue     - งานที่ค้างนานผิดปกติ\n"
        "/type        - สรุปตามประเภทงาน\n"
        "/urgent      - งานรอดำเนินการ\n"
        "/unit        - สรุปตามหน่วย\n"
        "/budget      - สรุปวงเงิน\n"
        "/status      - สรุปสถานะงาน\n"
        "/yearly      - สรุปแยกปีงบประมาณ\n"
        "/export      - ส่งไฟล์ข้อมูลล่าสุด\n"
        "/find_unit [ชื่อ]   - ค้นหางานของหน่วย\n"
        "/search [คำ]        - ค้นหาจากชื่องาน\n"
        "/job [เลขที่]        - ดูรายละเอียดงาน\n"
        "/summary [หน่วย]    - AI สรุปเฉพาะหน่วย\n\n"
        "หรือพิมพ์ถามอะไรก็ได้ Gemini AI จะตอบให้ครับ"
    )
    await update.message.reply_text(msg)

async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(build_report(data))

async def cmd_dashboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("กำลังสร้าง Dashboard รอสักครู่...")
    try:
        data = load_data()
        if not data:
            await msg.edit_text("ไม่พบข้อมูลครับ กรุณาตรวจสอบไฟล์ data.xls บน GitHub")
            return
        buf = build_dashboard_image(data)
        await update.message.reply_photo(
            photo=buf,
            caption=f"Dashboard จัดซื้อจัดจ้าง กบ.ทหาร\nข้อมูล ณ {datetime.now().strftime('%d/%m/%Y %H:%M น.')}"
        )
        await msg.delete()
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        await msg.edit_text(f"เกิดข้อผิดพลาด: {e}")

async def cmd_ai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Gemini AI กำลังวิเคราะห์ข้อมูล รอสักครู่...")
    data = load_data()
    total, budget, units, pending = get_summary(data)
    prompt = (
        f"วิเคราะห์ภาพรวมงานจัดซื้อจัดจ้าง กบ.ทหาร ทั้งหมด {total} รายการ "
        f"วงเงินรวม {budget/1e6:,.1f} ล้านบาท รอดำเนินการ {len(pending)} รายการ "
        f"สรุปประเด็นสำคัญที่ผู้บริหารควรทราบ ข้อเสี่ยง และข้อแนะนำ"
    )
    reply = ask_gemini(prompt, data)
    await msg.edit_text(f"Gemini AI วิเคราะห์:\n\n{reply}")

async def cmd_authority(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    auth_groups = {}
    for r in data:
        a = r["auth"]
        if a not in auth_groups:
            auth_groups[a] = []
        auth_groups[a].append(r)

    summary = "สรุปตามอำนาจอนุมัติ\n====================\n\n"
    for auth, items in sorted(auth_groups.items(), key=lambda x: len(x[1]), reverse=True):
        total_b = sum(r["budget"] for r in items)
        summary += f"📌 {auth}\n   จำนวน: {len(items)} รายการ | วงเงิน: {total_b/1e6:,.1f} ล้านบาท\n\n"
    await update.message.reply_text(summary)

    for auth, items in sorted(auth_groups.items(), key=lambda x: len(x[1]), reverse=True):
        total_b = sum(r["budget"] for r in items)
        msg  = f"📋 {auth} — {len(items)} รายการ | {total_b/1e6:,.1f} ล้านบาท\n"
        msg += "--------------------\n\n"
        for r in items:
            msg += f"[{r['no']}] {r['unit']}\n"
            msg += f"  {r['name'][:55]}\n"
            msg += f"  วงเงิน: {r['budget']/1e6:,.1f} ลบ. | สถานะ: {r['status']}\n\n"
            if len(msg) > 3800:
                await update.message.reply_text(msg)
                msg = f"📋 {auth} (ต่อ)\n--------------------\n\n"
        if msg.strip():
            await update.message.reply_text(msg)

async def cmd_progress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Pipeline ความคืบหน้าตามขั้นตอน"""
    data = load_data()

    # นิยามขั้นตอน pipeline
    stages = [
        ("เริ่มดำเนินการ / TOR",     ["เริ่มดำเนินการ", "TOR", "ราคากลาง", "อนุมัติแผน"]),
        ("ประกาศ / ยื่นข้อเสนอ",     ["ประกาศ", "ยื่นข้อเสนอ", "คณก"]),
        ("รออนุมัติซื้อจ้าง",         ["รายงานขออนุมัติ", "เห็นชอบผล", "รอง ผบ", "เสนอ"]),
        ("อนุมัติแล้ว / รอลงนาม",    ["อนุมัติ"]),
        ("ลงนามสัญญา / บริหาร",      ["ลงนาม", "บริหารสัญญา", "ตรวจรับ"]),
    ]

    stage_data = {s[0]: [] for s in stages}
    other = []

    for r in data:
        placed = False
        for stage_name, keywords in stages:
            if any(kw in r["status"] for kw in keywords):
                stage_data[stage_name].append(r)
                placed = True
                break
        if not placed:
            other.append(r)

    msg = "Pipeline ความคืบหน้างานจัดซื้อจัดจ้าง\n====================\n\n"
    icons = ["🟡", "🟠", "🔵", "🟣", "🟢"]
    for i, (stage_name, _) in enumerate(stages):
        items = stage_data[stage_name]
        total_b = sum(r["budget"] for r in items)
        icon = icons[i]
        msg += f"{icon} {stage_name}\n"
        msg += f"   {len(items)} รายการ | {total_b/1e6:,.1f} ล้านบาท\n"
        for r in items[:3]:
            msg += f"   - [{r['no']}] {r['unit']} — {r['name'][:40]}\n"
        if len(items) > 3:
            msg += f"   ... และอีก {len(items)-3} รายการ\n"
        msg += "\n"

    if other:
        msg += f"⚪ อื่นๆ: {len(other)} รายการ\n"

    await update.message.reply_text(msg)

async def cmd_overdue(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """งานที่ค้างอยู่ในขั้นตอนต้นๆ นานผิดปกติ"""
    data = load_data()

    early_stages = ["เริ่มดำเนินการ", "TOR", "ราคากลาง", "อนุมัติแผน"]
    overdue = [r for r in data if any(kw in r["status"] for kw in early_stages)]

    msg = f"งานที่ค้างอยู่ในขั้นตอนต้น ({len(overdue)} รายการ)\n"
    msg += "ควรเร่งรัดดำเนินการ\n"
    msg += "--------------------\n\n"

    if overdue:
        # จัดกลุ่มตามสถานะ
        by_status = {}
        for r in overdue:
            s = r["status"]
            if s not in by_status:
                by_status[s] = []
            by_status[s].append(r)

        for s, items in sorted(by_status.items(), key=lambda x: len(x[1]), reverse=True):
            total_b = sum(r["budget"] for r in items)
            msg += f"🔴 สถานะ: {s}\n"
            msg += f"   {len(items)} รายการ | {total_b/1e6:,.1f} ล้านบาท\n"
            for r in items[:5]:
                msg += f"   [{r['no']}] {r['unit']} — {r['name'][:40]}\n"
                msg += f"   วงเงิน: {r['budget']/1e6:,.1f} ลบ.\n"
            if len(items) > 5:
                msg += f"   ... และอีก {len(items)-5} รายการ\n"
            msg += "\n"
            if len(msg) > 3800:
                await update.message.reply_text(msg)
                msg = "งานค้าง (ต่อ)\n--------------------\n\n"
    else:
        msg += "ไม่มีงานที่ค้างในขั้นตอนต้นครับ"

    if msg.strip():
        await update.message.reply_text(msg)

async def cmd_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """สรุปตามประเภทงาน"""
    data = load_data()

    type_groups = {}
    for r in data:
        t = r["type"] if r["type"] not in ['nan', ''] else "ไม่ระบุ"
        if t not in type_groups:
            type_groups[t] = {"count": 0, "budget": 0, "items": []}
        type_groups[t]["count"] += 1
        type_groups[t]["budget"] += r["budget"]
        type_groups[t]["items"].append(r)

    total_b = sum(r["budget"] for r in data)
    msg = "สรุปตามประเภทงาน\n--------------------\n\n"

    for t, d in sorted(type_groups.items(), key=lambda x: x[1]["budget"], reverse=True):
        pct = d["budget"] / total_b * 100 if total_b else 0
        msg += f"📦 {t}\n"
        msg += f"   จำนวน: {d['count']} รายการ\n"
        msg += f"   วงเงิน: {d['budget']/1e6:,.1f} ล้านบาท ({pct:.1f}%)\n\n"

    await update.message.reply_text(msg)

async def cmd_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """ส่งไฟล์ data.xls กลับมาใน Telegram"""
    if not os.path.exists(XLS_FILE):
        await update.message.reply_text("ไม่พบไฟล์ข้อมูลครับ")
        return
    msg = await update.message.reply_text("กำลังส่งไฟล์...")
    try:
        with open(XLS_FILE, 'rb') as f:
            today = datetime.now().strftime("%d%m%Y")
            await update.message.reply_document(
                document=f,
                filename=f"รายการจัดซื้อจัดจ้าง_กบ.ทหาร_{today}.xls",
                caption=f"📎 ไฟล์ข้อมูลจัดซื้อจัดจ้าง กบ.ทหาร\nข้อมูล ณ {datetime.now().strftime('%d/%m/%Y %H:%M น.')}"
            )
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"ส่งไฟล์ไม่ได้ครับ: {e}")

async def cmd_summary_unit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """AI สรุปเฉพาะหน่วย"""
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "กรุณาระบุชื่อหน่วยครับ\nเช่น /summary นซบ.ทหาร"
        )
        return
    keyword  = " ".join(args).lower()
    data     = load_data()
    found    = [r for r in data if keyword in r["unit"].lower()]
    if not found:
        await update.message.reply_text(f"ไม่พบหน่วย '{' '.join(args)}' ครับ")
        return

    unit_name = found[0]["unit"]
    total_b   = sum(r["budget"] for r in found)
    msg = await update.message.reply_text(f"Gemini AI กำลังวิเคราะห์งานของ {unit_name}...")

    pending = [r for r in found if not any(
        w in r["status"] for w in ["บริหารสัญญา", "ตรวจรับ", "ลงนาม"]
    )]
    prompt = (
        f"วิเคราะห์งานจัดซื้อจัดจ้างของหน่วย {unit_name} "
        f"มีงานทั้งหมด {len(found)} รายการ วงเงินรวม {total_b/1e6:,.1f} ล้านบาท "
        f"รอดำเนินการ {len(pending)} รายการ "
        f"สรุปสถานะ ความเสี่ยง และข้อแนะนำสำหรับผู้บริหาร"
    )
    reply = ask_gemini(prompt, found)
    await msg.edit_text(f"AI วิเคราะห์งาน {unit_name}:\n\n{reply}")

async def cmd_urgent(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    _, _, _, pending = get_summary(data)
    msg = f"งานที่รอดำเนินการ ({len(pending)} รายการ)\n--------------------\n\n"
    if pending:
        for r in pending[:20]:
            msg += f"[{r['no']}] {r['unit']} — {r['name'][:45]}\n"
            msg += f"  สถานะ: {r['status']} | {r['budget']/1e6:,.1f} ลบ.\n\n"
            if len(msg) > 3800:
                await update.message.reply_text(msg)
                msg = "งานที่รอดำเนินการ (ต่อ)\n--------------------\n\n"
        if len(pending) > 20:
            msg += f"... และอีก {len(pending)-20} รายการ"
    else:
        msg += "ไม่มีงานที่รอดำเนินการครับ"
    if msg.strip():
        await update.message.reply_text(msg)

async def cmd_unit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    unit_budget = {}
    unit_count  = Counter(r["unit"] for r in data)
    for r in data:
        unit_budget[r["unit"]] = unit_budget.get(r["unit"], 0) + r["budget"]
    msg = "สรุปตามหน่วย\n--------------------\n\n"
    for u, c in unit_count.most_common():
        b = unit_budget.get(u, 0)
        msg += f"{u}  ({c} รายการ | {b/1e6:,.1f} ลบ.)\n"
    msg += "\nดูรายละเอียด: /find_unit [ชื่อหน่วย]\nAI วิเคราะห์: /summary [ชื่อหน่วย]"
    await update.message.reply_text(msg)

async def cmd_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    total, budget, _, _ = get_summary(data)
    auth_groups = {}
    for r in data:
        a = r["auth"]
        if a not in auth_groups:
            auth_groups[a] = {"count": 0, "budget": 0}
        auth_groups[a]["count"] += 1
        auth_groups[a]["budget"] += r["budget"]
    msg = (
        f"สรุปวงเงินจัดซื้อจัดจ้าง\n--------------------\n\n"
        f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n"
        f"จำนวนงาน: {total} รายการ\n"
        f"เฉลี่ยต่องาน: {budget/total/1e6:,.1f} ล้านบาท\n\n"
        f"แยกตามอำนาจ:\n"
    )
    for a, d in sorted(auth_groups.items(), key=lambda x: x[1]["budget"], reverse=True):
        msg += f"  - {a}: {d['count']} งาน | {d['budget']/1e6:,.1f} ลบ. ({d['budget']/budget*100:.1f}%)\n"
    await update.message.reply_text(msg)

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    status_count  = Counter()
    status_budget = {}
    for r in data:
        s = r.get("status", "ไม่ระบุ")
        if "บริหารสัญญา" in s or "ตรวจรับ" in s:
            key = "บริหารสัญญา/ตรวจรับ"
        elif "ลงนาม" in s:
            key = "ลงนามในสัญญา"
        elif "อนุมัติ" in s:
            key = "อนุมัติแล้ว"
        elif "เสนอ" in s or "รายงาน" in s:
            key = "อยู่ระหว่างเสนอ"
        elif "เริ่มดำเนินการ" in s or "TOR" in s or "ราคากลาง" in s:
            key = "เริ่มดำเนินการ/TOR"
        else:
            key = "อื่นๆ"
        status_count[key] += 1
        status_budget[key] = status_budget.get(key, 0) + r["budget"]
    msg = "สรุปสถานะงาน\n--------------------\n\n"
    for s, c in status_count.most_common():
        b = status_budget.get(s, 0)
        msg += f"{s}: {c} รายการ ({b/1e6:,.1f} ลบ.)\n"
    await update.message.reply_text(msg)

async def cmd_yearly(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    year_data = {}
    for r in data:
        y = r.get("year", "ไม่ระบุ")
        if y not in year_data:
            year_data[y] = {"count": 0, "budget": 0}
        year_data[y]["count"] += 1
        year_data[y]["budget"] += r["budget"]
    msg = "สรุปแยกปีงบประมาณ\n--------------------\n\n"
    for y in sorted(year_data.keys()):
        d = year_data[y]
        msg += f"งป. {y}:\n  - จำนวนงาน: {d['count']} รายการ\n  - วงเงิน: {d['budget']/1e6:,.1f} ล้านบาท\n\n"
    await update.message.reply_text(msg)

async def cmd_find_unit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("กรุณาระบุชื่อหน่วยครับ\nเช่น /find_unit นซบ.ทหาร")
        return
    keyword = " ".join(args).lower()
    data    = load_data()
    found   = [r for r in data if keyword in r["unit"].lower()]
    if not found:
        await update.message.reply_text(f"ไม่พบหน่วย '{' '.join(args)}' ครับ")
        return
    unit_name = found[0]["unit"]
    total_b   = sum(r["budget"] for r in found)
    msg  = f"หน่วย: {unit_name}\n"
    msg += f"จำนวนงาน: {len(found)} รายการ | วงเงินรวม: {total_b/1e6:,.1f} ล้านบาท\n"
    msg += "--------------------\n\n"
    for r in found:
        msg += f"[{r['no']}] {r['name'][:52]}\n"
        msg += f"  วงเงิน: {r['budget']/1e6:,.1f} ลบ. | {r['auth']} | {r['status']}\n\n"
        if len(msg) > 3800:
            await update.message.reply_text(msg)
            msg = f"หน่วย {unit_name} (ต่อ)\n--------------------\n\n"
    if msg.strip():
        await update.message.reply_text(msg)

async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("กรุณาระบุคำค้นหาครับ\nเช่น /search อากาศยาน")
        return
    keyword = " ".join(args).lower()
    data    = load_data()
    found   = [r for r in data if keyword in r["name"].lower() or keyword in r["unit"].lower()]
    if not found:
        await update.message.reply_text(f"ไม่พบงานที่เกี่ยวข้องกับ '{' '.join(args)}' ครับ")
        return
    msg  = f"ผลการค้นหา: '{' '.join(args)}'\nพบ {len(found)} รายการ\n--------------------\n\n"
    for r in found[:10]:
        msg += f"[{r['no']}] {r['unit']} — {r['name'][:45]}\n"
        msg += f"  วงเงิน: {r['budget']/1e6:,.1f} ลบ. | {r['auth']} | {r['status']}\n\n"
    if len(found) > 10:
        msg += f"... และอีก {len(found)-10} รายการ"
    await update.message.reply_text(msg)

async def cmd_job(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("กรุณาระบุเลขที่งานครับ\nเช่น /job 5")
        return
    no    = args[0]
    data  = load_data()
    found = [r for r in data if r["no"] == no]
    if not found:
        await update.message.reply_text(f"ไม่พบงานเลขที่ {no} ครับ")
        return
    r   = found[0]
    msg = (
        f"รายละเอียดงานที่ {r['no']}\n--------------------\n\n"
        f"หน่วย: {r['unit']}\n"
        f"งาน: {r['name']}\n"
        f"ประเภท: {r['type']}\n"
        f"วิธี: {r['method']}\n"
        f"อำนาจอนุมัติ: {r['auth']}\n"
        f"วงเงิน: {r['budget']/1e6:,.2f} ล้านบาท\n"
        f"ปีงบประมาณ: {r['year']}\n"
        f"สถานะ: {r['status']}"
    )
    await update.message.reply_text(msg)

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    data = load_data()
    if any(w in text for w in ["dashboard", "กราฟ", "ภาพ", "รูป"]):
        await cmd_dashboard(update, ctx)
    elif any(w in text for w in ["อำนาจ", "authority"]):
        await cmd_authority(update, ctx)
    elif any(w in text for w in ["pipeline", "ขั้นตอน", "progress", "คืบหน้า"]):
        await cmd_progress(update, ctx)
    elif any(w in text for w in ["ค้างนาน", "overdue", "เร่งรัด"]):
        await cmd_overdue(update, ctx)
    elif any(w in text for w in ["ประเภท", "type"]):
        await cmd_type(update, ctx)
    elif any(w in text for w in ["รายงาน", "สรุป", "report"]):
        await cmd_report(update, ctx)
    elif any(w in text for w in ["รอดำเนินการ", "เร่งด่วน", "ด่วน"]):
        await cmd_urgent(update, ctx)
    elif any(w in text for w in ["สถานะ", "status"]):
        await cmd_status(update, ctx)
    elif any(w in text for w in ["ปีงบ", "งบประมาณ"]):
        await cmd_yearly(update, ctx)
    elif any(w in text for w in ["วงเงิน", "งบ", "เงิน"]):
        await cmd_budget(update, ctx)
    elif any(w in text for w in ["รายการ", "ทั้งหมด", "มีกี่"]):
        total, budget, units, pending = get_summary(data)
        await update.message.reply_text(
            f"งานทั้งหมด: {total} รายการ\n"
            f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n"
            f"รอดำเนินการ: {len(pending)} รายการ"
        )
    else:
        msg = await update.message.reply_text("Gemini AI กำลังประมวลผล...")
        reply = ask_gemini(update.message.text, data)
        await msg.edit_text(reply)

# ==============================
# Scheduled Jobs
# ==============================
async def send_daily_report(ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await ctx.bot.send_message(chat_id=CHAT_ID, text=build_report(data))
    try:
        buf = build_dashboard_image(data)
        await ctx.bot.send_photo(
            chat_id=CHAT_ID, photo=buf,
            caption=f"Dashboard ประจำวัน {datetime.now().strftime('%d/%m/%Y')}"
        )
    except Exception as e:
        logger.error(f"Daily dashboard error: {e}")

async def send_weekly_report(ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    total, budget, units, pending = get_summary(data)
    prompt = (
        f"สรุปรายงานประจำสัปดาห์งานจัดซื้อจัดจ้าง กบ.ทหาร "
        f"งานทั้งหมด {total} รายการ วงเงิน {budget/1e6:,.1f} ล้านบาท "
        f"รอดำเนินการ {len(pending)} รายการ "
        f"สรุปสั้น 5 บรรทัด เน้นประเด็นที่ผู้บริหารต้องรู้"
    )
    ai_summary = ask_gemini(prompt, data)
    await ctx.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            f"รายงานประจำสัปดาห์ กบ.ทหาร\n"
            f"ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}\n"
            f"====================\n\n{ai_summary}\n\n#กบทหาร"
        )
    )

async def send_monthly_report(ctx: ContextTypes.DEFAULT_TYPE):
    """รายงานสิ้นเดือน"""
    data = load_data()
    total, budget, units, pending = get_summary(data)
    now = datetime.now()

    # นับตามอำนาจ
    auth_groups = {}
    for r in data:
        a = r["auth"]
        if a not in auth_groups:
            auth_groups[a] = {"count": 0, "budget": 0}
        auth_groups[a]["count"] += 1
        auth_groups[a]["budget"] += r["budget"]

    prompt = (
        f"สรุปรายงานประจำเดือน {now.strftime('%B %Y')} งานจัดซื้อจัดจ้าง กบ.ทหาร "
        f"งานทั้งหมด {total} รายการ วงเงิน {budget/1e6:,.1f} ล้านบาท "
        f"รอดำเนินการ {len(pending)} รายการ "
        f"วิเคราะห์ภาพรวม ความคืบหน้า ความเสี่ยง และข้อเสนอแนะสำหรับเดือนหน้า ไม่เกิน 10 บรรทัด"
    )
    ai_summary = ask_gemini(prompt, data)

    auth_lines = "\n".join([
        f"  - {a}: {d['count']} งาน | {d['budget']/1e6:,.1f} ลบ."
        for a, d in sorted(auth_groups.items(), key=lambda x: x[1]["budget"], reverse=True)
    ])

    msg = (
        f"รายงานสิ้นเดือน กบ.ทหาร\n"
        f"ประจำเดือน {now.strftime('%B %Y')}\n"
        f"====================\n\n"
        f"งานทั้งหมด: {total} รายการ\n"
        f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n"
        f"รอดำเนินการ: {len(pending)} รายการ\n\n"
        f"แยกตามอำนาจ:\n{auth_lines}\n\n"
        f"AI วิเคราะห์:\n{ai_summary}\n\n"
        f"#กบทหาร #รายงานสิ้นเดือน"
    )
    await ctx.bot.send_message(chat_id=CHAT_ID, text=msg)
    # ส่ง Dashboard ด้วย
    try:
        buf = build_dashboard_image(data)
        await ctx.bot.send_photo(
            chat_id=CHAT_ID, photo=buf,
            caption=f"Dashboard สิ้นเดือน {now.strftime('%B %Y')}"
        )
    except Exception as e:
        logger.error(f"Monthly dashboard error: {e}")

async def check_file_update(ctx: ContextTypes.DEFAULT_TYPE):
    """แจ้งเตือนเมื่อมีการอัปเดตไฟล์ data.xls"""
    current_hash = get_file_hash()
    if current_hash is None:
        return
    old_hash = load_hash()
    if old_hash is None:
        save_hash(current_hash)
        return
    if current_hash != old_hash:
        save_hash(current_hash)
        data = load_data()
        total, budget, units, pending = get_summary(data)
        msg = (
            f"อัปเดตข้อมูลใหม่!\n"
            f"ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y %H:%M น.')}\n"
            f"--------------------\n\n"
            f"งานทั้งหมด: {total} รายการ\n"
            f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n"
            f"รอดำเนินการ: {len(pending)} รายการ\n\n"
            f"พิมพ์ /dashboard เพื่อดู Dashboard ล่าสุด"
        )
        await ctx.bot.send_message(chat_id=CHAT_ID, text=msg)
        logger.info("File update detected and notified")

async def check_urgent_alert(ctx: ContextTypes.DEFAULT_TYPE):
    data    = load_data()
    pending = [r for r in data if "เริ่มดำเนินการ" in r["status"]]
    if pending:
        msg = f"แจ้งเตือน! งานเริ่มดำเนินการ {len(pending)} รายการ\n--------------------\n\n"
        for r in pending[:5]:
            msg += f"- {r['unit']} — {r['name'][:45]}\n  สถานะ: {r['status']}\n\n"
        await ctx.bot.send_message(chat_id=CHAT_ID, text=msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("help",       start))
    app.add_handler(CommandHandler("report",     cmd_report))
    app.add_handler(CommandHandler("dashboard",  cmd_dashboard))
    app.add_handler(CommandHandler("ai",         cmd_ai))
    app.add_handler(CommandHandler("authority",  cmd_authority))
    app.add_handler(CommandHandler("progress",   cmd_progress))
    app.add_handler(CommandHandler("overdue",    cmd_overdue))
    app.add_handler(CommandHandler("type",       cmd_type))
    app.add_handler(CommandHandler("export",     cmd_export))
    app.add_handler(CommandHandler("summary",    cmd_summary_unit))
    app.add_handler(CommandHandler("urgent",     cmd_urgent))
    app.add_handler(CommandHandler("unit",       cmd_unit))
    app.add_handler(CommandHandler("budget",     cmd_budget))
    app.add_handler(CommandHandler("status",     cmd_status))
    app.add_handler(CommandHandler("yearly",     cmd_yearly))
    app.add_handler(CommandHandler("find_unit",  cmd_find_unit))
    app.add_handler(CommandHandler("search",     cmd_search))
    app.add_handler(CommandHandler("job",        cmd_job))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # รายงานอัตโนมัติทุกวัน 08:00 น.
    app.job_queue.run_daily(send_daily_report,  time=time(hour=8,  minute=0))
    # รายงานรายสัปดาห์ทุกวันจันทร์ 07:30 น.
    app.job_queue.run_daily(send_weekly_report, time=time(hour=7,  minute=30), days=(0,))
    # แจ้งเตือนงานเร่งด่วน 08:30 น.
    app.job_queue.run_daily(check_urgent_alert, time=time(hour=8,  minute=30))
    # รายงานสิ้นเดือน วันสุดท้ายของเดือน 17:00 น.
    app.job_queue.run_daily(send_monthly_report, time=time(hour=17, minute=0), days=(0,1,2,3,4,5,6))
    # ตรวจสอบการอัปเดตไฟล์ทุก 30 นาที
    app.job_queue.run_repeating(check_file_update, interval=1800, first=60)

    logger.info("Bot started with all features!")
    app.run_polling()

if __name__ == "__main__":
    main()
