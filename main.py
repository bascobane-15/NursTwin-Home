import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import base64

# --- 1. SAYFA AYARI ---
st.set_page_config(page_title="NursTwin-Home: Bütünsel Bakım Yönetimi", layout="wide")

# --- 2. SESSION STATE ---
if "patients" not in st.session_state:
    st.session_state.patients = {
        "Ayşe Hanım": pd.DataFrame(columns=["Zaman", "Nabız", "Ateş", "SpO2", "Hareket_Skoru"]),
        "Mehmet Bey": pd.DataFrame(columns=["Zaman", "Nabız", "Ateş", "SpO2", "Hareket_Skoru"]),
        "Fatma Hanım": pd.DataFrame(columns=["Zaman", "Nabız", "Ateş", "SpO2", "Hareket_Skoru"]),
    }

# --- 3. FONKSİYONLAR ---

def get_simulated_data(patient_name):
    base_pulse = 75 if "Ayşe" in patient_name else 88 if "Mehmet" in patient_name else 70
    return {
        "Zaman": datetime.now(),
        "Nabız": np.random.randint(base_pulse-5, base_pulse+25),
        "SpO2": np.random.randint(92, 100),
        "Ateş": round(np.random.uniform(36.2, 38.3), 1),
        "Hareket_Skoru": np.random.randint(0, 100)
    }

def analyze_logic(df, note, braden, itaki):
    if df.empty:
        return "✅ STABİL", [], [], "green"

    last = df.iloc[0]
    risks, nics = [], []

    if last["Nabız"] > 105 or itaki > 12 or "baş dönmesi" in note.lower():
        risks.append("NANDA: Düşme Riski (00155)")
        nics.extend(["NIC: Düşmeleri Önleme (6490)", "NIC: Çevre Düzenlemesi (6486)"])

    if df["Hareket_Skoru"].head(5).mean() < 30 or braden < 14:
        risks.append("NANDA: Basınç Yaralanması Riski (00249)")
        nics.extend(["NIC: Pozisyon Yönetimi (0840)", "NIC: Basınçlı Bölge Bakımı (3500)"])

    status = "⚠️ KRİTİK" if len(risks) > 1 else "🟡 UYARI" if len(risks) == 1 else "✅ STABİL"
    color = "red" if status == "⚠️ KRİTİK" else "orange" if status == "🟡 UYARI" else "green"

    return status, risks, nics, color

def create_report_download(df, note, status, nandas, patient_name):
    report_text = f"NursTwin-Home Klinik Raporu - {patient_name}\n"
    report_text += f"Durum: {status}\n"
    report_text += f"NANDA: {', '.join(nandas) if nandas else 'Yok'}\n"
    report_text += f"Hemşire Notu: {note}\n\n"
    report_text += df.head(10).to_string(index=False)

    b64 = base64.b64encode(report_text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="rapor.txt">📥 Klinik Raporu İndir</a>'

# --- 4. SIDEBAR ---

with st.sidebar:
    st.header("👥 Hasta Portföyü")

    selected_patient = st.selectbox(
        "Hasta Seçin",
        list(st.session_state.patients.keys())
    )

    st.divider()

    st.subheader("📝 Hemşire Gözlem")

    nurse_note = st.text_area("Hemşire Notu")

    braden_score = st.slider("Braden Skoru", 6, 23, 16)
    itaki_score = st.slider("Itaki Skoru", 0, 20, 8)

    st.divider()
    st.subheader("📡 Canlı Sensör")

    if st.button("Yeni Sensör Verisi Al"):
        new_data = get_simulated_data(selected_patient)
        df = st.session_state.patients[selected_patient]
        df = pd.concat([pd.DataFrame([new_data]), df]).head(50)
        st.session_state.patients[selected_patient] = df
        st.rerun()

# --- 5. ANA PANEL ---

st.title(f"🩺 {selected_patient} Dijital İkiz Paneli")

current_df = st.session_state.patients[selected_patient]

if not current_df.empty:

    # --- VERİ TİPİ DÜZELTME ---
    current_df["Nabız"] = pd.to_numeric(current_df["Nabız"], errors="coerce")
    current_df["SpO2"] = pd.to_numeric(current_df["SpO2"], errors="coerce")
    current_df["Ateş"] = pd.to_numeric(current_df["Ateş"], errors="coerce")
    current_df["Hareket_Skoru"] = pd.to_numeric(current_df["Hareket_Skoru"], errors="coerce")
    current_df["Zaman"] = pd.to_datetime(current_df["Zaman"], errors="coerce")

    status, nandas, nics, color = analyze_logic(
        current_df,
        nurse_note,
        braden_score,
        itaki_score
    )

    # --- METRİKLER ---
    m1, m2, m3, m4, m5 = st.columns(5)
    last = current_df.iloc[0]

    m1.metric("Nabız", f"{last['Nabız']} bpm")
    m2.metric("SpO2", f"%{last['SpO2']}")
    m3.metric("Ateş", f"{last['Ateş']}°C")

    risk_val = int((20 - braden_score) * 3 + itaki_score * 4)
    m4.metric("Risk Skoru", f"%{risk_val}")
    m5.metric("Durum", status)

    st.divider()

    # --- GRAFİK + ANALİZ ---
    l_col, r_col = st.columns([2, 1])

    with l_col:
        st.subheader("📈 Vital Bulgular Trend")

        # --- PRO LEVEL LONG FORMAT ---
df_long = current_df.melt(
    id_vars="Zaman",
    value_vars=["Nabız", "SpO2", "Ateş"],
    var_name="Parametre",
    value_name="Değer"
)

fig = px.line(
    df_long,
    x="Zaman",
    y="Değer",
    color="Parametre",
    markers=True
)

st.plotly_chart(fig, use_container_width=True, key="vital_chart")


st.plotly_chart(fig, use_container_width=True, key="vital_chart")


    with r_col:
        st.subheader("🧠 AI Klinik Yorum")
        st.write("Durum:", status)
        st.write("Olası NANDA Tanıları:", nandas if nandas else "Yok")
        st.write("Önerilen NIC Müdahaleleri:", nics if nics else "Yok")

        report_link = create_report_download(
            current_df,
            nurse_note,
            status,
            nandas,
            selected_patient
        )

        st.markdown(report_link, unsafe_allow_html=True)

else:
    st.info("Henüz sensör verisi yok. Lütfen 'Yeni Sensör Verisi Al' butonuna basın.")










































