from flask import Flask, render_template_string, request, redirect, Response
import sqlite3
from datetime import datetime
import io
import csv

app = Flask(__name__)
app.secret_key = "omborim_sidebar_suite_2030"
DB = "omborim.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nomi TEXT,
        tur TEXT, 
        miqdor REAL DEFAULT 0,
        birlik TEXT, 
        narx REAL DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS retseptlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tayyor_id INTEGER,
        xomashyo_id INTEGER,
        ketadigan_miqdor REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mijozlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ism TEXT,
        telefon TEXT,
        manzil TEXT,
        izoh TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sotuvlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mijoz_id INTEGER,
        mijoz_nomi TEXT,
        tayyor_id INTEGER,
        miqdor REAL,
        jami_summa REAL,
        tolangan_summa REAL,
        qarz_summa REAL,
        sana TEXT,
        oy TEXT,
        yil TEXT
    )''')
    conn.commit()
    conn.close()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMBORIM OS - Industrial Suite</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <style>
        :root {
            --primary: #ffffff;
            --emerald: #10b981;
            --danger: #f43f5e;
            --accent-gold: #f59e0b;
            --text-main: #ffffff;
            --text-muted: #94a3b8;
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.16);
            --glass-card: rgba(255, 255, 255, 0.07);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }

        body {
            color: var(--text-main);
            padding: 16px;
            min-height: 100vh;
            background: linear-gradient(135deg, #000000, #0f141d, #1b2230, #05070a, #151a24, #000000);
            background-size: 500% 500%;
            animation: monochromeWave 20s ease-in-out infinite alternate;
            background-attachment: fixed;
            position: relative;
            overflow-x: hidden;
        }

        @keyframes monochromeWave {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .glass-panel {
            position: relative; z-index: 1;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 14px;
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.55), inset 0 1px 1px rgba(255, 255, 255, 0.15);
        }

        /* Yuqori Panel va Gamburger (Menyu) tugmasi */
        .top-nav {
            display: flex; justify-content: space-between; align-items: center;
            padding: 12px 16px; margin-bottom: 16px;
        }
        .nav-left { display: flex; align-items: center; gap: 10px; }
        .menu-toggle-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--glass-border);
            color: #fff; width: 38px; height: 38px;
            border-radius: 10px; display: flex; flex-direction: column;
            justify-content: center; align-items: center; gap: 4px;
            cursor: pointer;
        }
        .menu-line { width: 18px; height: 2px; background: #fff; border-radius: 1px; }

        .logo-tag {
            background: #ffffff; color: #000;
            padding: 4px 8px; border-radius: 6px; font-weight: 900; font-size: 11px;
        }

        .lang-switcher {
            display: flex; gap: 4px; background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--glass-border); border-radius: 8px; padding: 2px;
        }
        .lang-btn {
            background: transparent; border: none; color: var(--text-muted);
            padding: 5px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;
            cursor: pointer;
        }
        .lang-btn.active { background: #fff; color: #000; }

        /* CHAP DEVORDAN CHIQADIGAN SHAFFOF MENYU (SIDEBAR DRAWER) */
        .sidebar-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(12px);
            z-index: 998; opacity: 0; pointer-events: none; transition: opacity 0.3s;
        }
        .sidebar-overlay.active { opacity: 1; pointer-events: auto; }

        .sidebar-drawer {
            position: fixed; top: 0; left: -280px; width: 280px; height: 100%;
            background: rgba(15, 20, 32, 0.92);
            border-right: 1px solid var(--glass-border);
            backdrop-filter: blur(30px);
            z-index: 999; padding: 20px 16px;
            display: flex; flex-direction: column; gap: 8px;
            transition: left 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 10px 0 30px rgba(0,0,0,0.8);
        }
        .sidebar-drawer.active { left: 0; }

        .sidebar-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--glass-border);
        }
        .sidebar-item {
            padding: 12px 14px; border-radius: 10px; font-size: 13px; font-weight: 700;
            color: var(--text-muted); cursor: pointer; transition: all 0.2s;
            display: flex; align-items: center; justify-content: space-between;
        }
        .sidebar-item:hover, .sidebar-item.active {
            background: rgba(255, 255, 255, 0.12); color: #fff;
            border-left: 3px solid #fff;
        }

        .page-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 16px; position: relative; z-index: 1;
        }
        .page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }

        /* Metrikalar */
        .metrics-grid {
            display: grid; grid-template-columns: repeat(2, 1fr);
            gap: 12px; margin-bottom: 18px; position: relative; z-index: 1;
        }
        @media(min-width: 768px) { .metrics-grid { grid-template-columns: repeat(4, 1fr); } }
        .card { padding: 14px; }
        .card-label { font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; }
        .card-value { font-size: 20px; font-weight: 800; color: #fff; }

        .panel { padding: 18px; margin-bottom: 16px; }
        .panel-header { font-size: 14px; font-weight: 800; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; }

        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--glass-border); }
        th { color: var(--text-muted); font-weight: 700; text-transform: uppercase; font-size: 10px; }

        input, select {
            width: 100%; background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border); color: #fff;
            padding: 11px 14px; border-radius: 10px; font-size: 13px;
            margin-bottom: 10px; outline: none;
        }
        input:focus, select:focus { border-color: #ffffff; }

        .btn {
            background: #ffffff; color: #000; border: none; padding: 11px 18px;
            font-weight: 800; border-radius: 10px; cursor: pointer; font-size: 12px;
            text-decoration: none; display: inline-block; text-align: center;
        }
        .btn-danger {
            background: var(--danger); color: #fff; border: none; padding: 6px 12px;
            border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer;
            text-decoration: none;
        }

        .data-row {
            background: var(--glass-card);
            border: 1px solid var(--glass-border);
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* REYTING BO'LIMI: PODIUM SHOHSUPASI ANIMATSIYASI */
        .podium-box {
            display: grid; grid-template-columns: repeat(3, 1fr);
            gap: 10px; align-items: flex-end; margin-bottom: 24px; padding-top: 20px;
        }
        .podium-col {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--glass-border);
            border-radius: 12px 12px 0 0;
            text-align: center; padding: 12px 6px;
            position: relative; transform: translateY(50px); opacity: 0;
        }
        .podium-1 { height: 160px; background: rgba(245, 158, 11, 0.15); border-color: var(--accent-gold); }
        .podium-2 { height: 130px; }
        .podium-3 { height: 110px; }
        .podium-badge {
            width: 28px; height: 28px; border-radius: 50%; margin: -26px auto 8px auto;
            display: flex; align-items: center; justify-content: center;
            font-weight: 900; font-size: 13px; color: #000;
        }
    </style>
</head>
<body>

    <!-- Chap Devordan Chiqadigan Menyu (Sidebar) -->
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
    <div class="sidebar-drawer" id="sidebarDrawer">
        <div class="sidebar-header">
            <span style="font-weight:900; font-size:14px; letter-spacing:0.5px;">BO'LIMLAR</span>
            <span style="cursor:pointer; font-size:20px; color:var(--text-muted);" onclick="toggleSidebar()">✕</span>
        </div>
        
        <!-- SIZ AYTGAN ANIQ KETMA-KETLIK -->
        <div class="sidebar-item active" onclick="selectSection('s-sales', 'Sotuv (Kassa)')">1. Sotuv (Kassa) <span>→</span></div>
        <div class="sidebar-item" onclick="selectSection('s-inventory', 'Ombor Qoldig‘i')">2. Ombor Qoldig‘i <span>→</span></div>
        <div class="sidebar-item" onclick="selectSection('s-clients', 'Mijozlar (CRM)')">3. Mijozlar (CRM) <span>→</span></div>
        <div class="sidebar-item" onclick="selectSection('s-analytics', 'Savdo Nazorati')">4. Savdo Nazorati <span>→</span></div>
        <div class="sidebar-item" onclick="selectSection('s-production', 'Ishlab Chiqarish')">5. Ishlab Chiqarish <span>→</span></div>
        <div class="sidebar-item" onclick="selectSection('s-action', 'Yangi Kiritish')">6. Yangi Kiritish <span>→</span></div>
        <div class="sidebar-item" onclick="selectSection('s-ratings', 'Reyting & KPI')">7. Reyting & KPI <span>→</span></div>
        <div class="sidebar-item" onclick="selectSection('s-purge', 'Xavfsiz O‘chirish')" style="color:var(--danger);">8. O‘chirish Bo‘limi <span>→</span></div>
    </div>

    <!-- Yuqori Panel -->
    <div class="top-nav glass-panel">
        <div class="nav-left">
            <!-- Chap Menyuni Ochuvchi Tugma -->
            <div class="menu-toggle-btn" onclick="toggleSidebar()">
                <div class="menu-line"></div>
                <div class="menu-line"></div>
                <div class="menu-line"></div>
            </div>
            <span class="logo-tag">PRO</span>
            <span style="font-weight:900; font-size:14px;">OMBORIM OS</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <a href="/export/excel" class="btn" style="padding:6px 10px; font-size:11px;">Excel Export</a>
            <div class="lang-switcher">
                <button class="lang-btn active" onclick="setLang('uz')">UZ</button>
                <button class="lang-btn" onclick="setLang('ru')">RU</button>
                <button class="lang-btn" onclick="setLang('en')">EN</button>
            </div>
        </div>
    </div>

    <div class="page-header">
        <div class="page-title" id="pageTitleText">Sotuv (Kassa)</div>
        <div style="font-size:11px; color:var(--emerald); font-weight:700;">● Online Rejim</div>
    </div>

    <!-- 4 ta Katta Ko'rsatkich -->
    <div class="metrics-grid">
        <div class="card glass-panel">
            <div class="card-label" id="lbl-today">Bugungi Savdo</div>
            <div class="card-value" style="color:var(--emerald);">{{ "{:,.0f}".format(kunlik_savdo) }}</div>
            <span style="font-size:10px; color:var(--text-muted);">{{ bugun }}</span>
        </div>
        <div class="card glass-panel">
            <div class="card-label" id="lbl-month">Joriy Oy Savdosi</div>
            <div class="card-value" style="color:var(--emerald);">{{ "{:,.0f}".format(oylik_savdo) }}</div>
            <span style="font-size:10px; color:var(--text-muted);">{{ joriy_oy }}</span>
        </div>
        <div class="card glass-panel">
            <div class="card-label" id="lbl-year">Yillik Savdo</div>
            <div class="card-value" style="color:var(--primary);">{{ "{:,.0f}".format(yillik_savdo) }}</div>
            <span style="font-size:10px; color:var(--text-muted);">{{ joriy_yil }} yillik aylanma</span>
        </div>
        <div class="card glass-panel">
            <div class="card-label" id="lbl-qarz">Umumiy Nasiya (Qarz)</div>
            <div class="card-value" style="color:var(--danger);">{{ "{:,.0f}".format(jami_qarz) }}</div>
            <span style="font-size:10px; color:var(--danger);">● Undirilishi kerak</span>
        </div>
    </div>

    <!-- 1-BO'LIM: SOTUV (KASSA) -->
    <div id="sec-s-sales" class="tab-pane">
        <div style="display:grid; grid-template-columns: 1fr 340px; gap:16px;">
            <div class="panel glass-panel">
                <div class="panel-header"><span>Sotuvlar Tarixi</span></div>
                {% if not sotuvlar %}
                <p style="color:var(--text-muted); font-size:12px; text-align:center; padding:20px 0;">Sotuvlar mavjud emas.</p>
                {% else %}
                <table>
                    <thead>
                        <tr><th>Mijoz</th><th>Miqdor</th><th>Jami</th><th>To'landi</th><th>Qarz</th><th>Sana</th></tr>
                    </thead>
                    <tbody>
                        {% for s in sotuvlar %}
                        <tr>
                            <td><b>{{ s[2] }}</b></td>
                            <td>{{ s[4] }} dona</td>
                            <td>{{ "{:,.0f}".format(s[5]) }}</td>
                            <td style="color:var(--emerald);">{{ "{:,.0f}".format(s[6]) }}</td>
                            <td style="color:var(--danger); font-weight:700;">{{ "{:,.0f}".format(s[7]) }}</td>
                            <td style="color:var(--text-muted);">{{ s[8] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
            </div>

            <div class="panel glass-panel">
                <div class="panel-header"><span>Mahsulot Sotish</span></div>
                <form action="/sotish" method="POST">
                    <label style="font-size:11px; color:var(--text-muted);">Mijozni tanlang:</label>
                    <select name="mijoz_id" required>
                        <option value="">Mijozni tanlang</option>
                        {% for m in mijozlar %}
                        <option value="{{ m[0] }}">{{ m[1] }} ({{ m[2] }})</option>
                        {% endfor %}
                    </select>

                    <label style="font-size:11px; color:var(--text-muted);">Mahsulotni tanlang (Ombordagi barchasi):</label>
                    <select name="tayyor_id" id="sale_item_select" onchange="autoFillPrice()" required>
                        <option value="" data-price="0">Mahsulotni tanlang</option>
                        {% for item in items %}
                        <option value="{{ item[0] }}" data-price="{{ item[5] }}">
                            {{ item[1] }} (Omborda: {{ item[3] }} {{ item[4] }} | {{ "{:,.0f}".format(item[5]) }} so'm)
                        </option>
                        {% endfor %}
                    </select>

                    <input type="number" step="any" name="miqdor" placeholder="Sotilgan miqdor" required>
                    <input type="number" step="any" name="sotuv_narxi" id="sale_price_input" placeholder="Sotuv narxi" required>
                    <input type="number" step="any" name="tolangan_summa" placeholder="To'langan summa (naqd)" required>
                    <button type="submit" class="btn" style="width:100%;">Sotuvni Saqlash</button>
                </form>
            </div>
        </div>
    </div>

    <!-- 2-BO'LIM: OMBOR QOLDIG'I -->
    <div id="sec-s-inventory" class="tab-pane" style="display:none;">
        <div class="panel glass-panel">
            <div class="panel-header"><span>Ombor Zaxiralari</span></div>
            {% if not items %}
            <p style="color:var(--text-muted); font-size:12px; text-align:center; padding:20px 0;">Omborda tovarlar mavjud emas.</p>
            {% else %}
            <table>
                <thead>
                    <tr><th>Nomi</th><th>Turi</th><th>Qoldiq Miqdori</th><th>Tannarx</th><th>Jami Qiymat</th></tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td><b>{{ item[1] }}</b></td>
                        <td><span style="background:rgba(255,255,255,0.08); padding:3px 8px; border-radius:6px; font-size:10px;">{{ item[2] }}</span></td>
                        <td style="font-weight:700;">{{ item[3] }} {{ item[4] }}</td>
                        <td>{{ "{:,.0f}".format(item[5]) }} so'm</td>
                        <td><b>{{ "{:,.0f}".format(item[3] * item[5]) }}</b> so'm</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>
    </div>

    <!-- 3-BO'LIM: MIJOZLAR (CRM) -->
    <div id="sec-s-clients" class="tab-pane" style="display:none;">
        <div style="display:grid; grid-template-columns: 320px 1fr; gap:16px;">
            <div class="panel glass-panel">
                <div class="panel-header"><span>Yangi Mijoz Qo'shish</span></div>
                <form action="/add_client" method="POST">
                    <input type="text" name="ism" placeholder="Mijoz nomi" required>
                    <input type="text" name="telefon" placeholder="Telefon raqami" required>
                    <input type="text" name="manzil" placeholder="Manzil">
                    <input type="text" name="izoh" placeholder="Izoh">
                    <button type="submit" class="btn" style="width:100%;">Saqlash</button>
                </form>
            </div>

            <div class="panel glass-panel">
                <div class="panel-header"><span>Mijozlar Ro'yxati</span></div>
                {% for m in mijozlar %}
                <div class="data-row">
                    <div>
                        <h4 style="font-size:14px; font-weight:800;">{{ m[1] }}</h4>
                        <p style="font-size:11px; color:var(--text-muted);">{{ m[2] }} {% if m[3] %}| {{ m[3] }}{% endif %}</p>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:14px; font-weight:800; color:{% if m[4] > 0 %}var(--danger){% else %}var(--emerald){% endif %};">
                            {% if m[4] > 0 %}{{ "{:,.0f}".format(m[4]) }} so'm{% else %}Qarzi yo'q{% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- 4-BO'LIM: SAVDO NAZORATI -->
    <div id="sec-s-analytics" class="tab-pane" style="display:none;">
        <div class="panel glass-panel">
            <div class="panel-header"><span>Savdo Dinamikasi</span></div>
            <table>
                <thead>
                    <tr><th>Davr</th><th>Jami Savdo</th><th>Nasiya (Qarz)</th></tr>
                </thead>
                <tbody>
                    <tr><td><b>Bugun</b></td><td style="color:var(--emerald); font-weight:800;">{{ "{:,.0f}".format(kunlik_savdo) }}</td><td>-</td></tr>
                    <tr><td><b>Joriy Oy</b></td><td style="color:var(--emerald); font-weight:800;">{{ "{:,.0f}".format(oylik_savdo) }}</td><td>-</td></tr>
                    <tr><td><b>Yillik</b></td><td style="color:var(--primary); font-weight:800;">{{ "{:,.0f}".format(yillik_savdo) }}</td><td style="color:var(--danger); font-weight:800;">{{ "{:,.0f}".format(jami_qarz) }}</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- 5-BO'LIM: ISHLAB CHIQARISH -->
    <div id="sec-s-production" class="tab-pane" style="display:none;">
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
            <div class="panel glass-panel">
                <div class="panel-header"><span>Ishlab Chiqarishni Kiritish</span></div>
                <form action="/ishlab_chiqarish" method="POST">
                    <select name="tayyor_id" required>
                        <option value="">Qaysi mahsulot chiqarildi?</option>
                        {% for m in items %}
                        <option value="{{ m[0] }}">{{ m[1] }} (Omborda: {{ m[3] }} {{ m[4] }})</option>
                        {% endfor %}
                    </select>
                    <input type="number" step="any" name="miqdor" placeholder="Miqdori" required>
                    <button type="submit" class="btn" style="width:100%;">Zaxiraga Qo'shish & Xomashyoni Ayirish</button>
                </form>
            </div>
            <div class="panel glass-panel">
                <div class="panel-header"><span>Retsept Biriktirish</span></div>
                <form action="/retsept_qosh" method="POST">
                    <select name="tayyor_id" required>
                        <option value="">Tayyor mahsulot</option>
                        {% for m in items %}
                        <option value="{{ m[0] }}">{{ m[1] }}</option>
                        {% endfor %}
                    </select>
                    <select name="xomashyo_id" required>
                        <option value="">Sarflanadigan xomashyo</option>
                        {% for x in items %}
                        <option value="{{ x[0] }}">{{ x[1] }} ({{ x[4] }})</option>
                        {% endfor %}
                    </select>
                    <input type="number" step="any" name="sarf_miqdor" placeholder="1 dona uchun sarf" required>
                    <button type="submit" class="btn" style="width:100%;">Retseptni Saqlash</button>
                </form>
            </div>
        </div>
    </div>

    <!-- 6-BO'LIM: YANGI KIRITISH -->
    <div id="sec-s-action" class="tab-pane" style="display:none;">
        <div class="panel glass-panel" style="max-width:550px; margin:0 auto;">
            <div class="panel-header"><span>Yangi Mahsulot yoki Xomashyo</span></div>
            <form action="/add_item" method="POST">
                <input type="text" name="nomi" placeholder="Nomi" required>
                <select name="tur">
                    <option value="tayyor">Tayyor Mahsulot (sotiladigan)</option>
                    <option value="xomashyo">Xomashyo (sarflanadigan)</option>
                </select>
                <input type="number" step="any" name="miqdor" placeholder="Boshlang'ich qoldiq miqdori" required>
                <select name="birlik">
                    <option value="dona">dona</option>
                    <option value="kg">kg</option>
                    <option value="litr">litr</option>
                    <option value="quti">quti</option>
                </select>
                <input type="number" step="any" name="narx" placeholder="Tannarxi / Sotuv narxi (so'm)" required>
                <button type="submit" class="btn" style="width:100%;">Bazaga Saqlash</button>
            </form>
        </div>
    </div>

    <!-- 7-BO'LIM: REYTING & KPI (EKSKLYUZIV SHOHSUPA ANIMATSIYASI BILAN) -->
    <div id="sec-s-ratings" class="tab-pane" style="display:none;">
        <div class="panel glass-panel">
            <div class="panel-header">
                <span style="color:var(--accent-gold);">Top Mijozlar Shohsupasi (Podium)</span>
            </div>
            
            {% if top_mijozlar|length >= 3 %}
            <div class="podium-box">
                <!-- 2-O'rin -->
                <div class="podium-col podium-2">
                    <div class="podium-badge" style="background:#cbd5e1;">2</div>
                    <b style="font-size:13px;">{{ top_mijozlar[1][0] }}</b>
                    <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">{{ "{:,.0f}".format(top_mijozlar[1][1]) }}</div>
                </div>
                <!-- 1-O'rin (Oltin) -->
                <div class="podium-col podium-1">
                    <div class="podium-badge" style="background:var(--accent-gold);">1</div>
                    <b style="font-size:14px;">{{ top_mijozlar[0][0] }}</b>
                    <div style="font-size:12px; font-weight:800; color:var(--accent-gold); margin-top:4px;">{{ "{:,.0f}".format(top_mijozlar[0][1]) }}</div>
                </div>
                <!-- 3-O'rin (Bronza) -->
                <div class="podium-col podium-3">
                    <div class="podium-badge" style="background:#d97706; color:#fff;">3</div>
                    <b style="font-size:12px;">{{ top_mijozlar[2][0] }}</b>
                    <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">{{ "{:,.0f}".format(top_mijozlar[2][1]) }}</div>
                </div>
            </div>
            {% endif %}

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
                <div>
                    <h4 style="font-size:13px; margin-bottom:10px; color:var(--text-muted);">Mijozlar Reytingi (To'liq):</h4>
                    {% for c in top_mijozlar %}
                    <div class="data-row">
                        <span>{{ loop.index }}. <b>{{ c[0] }}</b></span>
                        <b style="color:var(--emerald);">{{ "{:,.0f}".format(c[1]) }} so'm</b>
                    </div>
                    {% endfor %}
                </div>
                <div>
                    <h4 style="font-size:13px; margin-bottom:10px; color:var(--text-muted);">Top Sotilgan Mahsulotlar:</h4>
                    {% for i in top_mahsulotlar %}
                    <div class="data-row">
                        <span>{{ loop.index }}. <b>{{ i[0] }}</b></span>
                        <b style="color:var(--primary);">{{ i[1] }} dona</b>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- 8-BO'LIM: XAVFSIZ O'CHIRISH BO'LIMI -->
    <div id="sec-s-purge" class="tab-pane" style="display:none;">
        <div class="panel glass-panel">
            <div class="panel-header">
                <span style="color:var(--danger);">Xavfsiz O'chirish Bo'limi</span>
                <span style="font-size:11px; color:var(--text-muted);">Xato kiritilgan ma'lumotlarni tozalash</span>
            </div>
            
            <h4 style="font-size:13px; margin:16px 0 8px 0; color:var(--text-muted);">Mahsulot va Xomashyolarni O'chirish:</h4>
            {% for item in items %}
            <div class="data-row">
                <span>{{ item[1] }} ({{ item[3] }} {{ item[4] }})</span>
                <a href="/delete/item/{{ item[0] }}" class="btn-danger" onclick="return confirm('Ushbu mahsulotni aniq o\'chirmoqchimisiz?');">O'chirish</a>
            </div>
            {% endfor %}

            <h4 style="font-size:13px; margin:20px 0 8px 0; color:var(--text-muted);">Mijozlarni O'chirish:</h4>
            {% for m in mijozlar %}
            <div class="data-row">
                <span>{{ m[1] }} ({{ m[2] }})</span>
                <a href="/delete/client/{{ m[0] }}" class="btn-danger" onclick="return confirm('Mijozni aniq o\'chirmoqchimisiz?');">O'chirish</a>
            </div>
            {% endfor %}

            <h4 style="font-size:13px; margin:20px 0 8px 0; color:var(--text-muted);">Sotuv Amallarini O'chirish:</h4>
            {% for s in sotuvlar %}
            <div class="data-row">
                <span>#{{ s[0] }} | Mijoz: {{ s[2] }} | Summa: {{ "{:,.0f}".format(s[5]) }}</span>
                <a href="/delete/sale/{{ s[0] }}" class="btn-danger" onclick="return confirm('Sotuv yozuvini aniq o\'chirmoqchimisiz?');">O'chirish</a>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        // Chap Menyuni ochish/yopish
        function toggleSidebar() {
            document.getElementById('sidebarDrawer').classList.toggle('active');
            document.getElementById('sidebarOverlay').classList.toggle('active');
        }

        // Chap Menyudan bo'limni tanlash
        function selectSection(tabId, title) {
            document.querySelectorAll('.tab-pane').forEach(el => el.style.display = 'none');
            document.getElementById('sec-' + tabId).style.display = 'block';

            document.querySelectorAll('.sidebar-item').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');

            document.getElementById('pageTitleText').innerText = title;
            toggleSidebar();

            // Reyting bo'limiga kirganda podium animatsiyasini yoqish
            if (tabId === 's-ratings') {
                gsap.to('.podium-col', {
                    y: 0,
                    opacity: 1,
                    duration: 0.6,
                    stagger: 0.15,
                    ease: "back.out(1.7)"
                });
            }
        }

        function autoFillPrice() {
            const select = document.getElementById('sale_item_select');
            const priceInput = document.getElementById('sale_price_input');
            if (select.selectedIndex > 0) {
                const price = select.options[select.selectedIndex].getAttribute('data-price');
                priceInput.value = price;
            }
        }

        const translations = {
            uz: {
                lblToday: "Bugungi Savdo", lblMonth: "Joriy Oy Savdosi", lblYear: "Yillik Savdo", lblQarz: "Umumiy Nasiya (Qarz)"
            },
            ru: {
                lblToday: "Продажи за Сегодня", lblMonth: "Продажи за Месяц", lblYear: "Годовой Оборот", lblQarz: "Общий Долг"
            },
            en: {
                lblToday: "Today's Sales", lblMonth: "Monthly Revenue", lblYear: "Annual Turnover", lblQarz: "Accounts Receivable"
            }
        };

        function setLang(lang) {
            document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            localStorage.setItem('omborim_app_lang', lang);

            const t = translations[lang] || translations['uz'];
            document.getElementById('lbl-today').innerText = t.lblToday;
            document.getElementById('lbl-month').innerText = t.lblMonth;
            document.getElementById('lbl-year').innerText = t.lblYear;
            document.getElementById('lbl-qarz').innerText = t.lblQarz;
        }

        window.onload = function() {
            const savedLang = localStorage.getItem('omborim_app_lang');
            if (savedLang) {
                const btn = Array.from(document.querySelectorAll('.lang-btn')).find(b => b.innerText.toLowerCase() === savedLang);
                if (btn) btn.click();
            }
        };
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, nomi, tur, miqdor, birlik, narx FROM items")
    items = c.fetchall()
    
    c.execute("""
        SELECT m.id, m.ism, m.telefon, m.manzil, 
               COALESCE(SUM(s.qarz_summa), 0) as jami_qarz
        FROM mijozlar m
        LEFT JOIN sotuvlar s ON m.id = s.mijoz_id
        GROUP BY m.id
        ORDER BY m.id DESC
    """)
    mijozlar = c.fetchall()
    
    c.execute("SELECT * FROM sotuvlar ORDER BY id DESC")
    sotuvlar = c.fetchall()
    
    bugun = datetime.now().strftime("%Y-%m-%d")
    joriy_oy = datetime.now().strftime("%Y-%m")
    joriy_yil = datetime.now().strftime("%Y")
    
    kunlik_savdo = sum(s[5] for s in sotuvlar if len(s) > 8 and s[8] == bugun)
    oylik_savdo = sum(s[5] for s in sotuvlar if len(s) > 9 and s[9] == joriy_oy)
    yillik_savdo = sum(s[5] for s in sotuvlar if len(s) > 10 and s[10] == joriy_yil)
    jami_qarz = sum(s[7] for s in sotuvlar)
    
    c.execute("""
        SELECT mijoz_nomi, SUM(jami_summa) as total_val, COUNT(id) as cnt
        FROM sotuvlar GROUP BY mijoz_nomi ORDER BY total_val DESC LIMIT 5
    """)
    top_mijozlar = c.fetchall()
    
    c.execute("""
        SELECT i.nomi, SUM(s.miqdor) as total_qty, SUM(s.jami_summa) as total_val
        FROM sotuvlar s JOIN items i ON s.tayyor_id = i.id
        GROUP BY s.tayyor_id ORDER BY total_qty DESC LIMIT 5
    """)
    top_mahsulotlar = c.fetchall()
    
    conn.close()
    return render_template_string(HTML_TEMPLATE, 
                                  items=items,
                                  mijozlar=mijozlar,
                                  kunlik_savdo=kunlik_savdo,
                                  oylik_savdo=oylik_savdo,
                                  yillik_savdo=yillik_savdo,
                                  jami_qarz=jami_qarz,
                                  sotuvlar=sotuvlar,
                                  bugun=bugun,
                                  joriy_oy=joriy_oy,
                                  joriy_yil=joriy_yil,
                                  top_mijozlar=top_mijozlar,
                                  top_mahsulotlar=top_mahsulotlar)

@app.route("/delete/item/<int:item_id>")
def delete_item(item_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/client/<int:client_id>")
def delete_client(client_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM mijozlar WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/sale/<int:sale_id>")
def delete_sale(sale_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM sotuvlar WHERE id = ?", (sale_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/add_client", methods=["POST"])
def add_client():
    ism = request.form.get("ism")
    telefon = request.form.get("telefon")
    manzil = request.form.get("manzil", "")
    izoh = request.form.get("izoh", "")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO mijozlar (ism, telefon, manzil, izoh) VALUES (?, ?, ?, ?)",
              (ism, telefon, manzil, izoh))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/sotish", methods=["POST"])
def sotish():
    mijoz_id = int(request.form.get("mijoz_id"))
    t_id = int(request.form.get("tayyor_id"))
    miqdor = float(request.form.get("miqdor", 0))
    narx = float(request.form.get("sotuv_narxi", 0))
    tolandi = float(request.form.get("tolangan_summa", 0))
    
    jami = miqdor * narx
    qarz = max(0, jami - tolandi)
    vaqt = datetime.now().strftime("%Y-%m-%d")
    oy = datetime.now().strftime("%Y-%m")
    yil = datetime.now().strftime("%Y")
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT ism FROM mijozlar WHERE id = ?", (mijoz_id,))
    mijoz_nomi = c.fetchone()[0]
    
    c.execute("UPDATE items SET miqdor = miqdor - ? WHERE id = ?", (miqdor, t_id))
    c.execute("""INSERT INTO sotuvlar 
                 (mijoz_id, mijoz_nomi, tayyor_id, miqdor, jami_summa, tolangan_summa, qarz_summa, sana, oy, yil) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (mijoz_id, mijoz_nomi, t_id, miqdor, jami, tolandi, qarz, vaqt, oy, yil))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/add_item", methods=["POST"])
def add_item():
    nomi = request.form.get("nomi")
    tur = request.form.get("tur")
    miqdor = float(request.form.get("miqdor", 0))
    birlik = request.form.get("birlik")
    narx = float(request.form.get("narx", 0))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO items (nomi, tur, miqdor, birlik, narx) VALUES (?, ?, ?, ?, ?)",
              (nomi, tur, miqdor, birlik, narx))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/retsept_qosh", methods=["POST"])
def retsept_qosh():
    tayyor_id = request.form.get("tayyor_id")
    xomashyo_id = request.form.get("xomashyo_id")
    sarf = float(request.form.get("sarf_miqdor", 0))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO retseptlar (tayyor_id, xomashyo_id, ketadigan_miqdor) VALUES (?, ?, ?)",
              (tayyor_id, xomashyo_id, sarf))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/ishlab_chiqarish", methods=["POST"])
def ishlab_chiqarish():
    tayyor_id = int(request.form.get("tayyor_id"))
    ishlab_miqdor = float(request.form.get("miqdor", 0))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT xomashyo_id, ketadigan_miqdor FROM retseptlar WHERE tayyor_id = ?", (tayyor_id,))
    retseptlar = c.fetchall()
    for r in retseptlar:
        c.execute("UPDATE items SET miqdor = miqdor - ? WHERE id = ?", (r[1] * ishlab_miqdor, r[0]))
    c.execute("UPDATE items SET miqdor = miqdor + ? WHERE id = ?", (ishlab_miqdor, tayyor_id))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/export/excel")
def export_excel():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, mijoz_nomi, miqdor, jami_summa, tolangan_summa, qarz_summa, sana FROM sotuvlar")
    rows = c.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Mijoz', 'Miqdor', 'Jami Summa (som)', 'Tolandi (som)', 'Qarz (som)', 'Sana'])
    for r in rows:
        writer.writerow(r)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=Omborim_Sotuvlar_{datetime.now().strftime('%Y_%m_%d')}.csv"}
    )

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
0

