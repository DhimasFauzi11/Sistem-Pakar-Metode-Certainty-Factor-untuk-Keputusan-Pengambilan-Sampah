import streamlit as st
import joblib
import numpy as np
import requests
import pandas as pd
import random
import base64
import os
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

# ==========================================
# KONFIGURASI WARNA TEMA
# ==========================================
THEME_GREEN = "#9DC209" # Hijau Lime (Detail, Grafik, Slider Fill)
LANDING_NEON = "#39FF14" # Hijau Neon (Landing Page Glow)
THEME_RED = "#ff3131"
THEME_YELLOW = "#ffcc00"
THEME_BLUE = "#0088ff"

# ==========================================
# 1. PAGE CONFIG & STATE
# ==========================================
st.set_page_config(
    page_title="Smart Waste Monitoring",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="♻️"
)

# --- STATE MANAJEMEN ---
if 'sim_b_an' not in st.session_state: st.session_state.sim_b_an = 65
if 'sim_b_org' not in st.session_state: st.session_state.sim_b_org = 55
if 'sim_c_an' not in st.session_state: st.session_state.sim_c_an = 20
if 'sim_c_org' not in st.session_state: st.session_state.sim_c_org = 15

if 'page' not in st.session_state: st.session_state.page = 'landing'
if 'selected_zone' not in st.session_state: st.session_state.selected_zone = None
if 'current_zone_id' not in st.session_state: st.session_state.current_zone_id = None
if 'hist_time' not in st.session_state: st.session_state.hist_time = []
if 'hist_an' not in st.session_state: st.session_state.hist_an = []
if 'hist_org' not in st.session_state: st.session_state.hist_org = []

# Buffer Smoothing untuk AI
if 'ai_buffer' not in st.session_state: st.session_state.ai_buffer = {}

# ==========================================
# 2. LOAD RESOURCES & DATA FUNCTIONS
# ==========================================
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

# --- BACKGROUND & CSS ANIMATION ---
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
    /* 1. ANIMASI FADE IN HALAMAN */
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translate3d(0, 20px, 0); }}
        to {{ opacity: 1; transform: translate3d(0, 0, 0); }}
    }}

    .block-container {{
        animation-duration: 0.8s;
        animation-fill-mode: both;
        animation-name: fadeInUp;
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }}
    
    header[data-testid="stHeader"] {{ background-color: transparent !important; z-index: 99; }}
    footer {{ display: none; }}
    .stApp {{ {bg_style} color: #FAFAFA; font-family: 'Segoe UI', sans-serif; }}
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {{ background-color: #111 !important; border-right: 1px solid #333; }}
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{ color: #e0e0e0 !important; }}
    
    [data-testid="stSidebarCollapsedControl"] {{
        color: white !important; background-color: rgba(0,0,0,0.5);
        border-radius: 5px; margin-top: 10px; margin-left: 10px;
        transition: transform 0.2s;
    }}
    [data-testid="stSidebarCollapsedControl"]:hover {{ transform: scale(1.1); color: {THEME_GREEN} !important; }}
    
    /* SLIDER FIX */
    div[data-baseweb="slider"] div[role="slider"] {{ 
        background-color: {THEME_GREEN} !important; 
        box-shadow: 0 0 10px {THEME_GREEN} !important;
        transition: transform 0.2s;
    }}
    div[data-baseweb="slider"] div[role="slider"]:hover {{ transform: scale(1.3); cursor: grab; }}
    div[data-baseweb="slider"] > div > div {{ background-color: #ffffff !important; }}
    div[data-baseweb="slider"] > div > div > div:last-child {{ background-color: {THEME_GREEN} !important; }}
    div[data-testid="stSliderTickBar"] {{ color: #ffffff !important; }}

    /* FONT METRICS */
    div[data-testid="stMetricValue"] {{ color: #FFFFFF !important; text-shadow: 0px 2px 4px rgba(0,0,0,0.9); }}
    label[data-testid="stMetricLabel"] {{ color: #FFFFFF !important; opacity: 1 !important; font-weight: bold; text-shadow: 0px 1px 3px rgba(0,0,0,0.9); }}
    
    /* CARDS & HOVER EFFECT */
    .neon-card {{
        background-color: rgba(20, 20, 20, 0.85); padding: 20px; border-radius: 15px;
        margin-bottom: 10px; text-align: center; backdrop-filter: blur(8px); border: 1px solid #333;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .neon-card:hover {{
        transform: translateY(-5px) scale(1.02);
        z-index: 10; cursor: pointer;
    }}
    
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

    /* BUTTONS */
    div.stButton > button {{
        background-color: rgba(20, 20, 20, 0.9) !important; color: {THEME_GREEN} !important; 
        border: 1px solid {THEME_GREEN} !important; width: 100%; border-radius: 8px; padding: 10px; font-weight: bold;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }}
    div.stButton > button:hover {{ 
        border-color: {THEME_GREEN} !important; background-color: {THEME_GREEN} !important; 
        color: black !important; box-shadow: 0 0 25px {THEME_GREEN}; transform: translateY(-2px);
    }}
    div.stButton > button:active {{ transform: translateY(1px); }}
    
    /* DETAIL BOXES */
    .neon-box-detail {{
        background: #0f0f0f; border-left: 5px solid #333; padding: 15px; margin-top: 15px;
        border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .neon-box-detail:hover {{ transform: translateX(5px); box-shadow: -5px 5px 15px rgba(0,0,0,0.7); }}
    
    .nb-green {{ border-color: {THEME_GREEN}; }} 
    .nb-red {{ border-color: {THEME_RED}; }} 
    .nb-yellow {{ border-color: {THEME_YELLOW}; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. LOGIC & DATA
# ==========================================
def get_real_data():
    try:
        response = requests.get(FIREBASE_URL)
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

# --- FUNGSI RIWAYAT KHUSUS ZONA A ---
def fetch_history_logs():
    """Mengambil riwayat_logs, convert ke DataFrame, resample per jam"""
    try:
        response = requests.get(HISTORY_URL)
        if response.status_code == 200:
            data = response.json()
            if not data: return None
            
            # Handling format dict/list dari Firebase
            if isinstance(data, dict):
                data_list = list(data.values())
            else:
                data_list = data 

            df = pd.DataFrame(data_list)
            
            # Mencari kolom waktu
            time_col = None
            possible_names = ['timestamp', 'waktu', 'time', 'date', 'Timestamp']
            for name in possible_names:
                if name in df.columns:
                    time_col = name
                    break
            
            if not time_col: return None 

            # Pre-processing
            df[time_col] = pd.to_datetime(df[time_col])
            
            numeric_cols = []
            if 'kapasitas_anorganik' in df.columns: numeric_cols.append('kapasitas_anorganik')
            if 'kapasitas_organik' in df.columns: numeric_cols.append('kapasitas_organik')
            
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Resample Per Jam
            df = df.set_index(time_col).sort_index()
            df_hourly = df[numeric_cols].resample('H').mean()
            df_hourly = df_hourly.dropna(how='all') # Hapus jam kosong
            
            # Rename untuk grafik
            df_hourly = df_hourly.rename(columns={
                'kapasitas_anorganik': 'Anorganik', 
                'kapasitas_organik': 'Organik'
            })
            
            return df_hourly
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

# --- SMART AI PREDICTION ---
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

# ==========================================
# 4. LANDING PAGE
# ==========================================
def show_landing():
    st.markdown("<h1 style='text-align: center; color: white; font-size: 3rem; margin-top: 20px; text-shadow: 0 0 15px rgba(0,0,0,0.8);'>SMART WASTE MONITORING</h1>", unsafe_allow_html=True)
    
    components.html("""
        <div style="text-align: center; font-family: 'Segoe UI', sans-serif; color: #ffffff; font-size: 1.2em; font-weight: 500; text-shadow: 0 0 5px rgba(0,0,0,0.5);">
            <span id="clock"></span>
        </div>
        <script>
            function updateTime() {
                const now = new Date();
                const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
                const datePart = now.toLocaleDateString('id-ID', options);
                const timePart = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                document.getElementById('clock').innerHTML = datePart + ' | ' + timePart + ' WIB';
            }
            setInterval(updateTime, 1000);
            updateTime();
        </script>
        """, height=50)

    st.write("") 
    
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
            elif an > 50 or org > 50:
                status_display = "PANTAU"; css_class = "glow-yellow"; text_class = "status-warning"
            
            html_card = f"""<div class="neon-card {css_class}">
<div class="card-title">{z['label']}</div>
<div style="color: #ccc; font-size: 0.9em; margin-bottom: 15px;">{z['loc_desc']}</div>
<div class="card-status {text_class}">{status_display}</div>
<div style="display: flex; justify-content: space-around; color: white; font-weight:bold; margin-bottom: 15px;">
<div>🟦 {an}%</div>
<div>🟩 {org}%</div>
</div>
</div>"""
            st.markdown(html_card, unsafe_allow_html=True)
            
            if st.button(f"Lihat Detail {z['label']}", key=z['id']):
                st.session_state.selected_zone = z
                st.session_state.page = 'detail'
                # Reset history untuk B/C, tapi A akan fetch dari server
                st.session_state.hist_time = []; st.session_state.hist_an = []; st.session_state.hist_org = []
                st.session_state.current_zone_id = z['id']
                st.rerun()

# ==========================================
# 5. DETAIL PAGE
# ==========================================
def show_detail():
    z_info = st.session_state.selected_zone
    if not z_info: st.session_state.page = 'landing'; st.rerun()
    zid = z_info['id']
    
    with st.sidebar:
        st.header("⚙️ Control Panel")
        
        if zid == 'Z-B':
            st.info("**MODE SIMULASI (Zona B)**")
            st.slider("Kapasitas Anorganik (%)", 0, 100, key='sim_b_an')
            st.slider("Kapasitas Organik (%)", 0, 100, key='sim_b_org')
        elif zid == 'Z-C':
            st.info("**MODE SIMULASI (Zona C)**")
            st.slider("Kapasitas Anorganik (%)", 0, 100, key='sim_c_an')
            st.slider("Kapasitas Organik (%)", 0, 100, key='sim_c_org')
        else:
            st.success("**MODE IOT LIVE**\nData realtime dari sensor.")
        
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
            <div id="date_detail" style="font-size: 0.75rem; font-weight: 500; opacity: 0.9; margin-bottom: 2px;"></div>
            <div id="clock_detail" style="font-size: 1.1rem; font-weight: bold; text-shadow: 0 0 5px {THEME_GREEN}99;"></div>
        </div>
        <script>
            function updateTime() {{
                const now = new Date();
                const optionsDate = {{ weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }};
                const datePart = now.toLocaleDateString('id-ID', optionsDate);
                const timePart = now.toLocaleTimeString('id-ID', {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }});
                document.getElementById('date_detail').innerHTML = datePart;
                document.getElementById('clock_detail').innerHTML = timePart + ' WIB';
            }}
            setInterval(updateTime, 1000);
            updateTime();
        </script>
        """, height=60)
    
    st.markdown("---")
    
    current_data = get_zone_data(zid)
    res = analyze_system(zid, current_data, event_bool, lokasi_opt)
    
    # Update state grafik simulasi (hanya untuk B & C)
    if zid != 'Z-A':
        st.session_state.hist_time.append(jam_str)
        st.session_state.hist_an.append(res['an']['lvl'])
        st.session_state.hist_org.append(res['org']['lvl'])
        if len(st.session_state.hist_time) > 20: 
            st.session_state.hist_time.pop(0); st.session_state.hist_an.pop(0); st.session_state.hist_org.pop(0)

    col1, col2, col3 = st.columns(3)
    
    def get_colors(color_code):
        if color_code == 'red': return 'nb-red', THEME_RED
        if color_code == 'yellow': return 'nb-yellow', THEME_YELLOW
        return 'nb-green', THEME_GREEN

    # --- ANORGANIK ---
    with col1:
        st.markdown("### 🟦 Anorganik")
        st.metric("Level Kapasitas", f"{res['an']['lvl']}%")
        st.progress(min(res['an']['lvl']/100, 1.0))
        css, txt_col = get_colors(res['an']['col'])
        html_an = f"""<div class="neon-box-detail {css}">
<div style="color:#bbb; font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">🤖 PREDIKSI PENUH</div>
<div style="color:white; font-weight:bold; font-size:1.5rem;">{res['an']['ai']}</div>
<hr style="border-color:#333; margin:15px 0;">
<div style="color:#bbb; font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">🧠 SISTEM PAKAR</div>
<div style="color:{txt_col}; font-weight:bold; font-size:1.2rem;">{res['an']['act']}</div>
<div style="font-size:0.85rem; margin-top:5px; color:#ddd;">
CF: <b>{res['an']['cf']}</b> | Status: {res['an']['st']}
</div>
</div>"""
        st.markdown(html_an, unsafe_allow_html=True)

    # --- ORGANIK ---
    with col2:
        st.markdown("### 🟩 Organik")
        st.metric("Level Kapasitas", f"{res['org']['lvl']}%")
        st.progress(min(res['org']['lvl']/100, 1.0))
        css, txt_col = get_colors(res['org']['col'])
        html_org = f"""<div class="neon-box-detail {css}">
<div style="color:#bbb; font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">🤖 PREDIKSI PENUH</div>
<div style="color:white; font-weight:bold; font-size:1.5rem;">{res['org']['ai']}</div>
<hr style="border-color:#333; margin:15px 0;">
<div style="color:#bbb; font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">🧠 SISTEM PAKAR</div>
<div style="color:{txt_col}; font-weight:bold; font-size:1.2rem;">{res['org']['act']}</div>
<div style="font-size:0.85rem; margin-top:5px; color:#ddd;">
CF: <b>{res['org']['cf']}</b> | Status: {res['org']['st']}
</div>
</div>"""
        st.markdown(html_org, unsafe_allow_html=True)

    # --- LINGKUNGAN ---
    with col3:
        st.markdown("### 🌡️ Lingkungan")
        c_a, c_b = st.columns(2)
        c_a.metric("Suhu", f"{res['env']['s']}°C")
        c_b.metric("Lembab", f"{res['env']['l']}%")
        st.metric("Gas (Bau)", f"{res['env']['g']} ppm")
        
        if res['env']['g'] > 200:
            st.markdown(f"<div style='background:{THEME_RED}; color:white; padding:15px; border-radius:8px; text-align:center; font-weight:bold; margin-top:10px;'>⚠️ BAU MENYENGAT</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:{THEME_GREEN}; color:black; padding:15px; border-radius:8px; text-align:center; font-weight:bold; margin-top:10px;'>✅ UDARA NORMAL</div>", unsafe_allow_html=True)

    st.write("")
    
    # --- CHART ---
    st.subheader("📈 Visualisasi Data")
    
    if zid == 'Z-A':
        # --- KHUSUS ZONA A: FETCH RIWAYAT SERVER (PER JAM) ---
        with st.spinner('Mengambil data riwayat per jam dari server...'):
            df_hist = fetch_history_logs()
        
        if df_hist is not None and not df_hist.empty:
            st.line_chart(df_hist, color=[THEME_BLUE, THEME_GREEN])
            st.caption("Grafik menampilkan rata-rata kapasitas per jam berdasarkan data server (riwayat_logs).")
        else:
            st.warning("Belum ada data riwayat yang cukup untuk ditampilkan.")
            
    else:
        # --- ZONA B & C: SIMULASI REALTIME (SESSION STATE) ---
        if len(st.session_state.hist_time) > 1:
            df_chart = pd.DataFrame({
                'Waktu': st.session_state.hist_time,
                'Anorganik': st.session_state.hist_an,
                'Organik': st.session_state.hist_org
            })
            st.line_chart(df_chart.set_index('Waktu'), color=[THEME_BLUE, THEME_GREEN])
        else:
            st.info("Menunggu data masuk untuk menampilkan grafik...")

# ==========================================
# 6. ROUTER
# ==========================================
if st.session_state.page == 'landing':
    show_landing()
elif st.session_state.page == 'detail':
    show_detail()