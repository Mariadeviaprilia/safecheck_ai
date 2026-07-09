import streamlit as st
import google.generativeai as genai
import json
import hashlib
import time
import logging
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

st.set_page_config(
    page_title="SafeCheck AI",
    page_icon="🛡️",
    layout="wide"
)

# ── LOGGING (Monitoring) ──
logging.basicConfig(filename="safecheck_log.txt", level=logging.INFO,
                     format="%(asctime)s - %(message)s")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #0F172A 100%) !important;
        min-height: 100vh;
    }
    .main-header {
        background: linear-gradient(135deg, #1B3A5C, #2563EB);
        padding: 2rem; border-radius: 16px; text-align: center;
        color: white; margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(37,99,235,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .auth-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px; padding: 2rem;
        backdrop-filter: blur(10px);
        max-width: 450px; margin: 0 auto;
    }
    .stat-card {
        background: #1E293B !important;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 1.2rem;
        text-align: center; color: white;
    }
    .history-item {
        background: #1E293B !important;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 0.8rem 1rem; margin: 0.4rem 0;
    }
    .disclaimer-box {
        background: #0F2D5C;
        border: 1px solid rgba(37,99,235,0.4);
        border-radius: 10px; padding: 1rem; margin-top: 1rem;
        font-size: 0.85rem; color: #FFFFFF;
    }
    .ref-box {
        background: #2E1065;
        border: 1px solid rgba(124,58,237,0.4);
        border-radius: 10px; padding: 1rem; margin-top: 0.5rem;
        font-size: 0.85rem; color: #FFFFFF;
    }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.95) !important;
        border: 1px solid rgba(37,99,235,0.5) !important;
        border-radius: 8px !important; color: #0F172A !important;
    }
    .stTextInput > div > div > input::placeholder { color: #94A3B8 !important; }
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.95) !important;
        border: 1px solid rgba(37,99,235,0.5) !important;
        border-radius: 8px !important; color: #0F172A !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        color: white !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8, #1E40AF) !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stSidebar"] {
        background: rgba(15,23,42,0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }
    div[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    div[data-testid="stSidebar"] h1,
    div[data-testid="stSidebar"] h2,
    div[data-testid="stSidebar"] h3 { color: white !important; }
    section[data-testid="stSidebar"] {
        background: #0F172A !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stAlert"] {
        background: #1E293B !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stAlert"] p {
        color: #FCD34D !important;
        font-weight: 600;
    }
    .sidebar-user {
        background: rgba(37,99,235,0.2);
        border: 1px solid rgba(37,99,235,0.4);
        border-radius: 10px; padding: 1rem;
        margin-bottom: 1rem; color: white; text-align: center;
    }
    h1, h2, h3, h4, h5 { color: white !important; }
    p, li { color: #CBD5E1 !important; }
    label { color: #E2E8F0 !important; }
    .stSpinner { color: white !important; }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] div {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ── SETUP GEMINI ──
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    llm = genai.GenerativeModel("gemini-2.5-flash-lite")
except Exception:
    st.error("❌ API Key tidak ditemukan.")
    st.stop()

# ── CUSTOM EMBEDDING FUNCTION ──
class CustomGeminiEF:
    def __call__(self, input):
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=input,
            task_type="retrieval_document"
        )
        embedding = result["embedding"]
        return embedding if isinstance(embedding[0], list) else [embedding]

    @staticmethod
    def name():
        return "custom_gemini_ef"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return CustomGeminiEF()

    def is_legacy(self):
        return False

# ── CHUNKING ──
def chunk_text(text, chunk_size=100, overlap=20):
    """Memecah teks jadi potongan kecil dengan overlap,
    supaya konteks antar potongan tidak terputus."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

# ── SETUP CHROMADB + RAG ──
@st.cache_resource
def setup_rag():
    try:
        df = pd.read_csv("dataset_scam.csv")
        client = chromadb.Client()

        ef = CustomGeminiEF()

        collection = client.get_or_create_collection(
            name="safecheck_db",
            embedding_function=ef
        )

        if collection.count() == 0:
            docs, metas, ids = [], [], []
            for i, row in df.iterrows():
                potongan = chunk_text(row["teks_pesan"])
                for j, chunk in enumerate(potongan):
                    docs.append(chunk)
                    metas.append({
                        "label": row["label"],
                        "penjelasan": row["penjelasan"],
                        "chunk_index": j,
                        "source_id": int(i)
                    })
                    ids.append(f"doc_{i}_chunk_{j}")
            collection.add(documents=docs, metadatas=metas, ids=ids)

        return collection, True
    except Exception as e:
        st.error(f"RAG gagal: {e}")
        return None, False

with st.spinner("🔄 Memuat database ancaman..."):
    collection, rag_ready = setup_rag()

# ── DATABASE USER ──
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

# ── HELPER ──
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def login_user(u, p):
    return u in st.session_state.users_db and \
           st.session_state.users_db[u]["password"] == hash_pw(p)

def register_user(u, p, n):
    if u in st.session_state.users_db: return False
    st.session_state.users_db[u] = {
        "password": hash_pw(p), "nama": n, "history": []
    }
    return True

def save_history(u, pesan, hasil):
    entry = {
        "pesan": pesan[:80] + "..." if len(pesan) > 80 else pesan,
        "status": hasil.get("status_risiko", "-"),
        "skor": hasil.get("skor_risiko", 0),
        "waktu": time.strftime("%d/%m/%Y %H:%M")
    }
    st.session_state.users_db[u]["history"].insert(0, entry)
    if len(st.session_state.users_db[u]["history"]) > 10:
        st.session_state.users_db[u]["history"] = \
            st.session_state.users_db[u]["history"][:10]
    logging.info(f"User={u} | Status={hasil.get('status_risiko')} | Skor={hasil.get('skor_risiko')}")

# ── COST CONTROL ──
MAX_ANALISIS_PER_SESI = 5

def cek_limit_analisis():
    if "jumlah_analisis" not in st.session_state:
        st.session_state.jumlah_analisis = 0
    return st.session_state.jumlah_analisis < MAX_ANALISIS_PER_SESI

# ── PROMPT MANAGEMENT ──
PROMPT_VERSION = "v1.2"
PROMPT_TEMPLATE = """
Kamu adalah Analis Keamanan Digital Senior spesialis mendeteksi penipuan digital di Indonesia.

PESAN YANG DIANALISIS:
"{pesan}"
{referensi}

INSTRUKSI:
- Gunakan referensi di atas untuk mendeteksi pola yang mirip
- Sebutkan indikator SPESIFIK dari teks pesan, bukan generik
- Gunakan bahasa sederhana untuk pengguna awam
- Jika tidak cukup bukti, tulis confidence_level "Rendah"
- Jangan menebak jika tidak ada bukti

Jawab HANYA dalam format JSON ini tanpa teks lain:
{{
    "status_risiko": "Berisiko Tinggi" atau "Perlu Waspada" atau "Aman",
    "skor_risiko": angka 0-100,
    "confidence_level": "Tinggi" atau "Sedang" atau "Rendah",
    "indikator_bahaya": ["indikator spesifik 1", "indikator spesifik 2"],
    "penjelasan_awam": "penjelasan 2-3 kalimat bahasa sederhana",
    "rekomendasi_tindakan": ["tindakan 1", "tindakan 2", "tindakan 3"]
}}
"""

# ── FUNGSI RAG + ANALISIS ──
def analisis_dengan_rag(pesan_user):
    referensi_konteks = ""
    sumber_referensi = []

    if rag_ready and collection:
        try:
            results = collection.query(
                query_texts=[pesan_user],
                n_results=3
            )
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            filtered = [(d, m) for d, m, dist in zip(docs, metas, distances) if dist < 1.2]

            if filtered:
                referensi_konteks = "\n\nREFERENSI DARI DATABASE ANCAMAN:\n"
                for i, (doc, meta) in enumerate(filtered, 1):
                    referensi_konteks += f"{i}. Contoh: '{doc}'\n"
                    referensi_konteks += f"   Label: {meta['label']}\n"
                    referensi_konteks += f"   Indikator: {meta['penjelasan']}\n"
                    sumber_referensi.append({
                        "contoh": doc[:60] + "...",
                        "label": meta["label"]
                    })
        except Exception as e:
            print(f"Query RAG gagal: {e}")
            referensi_konteks = ""

    prompt = PROMPT_TEMPLATE.format(pesan=pesan_user, referensi=referensi_konteks)

    response = llm.generate_content(prompt)
    teks = response.text.strip()
    if "```" in teks:
        teks = teks.split("```")[1]
        if teks.startswith("json"):
            teks = teks[4:]

    hasil = json.loads(teks.strip())
    hasil["_sumber_referensi"] = sumber_referensi
    return hasil

# ════════════════════════════
# HALAMAN LOGIN
# ════════════════════════════
def halaman_login():
    st.markdown("""
    <div class="main-header">
        <h1 style="font-size:2.5rem;margin:0;">🛡️ SafeCheck AI</h1>
        <p style="opacity:0.9;margin:0.5rem 0 0;">
        Deteksi Penipuan Digital Sebelum Terlambat</p>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("### Masuk ke Akun")
        username = st.text_input("Username", placeholder="Masukkan username")
        password = st.text_input("Password", type="password",
                                  placeholder="Masukkan password")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Login", use_container_width=True):
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.page = "app"
                    st.rerun()
                else:
                    st.error("❌ Username atau password salah!")
        with col_b:
            if st.button("Daftar", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
        st.markdown("""
        <p style="text-align:center;font-size:0.8rem;color:#64748B;margin-top:1rem;">
        Demo: <b style="color:#93C5FD;">demo</b> / 
        <b style="color:#93C5FD;">demo123</b></p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════
# HALAMAN REGISTER
# ════════════════════════════
def halaman_register():
    st.markdown("""
    <div class="main-header">
        <h1 style="font-size:2.5rem;margin:0;">🛡️ SafeCheck AI</h1>
        <p style="opacity:0.9;margin:0.5rem 0 0;">Buat Akun Baru</p>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("### Daftar Akun Baru")
        nama = st.text_input("Nama Lengkap", placeholder="Nama lengkap kamu")
        username = st.text_input("Username", placeholder="Buat username unik")
        password = st.text_input("Password", type="password",
                                  placeholder="Min. 6 karakter")
        password2 = st.text_input("Konfirmasi Password", type="password",
                                   placeholder="Ulangi password")
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
                    st.success("✅ Akun berhasil dibuat!")
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

# ════════════════════════════
# HALAMAN UTAMA APP
# ════════════════════════════
def halaman_app():
    user_data = st.session_state.users_db[st.session_state.current_user]
    nama_user = user_data["nama"]
    history = user_data["history"]

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-user">
            <div style="font-size:2rem;">👤</div>
            <div style="font-weight:600;font-size:1rem;color:white !important;">
            {nama_user}</div>
            <div style="font-size:0.8rem;color:#93C5FD !important;">
            @{st.session_state.current_user}</div>
        </div>""", unsafe_allow_html=True)

        if rag_ready:
            st.success("✅ Database RAG aktif")
        else:
            st.warning("⚠️ Mode tanpa RAG")

        total = len(history)
        high = sum(1 for h in history if h["status"] == "Berisiko Tinggi")

        st.markdown("#### 📊 Statistik")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.5rem;font-weight:700;
                color:#60A5FA !important;">{total}</div>
                <div style="font-size:0.7rem;color:#94A3B8 !important;">
                Total Cek</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.5rem;font-weight:700;
                color:#F87171 !important;">{high}</div>
                <div style="font-size:0.7rem;color:#94A3B8 !important;">
                Bahaya</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Riwayat")
        if history:
            for h in history[:5]:
                e = "🔴" if h["status"]=="Berisiko Tinggi" \
                    else "🟡" if h["status"]=="Perlu Waspada" else "🟢"
                st.markdown(f"""
                <div class="history-item">
                    <div style="font-size:0.7rem;color:#94A3B8 !important;">
                    {h['waktu']}</div>
                    <div style="font-size:0.8rem;color:#CBD5E1 !important;">
                    {e} {h['pesan'][:35]}...</div>
                    <div style="font-size:0.75rem;color:#60A5FA !important;">
                    Skor: {h['skor']}/100</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color:#64748B !important;font-size:0.85rem;
            text-align:center;">Belum ada riwayat</p>
            """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.page = "login"
            st.rerun()

    # ── KONTEN UTAMA ──
    st.markdown("""
    <div class="main-header">
        <h1 style="font-size:2rem;margin:0;">🛡️ SafeCheck AI</h1>
        <p style="opacity:0.9;margin:0.3rem 0 0;">
        Deteksi Penipuan Digital Sebelum Terlambat</p>
        <small style="opacity:0.7;">
        by Maria Devi Aparilia — Final Project AI01</small>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"### 👋 Halo, {nama_user}!")
    st.markdown(
        "Paste pesan, SMS, email, atau URL mencurigakan "
        "di bawah ini untuk dianalisis."
    )

    pesan_input = st.text_area(
        label="pesan",
        placeholder='Contoh: "Selamat! Nomor Anda terpilih memenangkan '
                    'hadiah Rp50.000.000 dari BRI. Klik bit.ly/xxx..."',
        height=130,
        label_visibility="collapsed",
        key="input_pesan"
    )

    with st.expander("Coba contoh pesan"):
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔴 Scam BRI", use_container_width=True):
                st.session_state.contoh = (
                    "Selamat! Nomor Anda terpilih memenangkan hadiah "
                    "Rp50.000.000 dari BRI. Klik bit.ly/xxx untuk klaim "
                    "hadiah sebelum 24 jam. Hubungi CS: 0812-xxxx"
                )
                st.rerun()
        with c2:
            if st.button("🟡 Phishing", use_container_width=True):
                st.session_state.contoh = (
                    "Halo, ini dari tim IT. Tolong konfirmasi akun Anda "
                    "dengan klik link berikut untuk keamanan sistem."
                )
                st.rerun()
        with c3:
            if st.button("🟢 Aman", use_container_width=True):
                st.session_state.contoh = (
                    "Halo! Pengingat dari BCA bahwa tagihan kartu kredit "
                    "Anda jatuh tempo tanggal 25. Hubungi 1500888."
                )
                st.rerun()

    if "contoh" in st.session_state:
        pesan_input = st.session_state.contoh
        st.info(f"📋 *{pesan_input[:70]}...*")

    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        tombol = st.button("Analisis Sekarang",
                           type="primary", use_container_width=True)

    if tombol:
        if "contoh" in st.session_state:
            pesan_input = st.session_state.contoh

        if not cek_limit_analisis():
            st.error(f"⚠️ Batas {MAX_ANALISIS_PER_SESI} analisis per sesi tercapai. Muat ulang halaman untuk mulai sesi baru (mencegah pemborosan kuota API).")
        elif not pesan_input.strip():
            st.warning("⚠️ Masukkan pesan terlebih dahulu!")
        else:
            with st.spinner("🔍 SafeCheck AI menganalisis dengan RAG..."):
                try:
                    hasil = analisis_dengan_rag(pesan_input)
                    save_history(
                        st.session_state.current_user, pesan_input, hasil
                    )
                    st.session_state.jumlah_analisis += 1

                    status = hasil.get("status_risiko", "Tidak diketahui")
                    skor = hasil.get("skor_risiko", 0)
                    conf = hasil.get("confidence_level", "Sedang")
                    refs = hasil.get("_sumber_referensi", [])

                    st.markdown("---")
                    st.markdown("### Hasil Analisis")

                    if status == "Berisiko Tinggi":
                        e, w = "🔴", "#F87171"
                    elif status == "Perlu Waspada":
                        e, w = "🟡", "#FCD34D"
                    else:
                        e, w = "🟢", "#4ADE80"

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div style="font-size:1.8rem;">{e}</div>
                            <div style="font-size:1rem;font-weight:700;
                            color:{w} !important;">{status}</div>
                            <div style="font-size:0.7rem;
                            color:#94A3B8 !important;">Status</div>
                        </div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div style="font-size:1.8rem;">📊</div>
                            <div style="font-size:1rem;font-weight:700;
                            color:{w} !important;">{skor}/100</div>
                            <div style="font-size:0.7rem;
                            color:#94A3B8 !important;">Skor Risiko</div>
                        </div>""", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div style="font-size:1.8rem;">🎯</div>
                            <div style="font-size:1rem;font-weight:700;
                            color:#60A5FA !important;">{conf}</div>
                            <div style="font-size:0.7rem;
                            color:#94A3B8 !important;">Keyakinan AI</div>
                        </div>""", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Indikator
                    indikator = hasil.get("indikator_bahaya", [])
                    if indikator:
                        st.markdown("#### Indikator Bahaya")
                        for i, item in enumerate(indikator, 1):
                            st.markdown(f"""
                            <div style="background:#1E293B;
                            border-left:4px solid #DC2626;padding:0.5rem 1rem;
                            border-radius:6px;margin:0.3rem 0;
                            color:#FFFFFF !important;">
                            <b>{i}.</b> {item}</div>
                            """, unsafe_allow_html=True)

                    # Penjelasan
                    st.markdown("#### Penjelasan")
                    st.markdown(f"""
                    <div style="background:#1E293B;
                    border-left:4px solid #2563EB;border-radius:10px;
                    padding:1rem;color:#FFFFFF !important;">
                    {hasil.get("penjelasan_awam","-")}</div>
                    """, unsafe_allow_html=True)

                    # Rekomendasi
                    rekom = hasil.get("rekomendasi_tindakan", [])
                    if rekom:
                        st.markdown("#### Rekomendasi Tindakan")
                        for item in rekom:
                            if "jangan" in item.lower():
                                st.markdown(f"""
                                <div style="background:#1E293B;
                                border-left:4px solid #DC2626;border-radius:8px;
                                margin:0.3rem 0;color:#FFFFFF !important;">
                                ❌ {item}</div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="background:#1E293B;
                                border-left:4px solid #16A34A;border-radius:8px;
                                margin:0.3rem 0;color:#FFFFFF !important;">
                                ✅ {item}</div>""", unsafe_allow_html=True)

                    # Referensi RAG
                    if refs:
                        st.markdown("#### Referensi dari Database Ancaman")
                        st.markdown("""
                        <div class="ref-box">
                        <b>SafeCheck AI mencocokkan pesan ini dengan 
                        database ancaman siber:</b><br>
                        """, unsafe_allow_html=True)
                        for r in refs:
                            badge = "🔴 SCAM/PHISHING" \
                                if r["label"] != "aman" else "🟢 AMAN"
                            st.markdown(f"""
                            <div style="margin:0.3rem 0;
                            color:#FFFFFF !important;">
                            {badge} — <i>"{r['contoh']}"</i></div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # Kontak darurat
                    if status == "Berisiko Tinggi":
                        st.markdown("#### 📞 Kontak Resmi")
                        ca, cb = st.columns(2)
                        with ca:
                            st.markdown("""
                            <div style="background:#1E293B;
                            border-left:4px solid #2563EB;border-radius:10px;padding:1rem;
                            color:#FFFFFF !important;">
                            🏦 <b>BRI:</b> 14017<br>
                            🏦 <b>BCA:</b> 1500888<br>
                            🏦 <b>Mandiri:</b> 14000<br>
                            🏦 <b>BNI:</b> 1500046
                            </div>""", unsafe_allow_html=True)
                        with cb:
                            st.markdown("""
                            <div style="background:#1E293B;
                            border-left:4px solid #2563EB;border-radius:10px;padding:1rem;
                            color:#FFFFFF !important;">
                            🌐 Kominfo: aduan.kominfo.go.id<br>
                            🌐 Lapor: lapor.go.id<br>
                            🚔 Polisi: 110<br>
                            🛡️ BSSN: bssn.go.id
                            </div>""", unsafe_allow_html=True)

                    # Disclaimer
                    st.markdown("""
                    <div class="disclaimer-box">
                    ℹ️ <b>Disclaimer:</b> Hasil ini adalah rekomendasi awal 
                    berbasis analisis AI + database ancaman. Bukan keputusan 
                    final. Verifikasi ke pihak resmi tetap disarankan.
                    </div>""", unsafe_allow_html=True)

                    if "contoh" in st.session_state:
                        del st.session_state.contoh

                except json.JSONDecodeError:
                    st.error("❌ Gagal memproses. Coba lagi.")
                except Exception as ex:
                    st.error(f"❌ Error: {str(ex)}")

    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center;color:#475569;font-size:0.8rem;">
        🛡️ SafeCheck AI · Maria Devi Aparilia · NIM 24110400032<br>
        Final Project AI01 · Powered by Gemini AI + ChromaDB RAG · Prompt {PROMPT_VERSION}
    </div>""", unsafe_allow_html=True)

# ── ROUTING ──
if not st.session_state.logged_in:
    if st.session_state.page == "register":
        halaman_register()
    else:
        halaman_login()
else:
    halaman_app()
