import os, logging, io
from datetime import datetime, time
from collections import Counter
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "-1003777924772")

# ==============================
# โหลดข้อมูล (TODO: เปลี่ยนเป็น Google Sheets)
# ==============================
def load_data():
    return [
        {"no":"1","unit":"ยก.ทหาร","name":"งานจัดซื้ออุปกรณ์ติดตามกำลังทางบก","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":14780000,"days":"134","status":"บริหารสัญญา","year":"2568"},
        {"no":"2","unit":"ยก.ทหาร","name":"งานจัดซื้ออุปกรณ์ระบบแผนที่สถานการณ์ร่วมดิจิทัล ระยะที่ 2","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":40840000,"days":"163","status":"บริหารสัญญา","year":"2568"},
        {"no":"3","unit":"ยก.ทหาร","name":"งานจัดซื้ออุปกรณ์ RPASS Phase 2","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":12960000,"days":"157","status":"บริหารสัญญา","year":"2568"},
        {"no":"4","unit":"สส.ทหาร","name":"งานจัดซื้อระบบนำเสนอห้องอำนวยการยุทธ์ร่วม ศบท.","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":25190000,"days":"88","status":"บริหารสัญญา","year":"2568"},
        {"no":"5","unit":"สส.ทหาร","name":"งานจัดหาระบบปฏิบัติการย่านความถี่ฯ (ผูกพัน 68-71)","method":"-","auth":"ปล.กห.","budget":800000000,"days":"761","status":"บริหารสัญญา","year":"2568"},
        {"no":"6","unit":"ผท.ทหาร","name":"เครื่องมือระบบประมวลผลจัดทำแผนที่ กลุ่มจังหวัดที่ 1","method":"-","auth":"ผบ.ทสส.","budget":55550000,"days":"2","status":"บริหารสัญญา งวดที่ 1","year":"2568"},
        {"no":"7","unit":"ผท.ทหาร","name":"เครื่องมือสำรวจข้อมูลภูมิประเทศ ปี 2568","method":"-","auth":"ผบ.ทสส.","budget":20750000,"days":"26","status":"บริหารสัญญา งวดที่ 1","year":"2568"},
        {"no":"8","unit":"ผท.ทหาร","name":"เครื่องมือทำแผนที่สามมิติ ปี 2568","method":"-","auth":"ผบ.ทสส.","budget":21980000,"days":"47","status":"บริหารสัญญา","year":"2568"},
        {"no":"9","unit":"ผท.ทหาร","name":"เช่าเครื่องบินถ่ายภาพทางอากาศ กลุ่มจังหวัดที่ 1","method":"-","auth":"ผบ.ทสส.","budget":128440000,"days":"","status":"ตรวจรับ/บริหารสัญญา","year":"2568"},
        {"no":"10","unit":"ผท.ทหาร","name":"เช่าเครื่องมือถ่ายภาพทางอากาศ ปี 2568","method":"-","auth":"ผบ.ทสส.","budget":69980000,"days":"","status":"ตรวจรับ/บริหารสัญญา","year":"2568"},
        {"no":"11","unit":"สส.ทหาร","name":"ชุดวิทยุไมโครเวฟ IP ภาค NE+เหนือล่าง","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":98570000,"days":"193","status":"บริหารสัญญา","year":"2568"},
        {"no":"12","unit":"สส.ทหาร","name":"ชุดไมโครเวฟ ภาคกลาง+เหนือบน","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":96880000,"days":"193","status":"บริหารสัญญา","year":"2568"},
        {"no":"13","unit":"สส.ทหาร","name":"ชุดไมโครเวฟ ภาคใต้","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":99220000,"days":"193","status":"บริหารสัญญา","year":"2568"},
        {"no":"14","unit":"นซบ.ทหาร","name":"งานจ้างอบรมชุดปฏิบัติการไซเบอร์","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":18820000,"days":"","status":"ทบทวน TOR","year":"2569"},
        {"no":"15","unit":"นซบ.ทหาร","name":"ระบบป้องกันภัยคุกคามไซเบอร์","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":26827416,"days":"","status":"รอ DCIO","year":"2569"},
        {"no":"16","unit":"นซบ.ทหาร","name":"ระบบสนับสนุนป้องกันภัยไซเบอร์","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":16532398,"days":"","status":"รอ DCIO","year":"2569"},
        {"no":"18","unit":"ยก.ทหาร","name":"พัฒนาระบบป้องกันยาเสพติด","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":21174984,"days":"","status":"รอดำเนินการ","year":"2569"},
        {"no":"19","unit":"ยก.ทหาร","name":"พัฒนาระบบประเมินพร้อมรบ","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":29500000,"days":"","status":"รอดำเนินการ","year":"2569"},
        {"no":"21","unit":"สส.ทหาร","name":"ระบบยืนยันตัวตนเครือข่าย บก.ทท. (210 วัน)","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":44000000,"days":"210","status":"รอดำเนินการ","year":"2569"},
        {"no":"23","unit":"สส.ทหาร","name":"Data Governance & Data Management (270 วัน)","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":22000000,"days":"270","status":"รอดำเนินการ","year":"2569"},
        {"no":"24","unit":"ผท.ทหาร","name":"ซ่อมบำรุงเฮลิคอปเตอร์ EC155 B1","method":"เจาะจง ม.56(2)(ซ)","auth":"ผบ.ทสส.","budget":31800000,"days":"289","status":"บริหารสัญญา","year":"2569"},
        {"no":"25","unit":"ผท.ทหาร","name":"ซ่อมบำรุง BEECHCRAFT KING AIR 350i #93311","method":"เจาะจง ม.56(2)(ค)","auth":"ผบ.ทสส.","budget":61250000,"days":"","status":"อยู่ระหว่างเสนอ จก.","year":"2569"},
        {"no":"26","unit":"ยบ.ทหาร","name":"รถยนต์โดยสารปรับอากาศ 42 ที่นั่ง 4 คัน","method":"ประกาศเชิญชวน","auth":"ผบ.ทสส.","budget":25800000,"days":"","status":"อยู่ระหว่างเสนอ ผบ.ทสส.","year":"2569"},
        {"no":"28","unit":"นทพ.","name":"รถบดล้อเหล็กสั่นสะเทือน 10 คัน","method":"เจาะจง ม.56(2)(จ)","auth":"ผบ.ทสส.","budget":32280000,"days":"","status":"เสนอ จก.กบ.ทหาร","year":"2569"},
        {"no":"29","unit":"นทพ.","name":"รถขุดตักมาตรฐาน 12 คัน","method":"ประกาศเชิญชวน","auth":"ผบ.ทสส.","budget":62016000,"days":"","status":"รอดำเนินการ","year":"2569"},
    ]

def get_summary(data=None):
    if data is None:
        data = load_data()
    total  = len(data)
    budget = sum(r['budget'] for r in data)
    units  = Counter(r['unit'] for r in data)
    urgent = [r for r in data if r['days'].isdigit() and int(r['days']) <= 50]
    return total, budget, units, urgent

def build_report(data=None):
    if data is None:
        data = load_data()
    total, budget, units, urgent = get_summary(data)
    today = datetime.now().strftime("%d/%m/%Y %H:%M น.")
    unit_lines = '\n'.join([f'  - {u}: {c} รายการ' for u, c in units.most_common()])
    urg_text = ""
    if urgent:
        urg_text = "\nงานใกล้ครบกำหนด:\n"
        for r in sorted(urgent, key=lambda x: int(x['days'])):
            urg_text += f"  - {r['unit']} - {r['name'][:35]}... (เหลือ {r['days']} วัน)\n"
    return (
        f"รายงานจัดซื้อจัดจ้าง กบ.ทหาร\n"
        f"ข้อมูล ณ {today}\n"
        f"--------------------\n\n"
        f"งานทั้งหมด: {total} รายการ\n"
        f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n\n"
        f"สรุปตามหน่วย:\n{unit_lines}\n"
        f"{urg_text}\n"
        f"งานต้องติดตาม:\n"
        f"  - จ้างสร้างเรือน้ำมัน ทร. - กสล.ฯ ตรวจ\n"
        f"  - BEECHCRAFT 350i - รอ จก.กบ.ทหาร\n"
        f"  - Anti-Drone ทอ. 9 ระบบ - คาดเสนอ เม.ย.69\n\n"
        f"#กบทหาร #จัดซื้อจัดจ้าง"
    )

def build_dashboard_image(data=None):
    if data is None:
        data = load_data()
    total, budget, units, urgent = get_summary(data)

    fig = plt.figure(figsize=(14, 9), facecolor='#0a1628')
    fig.suptitle('Dashboard จัดซื้อจัดจ้าง กบ.ทหาร',
                 fontsize=18, color='white', fontweight='bold', y=0.98)

    kpi_data = [
        ('งานทั้งหมด', f'{total}', '#00d4ff'),
        ('วงเงินรวม', f'{budget/1e6:,.0f} ลบ.', '#f5a623'),
        ('งานใกล้ครบ', f'{len(urgent)}', '#ff4d6d'),
        ('หน่วยงาน', f'{len(units)}', '#00c896'),
    ]
    for i, (label, val, color) in enumerate(kpi_data):
        ax = fig.add_axes([0.04 + i*0.245, 0.78, 0.22, 0.14])
        ax.set_facecolor('#0f2044')
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.axhline(y=1, color=color, linewidth=4)
        ax.text(0.5, 0.62, val, ha='center', va='center',
                color=color, fontsize=20, fontweight='bold')
        ax.text(0.5, 0.2, label, ha='center', va='center',
                color='#8a9bb8', fontsize=10)
        ax.axis('off')

    ax1 = fig.add_axes([0.03, 0.30, 0.30, 0.44])
    ax1.set_facecolor('#0a1628')
    unit_names = [u for u, c in units.most_common()]
    unit_vals  = [c for u, c in units.most_common()]
    colors = ['#00d4ff','#00c896','#f5a623','#ff4d6d','#a78bfa','#34d399']
    ax1.pie(unit_vals, colors=colors[:len(unit_vals)], startangle=90,
            wedgeprops=dict(width=0.5))
    ax1.set_title('สัดส่วนตามหน่วย', color='#8a9bb8', fontsize=11, pad=8)
    legend = [mpatches.Patch(color=colors[i],
              label=f'{unit_names[i]} ({unit_vals[i]})')
              for i in range(len(unit_names))]
    ax1.legend(handles=legend, loc='lower center',
               bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=8,
               labelcolor='white', facecolor='#0f2044', edgecolor='none')

    ax2 = fig.add_axes([0.38, 0.30, 0.58, 0.44])
    ax2.set_facecolor('#0f2044')
    unit_budget = {}
    for r in data:
        unit_budget[r['unit']] = unit_budget.get(r['unit'], 0) + r['budget']
    sorted_u = sorted(unit_budget.items(), key=lambda x: x[1], reverse=True)
    names = [x[0] for x in sorted_u]
    vals  = [x[1]/1e6 for x in sorted_u]
    bars  = ax2.barh(names, vals, color='#00d4ff', alpha=0.85)
    for bar, val in zip(bars, vals):
        ax2.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                 f'{val:,.0f}', va='center', color='#8a9bb8', fontsize=9)
    ax2.set_facecolor('#0f2044')
    ax2.tick_params(colors='#8a9bb8', labelsize=10)
    ax2.spines[:].set_visible(False)
    ax2.set_title('วงเงินตามหน่วย (ล้านบาท)', color='#8a9bb8', fontsize=11, pad=8)
    ax2.set_xlim(0, max(vals) * 1.25)

    ax3 = fig.add_axes([0.03, 0.03, 0.94, 0.22])
    ax3.set_facecolor('#0f2044')
    ax3.set_xlim(0, 1); ax3.set_ylim(0, 1); ax3.axis('off')
    ax3.text(0.01, 0.92, 'งานต้องติดตามเร่งด่วน',
             color='#ff4d6d', fontsize=11, fontweight='bold', va='top')
    urgent_show = sorted(urgent, key=lambda x: int(x['days'])) if urgent else []
    for i, r in enumerate(urgent_show[:4]):
        color = '#ff4d6d' if i < 2 else '#f5a623'
        ax3.text(0.01, 0.68 - i*0.17,
                 f'  - {r["unit"]} - {r["name"][:50]} (เหลือ {r["days"]} วัน)',
                 color=color, fontsize=9, va='top')
    ax3.text(0.98, 0.05,
             f'ข้อมูล ณ {datetime.now().strftime("%d/%m/%Y")}  |  กบ.ทหาร',
             color='#3a4a6a', fontsize=9, ha='right', va='bottom')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0a1628')
    buf.seek(0)
    plt.close()
    return buf

# ===== Command Handlers =====
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "สวัสดีครับ Bot จัดซื้อจัดจ้าง กบ.ทหาร\n\n"
        "คำสั่งทั้งหมด:\n"
        "/report - รายงานสรุปประจำวัน\n"
        "/dashboard - ภาพ Dashboard\n"
        "/urgent - งานเร่งด่วน\n"
        "/unit - สรุปตามหน่วย\n"
        "/budget - สรุปวงเงิน\n"
        "/status - สรุปสถานะงาน\n"
        "/yearly - สรุปแยกปีงบประมาณ\n\n"
        "ค้นหาข้อมูล:\n"
        "/หน่วย [ชื่อ] - ค้นหางานของหน่วย\n"
        "/ค้นหา [คำ] - ค้นหาจากชื่องาน\n"
        "/งาน [เลขที่] - ดูรายละเอียดงาน\n\n"
        "หรือพิมพ์ถามได้เลยครับ"
    )
    await update.message.reply_text(msg)

async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(build_report())

async def cmd_dashboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("กำลังสร้าง Dashboard รอสักครู่...")
    try:
        buf = build_dashboard_image()
        await update.message.reply_photo(
            photo=buf,
            caption=f"Dashboard จัดซื้อจัดจ้าง กบ.ทหาร\nข้อมูล ณ {datetime.now().strftime('%d/%m/%Y %H:%M น.')}"
        )
        await msg.delete()
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        await msg.edit_text(f"เกิดข้อผิดพลาด: {e}")

async def cmd_urgent(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    _, _, _, urgent = get_summary(data)
    msg = "งานเร่งด่วนที่ต้องติดตาม\n--------------------\n\n"
    if urgent:
        msg += "งานใกล้ครบกำหนด (เหลือ < 50 วัน):\n"
        for r in sorted(urgent, key=lambda x: int(x['days'])):
            msg += f"  - {r['unit']} - {r['name'][:45]}\n    เหลือ {r['days']} วัน | {r['budget']/1e6:,.1f} ลบ.\n\n"
    msg += "งานที่ต้องติดตามพิเศษ:\n"
    msg += "  - จ้างสร้างเรือน้ำมัน ทร. - กสล.ฯ ตรวจ\n"
    msg += "  - BEECHCRAFT 350i - รอ จก.กบ.ทหาร\n"
    msg += "  - Anti-Drone ทอ. 9 ระบบ - คาดเสนอ เม.ย.69\n"
    await update.message.reply_text(msg)

async def cmd_unit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    unit_budget = {}
    unit_count  = Counter(r['unit'] for r in data)
    for r in data:
        unit_budget[r['unit']] = unit_budget.get(r['unit'], 0) + r['budget']
    msg = "สรุปตามหน่วย\n--------------------\n\n"
    for u, c in unit_count.most_common():
        b = unit_budget.get(u, 0)
        msg += f"{u}\n   จำนวนงาน: {c} รายการ\n   วงเงิน: {b/1e6:,.1f} ล้านบาท\n\n"
    msg += "พิมพ์ /หน่วย [ชื่อ] เพื่อดูรายละเอียดครับ"
    await update.message.reply_text(msg)

async def cmd_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    total, budget, _, _ = get_summary(data)
    b_tbtsst = sum(r['budget'] for r in data if r['auth'] == 'ผบ.ทสส.')
    b_plkh   = sum(r['budget'] for r in data if r['auth'] == 'ปล.กห.')
    msg = (
        f"สรุปวงเงินจัดซื้อจัดจ้าง\n--------------------\n\n"
        f"วงเงินรวมทั้งหมด: {budget/1e6:,.1f} ล้านบาท\n"
        f"จำนวนงาน: {total} รายการ\n"
        f"วงเงินเฉลี่ยต่องาน: {budget/total/1e6:,.1f} ล้านบาท\n\n"
        f"แยกตามอำนาจ:\n"
        f"  - ผบ.ทสส.: {b_tbtsst/1e6:,.1f} ลบ. ({b_tbtsst/budget*100:.1f}%)\n"
        f"  - ปล.กห.: {b_plkh/1e6:,.1f} ลบ. ({b_plkh/budget*100:.1f}%)"
    )
    await update.message.reply_text(msg)

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    status_count  = Counter()
    status_budget = {}
    for r in data:
        s = r.get('status', 'ไม่ระบุ')
        if 'บริหารสัญญา' in s or 'ตรวจรับ' in s:
            key = 'บริหารสัญญา/ตรวจรับ'
        elif 'รอดำเนินการ' in s or 'รอ' in s:
            key = 'รอดำเนินการ'
        elif 'อยู่ระหว่าง' in s or 'เสนอ' in s:
            key = 'อยู่ระหว่างดำเนินการ'
        elif 'ทบทวน' in s or 'DCIO' in s:
            key = 'รอ TOR/DCIO'
        else:
            key = 'อื่นๆ'
        status_count[key] += 1
        status_budget[key] = status_budget.get(key, 0) + r['budget']
    msg = "สรุปสถานะงาน\n--------------------\n\n"
    for s, c in status_count.most_common():
        b = status_budget.get(s, 0)
        msg += f"{s}: {c} รายการ ({b/1e6:,.1f} ลบ.)\n"
    await update.message.reply_text(msg)

async def cmd_yearly(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    year_data = {}
    for r in data:
        y = r.get('year', 'ไม่ระบุ')
        if y not in year_data:
            year_data[y] = {'count': 0, 'budget': 0}
        year_data[y]['count'] += 1
        year_data[y]['budget'] += r['budget']
    msg = "สรุปแยกปีงบประมาณ\n--------------------\n\n"
    for y in sorted(year_data.keys()):
        d = year_data[y]
        msg += f"งป. {y}:\n"
        msg += f"  - จำนวนงาน: {d['count']} รายการ\n"
        msg += f"  - วงเงิน: {d['budget']/1e6:,.1f} ล้านบาท\n\n"
    await update.message.reply_text(msg)

async def cmd_search_unit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("กรุณาระบุชื่อหน่วยครับ\nเช่น /หน่วย ยก.ทหาร")
        return
    keyword = ' '.join(args).lower()
    data    = load_data()
    found   = [r for r in data if keyword in r['unit'].lower()]
    if not found:
        await update.message.reply_text(f"ไม่พบหน่วย '{' '.join(args)}' ครับ")
        return
    unit_name = found[0]['unit']
    total_b   = sum(r['budget'] for r in found)
    msg  = f"หน่วย: {unit_name}\n"
    msg += f"จำนวนงาน: {len(found)} รายการ\n"
    msg += f"วงเงินรวม: {total_b/1e6:,.1f} ล้านบาท\n"
    msg += "--------------------\n\n"
    for r in found:
        days_txt = f"เหลือ {r['days']} วัน" if r['days'].isdigit() else r['status']
        msg += f"[{r['no']}] {r['name'][:50]}\n"
        msg += f"  วงเงิน: {r['budget']/1e6:,.1f} ลบ. | {r['auth']} | {days_txt}\n\n"
    await update.message.reply_text(msg)

async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("กรุณาระบุคำค้นหาครับ\nเช่น /ค้นหา ไมโครเวฟ")
        return
    keyword = ' '.join(args).lower()
    data    = load_data()
    found   = [r for r in data if keyword in r['name'].lower() or keyword in r['unit'].lower()]
    if not found:
        await update.message.reply_text(f"ไม่พบงานที่เกี่ยวข้องกับ '{' '.join(args)}' ครับ")
        return
    msg  = f"ผลการค้นหา: '{' '.join(args)}'\n"
    msg += f"พบ {len(found)} รายการ\n--------------------\n\n"
    for r in found[:8]:
        msg += f"[{r['no']}] {r['unit']} - {r['name'][:45]}\n"
        msg += f"  วงเงิน: {r['budget']/1e6:,.1f} ลบ. | {r['status']}\n\n"
    if len(found) > 8:
        msg += f"... และอีก {len(found)-8} รายการ"
    await update.message.reply_text(msg)

async def cmd_job_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("กรุณาระบุเลขที่งานครับ\nเช่น /งาน 11")
        return
    no    = args[0]
    data  = load_data()
    found = [r for r in data if r['no'] == no]
    if not found:
        await update.message.reply_text(f"ไม่พบงานเลขที่ {no} ครับ")
        return
    r        = found[0]
    days_txt = f"เหลือ {r['days']} วัน" if r['days'].isdigit() else "-"
    msg = (
        f"รายละเอียดงานที่ {r['no']}\n"
        f"--------------------\n\n"
        f"หน่วย: {r['unit']}\n"
        f"งาน: {r['name']}\n"
        f"วิธี: {r['method']}\n"
        f"อำนาจอนุมัติ: {r['auth']}\n"
        f"วงเงิน: {r['budget']/1e6:,.2f} ล้านบาท\n"
        f"ปีงบประมาณ: {r['year']}\n"
        f"สถานะ: {r['status']}\n"
        f"เหลือเวลา: {days_txt}"
    )
    await update.message.reply_text(msg)

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    data = load_data()
    if any(w in text for w in ['dashboard', 'กราฟ', 'ภาพ', 'รูป']):
        await cmd_dashboard(update, ctx)
    elif any(w in text for w in ['รายงาน', 'สรุป', 'report']):
        await cmd_report(update, ctx)
    elif any(w in text for w in ['เร่งด่วน', 'ด่วน', 'ครบกำหนด']):
        await cmd_urgent(update, ctx)
    elif any(w in text for w in ['สถานะ', 'status']):
        await cmd_status(update, ctx)
    elif any(w in text for w in ['ปีงบ', 'งบประมาณ']):
        await cmd_yearly(update, ctx)
    elif any(w in text for w in ['วงเงิน', 'งบ', 'เงิน']):
        await cmd_budget(update, ctx)
    elif any(w in text for w in ['ค้าง', 'รายการ', 'ทั้งหมด']):
        total, budget, units, urgent = get_summary(data)
        await update.message.reply_text(
            f"งานค้างดำเนินการทั้งหมด: {total} รายการ\n"
            f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n"
            f"งานใกล้ครบกำหนด: {len(urgent)} รายการ"
        )
    else:
        found = [r for r in data if text in r['unit'].lower() or text in r['name'].lower()]
        if found:
            msg = f"พบ {len(found)} รายการที่เกี่ยวข้อง:\n\n"
            for r in found[:5]:
                msg += f"- [{r['no']}] {r['unit']} - {r['name'][:45]}\n"
                msg += f"  วงเงิน: {r['budget']/1e6:,.1f} ลบ. | {r['status']}\n\n"
            if len(found) > 5:
                msg += f"... และอีก {len(found)-5} รายการ\nใช้ /ค้นหา [คำ] เพื่อดูทั้งหมด"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text(
                "ไม่เข้าใจคำถามครับ ลองพิมพ์:\n"
                "/report /dashboard /urgent\n"
                "/unit /budget /status /yearly\n"
                "/หน่วย [ชื่อ] /ค้นหา [คำ] /งาน [เลขที่]"
            )

async def send_daily_report(ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await ctx.bot.send_message(chat_id=CHAT_ID, text=build_report(data))
    try:
        buf = build_dashboard_image(data)
        await ctx.bot.send_photo(chat_id=CHAT_ID, photo=buf,
            caption=f"Dashboard ประจำวัน {datetime.now().strftime('%d/%m/%Y')}")
    except Exception as e:
        logger.error(f"Daily dashboard error: {e}")

async def send_weekly_report(ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    total, budget, units, urgent = get_summary(data)
    msg = (
        f"รายงานประจำสัปดาห์ กบ.ทหาร\n"
        f"ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}\n"
        f"====================\n\n"
        f"งานทั้งหมด: {total} รายการ\n"
        f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n"
        f"งานใกล้ครบกำหนด: {len(urgent)} รายการ\n\n"
        f"#กบทหาร #รายงานรายสัปดาห์"
    )
    await ctx.bot.send_message(chat_id=CHAT_ID, text=msg)

async def check_urgent_alert(ctx: ContextTypes.DEFAULT_TYPE):
    data   = load_data()
    urgent = [r for r in data if r['days'].isdigit() and int(r['days']) <= 7]
    if urgent:
        msg = "แจ้งเตือน! งานใกล้ครบกำหนด 7 วัน\n--------------------\n\n"
        for r in sorted(urgent, key=lambda x: int(x['days'])):
            msg += f"- {r['unit']} - {r['name'][:45]}\n  เหลือ {r['days']} วัน\n\n"
        await ctx.bot.send_message(chat_id=CHAT_ID, text=msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",     start))
    app.add_handler(CommandHandler("help",      start))
    app.add_handler(CommandHandler("report",    cmd_report))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))
    app.add_handler(CommandHandler("urgent",    cmd_urgent))
    app.add_handler(CommandHandler("unit",      cmd_unit))
    app.add_handler(CommandHandler("budget",    cmd_budget))
    app.add_handler(CommandHandler("status",    cmd_status))
    app.add_handler(CommandHandler("yearly",    cmd_yearly))
    app.add_handler(CommandHandler("หน่วย",     cmd_search_unit))
    app.add_handler(CommandHandler("ค้นหา",     cmd_search))
    app.add_handler(CommandHandler("งาน",       cmd_job_detail))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.job_queue.run_daily(send_daily_report,  time=time(hour=8,  minute=0))
    app.job_queue.run_daily(send_weekly_report, time=time(hour=7,  minute=30), days=(0,))
    app.job_queue.run_daily(check_urgent_alert, time=time(hour=8,  minute=30))
    logger.info("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
