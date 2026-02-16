import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import base64

# --- 1. SAYFA VE STİL YAPILANDIRMASI ---
st.set_page_config(page_title="Kutup Dijital İkiz v2", layout="wide")

# --- KESİN ÇÖZÜM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0a192f; color: white; }
    [data-testid="stSidebar"] { background-color: #F0F8FF !important; border-right: 1px solid #dee2e6; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { 
        color: #000000 !important; font-weight: 700 !important; 
    }
    div[data-testid="metric-container"] { 
        background-color: rgba(0, 212, 255, 0.1); border: 1px solid #00d4ff; padding: 15px; border-radius: 12px; 
    }
    [data-testid="stMetricValue"] { color: #A0D6E8 !important; }
    [data-testid="stMetricLabel"] { color: #E1FFFF !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. ÇOKLU HASTA VERİ YAPISI ---
if 'patients' not in st.session_state:
    st.session_state.patients = {
        "Ayşe Hanım": pd.DataFrame(),
        "Mehmet Bey": pd.DataFrame(),
        "Fatma Hanım": pd.DataFrame()
    }

# --- 3. YARDIMCI FONKSİYONLAR ---
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
    if df.empty: return "Normal", [], [], "green"
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
    st.title("🚀 Görev Kontrol")
    sayfa_secimi = st.selectbox("Bölüm Seçiniz:", ["🏠 Ana Kontrol Paneli", "📊 Fizyolojik Derin Analiz", "🚨 Acil Durum Rehberi"])
    
    st.divider()
    st.header("👥 Hasta Portföyü")
    selected_patient = st.selectbox("İzlenecek Hastayı Seçin:", list(st.session_state.patients.keys()))
    
    st.divider()
    st.header(f"📋 {selected_patient} Değerlendirme")
    braden_score = st.slider("Braden (Bası Riski)", 6, 23, 16)
    itaki_score = st.slider("Itaki (Düşme Riski)", 0, 20, 8)
    nurse_note = st.text_area("Hemşire Gözlem Notu:", placeholder="Klinik notlarınızı buraya yazın...")

# --- 5. ANA PANEL ---
if sayfa_secimi == "🏠 Ana Kontrol Paneli":
    st.title(f"🩺 NursTwin-Home: {selected_patient} Dijital İkiz Paneli")
    
    # Veri Güncelleme Butonu
    if st.button("Verileri Simüle Et"):
        yeni_veri = get_simulated_data(selected_patient)
        st.session_state.patients[selected_patient] = pd.concat([pd.DataFrame([yeni_veri]), st.session_state.patients[selected_patient]]).head(50)
    
    df = st.session_state.patients[selected_patient]
    if not df.empty:
        status, nandas, nics, color = analyze_logic(df, nurse_note, braden_score, itaki_score)
        
        # Metrik Kutuları
        last = df.iloc[0]
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Nabız", f"{last['Nabız']} bpm")
        m2.metric("SpO2", f"%{last['SpO2']}")
        m3.metric("Ateş", f"{last['Ateş']}°C")
        m4.metric("Risk Skoru", f"%{last['Hareket_Skoru']}")
        m5.metric("Durum", status)

        st.divider()
        
        # Grafik ve Tablo
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📈 Dijital İkiz Trend Analizi")
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=df["Nabız"], mode='lines+markers', line=dict(color='red')))
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📂 Gerçek Zamanlı Sistem Kayıtları")
            st.dataframe(df, use_container_width=True)
        
        with col2:
            st.subheader("📋 Karar Destek (NIC)")
            st.write(f"**Aktif NANDA Tanıları:** {', '.join(nandas) if nandas else 'Yok'}")
            for nic in nics:
                st.checkbox(nic, value=True)
    else:
        st.info("Lütfen veri akışını başlatmak için butona basın.")
