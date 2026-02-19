import streamlit as st
import pandas as pd
import random
import numpy as np
import time
import plotly.express as px

import plotly.graph_objects as go
from datetime import datetime
import base64

# --- 1. SAYFA VE STİL YAPILANDIRMASI ---
st.set_page_config(page_title="NursTwin-Home: Bütünsel Bakım Yönetimi", layout="wide")

# --- 2. ÇOKLU HASTA VERİ YAPISI ---
st.session_state.patients = {
"Ayşe Hanım": pd.DataFrame(columns=["Zaman", "Nabız", "Ateş", "SpO2"]),
"Mehmet Bey": pd.DataFrame(columns=["Zaman", "Nabız", "Ateş", "SpO2"]),
"Fatma Hanım": pd.DataFrame(columns=["Zaman", "Nabız", "Ateş", "SpO2"]),
}


# --- 3. YARDIMCI FONKSİYONLAR (MİMARİ KATMAN B & C) ---
def simulate_sensor_data():
    return {
        "Zaman": datetime.now(),
        "Nabız": np.random.randint(70, 110),
        "Ateş": round(np.random.uniform(36.5, 38.5), 1),
        "SpO2": np.random.randint(94, 100)
    }

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

    selected_patient = st.selectbox(
        "İzlenecek Hastayı Seçin:",
        list(st.session_state.patients.keys())
    )

    st.divider()

    st.header(f"📋 {selected_patient} Değerlendirme")

    braden_score = st.slider(
        "Braden (Bası Riski)",
        6, 23, 16,
        key=f"braden_{selected_patient}"
    )

    itaki_score = st.slider(
        "Itaki (Düşme Riski)",
        0, 20, 8,
        key=f"itaki_{selected_patient}"
    )

    st.divider()

    # ✅ Sensör Butonu Sidebar İçinde
    st.subheader("📡 Canlı Sensör")

   # 1️⃣ BUTON
if st.button("Yeni Sensör Verisi Al"):
    new_data = get_simulated_data(selected_patient)

    df = st.session_state.patients[selected_patient]
    df = pd.concat([pd.DataFrame([new_data]), df]).head(50)

    st.session_state.patients[selected_patient] = df
    st.rerun()

# 2️⃣ BURAYA YAZACAKSIN 👇👇👇
current_df = st.session_state.patients[selected_patient]

st.write("Satır sayısı:", len(current_df))
st.write(current_df)

# 3️⃣ ANALİZ
if not current_df.empty:
    status, nandas, nics, color = analyze_logic(
        current_df,
        nurse_note,
        braden_score,
        itaki_score
    )

# 4️⃣ GRAFİK
l_col, r_col = st.columns(2)


# --- 5. ANA PANEL (KATMAN C) ---
st.title(f"🩺 NursTwin-Home: {selected_patient} Dijital İkiz Paneli")

st.subheader("📊 Canlı Sensör Verileri")

# Mevcut seçili hastanın verisi
current_df = st.session_state.patients[selected_patient]

# Analiz
status, nandas, nics, color = analyze_logic(
    current_df,
    nurse_note,
    braden_score,
    itaki_score
)

# Mobil Bildirim
check_mobile_alerts(status, nandas, selected_patient)


    # Rapor Butonu Güncelleme
if not current_df.empty:
        report_link = create_report_download(current_df, nurse_note, status, nandas, selected_patient)
        report_placeholder.markdown(report_link, unsafe_allow_html=True)
    
if not current_df.empty:
    report_link = create_report_download(
        current_df,
        nurse_note,
        status,
        nandas,
        selected_patient
    )
    report_placeholder.markdown(report_link, unsafe_allow_html=True)

# 👇 BURASI AYNI HİZADA OLMALI
if not current_df.empty:
    m1, m2, m3, m4, m5 = st.columns(5)

    last_val = current_df.iloc[0]

    m1.metric("Nabız", f"{last_val['Nabız']} bpm")
    m2.metric("SpO2", f"%{last_val['SpO2']}")
    m3.metric("Ateş", f"{last_val['Ateş']}°C")

    risk_val = int((20 - braden_score) * 3 + itaki_score * 4)
    m4.metric("Risk Skoru", f"%{risk_val}")
    m5.metric("Durum", status)

    st.divider()

    # Grafik ve Bakım Planı
    l_col, r_col = st.columns([2, 1])
        
l_col, r_col = st.columns(2)

l_col, r_col = st.columns(2)

with l_col:
    st.subheader("📈 Vital Bulgular Trend")
    fig = px.line(
        current_df,
        x="Zaman",
        y=["Nabız", "SpO2", "Ateş"],
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)

with r_col:
    st.subheader("🧠 AI Klinik Yorum")
    st.write("Durum:", status)
    st.write("Olası NANDA Tanıları:", nandas)
    st.write("Önerilen NIC Müdahaleleri:", nics)


    if not current_df.empty:
        last_val = current_df.iloc[-1]

        fig.add_trace(go.Scatter(
            y=current_df["Nabız"],
            name="Mevcut Nabız",
            line=dict(color='red', width=2)
        ))

        future_y = [
            last_val["Nabız"],
            last_val["Nabız"] + (6 if last_val["Nabız"] > 95 else -2)
        ]

        fig.add_trace(go.Scatter(
            x=[len(current_df)-1, len(current_df)+2],
            y=future_y,
            name="Tahmin (AI)",
            line=dict(color='gray', dash='dot')
        ))

    st.plotly_chart(
    fig,
    use_container_width=True,
    key="vital_trend_chart"
)






































