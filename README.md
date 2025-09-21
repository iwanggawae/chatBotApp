# 🐱 Gemini Chatbot App (Streamlit)

Chatbot Streamlit berbasis Google Gemini dengan pilihan persona.

---

## ✨ Fitur
- Persona picker: Ahli Kucing, Ahli Strategi Bisnis, Ahli Periklanan, Ahli Gizi & Nutrisi, Ahli Manajemen Proyek, dan lainnya.
- Input **Gemini API Key** langsung di sidebar.
- Indikator hijau kecil saat koneksi API sukses.
- Statistik pemakaian: Requests, Prompt Tokens, Candidate Tokens, Total Tokens.

---

## ⚙️ Prasyarat
- Python 3.10+ (disarankan 3.12)
- Akun Google AI Studio (untuk Gemini API Key)

---

## 📦 Instalasi

### 1) Clone repositori
```
git clone https://github.com/iwanggawae/chatBotApp.git
cd chatBotApp
```
### 2) Buat virtual environment & instal dependensi
```
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```
### 3) (Opsional) Konfigurasi Streamlit (untuk Cloud Shell)
```
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml <<'CFG'
[server]
headless = true
address = "0.0.0.0"
port = 8080
enableCORS = false
enableXsrfProtection = false
fileWatcherType = "none"
runOnSave = false
CFG
```
---
### ▶️ Menjalankan Aplikasi
```
streamlit run app.py --server.port=8080 --server.address=0.0.0.0
```

