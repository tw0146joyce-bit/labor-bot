# -*- coding: utf-8 -*-
"""
勞健保 Telegram 機器人 2026年最新版
功能：勞保/災保/健保/勞退費用試算、完整58級查詢、身障眷屬補助試算、常見問答
"""

import os
import sys
import asyncio
import logging
import threading

# Python 3.10+ requires explicit event loop creation
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

# ============================================================
# Token 從環境變數讀取（部署到 Render 時在後台設定，不需寫在程式裡）
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
# ============================================================

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# ===== 完整58級數據 =====
# [級距, 公司勞保, 公司災保, 公司勞+職, 公司勞退, 員工勞保, 備註]
DATA = [
    (29500,2582,35,2617,1770,738,'健保最低級距'),
    (30300,2651,36,2687,1818,758,''),
    (31800,2783,38,2821,1908,795,''),
    (33300,2914,40,2954,1998,833,''),
    (34800,3045,42,3087,2088,870,''),
    (36300,3176,44,3220,2178,908,''),
    (38200,3342,46,3388,2292,955,''),
    (40100,3509,48,3557,2406,1002,''),
    (42000,3675,50,3725,2520,1050,''),
    (43900,3841,53,3894,2634,1098,''),
    (45800,4008,55,4063,2748,1145,'勞保最高級距'),
    (48200,4008,58,4066,2892,1145,''),
    (50600,4008,61,4069,3036,1145,''),
    (53000,4008,64,4072,3180,1145,''),
    (55400,4008,66,4074,3324,1145,''),
    (57800,4008,69,4077,3468,1145,''),
    (60800,4008,73,4081,3648,1145,''),
    (63800,4008,77,4085,3828,1145,''),
    (66800,4008,80,4088,4008,1145,''),
    (69800,4008,84,4092,4188,1145,''),
    (72800,4008,87,4095,4368,1145,'災保最高級距'),
    (76500,4008,87,4095,4590,1145,''),
    (80200,4008,87,4095,4812,1145,''),
    (83900,4008,87,4095,5034,1145,''),
    (87600,4008,87,4095,5256,1145,''),
    (92100,4008,87,4095,5526,1145,''),
    (96600,4008,87,4095,5796,1145,''),
    (101100,4008,87,4095,6066,1145,''),
    (105600,4008,87,4095,6336,1145,''),
    (110100,4008,87,4095,6606,1145,''),
    (115500,4008,87,4095,6930,1145,''),
    (120900,4008,87,4095,7254,1145,''),
    (126300,4008,87,4095,7578,1145,''),
    (131700,4008,87,4095,7902,1145,''),
    (137100,4008,87,4095,8226,1145,''),
    (142500,4008,87,4095,8550,1145,''),
    (147900,4008,87,4095,8874,1145,''),
    (150000,4008,87,4095,9000,1145,'勞退最高級距'),
    (156400,4008,87,4095,9000,1145,''),
    (162800,4008,87,4095,9000,1145,''),
    (169200,4008,87,4095,9000,1145,''),
    (175600,4008,87,4095,9000,1145,''),
    (182000,4008,87,4095,9000,1145,''),
    (189500,4008,87,4095,9000,1145,''),
    (197000,4008,87,4095,9000,1145,''),
    (204500,4008,87,4095,9000,1145,''),
    (212000,4008,87,4095,9000,1145,''),
    (219500,4008,87,4095,9000,1145,''),
    (228200,4008,87,4095,9000,1145,''),
    (236900,4008,87,4095,9000,1145,''),
    (245600,4008,87,4095,9000,1145,''),
    (254300,4008,87,4095,9000,1145,''),
    (263000,4008,87,4095,9000,1145,''),
    (273000,4008,87,4095,9000,1145,''),
    (283000,4008,87,4095,9000,1145,''),
    (293000,4008,87,4095,9000,1145,''),
    (303000,4008,87,4095,9000,1145,''),
    (313000,4008,87,4095,9000,1145,'健保最高級距'),
]

# 健保數據：[本人, +1眷, +2眷, +3眷, 雇主60%, 政府10%]
HEALTH = [
    (458,916,1374,1832,1428,238),(470,940,1410,1880,1466,244),
    (493,986,1479,1972,1539,256),(516,1032,1548,2064,1611,269),
    (540,1080,1620,2160,1684,281),(563,1126,1689,2252,1757,293),
    (592,1184,1776,2368,1849,308),(622,1244,1866,2488,1940,323),
    (651,1302,1953,2604,2032,339),(681,1362,2043,2724,2124,354),
    (710,1420,2130,2840,2216,369),(748,1496,2244,2992,2332,389),
    (785,1570,2355,3140,2449,408),(822,1644,2466,3288,2565,427),
    (859,1718,2577,3436,2681,447),(896,1792,2688,3584,2797,466),
    (943,1886,2829,3772,2942,490),(990,1980,2970,3960,3087,515),
    (1036,2072,3108,4144,3233,539),(1083,2166,3249,4332,3378,563),
    (1129,2258,3387,4516,3523,587),(1187,2374,3561,4748,3702,617),
    (1244,2488,3732,4976,3881,647),(1301,2602,3903,5204,4060,677),
    (1359,2718,4077,5436,4239,707),(1428,2856,4284,5712,4457,743),
    (1498,2996,4494,5992,4675,779),(1568,3136,4704,6272,4892,815),
    (1638,3276,4914,6552,5110,852),(1708,3416,5124,6832,5328,888),
    (1791,3582,5373,7164,5589,932),(1875,3750,5625,7500,5850,975),
    (1959,3918,5877,7836,6112,1019),(2043,4086,6129,8172,6373,1062),
    (2126,4252,6378,8504,6634,1106),(2210,4420,6630,8840,6896,1149),
    (2294,4588,6882,9176,7157,1193),(2327,4654,6981,9308,7259,1210),
    (2426,4852,7278,9704,7568,1261),(2525,5050,7575,10100,7878,1313),
    (2624,5248,7872,10496,8188,1365),(2724,5448,8172,10896,8497,1416),
    (2823,5646,8469,11292,8807,1468),(2939,5878,8817,11756,9170,1528),
    (3055,6110,9165,12220,9533,1589),(3172,6344,9516,12688,9896,1649),
    (3288,6576,9864,13152,10259,1710),(3404,6808,10212,13616,10622,1770),
    (3539,7078,10617,14156,11043,1840),(3674,7348,11022,14696,11464,1911),
    (3809,7618,11427,15236,11885,1981),(3944,7888,11832,15776,12306,2051),
    (4079,8158,12237,16316,12727,2121),(4234,8468,12702,16936,13211,2202),
    (4389,8778,13167,17556,13695,2282),(4544,9088,13632,18176,14179,2363),
    (4700,9400,14100,18800,14663,2444),(4855,9710,14565,19420,15146,2524),
]

def N(n): return f"{int(n):,}"

def find_grade(salary):
    """找最接近且不低於薪資的級距，回傳 index"""
    for i, row in enumerate(DATA):
        if salary <= row[0]:
            return i
    return len(DATA) - 1

# ===== 主選單鍵盤 =====
MAIN_KEYBOARD = ReplyKeyboardMarkup([
    ["🧮 費用試算", "📋 查詢級距"],
    ["♿ 身障補助試算", "❓ 常見問題"],
    ["📊 費率總表", "ℹ️ 使用說明"],
    ["🌐 網頁版計算機"],
], resize_keyboard=True)

WEB_URL = "https://tw0146joyce-bit.github.io/labor-bot/"

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 您好！我是 *2026年勞健保計算機器人* 🤖\n\n"
        "📅 資料版本：民國115年（2026.01.01起生效）\n"
        "📂 資料來源：勞保局＋健保署官方文件\n\n"
        "請選擇下方功能：",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD
    )

# ===== /help =====
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *使用說明*\n\n"
        "🧮 *費用試算* — 輸入薪資，算出公司＋員工每月負擔\n"
        "📋 *查詢級距* — 查看完整58級對照表（分段顯示）\n"
        "♿ *身障補助試算* — 計算有身障眷屬時的健保優惠\n"
        "❓ *常見問題* — 勞健保相關Q&A\n"
        "📊 *費率總表* — 2026年完整費率說明\n\n"
        "💡 *快速試算指令：*\n"
        "`試算 40000` — 試算月薪40,000元\n"
        "`試算 40000 2` — 月薪40,000＋1位眷屬\n"
        "`試算 40000 2 6` — 加上自提6%勞退",
        parse_mode="Markdown"
    )

# ===== 費用試算 =====
async def calc_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧮 *費用試算*\n\n"
        "請輸入：`試算 月薪 眷屬人數 自提%`\n\n"
        "範例：\n"
        "`試算 40000` — 月薪4萬，無眷屬，不自提\n"
        "`試算 45800 2` — 月薪45,800，本人+1眷屬\n"
        "`試算 60000 3 6` — 月薪6萬，本人+2眷屬，自提6%",
        parse_mode="Markdown"
    )

async def do_calc(update: Update, context: ContextTypes.DEFAULT_TYPE, salary: int, dep: int = 0, self_pct: int = 0):
    idx = find_grade(salary)
    row = DATA[idx]
    grade, cLabor, cDis, cLaborDis, cPension, eLabor, note = row
    h = HEALTH[idx]
    eHealth = h[dep]       # 員工健保（依眷屬）
    cHealth = h[4]         # 雇主健保
    cGov = h[5]            # 政府補助
    cTotal = cLaborDis + cPension + cHealth
    self_base = min(grade, 150000)
    self_amt = round(self_base * self_pct / 100)
    eTotal = eLabor + eHealth + self_amt
    dep_labels = ["本人（無眷屬）","本人＋1眷口","本人＋2眷口","本人＋3眷口"]
    grade_note = f"（{note}）" if note else ""

    text = (
        f"🧮 *費用試算結果* {grade_note}\n"
        f"第{idx+1}級・投保金額 {N(grade)} 元 ／ {dep_labels[dep]} ／ 自提{self_pct}%\n"
        f"{'─'*28}\n\n"
        f"🏢 *公司每月負擔*\n"
        f"・勞保（含就保）：{N(cLabor)} 元\n"
        f"・職災保險（0.12%）：{cDis} 元\n"
        f"・健保（60%）：{N(cHealth)} 元\n"
        f"・勞退提撥（6%）：{N(cPension)} 元\n"
        f"・*公司合計：{N(cTotal)} 元*\n"
        f"・政府補助健保（10%）：{N(cGov)} 元\n\n"
        f"👤 *員工每月扣繳*\n"
        f"・勞保（20%）：{N(eLabor)} 元\n"
        f"・健保（30%・{dep_labels[dep]}）：{N(eHealth)} 元\n"
        f"・勞退自提（{self_pct}%）：{N(self_amt)} 元\n"
        f"・*員工合計：{N(eTotal)} 元*\n"
    )
    if self_pct > 0:
        text += f"\n✅ 年度自提節稅金額：{N(self_amt*12)} 元"
    text += f"\n\n※ 數據來自勞保局＋健保署官方文件"
    await update.message.reply_text(text, parse_mode="Markdown")

# ===== 查詢級距（分頁顯示） =====
async def grade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("第1-11級（29,500～45,800）", callback_data="grade_0")],
        [InlineKeyboardButton("第12-21級（48,200～72,800）", callback_data="grade_1")],
        [InlineKeyboardButton("第22-38級（76,500～150,000）", callback_data="grade_2")],
        [InlineKeyboardButton("第39-58級（156,400～313,000）", callback_data="grade_3")],
    ])
    await update.message.reply_text("📋 請選擇要查詢的級距範圍：", reply_markup=keyboard)

async def grade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[1])
    ranges = [(0,11),(11,21),(21,38),(38,58)]
    s, e = ranges[page]
    lines = [f"{'─'*32}\n📋 *勞保+災保+勞退+健保 級距表*\n{'─'*32}"]
    lines.append("`級  投保額  員工勞保  員工健保  員工合計`")
    for i in range(s, e):
        row = DATA[i]
        h = HEALTH[i]
        note_tag = "⭐" if row[6] else "  "
        lines.append(f"`{str(i+1).rjust(2)}{note_tag} {N(row[0]).rjust(7)}  {N(row[5]).rjust(6)}  {N(h[0]).rjust(6)}  {N(row[5]+h[0]).rjust(6)}`")
    notes = {10:"⭐勞保最高",20:"⭐災保最高",37:"⭐勞退最高",57:"⭐健保最高"}
    for k,v in notes.items():
        if s <= k < e:
            lines.append(f"  {v}（第{k+1}級）")
    await query.edit_message_text("\n".join(lines), parse_mode="Markdown")

# ===== 身障補助試算 =====
async def disability_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "♿ *身障眷屬健保補助試算*\n\n"
        "*補助標準（針對眷屬持有身障手冊者）：*\n"
        "・重度／極重度：政府補助 *1/2*，眷屬自付50%\n"
        "・中度身障：政府補助 *1/3*，眷屬自付約67%\n"
        "・輕度身障：政府補助 *1/4*，眷屬自付75%\n"
        "・無身障：無補助，自付100%\n\n"
        "請輸入：`身障 月薪 眷屬身障等級`\n\n"
        "身障等級代碼：\n"
        "`0` = 無身障　`1` = 輕度　`2` = 中度　`3` = 重度/極重度\n\n"
        "範例（最多3位眷屬）：\n"
        "`身障 45800 1` — 1位輕度眷屬\n"
        "`身障 45800 1 0 0` — 太太輕度、兒子無、女兒無\n"
        "`身障 60000 3 2` — 2位眷屬，一重度一中度",
        parse_mode="Markdown"
    )

async def do_disability(update: Update, context: ContextTypes.DEFAULT_TYPE, salary: int, levels: list):
    idx = find_grade(salary)
    grade = DATA[idx][0]
    h = HEALTH[idx]
    self_fee = h[0]   # 本人健保30%
    dep_base = h[0]   # 單名眷屬基數

    subsidy_map = {0: 0, 1: 0.25, 2: 1/3, 3: 0.5}
    label_map   = {0:"無身障", 1:"輕度（補1/4）", 2:"中度（補1/3）", 3:"重度/極重度（補1/2）"}

    lines = [
        f"♿ *身障眷屬健保補助試算*",
        f"投保金額：{N(grade)} 元 ／ 眷屬 {len(levels)} 人",
        f"{'─'*28}",
        f"本人健保費（30%）：*{N(self_fee)} 元*",
        f"眷屬每人基數（30%）：{N(dep_base)} 元/人",
        ""
    ]

    dep_total = 0
    orig_total = 0
    for i, lv in enumerate(levels):
        sub = subsidy_map.get(lv, 0)
        after = round(dep_base * (1 - sub))
        saved = dep_base - after
        dep_total += after
        orig_total += dep_base
        saved_str = f"（省{saved}元）" if saved > 0 else ""
        lines.append(f"眷屬{i+1}【{label_map[lv]}】：*{N(after)} 元* {saved_str}")

    grand = self_fee + dep_total
    orig_grand = self_fee + orig_total
    total_saved = orig_grand - grand

    lines += [
        "",
        f"眷屬保費合計：{N(dep_total)} 元",
        f"{'─'*28}",
        f"💸 *本人＋眷屬合計：{N(grand)} 元/月*",
    ]
    if total_saved > 0:
        lines.append(f"✅ 較一般身份每月省：*{N(total_saved)} 元*（年省 {N(total_saved*12)} 元）")

    lines += [
        "",
        "※ 需向公司人資申報身障手冊，由公司向健保署申請",
        "※ 資料來源：勞保局 bli.gov.tw/0005481.html"
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ===== 費率總表 =====
async def show_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 *2026年勞健保費率總表*\n"
        "（民國115年1月1日起生效）\n"
        f"{'─'*28}\n\n"
        "🛡️ *勞工保險 合計12.5%*\n"
        "・普通事故：11.5%\n"
        "・就業保險：1%\n"
        "・勞工負擔20%，雇主70%，政府10%\n"
        "・最高級距：45,800元（第11級）\n\n"
        "⚙️ *職業災害保險 0.12%*\n"
        "・雇主全額負擔，勞工不需付費\n"
        "・最高級距：72,800元（第21級）\n\n"
        "🏥 *全民健保 5.17%*\n"
        "・個人30%、雇主60%、政府10%\n"
        "・眷屬每多1口多計1份30%（最多3口）\n"
        "・最低29,500元，最高313,000元\n\n"
        "💰 *勞退提撥*\n"
        "・雇主強制6%（上限150,000元）\n"
        "・勞工自提0~6%（全額免所得稅）\n\n"
        "📌 *二代健保補充費 2.11%*\n"
        "・獎金超投保金額4倍的部分\n"
        "・兼職超29,500元的部分\n"
        "・股利/租金年超2萬元的部分\n\n"
        "📅 *2026年基本工資*\n"
        "・月薪：29,500元（↑較2025多2,030元）\n"
        "・時薪：196元（↑較2025多13元）"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ===== 常見問題 =====
async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("勞保費率是多少？", callback_data="faq_labor")],
        [InlineKeyboardButton("災保費率是多少？", callback_data="faq_dis")],
        [InlineKeyboardButton("健保費率是多少？", callback_data="faq_health")],
        [InlineKeyboardButton("勞退雇主提撥多少？", callback_data="faq_pension")],
        [InlineKeyboardButton("眷屬如何加健保？", callback_data="faq_dep")],
        [InlineKeyboardButton("自提勞退節稅優惠？", callback_data="faq_tax")],
        [InlineKeyboardButton("二代健保補充費？", callback_data="faq_supp")],
        [InlineKeyboardButton("新進員工幾天內加保？", callback_data="faq_new")],
        [InlineKeyboardButton("身障眷屬有補助嗎？", callback_data="faq_dis_dep")],
    ])
    await update.message.reply_text("❓ 請選擇常見問題：", reply_markup=keyboard)

FAQ = {
    "faq_labor": "🛡️ *2026年勞工保險費率*\n總費率：*12.5%*\n・普通事故：11.5%\n・就業保險：1%\n負擔比：勞工20%、雇主70%、政府10%\n最高級距45,800元，勞工固定扣 *1,145元/月*",
    "faq_dis":   "⚙️ *2026年職業災害保險費率*\n費率：*0.12%*\n・*雇主全額負擔*，勞工不需付費\n・最高級距72,800元，超過固定87元/月",
    "faq_health": "🏥 *2026年健保費率 5.17%*\n・個人：30%\n・雇主：60%（含平均眷口0.56人）\n・政府：10%\n眷屬每多1口多1份30%，最多3口\n最低29,500元，最高313,000元（共58級）",
    "faq_pension":"💰 *勞工退休金 2026年*\n・雇主強制提撥6%\n・月提撥上限150,000元（超過固定9,000元）\n・勞工自提0~6%，自提全額免所得稅",
    "faq_dep":   "👨‍👩‍👧 *健保眷屬加保*\n可加保：配偶、父母、子女（直系血親）\n每多1口多計1份30%，最多3口\n眷屬本身有工作者，以工作單位投保為主",
    "faq_tax":   "✅ *勞退自提節稅*\n自提金額全額從綜合所得扣除\n舉例：月薪45,800，自提6%=每月2,748元\n全年32,976元，稅率20%省約 *6,595元*",
    "faq_supp":  "📌 *二代健保補充費 2.11%*\n・獎金超當月投保金額4倍\n・兼職超基本工資29,500元\n・股利/利息/租金年度超2萬元\n由公司/銀行代扣，不需自行繳納",
    "faq_new":   "📅 *新進員工加保規定*\n雇主須於到職日 *當天或前一日* 完成加保\n未及時加保發生事故，雇主須自行賠償\n2026年勞保局自動逕調至29,500元",
    "faq_dis_dep":"♿ *身障眷屬健保補助*\n眷屬持有身障手冊者可申請：\n・重度/極重度：補助1/2，自付50%\n・中度：補助1/3，自付約67%\n・輕度：補助1/4，自付75%\n向公司人資申報，備妥身障手冊影本\n資料來源：bli.gov.tw/0005481.html",
}

async def faq_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(FAQ.get(query.data, "查無資料"), parse_mode="Markdown")

# ===== 訊息主處理 =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # 按鈕觸發
    if text == "🧮 費用試算":     await calc_menu(update, context); return
    if text == "📋 查詢級距":     await grade_menu(update, context); return
    if text == "♿ 身障補助試算":  await disability_menu(update, context); return
    if text == "❓ 常見問題":     await show_faq(update, context); return
    if text == "📊 費率總表":     await show_rates(update, context); return
    if text == "ℹ️ 使用說明":     await help_cmd(update, context); return
    if text == "🌐 網頁版計算機":
        await update.message.reply_text(
            "🌐 *勞健保網頁版計算機*

點擊下方連結開啟網頁版，支援完整費用試算、級距查詢、身障補助計算：

" + WEB_URL,
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD
        )
        return

    parts = text.replace("，"," ").split()

    # 試算指令：試算 40000 [dep] [self%]
    if parts[0] in ["試算","计算","labor"]:
        try:
            salary = int(parts[1])
            dep    = min(int(parts[2]) - 1, 3) if len(parts) >= 3 else 0
            dep    = max(dep, 0)
            selfp  = min(int(parts[3]), 6) if len(parts) >= 4 else 0
            await do_calc(update, context, salary, dep, selfp)
        except:
            await update.message.reply_text("格式錯誤，請輸入：`試算 月薪 眷屬人數 自提%`\n例如：`試算 40000 2 6`", parse_mode="Markdown")
        return

    # 身障試算：身障 45800 1 0 0
    if parts[0] in ["身障","身心障礙","disability"]:
        try:
            salary = int(parts[1])
            levels = [min(int(x), 3) for x in parts[2:2+3]]  # 最多3位眷屬
            if not levels:
                await disability_menu(update, context)
                return
            await do_disability(update, context, salary, levels)
        except:
            await update.message.reply_text(
                "格式錯誤，請輸入：`身障 月薪 眷屬等級...`\n"
                "等級：0=無身障 1=輕度 2=中度 3=重度\n"
                "例如：`身障 45800 1 0 0`",
                parse_mode="Markdown"
            )
        return

    # 關鍵字自動回答
    for keys, faq_key in [
        (["勞保費率","12.5","11.5"], "faq_labor"),
        (["災保","職災","0.12"],     "faq_dis"),
        (["健保費率","5.17"],        "faq_health"),
        (["勞退","提撥"],            "faq_pension"),
        (["眷屬","加保"],            "faq_dep"),
        (["自提","節稅"],            "faq_tax"),
        (["二代健保","補充"],        "faq_supp"),
        (["幾天","新進","到職"],     "faq_new"),
        (["身障","身心障礙","補助"], "faq_dis_dep"),
    ]:
        if any(k in text for k in keys):
            await update.message.reply_text(FAQ[faq_key], parse_mode="Markdown")
            return

    # 預設
    await update.message.reply_text(
        "🤖 請選擇下方功能按鈕，或輸入：\n"
        "`試算 40000 2 6` — 費用試算\n"
        "`身障 45800 1 0` — 身障補助試算\n"
        "輸入 `/help` 查看完整說明",
        parse_mode="Markdown"
    )

# ===== 主程式 =====
import asyncio
from aiohttp import web

async def health_handler(request):
    return web.Response(text='OK')

async def run_bot_async():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(CommandHandler('rates', show_rates))
    app.add_handler(CommandHandler('faq', show_faq))
    app.add_handler(CallbackQueryHandler(faq_callback, pattern='^faq_'))
    app.add_handler(CallbackQueryHandler(grade_callback, pattern='^grade_'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print('Bot starting...')
    async with app:
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        print('Bot is polling...')
        # Keep running forever
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()

async def run_health_async():
    port = int(os.environ.get('PORT', 10000))
    web_app = web.Application()
    web_app.router.add_get('/', health_handler)
    web_app.router.add_get('/health', health_handler)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print('Health server started on port ' + str(port))

async def main_async():
    await run_health_async()
    await run_bot_async()

def main():
    if not BOT_TOKEN:
        print('ERROR: BOT_TOKEN not set')
        return
    asyncio.run(main_async())

if __name__ == "__main__":
    main()