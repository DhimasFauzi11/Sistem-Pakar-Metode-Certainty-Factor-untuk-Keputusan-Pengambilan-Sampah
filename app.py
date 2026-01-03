import streamlit as st
import joblib
import numpy as np
import requests
import pandas as pd
import random
import base64
import os
import time
import json
import streamlit.components.v1 as components
from datetime import datetime

# Import modul lokal
try:
    from expert_system import expert_system_config
    from fuzzy_functions import calculate_fuzzy_1_internal, calculate_fuzzy_2_external
except ImportError:
    expert_system_config = {'global_fusion_weights': {'cf_fuzzy_1_internal': 0.6, 'cf_fuzzy_2_external': 0.4}}
    def calculate_fuzzy_1_internal(lvl, gas, type): return 0.5
    def calculate_fuzzy_2_external(suhu, hum, event, loc, time): return 0.5

# Konfigurasi Warna Tema
THEME_GREEN = "#9DC209" 
LANDING_NEON = "#39FF14" 
THEME_RED = "#ff3131"
THEME_YELLOW = "#ffcc00"
THEME_BLUE = "#0088ff"

# Page Config & State
st.set_page_config(
    page_title="Smart Waste Monitoring",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="♻️"
)

# State Manajemen
if 'sim_b_an' not in st.session_state: st.session_state.sim_b_an = 65
if 'sim_b_org' not in st.session_state: st.session_state.sim_b_org = 55
if 'sim_c_an' not in st.session_state: st.session_state.sim_c_an = 20
if 'sim_c_org' not in st.session_state: st.session_state.sim_c_org = 15

if 'page' not in st.session_state: st.session_state.page = 'landing'
if 'selected_zone' not in st.session_state: st.session_state.selected_zone = None
if 'current_zone_id' not in st.session_state: st.session_state.current_zone_id = None

# --- STATE UNTUK DETEKSI OFFLINE ---
if 'last_data_snapshot' not in st.session_state: st.session_state.last_data_snapshot = ""
if 'last_update_time' not in st.session_state: st.session_state.last_update_time = time.time()

# History Buffer
if 'hist_time' not in st.session_state: st.session_state.hist_time = []
if 'hist_an' not in st.session_state: st.session_state.hist_an = []
if 'hist_org' not in st.session_state: st.session_state.hist_org = []
if 'hist_temp' not in st.session_state: st.session_state.hist_temp = []
if 'hist_hum' not in st.session_state: st.session_state.hist_hum = []
if 'hist_gas' not in st.session_state: st.session_state.hist_gas = []

if 'ai_buffer' not in st.session_state: st.session_state.ai_buffer = {}

# Load Resources & Data Functions
FIREBASE_URL = "https://pemilah-sampah-cb971-default-rtdb.asia-southeast1.firebasedatabase.app/.json"
HISTORY_URL = "https://pemilah-sampah-cb971-default-rtdb.asia-southeast1.firebasedatabase.app/riwayat_logs.json"

@st.cache_resource
def load_ml_model():
    try: return joblib.load('model_waste.pkl')
    except: return None

model_ml = load_ml_model()

def get_img_as_base64(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

# Background & CSS
img_base64 = get_img_as_base64("bg.jpg")
bg_style = ""
if img_base64:
    bg_style = f"""
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                    url("data:image/jpg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    """
else:
    bg_style = "background-color: #050505;"

st.markdown(f"""
    <style>
    @keyframes fadeInUp {{ from {{ opacity: 0; transform: translate3d(0, 20px, 0); }} to {{ opacity: 1; transform: translate3d(0, 0, 0); }} }}
    .block-container {{ animation: fadeInUp 0.8s both; padding-top: 1rem !important; }}
    header[data-testid="stHeader"] {{ background-color: transparent !important; z-index: 99; }}
    footer {{ display: none; }}
    .stApp {{ {bg_style} color: #FAFAFA; font-family: 'Segoe UI', sans-serif; }}
    
    section[data-testid="stSidebar"] {{ background-color: #111 !important; border-right: 1px solid #333; }}
    section[data-testid="stSidebar"] * {{ color: #e0e0e0 !important; }}
    
    [data-testid="stSidebarCollapsedControl"] {{ color: white !important; background-color: rgba(0,0,0,0.5); border-radius: 5px; margin-top: 10px; margin-left: 10px; transition: transform 0.2s; }}
    [data-testid="stSidebarCollapsedControl"]:hover {{ transform: scale(1.1); color: {THEME_GREEN} !important; }}
    
    div[data-baseweb="slider"] div[role="slider"] {{ background-color: {THEME_GREEN} !important; box-shadow: 0 0 10px {THEME_GREEN} !important; transition: transform 0.2s; }}
    div[data-baseweb="slider"] div[role="slider"]:hover {{ transform: scale(1.3); cursor: grab; }}
    div[data-baseweb="slider"] > div > div {{ background-color: #ffffff !important; }}
    div[data-baseweb="slider"] > div > div > div:last-child {{ background-color: {THEME_GREEN} !important; }}
    div[data-testid="stSliderTickBar"] {{ color: #ffffff !important; }}
    
    /* FONT METRIC */
    [data-testid="stMetricLabel"] {{ color: #FFFFFF !important; font-size: 1rem !important; opacity: 1 !important; }}
    [data-testid="stMetricLabel"] > div, [data-testid="stMetricLabel"] > label, [data-testid="stMetricLabel"] p {{
        color: #FFFFFF !important; font-weight: 600 !important; opacity: 1 !important;
    }}
    [data-testid="stMetricValue"] {{ color: #FFFFFF !important; text-shadow: 0px 2px 4px rgba(0,0,0,0.9); }}
    
    /* STATUS INDIKATOR */
    .status-badge {{
        display: flex; justify-content: center; align-items: center;
        background-color: rgba(0, 0, 0, 0.6); padding: 10px 20px;
        border-radius: 30px; border: 1px solid #333;
        width: fit-content; margin: 0 auto 20px auto;
        backdrop-filter: blur(5px);
    }}
    .status-dot {{
        height: 12px; width: 12px; border-radius: 50%;
        display: inline-block; margin-right: 10px;
    }}
    .dot-online {{
        background-color: {LANDING_NEON};
        box-shadow: 0 0 15px {LANDING_NEON};
        animation: pulse 2s infinite;
    }}
    .dot-offline {{
        background-color: {THEME_RED};
        box-shadow: 0 0 15px {THEME_RED};
    }}
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(57, 255, 20, 0.7); }}
        70% {{ box-shadow: 0 0 0 10px rgba(57, 255, 20, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(57, 255, 20, 0); }}
    }}
    .status-text {{ color: white; font-weight: bold; letter-spacing: 1px; font-size: 0.9rem; }}

    .neon-card {{ background-color: rgba(20, 20, 20, 0.85); padding: 20px; border-radius: 15px; margin-bottom: 10px; text-align: center; backdrop-filter: blur(8px); border: 1px solid #333; transition: transform 0.3s ease, box-shadow 0.3s ease; }}
    .neon-card:hover {{ transform: translateY(-5px) scale(1.02); z-index: 10; cursor: pointer; }}
    
    .glow-green {{ border: 2px solid {LANDING_NEON}; box-shadow: 0 0 25px {LANDING_NEON}80; }}
    .glow-green:hover {{ box-shadow: 0 0 50px {LANDING_NEON}; }}
    .status-safe {{ color: {LANDING_NEON}; text-shadow: 0 0 8px {LANDING_NEON}; }} 
    
    .glow-red {{ border: 2px solid {THEME_RED}; box-shadow: 0 0 15px {THEME_RED}66; }}
    .glow-red:hover {{ box-shadow: 0 0 40px {THEME_RED}; }}
    .status-danger {{ color: {THEME_RED}; }} 
    
    .glow-yellow {{ border: 2px solid {THEME_YELLOW}; box-shadow: 0 0 15px {THEME_YELLOW}66; }}
    .glow-yellow:hover {{ box-shadow: 0 0 40px {THEME_YELLOW}; }}
    .status-warning {{ color: {THEME_YELLOW}; }}
    
    .card-title {{ font-size: 1.5rem; font-weight: bold; color: white; margin-bottom: 5px; }}

    div.stButton > button {{ background-color: rgba(20, 20, 20, 0.9) !important; color: {THEME_GREEN} !important; border: 1px solid {THEME_GREEN} !important; width: 100%; border-radius: 8px; padding: 10px; font-weight: bold; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); }}
    div.stButton > button:hover {{ border-color: {THEME_GREEN} !important; background-color: {THEME_GREEN} !important; color: black !important; box-shadow: 0 0 25px {THEME_GREEN}; transform: translateY(-2px); }}
    div.stButton > button:active {{ transform: translateY(1px); }}
    
    .neon-box-detail {{ background: #0f0f0f; border-left: 5px solid #333; padding: 15px; margin-top: 15px; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.5); transition: transform 0.3s ease, box-shadow 0.3s ease; }}
    .neon-box-detail:hover {{ transform: translateX(5px); box-shadow: -5px 5px 15px rgba(0,0,0,0.7); }}
    
    .nb-green {{ border-color: {THEME_GREEN}; }} 
    .nb-red {{ border-color: {THEME_RED}; }} 
    .nb-yellow {{ border-color: {THEME_YELLOW}; }}
    </style>
    """, unsafe_allow_html=True)

# Logic & Data
def get_real_data():
    try:
        response = requests.get(FIREBASE_URL, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                if 'Monitoring' in data: return data['Monitoring']
                if 'monitoring' in data: return data['monitoring']
                if 'kapasitas_anorganik' in data: return data
                for k, v in data.items():
                    if isinstance(v, dict) and 'kapasitas_anorganik' in v: return v
            return None
    except: return None

# Fetch History (Robust - Hybrid Logic)
def fetch_history_logs():
    try:
        response = requests.get(HISTORY_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if not data: return None
            
            if isinstance(data, dict):
                data_list = list(data.values())
            else:
                data_list = data 

            df = pd.DataFrame(data_list)
            if df.empty: return None

            df.columns = df.columns.str.lower()
            
            time_cols = [c for c in df.columns if any(x in c for x in ['time', 'date', 'waktu', 'timestamp'])]
            
            use_real_time = False
            if time_cols:
                time_col = time_cols[0]
                df['valid_time'] = pd.to_datetime(df[time_col], errors='coerce')
                
                if df['valid_time'].isna().sum() < (len(df) * 0.5):
                    use_real_time = True
                    df = df.dropna(subset=['valid_time']) 
                    df = df.set_index('valid_time').sort_index()
            
            target_cols = ['kapasitas_anorganik', 'kapasitas_organik', 'suhu', 'kelembapan', 'gas_level', 'gas']
            available_cols = [c for c in target_cols if c in df.columns]
            
            if not available_cols: return None

            for col in available_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df_final = df[available_cols].dropna(how='all')

            if use_real_time:
                try:
                    duration = (df_final.index.max() - df_final.index.min()).total_seconds()
                    if duration > 3600:
                        df_final = df_final.resample('H').mean()
                    else:
                        df_final = df_final.tail(50)
                except:
                    df_final = df_final.tail(50)
            else:
                df_final = df_final.reset_index(drop=True)
                df_final.index.name = 'Urutan Data'
                df_final = df_final.tail(50) 

            rename_map = {
                'kapasitas_anorganik': 'Anorganik', 
                'kapasitas_organik': 'Organik',
                'suhu': 'Suhu',
                'kelembapan': 'Kelembapan',
                'gas_level': 'Gas',
                'gas': 'Gas'
            }
            df_final = df_final.rename(columns=rename_map)
            
            return df_final
    except Exception:
        return None
    return None

def get_zone_data(zone_id):
    if zone_id == 'Z-A':
        return get_real_data() or {'kapasitas_anorganik': 0, 'kapasitas_organik': 0, 'suhu': 0, 'kelembapan': 0, 'gas_level': 0}
    elif zone_id == 'Z-B':
        return {'kapasitas_anorganik': st.session_state.sim_b_an, 'kapasitas_organik': st.session_state.sim_b_org, 'gas_level': 30, 'suhu': 31.5, 'kelembapan': 70}
    elif zone_id == 'Z-C':
        return {'kapasitas_anorganik': st.session_state.sim_c_an, 'kapasitas_organik': st.session_state.sim_c_org, 'gas_level': 20, 'suhu': 28.0, 'kelembapan': 60}
    return {}

def get_smart_prediction(zone_id, waste_type, level, is_simulation=False):
    ratio = level / 100.0
    days_by_volume = 7.0 * (1.0 - ratio)
    ml_days = days_by_volume 
    if model_ml:
        try:
            pred = model_ml.predict(np.array([[level, 5, 0, 0]]))[0]
            ml_days = float(pred)
        except: pass
    final_score = (days_by_volume * 0.5) + (ml_days * 0.5)
    if level >= 90: final_score = 0
    elif level <= 5: final_score = 7
    elif final_score > 7: final_score = 7 
    elif final_score < 0: final_score = 0 
    
    if not is_simulation:
        key = f"{zone_id}_{waste_type}"
        if key not in st.session_state.ai_buffer: st.session_state.ai_buffer[key] = []
        buffer = st.session_state.ai_buffer[key]
        buffer.append(final_score)
        if len(buffer) > 5: buffer.pop(0)
        avg_val = sum(buffer) / len(buffer)
        return int(round(avg_val))
    return int(round(final_score))

def analyze_system(zone_id, data, event_bool, lokasi_input):
    anorganik = float(data.get('kapasitas_anorganik', 0))
    organik = float(data.get('kapasitas_organik', 0))
    suhu = float(data.get('suhu', 0))
    lembab = float(data.get('kelembapan', 0))
    gas = float(data.get('gas_level', 0))
    
    res = {'an': {'lvl': anorganik}, 'org': {'lvl': organik}, 'env': {'s': suhu, 'l': lembab, 'g': gas}, 'alert': False}
    is_sim = zone_id in ['Z-B', 'Z-C']
    
    for jenis in ['an', 'org']:
        lvl = res[jenis]['lvl']
        key_jenis = 'anorganik' if jenis == 'an' else 'organik'
        days = get_smart_prediction(zone_id, key_jenis, lvl, is_simulation=is_sim)
        ai_txt = f"{days} Hari"
            
        status = "AMAN"; color = "green"; action = "STANDBY"; cf_val = 0.0
        try:
            score_int = calculate_fuzzy_1_internal(lvl, gas, key_jenis) 
            score_ext = calculate_fuzzy_2_external(suhu, lembab, event_bool, lokasi_input.lower(), 10) 
            w = expert_system_config['global_fusion_weights']
            cf = ((score_int * w['cf_fuzzy_1_internal']) + (score_ext * w['cf_fuzzy_2_external'])) / (w['cf_fuzzy_1_internal'] + w['cf_fuzzy_2_external'])
            cf_val = cf 

            if lvl > 90:
                status="PENUH MUTLAK"; color="red"; action="ANGKUT SEKARANG"; res['alert']=True
            elif cf >= 0.70:
                status="URGENT"; color="red"; action="JADWALKAN ANGKUT"; res['alert']=True
            elif cf >= 0.45:
                status="WASPADA"; color="yellow"; action="PANTAU DULU"
            else:
                status="AMAN"; color="green"; action="STANDBY"
        except: pass
        res[jenis].update({'ai': ai_txt, 'st': status, 'col': color, 'act': action, 'cf': f"{cf_val:.2f}"})
    return res

# Landing Page
def show_landing():
    st.markdown("<h1 style='text-align: center; color: white; font-size: 3rem; margin-top: 20px; text-shadow: 0 0 15px rgba(0,0,0,0.8);'>SMART WASTE MONITORING</h1>", unsafe_allow_html=True)
    
    components.html("""
        <div style="text-align: center; font-family: 'Segoe UI', sans-serif; color: #ffffff; font-size: 1.2em; font-weight: 500; text-shadow: 0 0 5px rgba(0,0,0,0.5);">
            <span id="clock"></span>
        </div>
        <script>
            function updateTime() {
                const now = new Date();
                const d = now.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
                const t = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                document.getElementById('clock').innerHTML = d + ' | ' + t + ' WIB';
            }
            setInterval(updateTime, 1000); updateTime();
        </script>
        """, height=50)

    st.write("") 
    
    if hasattr(st, "fragment"):
        @st.fragment(run_every=2)
        def render_cards(): _render_landing_cards_logic()
        render_cards()
    else:
        _render_landing_cards_logic()
        time.sleep(2)
        st.rerun()

def _render_landing_cards_logic():
    # --- LOGIKA BARU: DETEKSI PERUBAHAN DATA (10 DETIK) ---
    real_data = get_real_data()
    
    # 1. Ambil snapshot data saat ini (Ubah jadi string agar bisa dibandingkan)
    current_snapshot = json.dumps(real_data, sort_keys=True) if real_data else "None"
    
    # 2. Bandingkan dengan snapshot sebelumnya
    if current_snapshot != st.session_state.last_data_snapshot:
        # Jika BERBEDA (ada update dari alat), reset timer & simpan snapshot baru
        st.session_state.last_data_snapshot = current_snapshot
        st.session_state.last_update_time = time.time()
    
    # 3. Hitung selisih waktu dari terakhir kali data berubah
    seconds_since_change = time.time() - st.session_state.last_update_time
    
    # 4. Tentukan status (Jika diam > 10 detik = OFFLINE)
    is_online = seconds_since_change <= 10
    
    if is_online:
        status_html = f"""
        <div class="status-badge">
            <span class="status-dot dot-online"></span>
            <span class="status-text">SISTEM ONLINE</span>
        </div>
        """
    else:
        status_html = f"""
        <div class="status-badge">
            <span class="status-dot dot-offline"></span>
            <span class="status-text" style="color:#ff3131">SISTEM OFFLINE</span>
        </div>
        """
    st.markdown(status_html, unsafe_allow_html=True)
    # ----------------------------------------------------

    zones = [
        {'id': 'Z-A', 'label': 'ZONA A', 'loc_desc': 'Parkiran (IoT Real-time)', 'data': get_zone_data('Z-A')},
        {'id': 'Z-B', 'label': 'ZONA B', 'loc_desc': 'Area Masjid (Simulasi)', 'data': get_zone_data('Z-B')}, 
        {'id': 'Z-C', 'label': 'ZONA C', 'loc_desc': 'Area Kantin (Simulasi)', 'data': get_zone_data('Z-C')}
    ]
    cols = st.columns(3)
    for idx, z in enumerate(zones):
        with cols[idx]:
            an = z['data'].get('kapasitas_anorganik', 0)
            org = z['data'].get('kapasitas_organik', 0)
            status_display = "AMAN"; css_class = "glow-green"; text_class = "status-safe"
            
            if an > 80 or org > 80:
                status_display = "PERLU ANGKUT"; css_class = "glow-red"; text_class = "status-danger"
            elif z['id'] == 'Z-B': 
                status_display = "WASPADA"; css_class = "glow-yellow"; text_class = "status-warning"
            elif an > 50 or org > 50:
                status_display = "PANTAU"; css_class = "glow-yellow"; text_class = "status-warning"
            
            html_card = f"""<div class="neon-card {css_class}">
                <div class="card-title">{z['label']}</div>
                <div style="color: #ccc; font-size: 0.9em; margin-bottom: 15px;">{z['loc_desc']}</div>
                <div class="card-status {text_class}">{status_display}</div>
                <div style="display: flex; justify-content: space-around; color: white; font-weight:bold; margin-bottom: 15px;">
                <div>🟦 {an}%</div> <div>🟩 {org}%</div>
                </div>
            </div>"""
            st.markdown(html_card, unsafe_allow_html=True)
            
            if st.button(f"Lihat Detail {z['label']}", key=f"btn_{z['id']}"):
                st.session_state.selected_zone = z
                st.session_state.page = 'detail'
                st.session_state.hist_time = []; st.session_state.hist_an = []; st.session_state.hist_org = []
                st.session_state.hist_temp = []; st.session_state.hist_hum = []; st.session_state.hist_gas = []
                st.session_state.current_zone_id = z['id']
                st.rerun()

# Detail Page
def show_detail():
    z_info = st.session_state.selected_zone
    if not z_info: st.session_state.page = 'landing'; st.rerun()
    zid = z_info['id']
    
    with st.sidebar:
        st.header("⚙️ Control Panel")
        if zid in ['Z-B', 'Z-C']:
            st.info(f"**MODE SIMULASI ({zid})**")
            st.slider("Kapasitas Anorganik (%)", 0, 100, key=f'sim_{zid[-1].lower()}_an')
            st.slider("Kapasitas Organik (%)", 0, 100, key=f'sim_{zid[-1].lower()}_org')
        else:
            st.success("**MODE IOT LIVE**\nData realtime dari sensor.")
            st.caption("Data diperbarui setiap 2 detik.")
        
        st.divider()
        st.subheader("Parameter Pakar")
        event_opt = st.selectbox("Event Keramaian?", ["Tidak", "Ada"])
        lokasi_opt = st.selectbox("Lokasi Tong?", ["Biasa", "Strategis"])
        event_bool = True if event_opt == "Ada" else False
        
        st.divider()
        if st.button("KEMBALI KE MENU UTAMA"):
            st.session_state.page = 'landing'
            st.rerun()

    now = datetime.now()
    jam_str = now.strftime('%H:%M:%S')
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title(f"{z_info['label']} - {z_info['loc_desc']}")
        st.caption(f"ID: {z_info['id']} | Dashboard Monitoring Terpadu")
    with c2:
        components.html(f"""
        <div style="text-align: right; font-family: 'Segoe UI', sans-serif; color: {THEME_GREEN};">
            <div id="date_detail" style="font-size: 0.75rem; font-weight: 500; opacity: 0.9;"></div>
            <div id="clock_detail" style="font-size: 1.1rem; font-weight: bold; text-shadow: 0 0 5px {THEME_GREEN}99;"></div>
        </div>
        <script>
            function updateTime() {{
                const now = new Date();
                document.getElementById('date_detail').innerHTML = now.toLocaleDateString('id-ID', {{ weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }});
                document.getElementById('clock_detail').innerHTML = now.toLocaleTimeString('id-ID', {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }}) + ' WIB';
            }}
            setInterval(updateTime, 1000); updateTime();
        </script>
        """, height=60)
    st.markdown("---")
    
    if hasattr(st, "fragment"):
        @st.fragment(run_every=2)
        def render_detail_content(): _render_detail_logic(zid, event_bool, lokasi_opt, jam_str)
        render_detail_content()
    else:
        _render_detail_logic(zid, event_bool, lokasi_opt, jam_str)
        time.sleep(2)
        st.rerun()

def _render_detail_logic(zid, event_bool, lokasi_opt, jam_str):
    current_data = get_zone_data(zid)
    res = analyze_system(zid, current_data, event_bool, lokasi_opt)
    
    # Update Session State Buffer (Berlaku untuk SEMUA Zona)
    if not st.session_state.hist_time or st.session_state.hist_time[-1] != jam_str:
        st.session_state.hist_time.append(jam_str)
        st.session_state.hist_an.append(res['an']['lvl'])
        st.session_state.hist_org.append(res['org']['lvl'])
        st.session_state.hist_temp.append(res['env']['s'])
        st.session_state.hist_hum.append(res['env']['l'])
        st.session_state.hist_gas.append(res['env']['g'])

        if len(st.session_state.hist_time) > 50: 
            st.session_state.hist_time.pop(0)
            st.session_state.hist_an.pop(0); st.session_state.hist_org.pop(0)
            st.session_state.hist_temp.pop(0); st.session_state.hist_hum.pop(0); st.session_state.hist_gas.pop(0)

    col1, col2, col3 = st.columns(3)
    def get_colors(code): return ('nb-red', THEME_RED) if code == 'red' else (('nb-yellow', THEME_YELLOW) if code == 'yellow' else ('nb-green', THEME_GREEN))

    with col1:
        st.markdown("### 🟦 Anorganik")
        st.metric("Level Kapasitas", f"{res['an']['lvl']}%")
        st.progress(min(res['an']['lvl']/100, 1.0))
        css, txt_col = get_colors(res['an']['col'])
        st.markdown(f"""<div class="neon-box-detail {css}">
            <div style="color:#bbb; font-size:0.8rem;">🤖 PREDIKSI PENUH</div>
            <div style="color:white; font-weight:bold; font-size:1.5rem;">{res['an']['ai']}</div>
            <hr style="border-color:#333; margin:10px 0;">
            <div style="color:#bbb; font-size:0.8rem;">🧠 SISTEM PAKAR</div>
            <div style="color:{txt_col}; font-weight:bold; font-size:1.2rem;">{res['an']['act']}</div>
            <div style="font-size:0.85rem; margin-top:5px; color:#ddd;">CF: <b>{res['an']['cf']}</b> | Status: {res['an']['st']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("### 🟩 Organik")
        st.metric("Level Kapasitas", f"{res['org']['lvl']}%")
        st.progress(min(res['org']['lvl']/100, 1.0))
        css, txt_col = get_colors(res['org']['col'])
        st.markdown(f"""<div class="neon-box-detail {css}">
            <div style="color:#bbb; font-size:0.8rem;">🤖 PREDIKSI PENUH</div>
            <div style="color:white; font-weight:bold; font-size:1.5rem;">{res['org']['ai']}</div>
            <hr style="border-color:#333; margin:10px 0;">
            <div style="color:#bbb; font-size:0.8rem;">🧠 SISTEM PAKAR</div>
            <div style="color:{txt_col}; font-weight:bold; font-size:1.2rem;">{res['org']['act']}</div>
            <div style="font-size:0.85rem; margin-top:5px; color:#ddd;">CF: <b>{res['org']['cf']}</b> | Status: {res['org']['st']}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown("### 🌡️ Lingkungan")
        c_a, c_b = st.columns(2)
        c_a.metric("Suhu", f"{res['env']['s']}°C")
        c_b.metric("Lembab", f"{res['env']['l']}%")
        st.metric("Gas (Bau)", f"{res['env']['g']} ppm")
        if res['env']['g'] > 200:
            st.markdown(f"<div style='background:{THEME_RED}; color:white; padding:15px; border-radius:8px; text-align:center; font-weight:bold;'>⚠️ BAU MENYENGAT</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:{THEME_GREEN}; color:black; padding:15px; border-radius:8px; text-align:center; font-weight:bold;'>✅ UDARA NORMAL</div>", unsafe_allow_html=True)

    st.write("")
    st.subheader("📈 Visualisasi Data")
    
    df_chart = pd.DataFrame()
    chart_source = ""
    
    if zid == 'Z-A':
        df_hist = fetch_history_logs()
        
        if df_hist is not None and not df_hist.empty:
            df_chart = df_hist
            chart_source = "server"
        else:
            if len(st.session_state.hist_time) > 1:
                df_chart = pd.DataFrame({
                    'Waktu': st.session_state.hist_time,
                    'Anorganik': st.session_state.hist_an,
                    'Organik': st.session_state.hist_org,
                    'Suhu': st.session_state.hist_temp,
                    'Kelembapan': st.session_state.hist_hum,
                    'Gas': st.session_state.hist_gas
                })
                df_chart = df_chart.set_index('Waktu')
                chart_source = "fallback"
                
                if not st.session_state.hist_time or st.session_state.hist_time[-1] != jam_str:
                    st.session_state.hist_time.append(jam_str)
                    st.session_state.hist_an.append(res['an']['lvl'])
                    st.session_state.hist_org.append(res['org']['lvl'])
                    st.session_state.hist_temp.append(res['env']['s'])
                    st.session_state.hist_hum.append(res['env']['l'])
                    st.session_state.hist_gas.append(res['env']['g'])
                    if len(st.session_state.hist_time) > 50: 
                        st.session_state.hist_time.pop(0); st.session_state.hist_an.pop(0); st.session_state.hist_org.pop(0)
                        st.session_state.hist_temp.pop(0); st.session_state.hist_hum.pop(0); st.session_state.hist_gas.pop(0)

    else:
        if len(st.session_state.hist_time) > 1:
            df_chart = pd.DataFrame({
                'Waktu': st.session_state.hist_time,
                'Anorganik': st.session_state.hist_an,
                'Organik': st.session_state.hist_org,
                'Suhu': st.session_state.hist_temp,
                'Kelembapan': st.session_state.hist_hum,
                'Gas': st.session_state.hist_gas
            })
            df_chart = df_chart.set_index('Waktu')
            chart_source = "simulasi"

    if not df_chart.empty:
        tab1, tab2, tab3 = st.tabs(["Kapasitas Sampah", "Suhu & Lembab", "Level Gas"])
        
        with tab1:
            cols_cap = ['Anorganik', 'Organik']
            if all(col in df_chart.columns for col in cols_cap):
                st.line_chart(df_chart[cols_cap], color=[THEME_BLUE, THEME_GREEN])
            else: st.warning("Data kapasitas belum tersedia.")
            
        with tab2:
            cols_env = ['Suhu', 'Kelembapan']
            if all(col in df_chart.columns for col in cols_env):
                st.line_chart(df_chart[cols_env], color=[THEME_RED, THEME_BLUE])
            else: st.warning("Data suhu/lembab belum tersedia.")

        with tab3:
            if 'Gas' in df_chart.columns:
                st.line_chart(df_chart[['Gas']], color=[THEME_YELLOW])
            else: st.warning("Data gas belum tersedia.")

        if chart_source == "server":
            st.caption("Grafik dari riwayat server (Log History).")
        elif chart_source == "fallback":
            st.caption("⚠️ Timestamp di server rusak/tidak valid. Menampilkan grafik urutan data masuk (Live).")
        else:
            st.caption("Grafik berdasarkan simulasi realtime (session state).")
    else:
        if zid == 'Z-A':
            st.warning("Belum ada data riwayat yang valid untuk ditampilkan.")
        else:
            st.info("Menunggu data masuk untuk menampilkan grafik...")

# Router
if st.session_state.page == 'landing':
    show_landing()
elif st.session_state.page == 'detail':
    show_detail()