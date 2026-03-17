async def screenshot_dashboard():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    
    total, budget, units, urgent = get_summary()
    fig = plt.figure(figsize=(14, 9), facecolor='#0a1628')
    fig.suptitle('Dashboard จัดซื้อจัดจ้าง กบ.ทหาร', 
                 fontsize=18, color='white', fontweight='bold', y=0.98)

    # KPI row
    kpi_data = [
        ('งานทั้งหมด', f'{total}', '#00d4ff'),
        ('วงเงินรวม', f'{budget/1e6:,.0f} ลบ.', '#f5a623'),
        ('งานใกล้ครบ', f'{len(urgent)}', '#ff4d6d'),
        ('หน่วยงาน', f'{len(units)}', '#00c896'),
    ]
    for i, (label, val, color) in enumerate(kpi_data):
        ax = fig.add_axes([0.04 + i*0.245, 0.78, 0.22, 0.14])
        ax.set_facecolor('#0f2044')
        ax.set_xlim(0,1); ax.set_ylim(0,1)
        ax.axhline(y=1, color=color, linewidth=4)
        ax.text(0.5, 0.62, val, ha='center', va='center', 
                color=color, fontsize=20, fontweight='bold')
        ax.text(0.5, 0.2, label, ha='center', va='center', 
                color='#8a9bb8', fontsize=10)
        ax.axis('off')

    # Donut chart
    ax1 = fig.add_axes([0.03, 0.30, 0.30, 0.44])
    ax1.set_facecolor('#0a1628')
    unit_names = [u for u,c in units.most_common()]
    unit_vals  = [c for u,c in units.most_common()]
    colors = ['#00d4ff','#00c896','#f5a623','#ff4d6d','#a78bfa','#34d399']
    ax1.pie(unit_vals, colors=colors[:len(unit_vals)], startangle=90,
            wedgeprops=dict(width=0.5))
    ax1.set_title('สัดส่วนตามหน่วย', color='#8a9bb8', fontsize=11, pad=8)
    legend = [mpatches.Patch(color=colors[i], 
              label=f'{unit_names[i]} ({unit_vals[i]})')
              for i in range(len(unit_names))]
    ax1.legend(handles=legend, loc='lower center', 
               bbox_to_anchor=(0.5,-0.22), ncol=2, fontsize=8,
               labelcolor='white', facecolor='#0f2044', edgecolor='none')

    # Bar chart
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
        ax2.text(bar.get_width()+5, bar.get_y()+bar.get_height()/2,
                 f'{val:,.0f}', va='center', color='#8a9bb8', fontsize=9)
    ax2.set_facecolor('#0f2044')
    ax2.tick_params(colors='#8a9bb8', labelsize=10)
    ax2.spines[:].set_visible(False)
    ax2.set_title('วงเงินตามหน่วย (ล้านบาท)', color='#8a9bb8', fontsize=11, pad=8)
    ax2.set_xlim(0, max(vals)*1.25)

    # Urgent table
    ax3 = fig.add_axes([0.03, 0.03, 0.94, 0.22])
    ax3.set_facecolor('#0f2044')
    ax3.set_xlim(0,1); ax3.set_ylim(0,1); ax3.axis('off')
    ax3.text(0.01, 0.92, 'งานต้องติดตามเร่งด่วน', 
             color='#ff4d6d', fontsize=11, fontweight='bold', va='top')
    for i, item in enumerate(URGENT_ITEMS[:4]):
        color = '#ff4d6d' if i < 2 else '#f5a623'
        ax3.text(0.01, 0.68 - i*0.17, f'  • {item}', 
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
