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

# --- 2. ÇOKLU HASTA VERİ YAPISI ---
if 'patients' not in st.session_state:
    st.session_state.patients = {
        "Ayşe Hanım": pd.DataFrame(),
        "Mehmet Bey": pd.DataFrame(),
        "Fatma Hanım": pd.DataFrame()
    }

# --- 3. YARDIMCI FONKSİYONLAR ---
def get_phyphox_live_data():
    """Phyphox üzerinden canlı ivme verisini çeker."""
    url = "http://192.168.1.102:8080/get?linear_acceleration"
    try:
        response = requests.get(url, timeout=0.5)
        data = response.json()
        x = data['buffer']['linear_accelerationX']['buffer'][0]
        y = data['buffer']['linear_accelerationY']['buffer'][0]
        z = data['buffer']['linear_accelerationZ']['buffer'][0]
        return (x**2 + y**2 + z**2)**0.5
    except:
        return None

def create_report_download(df, note, status, nandas, patient_name):
    """Klinik verileri indirilebilir bir metin dosyasına dönüştürür."""
    report_text = f"NursTwin-Home Klinik Raporu - {patient_name}\n{'='*45}\n"
    report_text += f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report_text += f"Genel Durum: {status}\n"
    report_text += f"Tespit Edilen NANDA Tanıları: {', '.join(nandas) if nandas else 'Normal'}\n"
    report_text += f"Hemşire Notu: {note if note else 'Not girilmedi.'}\n\n"
    if not df.empty:
        report_text += f"SON VİTAL BULGULAR:\n{df.head(10).to_string(index=False)}\n"
    
    b64 = base64.b64encode(report_text.encode('utf-8-sig')).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="NursTwin_{patient_name}_Rapor.txt" style="text-decoration:none;"><button style="width:100%; cursor:pointer; background-color:#4CAF50; color:white; border:none; padding:10px; border-radius:5px;">📥 Klinik Raporu İndir</button></a>'

def get_simulated_data(patient_name):
    """Simülasyon verisi üretir."""
    base_pulse = 75 if "Ayşe" in patient_name else 88 if "Mehmet" in patient_name else 70
    return {
        "Tarih": datetime.now().strftime("%H:%M:%S"),
        "Nabız": np.random.randint(base_pulse-5, base_pulse+25),
        "SpO2": np.random.randint(92, 100),
        "Ateş": round(np.random.uniform(36.2, 38.3), 1),
        "Hareket_Skoru": np.random.randint(0, 100)
    }

def analyze_logic(df, note, braden, itaki):
    """Karar Motoru: NANDA önerilerini üretir."""
    if df.empty: return "✅ STABİL", [], [], "green"
    last = df.iloc[0]
    risks, nics = [], []
    
    if last["Nabız"] > 105 or itaki > 12 or "baş dönmesi" in note.lower():
        risks.append("NANDA: Düşme Riski (00155)")
        nics.extend(["NIC: Düşmeleri Önleme (6490)"])
    
    if last["Hareket_Skoru"] < 30 or braden < 14:
        risks.append("NANDA: Basınç Yaralanması Riski (00249)")
        nics.extend(["NIC: Pozisyon Yönetimi (0840)"])

    status = "⚠️ KRİTİK" if len(risks) > 1 else "🟡 UYARI" if len(risks) == 1 else "✅ STABİL"
    color = "red" if status == "⚠️ KRİTİK" else "orange" if status == "🟡 UYARI" else "green"
    return status, risks, nics, color

# --- 4. SIDEBAR VE MENÜ ---
with st.sidebar:
    st.title("🏥 NursTwin-Home")
    sayfa_secimi = st.selectbox(
        "Bölüm Seçiniz:",
        [
            "🏠 Ana Kontrol Paneli", 
            "📊 Fizyolojik Derin Analiz", 
            "🛰️ Gerçek Veri Entegrasyonu"
        ]
    )
    
    st.divider()
    selected_patient = st.selectbox("İzlenecek Hastayı Seçin:", list(st.session_state.patients.keys()))
    braden_score = st.slider("Braden (Bası Riski)", 6, 23, 16)
    itaki_score = st.slider("Itaki (Düşme Riski)", 0, 20, 8)
    nurse_note = st.text_area("Hemşire Gözlem Notu:", height=100)

# --- 5. SAYFA İÇERİKLERİ ---

if sayfa_secimi == "🏠 Ana Kontrol Paneli":
    st.header(f"🏠 {selected_patient} Genel Durum")
    if st.button("Verileri Güncelle (Simülasyon)"):
        yeni_veri = get_simulated_data(selected_patient)
        st.session_state.patients[selected_patient] = pd.concat([pd.DataFrame([yeni_veri]), st.session_state.patients[selected_patient]]).head(20)
    
    df = st.session_state.patients[selected_patient]
    status, risks, nics, color = analyze_logic(df, nurse_note, braden_score, itaki_score)
    
    st.subheader(f"Durum: :{color}[{status}]")
    if risks:
        st.error(f"Tespit Edilen Riskler: {', '.join(risks)}")
    st.table(df)

elif sayfa_secimi == "🛰️ Gerçek Veri Entegrasyonu":
    st.header("🛰️ Ayşe Hanım - Canlı İzleme Paneli")
    st.info("Bu sayfa doğrudan Phyphox uygulamasından gelen canlı ivme verilerini kullanır.")
    
    if st.button("🔴 Canlı Veri Akışını Başlat"):
        k1, k2 = st.columns(2)
        uyari = st.empty()
        
        while True:
            ivme = get_phyphox_live_data()
            
            if ivme is not None:
                k1.metric("Telefon İvmesi", f"{ivme:.2f} m/s²")
                skor = min(int(ivme * 10), 100)
                k2.metric("Hareket Skoru (Simüle)", skor)
                
                if skor < 30:
                    uyari.error("⚠️ Ayşe Hanım Hareketsiz! Basınç Yaralanması Riski.")
                else:
                    uyari.success("✅ Hareketlilik Algılandı. Hasta Aktif.")
            else:
                st.warning("Bağlantı yok. Lütfen telefonda Phyphox 'Remote Access'i açın.")
                break
            time.sleep(0.5)

else:
    st.header("📊 Fizyolojik Derin Analiz")
    st.write("Bu bölüm geliştirilme aşamasındadır.")

