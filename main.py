import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import plotly.graph_objects as go
from datetime import datetime
import base64

# --- 1. SAYFA VE STİL YAPILANDIRMASI ---
st.set_page_config(page_title="NursTwin-Home: Bütünsel Bakım Yönetimi", layout="wide")

# Orijinal Koyu Arka Plan Stilin (Geri Getirildi)
st.markdown("""
<style>
    .stApp { background-color: #0a192f; color: white; }
    [data-testid="stSidebar"] { background-color: #F0F8FF !important; border-right: 1px solid #dee2e6; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #000000 !important; font-weight: 700 !important; }
    div[data-testid="metric-container"] { background-color: rgba(0, 212, 255, 0.1); border: 1px solid #00d4ff; padding: 15px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- 2. ÇOKLU HASTA VERİ YAPISI ---
if 'patients' not in st.session_state:
    st.session_state.patients = {
        "Ayşe Hanım": pd.DataFrame(),
        "Mehmet Bey": pd.DataFrame(),
        "Fatma Hanım": pd.DataFrame()
    }

# --- 3. YARDIMCI FONKSİYONLAR (ALGORİTMALARIN) ---
def get_phyphox_live_data():
    url = "http://192.168.1.102:8080/get?linear_acceleration"
    try:
        response = requests.get(url, timeout=0.5)
        data = response.json()
        x = data['buffer']['linear_accelerationX']['buffer'][0]
        y = data['buffer']['linear_accelerationY']['buffer'][0]
        z = data['buffer']['linear_accelerationZ']['buffer'][0]
        return (x**2 + y**2 + z**2)**0.5
    except: return None

def get_simulated_data(patient_name):
    base_pulse = 75 if "Ayşe" in patient_name else 88 if "Mehmet" in patient_name else 70
    return {
        "Tarih": datetime.now().strftime("%H:%M:%S"),
        "Nabız": np.random.randint(base_pulse-5, base_pulse+25),
        "SpO2": np.random.randint(92, 100),
        "Ateş": round(np.random.uniform(36.2, 38.3), 1),
        "Hareket_Skoru": np.random.randint(0, 100)
    }

def analyze_logic(df, note, braden, itaki):
    if df.empty: return "✅ STABİL", [], [], "green"
    last = df.iloc[0]
    risks, nics = [], []
    if last["Nabız"] > 105 or itaki > 12:
        risks.append("NANDA: Düşme Riski (00155)")
        nics.extend(["NIC: Düşmeleri Önleme (6490)", "NIC: Çevre Düzenlemesi (6486)"])
    if last["Hareket_Skoru"] < 30 or braden < 14:
        risks.append("NANDA: Basınç Yaralanması Riski (00249)")
        nics.extend(["NIC: Pozisyon Yönetimi (0840)", "NIC: Basınçlı Bölge Bakımı (3500)"])
    status = "⚠️ KRİTİK" if len(risks) > 1 else "🟡 UYARI" if len(risks) == 1 else "✅ STABİL"
    color = "red" if status == "⚠️ KRİTİK" else "orange" if status == "🟡 UYARI" else "green"
    return status, risks, nics, color

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🏥 NursTwin-Home")
    sayfa_secimi = st.selectbox("Bölüm Seçiniz:", ["🏠 Ana Kontrol Paneli", "🛰️ Gerçek Veri Entegrasyonu"])
    st.divider()
    selected_patient = st.selectbox("İzlenecek Hastayı Seçin:", list(st.session_state.patients.keys()))
    braden_score = st.slider("Braden (Bası Riski)", 6, 23, 16)
    itaki_score = st.slider("Itaki (Düşme Riski)", 0, 20, 8)
    nurse_note = st.text_area("Hemşire Gözlem Notu:")

# --- 5. ANA KONTROL PANELİ (SENİN ORİJİNAL TASARIMIN) ---
if sayfa_secimi == "🏠 Ana Kontrol Paneli":
    st.title(f"🩺 NursTwin-Home: {selected_patient} Dijital İkiz Paneli")
    
    # Otomatik Veri Üretimi
    yeni_veri = get_simulated_data(selected_patient)
    st.session_state.patients[selected_patient] = pd.concat([pd.DataFrame([yeni_veri]), st.session_state.patients[selected_patient]]).head(50)
    df = st.session_state.patients[selected_patient]
    
    # Algoritmik Analiz
    status, nandas, nics, color = analyze_logic(df, nurse_note, braden_score, itaki_score)
    
    # Metrikler (Orijinal haliyle)
    m1, m2, m3, m4, m5 = st.columns(5)
    last = df.iloc[0]
    m1.metric("Nabız", f"{last['Nabız']} bpm")
    m2.metric("SpO2", f"%{last['SpO2']}")
    m3.metric("Ateş", f"{last['Ate[']}°C")
    m4.metric("Hareket Skoru", f"%{last['Hareket_Skoru']}")
    m5.subheader(f":{color}[{status}]")

    st.divider()
    
    col_sol, col_sag = st.columns([2, 1])
    
    with col_sol:
        st.subheader("📈 Dijital İkiz Trend Analizi")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(len(df))), y=df["Nabız"], mode='lines+markers', name="Mevcut Nabız", line=dict(color='red')))
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📁 Gerçek Zamanlı Sistem Kayıtları")
        st.dataframe(df, use_container_width=True)

    with col_sag:
        st.subheader("📋 Karar Destek (NIC)")
        st.write(f"**Aktif NANDA Tanıları:** {', '.join(nandas) if nandas else 'Yok'}")
        for nic in nics:
            st.checkbox(nic, value=True)

# --- 6. CANLI VERİ SAYFASI ---
elif sayfa_secimi == "🛰️ Gerçek Veri Entegrasyonu":
    st.header("🛰️ Ayşe Hanım - Canlı İzleme Paneli")
    if st.button("🔴 Canlı Veri Akışını Başlat"):
        k1, k2 = st.columns(2)
        uyari = st.empty()
        while True:
            ivme = get_phyphox_live_data()
            if ivme is not None:
                k1.metric("Anlık İvme", f"{ivme:.2f} m/s²")
                skor = min(int(ivme * 10), 100)
                k2.metric("Hareket Skoru", skor)
                if skor < 30: uyari.error("⚠️ Ayşe Hanım Hareketsiz! Basınç Yaralanması Riski.")
                else: uyari.success("✅ Hareketlilik Algılandı.")
            else:
                st.warning("Phyphox bağlantısını kontrol edin.")
                break
            time.sleep(0.5)
