import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from datetime import datetime
import base64

# --- 1. SAYFA VE STİL YAPILANDIRMASI ---
st.set_page_config(page_title="NursTwin-Home: Bütünsel Bakım Yönetimi", layout="wide")

# --- 2. ÇOKLU HASTA VERİ YAPISI ---
if 'patients' not in st.session_state:
    st.session_state.patients = {
        "Ayşe Hanım": pd.DataFrame(),
        "Mehmet Bey": pd.DataFrame(),
        "Fatma Hanım": pd.DataFrame()
    }

# --- 3. YARDIMCI FONKSİYONLAR (MİMARİ KATMAN B & C) ---

def create_report_download(df, note, status, nandas, patient_name):
    """Klinik verileri indirilebilir bir metin dosyasına dönüştürür."""
    report_text = f"NursTwin-Home Klinik Raporu - {patient_name}\n{'='*45}\n"
    report_text += f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report_text += f"Genel Durum: {status}\n"
    report_text += f"Tespit Edilen NANDA Tanıları: {', '.join(nandas) if nandas else 'Normal'}\n"
    report_text += f"Hemşire Notu: {note if note else 'Not girilmedi.'}\n\n"
    report_text += f"SON VİTAL BULGULAR:\n{df.head(10).to_string(index=False)}\n"
    
    b64 = base64.b64encode(report_text.encode('utf-8-sig')).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="NursTwin_{patient_name}_Rapor.txt" style="text-decoration:none;"><button style="width:100%; cursor:pointer; background-color:#4CAF50; color:white; border:none; padding:10px; border-radius:5px;">📥 Klinik Raporu İndir</button></a>'

def get_simulated_data(patient_name):
    """Mimarideki 'Donanım/Sensör' katmanını simüle eder."""
    base_pulse = 75 if "Ayşe" in patient_name else 88 if "Mehmet" in patient_name else 70
    return {
        "Tarih": datetime.now().strftime("%H:%M:%S"),
        "Nabız": np.random.randint(base_pulse-5, base_pulse+25),
        "SpO2": np.random.randint(92, 100),
        "Ateş": round(np.random.uniform(36.2, 38.3), 1),
        "Hareket_Skoru": np.random.randint(0, 100)
    }

def analyze_logic(df, note, braden, itaki):
    """Karar Motoru: NANDA ve NIC önerilerini üretir."""
    if df.empty: return "Normal", [], [], "green"
    last = df.iloc[0]
    risks, nics = [], []
    
    # NANDA Tanılama Algoritması
    if last["Nabız"] > 105 or itaki > 12 or "baş dönmesi" in note.lower():
        risks.append("NANDA: Düşme Riski (00155)")
        nics.extend(["NIC: Düşmeleri Önleme (6490)", "NIC: Çevre Düzenlemesi (6486)"])
    
    if df["Hareket_Skoru"].head(5).mean() < 30 or braden < 14:
        risks.append("NANDA: Basınç Yaralanması Riski (00249)")
        nics.extend(["NIC: Pozisyon Yönetimi (0840)", "NIC: Basınçlı Bölge Bakımı (3500)"])

    status = "⚠️ KRİTİK" if len(risks) > 1 else "🟡 UYARI" if len(risks) == 1 else "✅ STABİL"
    color = "red" if status == "⚠️ KRİTİK" else "orange" if status == "🟡 UYARI" else "green"
    return status, risks, nics, color

def check_mobile_alerts(status, nandas, patient_name):
    """İletişim Katmanı: Mobil bildirim simülasyonu yapar."""
    if status == "⚠️ KRİTİK":
        st.toast(f"🚨 MOBİL UYARI: {patient_name} için acil kontrol gerekli!", icon="📱")

# --- 4. SIDEBAR: HASTA SEÇİMİ VE VERİ GİRİŞİ (KATMAN A) ---
with st.sidebar:
    st.header("👥 Hasta Portföyü")
    selected_patient = st.selectbox("İzlenecek Hastayı Seçin:", list(st.session_state.patients.keys()))
    
    st.divider()
    st.header(f"📋 {selected_patient} Değerlendirme")
    braden_score = st.slider("Braden (Bası Riski)", 6, 23, 16, key=f"braden_{selected_patient}")
    itaki_score = st.slider("Itaki (Düşme Riski)", 0, 20, 8, key=f"itaki_{selected_patient}")
    
    st.divider()
    nurse_note = st.text_area("Hemşire Gözlem Notu:", height=100, placeholder="Klinik notlarınızı buraya yazın...")
    
    st.divider()
    st.subheader("📥 Raporlama")
    report_placeholder = st.empty()

