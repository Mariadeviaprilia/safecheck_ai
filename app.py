import streamlit as st
import google.generativeai as genai
import json
import hashlib
import time

st.set_page_config(
    page_title="SafeCheck AI",
    page_icon="🛡️",
    layout="wide"
)

# ── CSS LENGKAP ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #0F172A 100%);
        min-height: 100vh;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1B3A5C, #2563EB);
        padding: 2.5rem;
        border-radius: 16px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(37, 99, 235, 0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .auth-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 2rem;
        backdrop-filter: blur(10px);
        max-width: 450px;
        margin: 0 auto;
    }
    
    .result-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .risk-high {
        background: linear-gradient(135deg, rgba(220,38,38,0.2), rgba(220,38,38,0.1));
        border: 1px solid #DC2626;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .risk-medium {
        background: linear-gradient(135deg, rgba(217,119,6,0.2), rgba(217,119,6,0.1));
        border: 1px solid #D97706;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .risk-safe {
        background: linear-gradient(135deg, rgba(22,163,74,0.2), rgba(22,163,74,0.1));
        border: 1px solid #16A34A;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .disclaimer-box {
        background: rgba(37,99,235,0.15);
        border: 1px solid rgba(37,99,235,0.4);
        border-radius: 10px;
        padding: 1rem;
        margin-top: 1rem;
        font-size: 0.85rem;
        color: #93C5FD;
    }
    
    .stat-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        color: white;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.95) !important;
        border: 1px solid rgba(37,99,235,0.5) !important;
        border-radius: 8px !important;
        color: #0F172A !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #94A3B8 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border: 1px solid #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.2) !important;
    }
    
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.95) !important;
        border: 1px solid rgba(37,99,235,0.5) !important;
        border-radius: 8px !important;
        color: #0F172A !important;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: #94A3B8 !important;
    }
    
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
        color: white !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8, #1E40AF) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 25px rgba(37,99,235,0.4) !important;
    }
    
    div[data-testid="stSidebar"] {
        background: rgba(15,23,42,0.9) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }
    
    .sidebar-user {
        background: rgba(37,99,235,0.2);
        border: 1px solid rgba(37,99,235,0.4);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        color: white;
        text-align: center;
    }
    
    h1, h2, h3, h4, h5 { color: white !important; }
    p, li { color: #CBD5E1 !important; }
    label { color: #94A3B8 !important; }
    
    .history-item {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
    }
    
    .badge-high { 
        background: #DC2626; color: white; 
        padding: 2px 10px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600;
    }
    .badge-medium { 
        background: #D97706; color: white; 
        padding: 2px 10px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600;
    }
    .badge-safe { 
        background: #16A34A; color: white; 
        padding: 2px 10px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── DATABASE SEDERHANA (pakai session state) ──
if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "demo": {
            "password": hashlib.sha256("demo123".encode()).hexdigest(),
            "nama": "Demo User",
            "history": []
        }
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "page" not in st.session_state:
    st.session_state.page = "login"

# ── FUNGSI HELPER ──
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    if username in st.session_state.users_db:
        if st.session_state.users_db[username]["password"] == hash_password(password):
            return True
    return False

def register_user(username, password, nama):
    if username in st.session_state.users_db:
        return False
    st.session_state.users_db[username] = {
        "password": hash_password(password),
        "nama": nama,
        "history": []
    }
    return True

def save_history(username, pesan, hasil):
    entry = {
        "pesan": pesan[:80] + "..." if len(pesan) > 80 else pesan,
        "status": hasil.get("status_risiko", "-"),
        "skor": hasil.get("skor_risiko", 0),
        "waktu": time.strftime("%d/%m/%Y %H:%M")
    }
    st.session_state.users_db[username]["history"].insert(0, entry)
    if len(st.session_state.users_db[username]["history"]) > 10:
        st.session_state.users_db[username]["history"] = \
            st.session_state.users_db[username]["history"][:10]

# ── SETUP GEMINI ──
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
except Exception:
    st.error("❌ API Key tidak ditemukan.")
    st.stop()

# ── FUNGSI ANALISIS ──
def analisis_pesan(pesan_user):
    prompt = f"""
Kamu adalah Analis Keamanan Digital Senior spesialis mendeteksi penipuan digital di Indonesia.

Analisis pesan berikut: "{pesan_user}"

Pengguna adalah orang awam. Gunakan bahasa sederhana.

Jawab HANYA dalam format JSON ini:
{{
    "status_risiko": "Berisiko Tinggi" atau "Perlu Waspada" atau "Aman",
    "skor_risiko": angka 0-100,
    "confidence_level": "Tinggi" atau "Sedang" atau "Rendah",
    "indikator_bahaya": ["indikator spesifik 1", "indikator spesifik 2"],
    "penjelasan_awam": "penjelasan 2-3 kalimat bahasa sederhana",
    "rekomendasi_tindakan": ["tindakan 1", "tindakan 2", "tindakan 3"]
}}

Sebutkan indikator SPESIFIK dari teks. Jangan generik.
Jika tidak cukup bukti, tulis confidence_level: "Rendah".
"""
    response = model.generate_content(prompt)
    teks = response.text.strip()
    if "```" in teks:
        teks = teks.split("```")[1]
        if teks.startswith("json"):
            teks = teks[4:]
    return json.loads(teks.strip())

# ════════════════════════════════════════
# HALAMAN LOGIN
# ════════════════════════════════════════
def halaman_login():
    st.markdown("""
    <div class="main-header">
        <h1 style="font-size:2.5rem; margin:0;">🛡️ SafeCheck AI</h1>
        <p style="font-size:1.1rem; opacity:0.9; margin:0.5rem 0 0;">
        Deteksi Penipuan Digital Sebelum Terlambat</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("### Masuk ke Akun")
        
        username = st.text_input("Username", placeholder="Masukkan username")
        password = st.text_input("Password", type="password", placeholder="Masukkan password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Login", use_container_width=True):
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.page = "app"
                    st.rerun()
                else:
                    st.error("Username atau password salah!")
        with col_b:
            if st.button("Daftar", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <p style="text-align:center; font-size:0.8rem; color:#64748B;">
        Demo: username <b style="color:#93C5FD;">demo</b> / 
        password <b style="color:#93C5FD;">demo123</b>
        </p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════
# HALAMAN REGISTER
# ════════════════════════════════════════
def halaman_register():
    st.markdown("""
    <div class="main-header">
        <h1 style="font-size:2.5rem; margin:0;">🛡️ SafeCheck AI</h1>
        <p style="opacity:0.9; margin:0.5rem 0 0;">Buat Akun Baru</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("### Daftar Akun Baru")
        
        nama = st.text_input("Nama Lengkap", placeholder="Contoh: Maria Devi")
        username = st.text_input("Username", placeholder="Buat username unik")
        password = st.text_input("Password", type="password", placeholder="Min. 6 karakter")
        password2 = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Daftar", use_container_width=True):
                if not nama or not username or not password:
                    st.error("❌ Semua field harus diisi!")
                elif len(password) < 6:
                    st.error("❌ Password minimal 6 karakter!")
                elif password != password2:
                    st.error("❌ Password tidak cocok!")
                elif register_user(username, password, nama):
                    st.success("✅ Akun berhasil dibuat! Silakan login.")
                    time.sleep(1)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error("❌ Username sudah dipakai!")
        with col_b:
            if st.button("← Kembali", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════
# HALAMAN UTAMA APP
# ════════════════════════════════════════
def halaman_app():
    user_data = st.session_state.users_db[st.session_state.current_user]
    nama_user = user_data["nama"]
    history = user_data["history"]
    
    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-user">
            <div style="font-size:2rem;">👤</div>
            <div style="font-weight:600; font-size:1rem; color:white;">{nama_user}</div>
            <div style="font-size:0.8rem; color:#93C5FD;">
            @{st.session_state.current_user}</div>
        </div>
        """, unsafe_allow_html=True)
        
        total = len(history)
        high = sum(1 for h in history if h["status"] == "Berisiko Tinggi")
        aman = sum(1 for h in history if h["status"] == "Aman")
        
        st.markdown("#### 📊 Statistik Kamu")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.5rem;font-weight:700;color:#60A5FA;">{total}</div>
                <div style="font-size:0.7rem;color:#94A3B8;">Total Cek</div>
            </div>""", unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.5rem;font-weight:700;color:#F87171;">{high}</div>
                <div style="font-size:0.7rem;color:#94A3B8;">Bahaya</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 🕒 Riwayat Analisis")
        
        if history:
            for h in history[:5]:
                if h["status"] == "Berisiko Tinggi":
                    badge = "🔴"
                elif h["status"] == "Perlu Waspada":
                    badge = "🟡"
                else:
                    badge = "🟢"
                st.markdown(f"""
                <div class="history-item">
                    <div style="font-size:0.75rem;color:#94A3B8;">{h['waktu']}</div>
                    <div style="font-size:0.8rem;color:#CBD5E1;margin:2px 0;">
                    {badge} {h['pesan'][:40]}...</div>
                    <div style="font-size:0.75rem;color:#60A5FA;">
                    Skor: {h['skor']}/100</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color:#64748B;font-size:0.85rem;text-align:center;">
            Belum ada riwayat analisis</p>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.page = "login"
            st.rerun()
    
    # ── KONTEN UTAMA ──
    st.markdown("""
    <div class="main-header">
        <h1 style="font-size:2.2rem;margin:0;">🛡️ SafeCheck AI</h1>
        <p style="opacity:0.9;margin:0.3rem 0 0;">
        Deteksi Penipuan Digital Sebelum Terlambat</p>
        <small style="opacity:0.7;">
        by Maria Devi Aparilia — Final Project AI01</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"### 👋 Halo, {nama_user}!")
    st.markdown("Paste pesan, SMS, email, atau URL mencurigakan di bawah ini untuk dianalisis.")
    
    # ── INPUT AREA ──
    pesan_input = st.text_area(
        label="pesan",
        placeholder='Contoh: "Selamat! Nomor Anda terpilih memenangkan hadiah Rp50.000.000 dari BRI. Klik bit.ly/xxx untuk klaim sebelum 24 jam."',
        height=130,
        label_visibility="collapsed"
    )
    
    # ── CONTOH PESAN ──
    with st.expander("💡 Coba dengan contoh pesan"):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔴 Scam BRI", use_container_width=True):
                st.session_state.contoh_pesan = "Selamat! Nomor Anda terpilih memenangkan hadiah Rp50.000.000 dari BRI. Klik bit.ly/xxx untuk klaim hadiah sebelum 24 jam. Hubungi CS: 0812-xxxx"
                st.rerun()
        with col2:
            if st.button("🟡 Phishing IT", use_container_width=True):
                st.session_state.contoh_pesan = "Halo, ini dari tim IT perusahaan. Tolong konfirmasi akun Anda dengan klik link berikut untuk keamanan sistem kami."
                st.rerun()
        with col3:
            if st.button("🟢 Pesan Aman", use_container_width=True):
                st.session_state.contoh_pesan = "Halo! Pengingat dari BCA bahwa tagihan kartu kredit Anda jatuh tempo tanggal 25. Hubungi 1500888 untuk info lebih lanjut."
                st.rerun()
    
    if "contoh_pesan" in st.session_state:
        pesan_input = st.session_state.contoh_pesan
        st.info(f"📋 Contoh dimuat: *{pesan_input[:60]}...*")
    
    # ── TOMBOL ANALISIS ──
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tombol = st.button("🔍 Analisis Sekarang", type="primary", use_container_width=True)
    
    # ── HASIL ──
    if tombol:
        if "contoh_pesan" in st.session_state:
            pesan_input = st.session_state.contoh_pesan
        
        if not pesan_input.strip():
            st.warning("⚠️ Masukkan pesan terlebih dahulu!")
        else:
            with st.spinner("🔍 SafeCheck AI sedang menganalisis..."):
                try:
                    hasil = analisis_pesan(pesan_input)
                    save_history(st.session_state.current_user, pesan_input, hasil)
                    
                    status = hasil.get("status_risiko", "Tidak diketahui")
                    skor = hasil.get("skor_risiko", 0)
                    confidence = hasil.get("confidence_level", "Sedang")
                    
                    st.markdown("---")
                    st.markdown("### 📊 Hasil Analisis")
                    
                    if status == "Berisiko Tinggi":
                        emoji_s = "🔴"
                        css = "risk-high"
                        warna = "#F87171"
                    elif status == "Perlu Waspada":
                        emoji_s = "🟡"
                        css = "risk-medium"
                        warna = "#FCD34D"
                    else:
                        emoji_s = "🟢"
                        css = "risk-safe"
                        warna = "#4ADE80"
                    
                    # Status card
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div style="font-size:2rem;">{emoji_s}</div>
                            <div style="font-size:1rem;font-weight:700;
                            color:{warna};">{status}</div>
                            <div style="font-size:0.75rem;color:#94A3B8;">Status</div>
                        </div>""", unsafe_allow_html=True)
                    with col_r2:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div style="font-size:2rem;font-weight:700;
                            color:{warna};">{skor}</div>
                            <div style="font-size:0.75rem;color:#94A3B8;">
                            Skor Risiko (0-100)</div>
                        </div>""", unsafe_allow_html=True)
                    with col_r3:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div style="font-size:1.5rem;">🎯</div>
                            <div style="font-size:1rem;font-weight:700;
                            color:#60A5FA;">{confidence}</div>
                            <div style="font-size:0.75rem;color:#94A3B8;">
                            Keyakinan AI</div>
                        </div>""", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Indikator
                    indikator = hasil.get("indikator_bahaya", [])
                    if indikator:
                        st.markdown("#### ⚠️ Indikator Bahaya Ditemukan")
                        for i, item in enumerate(indikator, 1):
                            st.markdown(f"""
                            <div style="background:rgba(220,38,38,0.1);
                            border-left:3px solid #DC2626;
                            padding:0.5rem 1rem;border-radius:6px;
                            margin:0.3rem 0;color:#FCA5A5;">
                            <strong>{i}.</strong> {item}
                            </div>""", unsafe_allow_html=True)
                    
                    # Penjelasan
                    st.markdown("#### 💬 Penjelasan")
                    st.markdown(f"""
                    <div style="background:rgba(37,99,235,0.15);
                    border:1px solid rgba(37,99,235,0.3);
                    border-radius:10px;padding:1rem;color:#BFDBFE;">
                    {hasil.get("penjelasan_awam", "-")}
                    </div>""", unsafe_allow_html=True)
                    
                    # Rekomendasi
                    rekomendasi = hasil.get("rekomendasi_tindakan", [])
                    if rekomendasi:
                        st.markdown("#### 📋 Rekomendasi Tindakan")
                        for item in rekomendasi:
                            if "jangan" in item.lower():
                                st.markdown(f"""
                                <div style="background:rgba(220,38,38,0.1);
                                border-radius:8px;padding:0.5rem 1rem;
                                margin:0.3rem 0;color:#FCA5A5;">
                                ❌ {item}</div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="background:rgba(22,163,74,0.1);
                                border-radius:8px;padding:0.5rem 1rem;
                                margin:0.3rem 0;color:#86EFAC;">
                                ✅ {item}</div>""", unsafe_allow_html=True)
                    
                    # Kontak darurat
                    if status == "Berisiko Tinggi":
                        st.markdown("#### 📞 Kontak Resmi")
                        col_k1, col_k2 = st.columns(2)
                        with col_k1:
                            st.markdown("""
                            <div style="background:rgba(37,99,235,0.15);
                            border-radius:10px;padding:1rem;color:#BFDBFE;">
                            🏦 <b>BRI:</b> 14017<br>
                            🏦 <b>BCA:</b> 1500888<br>
                            🏦 <b>Mandiri:</b> 14000<br>
                            🏦 <b>BNI:</b> 1500046
                            </div>""", unsafe_allow_html=True)
                        with col_k2:
                            st.markdown("""
                            <div style="background:rgba(37,99,235,0.15);
                            border-radius:10px;padding:1rem;color:#BFDBFE;">
                            🌐 <b>Kominfo:</b> aduan.kominfo.go.id<br>
                            🌐 <b>Portal Aduan:</b> lapor.go.id<br>
                            🚔 <b>Polisi:</b> 110<br>
                            📱 <b>BSSN:</b> bssn.go.id
                            </div>""", unsafe_allow_html=True)
                    
                    # Disclaimer
                    st.markdown("""
                    <div class="disclaimer-box">
                    ℹ️ <b>Disclaimer:</b> Hasil ini adalah rekomendasi awal berbasis 
                    analisis AI dan bukan keputusan final. Verifikasi ke pihak resmi 
                    tetap sangat disarankan sebelum mengambil tindakan apapun.
                    </div>""", unsafe_allow_html=True)
                    
                    # Clear contoh
                    if "contoh_pesan" in st.session_state:
                        del st.session_state.contoh_pesan
                    
                    st.rerun()
                    
                except json.JSONDecodeError:
                    st.error("❌ Gagal memproses jawaban AI. Coba lagi.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # ── FOOTER ──
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;color:#475569;font-size:0.8rem;padding:1rem;">
        🛡️ SafeCheck AI · Maria Devi Aparilia · NIM 24110400032<br>
        Final Project AI01 — Artificial Intelligence · Sistem Informasi<br>
        <span style="color:#2563EB;">Powered by Google Gemini AI</span>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════
# ROUTING HALAMAN
# ════════════════════════════════════════
if not st.session_state.logged_in:
    if st.session_state.page == "register":
        halaman_register()
    else:
        halaman_login()
else:
    halaman_app()
