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

 # Dosyanın en sonuna ekle
if sayfa_secimi == "🛰️ Gerçek Veri Entegrasyonu":
    st.header("🛰️ Ayşe Hanım - Canlı İzleme Paneli")
    
    if st.button("🔴 Canlı Veri Akışını Başlat"):
        k1, k2 = st.columns(2)
        uyari = st.empty()
        
        while True:
            ivme = get_phyphox_live_data() # Yukarıdaki fonksiyonu çağırır
            
            if ivme is not None:
                k1.metric("Telefon İvmesi", f"{ivme:.2f} m/s²")
                skor = min(int(ivme * 10), 100)
                k2.metric("Hareket Skoru", skor)
                
                if skor < 30:
                    uyari.error("⚠️ Ayşe Hanım Hareketsiz! Basınç Yaralanması Riski.")
                else:
                    uyari.success("✅ Hareketlilik Algılandı.")
            else:
                st.warning("Bağlantı yok. Phyphox'u kontrol edin.")
                break
            time.sleep(0.5)
