import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(
    page_title="SafeCheck AI",
    page_icon="🛡️",
    layout="centered"
)

st.markdown("""
<style>
    .risk-high {
        background-color: #FEE2E2;
        border-left: 5px solid #DC2626;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .risk-medium {
        background-color: #FEF3C7;
        border-left: 5px solid #D97706;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .risk-safe {
        background-color: #DCFCE7;
        border-left: 5px solid #16A34A;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: linear-gradient(135deg, #1B3A5C, #2563EB); 
            padding: 2rem; border-radius: 12px; text-align: center; 
            color: white; margin-bottom: 2rem;">
    <h1>🛡️ SafeCheck AI</h1>
    <p>Deteksi Penipuan Digital Sebelum Terlambat</p>
    <small>by Maria Devi Aparilia — Final Project AI01</small>
</div>
""", unsafe_allow_html=True)

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception:
    st.error("❌ API Key tidak ditemukan.")
    st.stop()

def analisis_pesan(pesan_user):
    prompt = f"""
Kamu adalah Analis Keamanan Digital Senior spesialis mendeteksi penipuan digital di Indonesia.

Analisis pesan berikut dan tentukan apakah mengandung indikasi penipuan digital.

Pesan: "{pesan_user}"

Jawab HANYA dalam format JSON ini (tanpa teks lain di luar JSON):
{{
    "status_risiko": "Berisiko Tinggi" atau "Perlu Waspada" atau "Aman",
    "skor_risiko": angka 0-100,
    "confidence_level": "Tinggi" atau "Sedang" atau "Rendah",
    "indikator_bahaya": ["indikator spesifik 1", "indikator spesifik 2"],
    "penjelasan_awam": "penjelasan 2-3 kalimat bahasa sederhana",
    "rekomendasi_tindakan": ["tindakan 1", "tindakan 2", "tindakan 3"]
}}

Penting: sebutkan indikator SPESIFIK dari teks, bukan pernyataan generik.
"""
    response = model.generate_content(prompt)
    teks = response.text.strip()
    if "```" in teks:
        teks = teks.split("```")[1]
        if teks.startswith("json"):
            teks = teks[4:]
    return json.loads(teks.strip())

st.markdown("### 📋 Masukkan Pesan yang Ingin Dicek")

pesan_input = st.text_area(
    label="pesan",
    placeholder='Contoh: "Selamat! Nomor Anda terpilih memenangkan hadiah Rp50.000.000 dari BRI. Klik bit.ly/xxx untuk klaim sebelum 24 jam."',
    height=150,
    label_visibility="collapsed"
)

with st.expander("💡 Coba dengan contoh pesan"):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔴 Scam BRI"):
            pesan_input = "Selamat! Nomor Anda terpilih memenangkan hadiah Rp50.000.000 dari BRI. Klik bit.ly/xxx untuk klaim hadiah sebelum 24 jam. Hubungi CS: 0812-xxxx"
    with col2:
        if st.button("🟡 Pesan Ambigu"):
            pesan_input = "Halo, ini dari tim IT. Tolong konfirmasi akun Anda dengan klik link berikut untuk keamanan sistem."
    with col3:
        if st.button("🟢 Pesan Aman"):
            pesan_input = "Halo! Pengingat dari BCA bahwa tagihan kartu kredit Anda jatuh tempo tanggal 25. Hubungi 1500888 untuk info."

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    tombol = st.button("🔍 Analisis Sekarang", type="primary", use_container_width=True)

if tombol:
    if not pesan_input.strip():
        st.warning("⚠️ Masukkan pesan terlebih dahulu!")
    else:
        with st.spinner("🔍 Sedang menganalisis..."):
            try:
                hasil = analisis_pesan(pesan_input)

                st.markdown("---")
                st.markdown("### 📊 Hasil Analisis SafeCheck AI")

                status = hasil.get("status_risiko", "Tidak diketahui")
                skor = hasil.get("skor_risiko", 0)
                confidence = hasil.get("confidence_level", "Sedang")

                if status == "Berisiko Tinggi":
                    emoji_status = "🔴"
                    css_class = "risk-high"
                elif status == "Perlu Waspada":
                    emoji_status = "🟡"
                    css_class = "risk-medium"
                else:
                    emoji_status = "🟢"
                    css_class = "risk-safe"

                st.markdown(f"""
                <div class="{css_class}">
                    <h3>{emoji_status} {status}</h3>
                    <p><strong>Skor Risiko:</strong> {skor}/100 &nbsp;|&nbsp;
                    <strong>Keyakinan AI:</strong> {confidence}</p>
                </div>
                """, unsafe_allow_html=True)

                indikator = hasil.get("indikator_bahaya", [])
                if indikator:
                    st.markdown("#### ⚠️ Indikator Bahaya yang Ditemukan")
                    for i, item in enumerate(indikator, 1):
                        st.markdown(f"**{i}.** {item}")

                st.markdown("#### 💬 Penjelasan")
                st.info(hasil.get("penjelasan_awam", "-"))

                rekomendasi = hasil.get("rekomendasi_tindakan", [])
                if rekomendasi:
                    st.markdown("#### ✅ Rekomendasi Tindakan")
                    for item in rekomendasi:
                        if "jangan" in item.lower():
                            st.markdown(f"❌ {item}")
                        else:
                            st.markdown(f"✅ {item}")

                st.markdown("""
                <div style="background:#EFF6FF; border:1px solid #BFDBFE; 
                            padding:1rem; border-radius:8px; margin-top:1rem; 
                            font-size:0.85rem; color:#1E40AF;">
                    ℹ️ <strong>Disclaimer:</strong> Hasil ini adalah rekomendasi awal 
                    berbasis analisis AI, bukan keputusan final. Verifikasi ke pihak 
                    resmi tetap sangat disarankan.
                </div>
                """, unsafe_allow_html=True)

                if status == "Berisiko Tinggi":
                    st.markdown("#### 📞 Kontak Resmi untuk Verifikasi")
                    st.markdown("""
                    - 🏦 **BRI:** 14017
                    - 🏦 **BCA:** 1500888
                    - 🏦 **Mandiri:** 14000
                    - 🌐 **Lapor ke Kominfo:** aduan.kominfo.go.id
                    """)

            except json.JSONDecodeError:
                st.error("❌ Gagal memproses jawaban AI. Coba lagi.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#6B7280; font-size:0.8rem;">
    SafeCheck AI · Maria Devi Aparilia · NIM 24110400032<br>
    Final Project AI01 — Artificial Intelligence
</div>
""", unsafe_allow_html=True)
