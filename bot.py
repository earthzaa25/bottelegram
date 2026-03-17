import os, logging, asyncio, io
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

PROCUREMENT_DATA = [
    {"no":"1","unit":"ยก.ทหาร","name":"งานจัดซื้ออุปกรณ์ติดตามกำลังทางบก","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":14780000,"days":"134"},
    {"no":"2","unit":"ยก.ทหาร","name":"งานจัดซื้ออุปกรณ์ระบบแผนที่สถานการณ์ร่วมดิจิทัล ระยะที่ 2","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":40840000,"days":"163"},
    {"no":"3","unit":"ยก.ทหาร","name":"งานจัดซื้ออุปกรณ์ RPASS Phase 2","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":12960000,"days":"157"},
    {"no":"4","unit":"สส.ทหาร","name":"งานจัดซื้อระบบนำเสนอห้องอำนวยการยุทธ์ร่วม ศบท.","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":25190000,"days":"88"},
    {"no":"5","unit":"สส.ทหาร","name":"งานจัดหาระบบปฏิบัติการย่านความถี่ฯ (ผูกพัน 68-71)","method":"-","auth":"ปล.กห.","budget":800000000,"days":"761"},
    {"no":"6","unit":"ผท.ทหาร","name":"เครื่องมือระบบประมวลผลจัดทำแผนที่ กลุ่มจังหวัดที่ 1","method":"-","auth":"ผบ.ทสส.","budget":55550000,"days":"2"},
    {"no":"7","unit":"ผท.ทหาร","name":"เครื่องมือสำรวจข้อมูลภูมิประเทศ ปี 2568","method":"-","auth":"ผบ.ทสส.","budget":20750000,"days":"26"},
    {"no":"8","unit":"ผท.ทหาร","name":"เครื่องมือทำแผนที่สามมิติ ปี 2568","method":"-","auth":"ผบ.ทสส.","budget":21980000,"days":"47"},
    {"no":"9","unit":"ผท.ทหาร","name":"เช่าเครื่องบินถ่ายภาพทางอากาศ กลุ่มจังหวัดที่ 1","method":"-","auth":"ผบ.ทสส.","budget":128440000,"days":""},
    {"no":"10","unit":"ผท.ทหาร","name":"เช่าเครื่องมือถ่ายภาพทางอากาศ ปี 2568","method":"-","auth":"ผบ.ทสส.","budget":69980000,"days":""},
    {"no":"11","unit":"สส.ทหาร","name":"ชุดวิทยุไมโครเวฟ IP ภาค NE+เหนือล่าง","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":98570000,"days":"193"},
    {"no":"12","unit":"สส.ทหาร","name":"ชุดไมโครเวฟ ภาคกลาง+เหนือบน","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":96880000,"days":"193"},
    {"no":"13","unit":"สส.ทหาร","name":"ชุดไมโครเวฟ ภาคใต้","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":99220000,"days":"193"},
    {"no":"14","unit":"นซบ.ทหาร","name":"งานจ้างอบรมชุดปฏิบัติการไซเบอร์","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":18820000,"days":""},
    {"no":"15","unit":"นซบ.ทหาร","name":"ระบบป้องกันภัยคุกคามไซเบอร์","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":26827416,"days":""},
    {"no":"16","unit":"นซบ.ทหาร","name":"ระบบสนับสนุนป้องกันภัยไซเบอร์","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":16532398,"days":""},
    {"no":"18","unit":"ยก.ทหาร","name":"พัฒนาระบบป้องกันยาเสพติด","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":21174984,"days":""},
    {"no":"19","unit":"ยก.ทหาร","name":"พัฒนาระบบประเมินพร้อมรบ","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":29500000,"days":""},
    {"no":"21","unit":"สส.ทหาร","name":"ระบบยืนยันตัวตนเครือข่าย บก.ทท. (210 วัน)","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":44000000,"days":"210"},
    {"no":"23","unit":"สส.ทหาร","name":"Data Governance & Data Management (270 วัน)","method":"คัดเลือก ม.56(1)(ฉ)","auth":"ผบ.ทสส.","budget":22000000,"days":"270"},
    {"no":"24","unit":"ผท.ทหาร","name":"ซ่อมบำรุงเฮลิคอปเตอร์ EC155 B1","method":"เจาะจง ม.56(2)(ซ)","auth":"ผบ.ทสส.","budget":31800000,"days":"289"},
    {"no":"25","unit":"ผท.ทหาร","name":"ซ่อมบำรุง BEECHCRAFT KING AIR 350i #93311","method":"เจาะจง ม.56(2)(ค)","auth":"ผบ.ทสส.","budget":61250000,"days":""},
    {"no":"26","unit":"ยบ.ทหาร","name":"รถยนต์โดยสารปรับอากาศ 42 ที่นั่ง 4 คัน","method":"ประกาศเชิญชวน","auth":"ผบ.ทสส.","budget":25800000,"days":""},
    {"no":"28","unit":"นทพ.","name":"รถบดล้อเหล็กสั่นสะเทือน 10 คัน","method":"เจาะจง ม.56(2)(จ)","auth":"ผบ.ทสส.","budget":32280000,"days":""},
    {"no":"29","unit":"นทพ.","name":"รถขุดตักมาตรฐาน 12 คัน","method":"ประกาศเชิญชวน","auth":"ผบ.ทสส.","budget":62016000,"days":""},
]

URGENT_ITEMS = [
    "จ้างสร้างเรือน้ำมัน ทร. - กสล.ฯ ตรวจ (ค้าง 32 วัน)",
    "BEECHCRAFT KING AIR 350i - รอ จก.กบ.ทหาร",
    "Anti-Drone ทอ. 9 ระบบ - คาดเสนอ เม.ย.69",
    "รถยนต์โดยสาร 42 ที่นั่ง - รอ ผบ.ทสส. (ค้าง 54 วัน)",
]

def get_summary():
    total  = len(PROCUREMENT_DATA)
    budget = sum(r['budget'] for r in PROCUREMENT_DATA)
    units  = Counter(r['unit'] for r in PROCUREMENT_DATA)
    urgent = [r for r in PROCUREMENT_DATA if r['days'].isdigit() and int(r['days']) <= 50]
    return total, budget, units, urgent

def build_report():
    total, budget, units, urgent = get_summary()
    today = datetime.now().strftime("%d/%m/%Y %H:%M น.")
    unit_lines = '\n'.join([f'  - {u}: {c} รายการ' for u,c in units.most_common()])
    urg = '\n'.join([f'  - {r["unit"]} - {r["name"][:35]}... (เหลือ {r["days"]} วัน)'
                     for r in sorted(urgent, key=lambda x: int(x['days']))])
    urgent_block = f"\nงานใกล้ครบกำหนด:\n{urg}\n" if urg else ""
    return (
        f"รายงานจัดซื้อจัดจ้าง กบ.ทหาร\n"
        f"ข้อมูล ณ {today}\n"
        f"--------------------\n\n"
        f"งานทั้งหมด: {total} รายการ\n"
        f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n\n"
        f"สรุปตามหน่วย:\n{unit_lines}\n"
        f"{urgent_block}\n"
        f"งานต้องติดตาม:\n"
        + '\n'.join([f'  - {x}' for x in URGENT_ITEMS])
        + "\n\n#กบทหาร #จัดซื้อจัดจ้าง"
    )

def build_dashboard_image():
    total, budget, units, urgent = get_summary()

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
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
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
    colors = ['#00d4ff', '#00c896', '#f5a623', '#ff4d6d', '#a78bfa', '#34d399']
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
    for r in PROCUREMENT_DATA:
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
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)
    ax3.axis('off')
    ax3.text(0.01, 0.92, 'งานต้องติดตามเร่งด่วน',
             color='#ff4d6d', fontsize=11, fontweight='bold', va='top')
    for i, item in enumerate(URGENT_ITEMS[:4]):
        color = '#ff4d6d' if i < 2 else '#f5a623'
        ax3.text(0.01, 0.68 - i*0.17, f'  - {item}',
                 color=color, fontsize=10, va='top')
    ax3.text(0.98, 0.05,
             f'ข้อมูล ณ {datetime.now().strftime("%d/%m/%Y")}  |  กบ.ทหาร',
             color='#3a4a6a', fontsize=9, ha='right', va='bottom')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='#0a1628')
    buf.seek(0)
    plt.close()
    return buf

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "สวัสดีครับ Bot จัดซื้อจัดจ้าง กบ.ทหาร\n\n"
        "คำสั่งที่ใช้ได้:\n"
        "/report - รายงานสรุปประจำวัน\n"
        "/dashboard - ภาพ Dashboard\n"
        "/urgent - งานเร่งด่วน\n"
        "/unit - สรุปตามหน่วย\n"
        "/budget - สรุปวงเงิน\n\n"
        "หรือพิมพ์ถามได้เลย เช่น:\n"
        "งานค้างกี่รายการ\n"
        "วงเงินรวมเท่าไหร่\n"
        "งานเร่งด่วนมีอะไรบ้าง"
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
    total, budget, units, urgent = get_summary()
    msg = "งานเร่งด่วนที่ต้องติดตาม\n--------------------\n\n"
    if urgent:
        msg += "งานใกล้ครบกำหนด (เหลือ < 50 วัน):\n"
        for r in sorted(urgent, key=lambda x: int(x['days'])):
            msg += f"  - {r['unit']} - {r['name'][:40]}...\n    เหลือ {r['days']} วัน\n\n"
    msg += "งานที่ต้องติดตามพิเศษ:\n"
    for x in URGENT_ITEMS:
        msg += f"  - {x}\n"
    await update.message.reply_text(msg)

async def cmd_unit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    total, budget, units, _ = get_summary()
    unit_budget = {}
    for r in PROCUREMENT_DATA:
        unit_budget[r['unit']] = unit_budget.get(r['unit'], 0) + r['budget']
    msg = "สรุปตามหน่วย\n--------------------\n\n"
    for u, c in units.most_common():
        b = unit_budget.get(u, 0)
        msg += f"{u}\n   จำนวนงาน: {c} รายการ\n   วงเงิน: {b/1e6:,.1f} ล้านบาท\n\n"
    await update.message.reply_text(msg)

async def cmd_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    total, budget, units, _ = get_summary()
    msg = (
        f"สรุปวงเงินจัดซื้อจัดจ้าง\n--------------------\n\n"
        f"วงเงินรวมทั้งหมด: {budget/1e6:,.1f} ล้านบาท\n"
        f"จำนวนงาน: {total} รายการ\n"
        f"วงเงินเฉลี่ยต่องาน: {budget/total/1e6:,.1f} ล้านบาท\n\n"
        f"อำนาจ ผบ.ทสส.: {sum(r['budget'] for r in PROCUREMENT_DATA if r['auth']=='ผบ.ทสส.')/1e6:,.1f} ลบ.\n"
        f"อำนาจ ปล.กห.: {sum(r['budget'] for r in PROCUREMENT_DATA if r['auth']=='ปล.กห.')/1e6:,.1f} ลบ."
    )
    await update.message.reply_text(msg)

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if any(w in text for w in ['dashboard', 'กราฟ', 'ภาพ', 'รูป']):
        await cmd_dashboard(update, ctx)
    elif any(w in text for w in ['รายงาน', 'สรุป', 'report']):
        await cmd_report(update, ctx)
    elif any(w in text for w in ['เร่งด่วน', 'urgent', 'ด่วน', 'ครบกำหนด']):
        await cmd_urgent(update, ctx)
    elif any(w in text for w in ['หน่วย', 'unit']):
        await cmd_unit(update, ctx)
    elif any(w in text for w in ['วงเงิน', 'งบ', 'budget', 'เงิน']):
        await cmd_budget(update, ctx)
    elif any(w in text for w in ['ค้าง', 'รายการ', 'ทั้งหมด']):
        total, budget, units, urgent = get_summary()
        await update.message.reply_text(
            f"งานค้างดำเนินการทั้งหมด: {total} รายการ\n"
            f"วงเงินรวม: {budget/1e6:,.1f} ล้านบาท\n"
            f"งานใกล้ครบกำหนด: {len(urgent)} รายการ"
        )
    else:
        found = [r for r in PROCUREMENT_DATA
                 if text in r['unit'].lower() or text in r['name'].lower()]
        if found:
            msg = f"พบ {len(found)} รายการ:\n\n"
            for r in found[:5]:
                msg += f"- {r['unit']} - {r['name'][:50]}\n  วงเงิน: {r['budget']/1e6:,.1f} ลบ.\n\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text(
                "ไม่เข้าใจคำถามครับ ลองพิมพ์:\n"
                "/report, /dashboard, /urgent, /unit, /budget"
            )

async def send_daily_report(ctx: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending daily report...")
    await ctx.bot.send_message(chat_id=CHAT_ID, text=build_report())
    try:
        buf = build_dashboard_image()
        await ctx.bot.send_photo(
            chat_id=CHAT_ID, photo=buf,
            caption=f"Dashboard ประจำวัน {datetime.now().strftime('%d/%m/%Y')}"
        )
    except Exception as e:
        logger.error(f"Daily dashboard error: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",     start))
    app.add_handler(CommandHandler("help",      start))
    app.add_handler(CommandHandler("report",    cmd_report))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))
    app.add_handler(CommandHandler("urgent",    cmd_urgent))
    app.add_handler(CommandHandler("unit",      cmd_unit))
    app.add_handler(CommandHandler("budget",    cmd_budget))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.job_queue.run_daily(send_daily_report, time=time(hour=8, minute=0))
    logger.info("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
