# 📅 Sistem Penjadwalan Sidang Tugas Akhir Terotomasi

> Implementasi konsep **Sistem Operasi** (manajemen proses, penjadwalan resource, dan deadlock avoidance) ke dalam kasus nyata: penjadwalan sidang skripsi mahasiswa.

---

## 🎯 Latar Belakang

Sistem ini menganalogikan penjadwalan sidang skripsi dengan konsep-konsep inti Sistem Operasi:

| Konsep OS              | Analogi dalam Sistem                                 |
|------------------------|------------------------------------------------------|
| **Resource**           | Dosen penguji & Ruang sidang                         |
| **Process**            | Sidang mahasiswa yang membutuhkan resource            |
| **Mutual Exclusion**   | 1 dosen/ruang hanya bisa 1 sidang per waktu          |
| **Deadlock Avoidance** | Cek konflik sebelum alokasi (mirip Banker's Algorithm)|
| **Process State**      | PENDING → TERJADWAL (Running) / GAGAL (Blocked)      |
| **Recovery**           | Saran slot alternatif ketika sidang gagal dijadwalkan |

---

## 📁 Struktur Proyek

```
sidang-scheduler/
├── backend/
│   ├── models.py           # Dataclass: Dosen, Ruang, Sidang (+ analogi OS)
│   ├── scheduler.py        # Logika cek_konflik() dan jadwalkan_sidang()
│   ├── database.py         # Setup SQLite + SQLAlchemy (tabel + relasi)
│   ├── main.py             # FastAPI app + semua endpoint + seed data
│   └── requirements.txt    # Dependency Python
├── frontend/
│   ├── index.html          # Halaman utama (form + tabel + konsep OS)
│   ├── style.css           # Styling dark theme premium
│   └── script.js           # Fetch API ke backend (tanpa logic bisnis)
└── README.md               # Dokumentasi ini
```

---

## 🚀 Cara Install & Menjalankan

### Prasyarat
- **Python 3.8+** terinstall
- **pip** (package manager Python)
- **Browser modern** (Chrome, Firefox, Edge)

### 1. Clone / Download Proyek

```bash
cd sidang-scheduler
```

### 2. Buat Virtual Environment & Install Dependency

```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# macOS / Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dependency
pip install -r backend/requirements.txt
```

### 3. Jalankan Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend akan berjalan di **http://127.0.0.1:8000**

- 📖 Swagger UI (dokumentasi interaktif): http://127.0.0.1:8000/docs
- 📖 ReDoc (dokumentasi alternatif): http://127.0.0.1:8000/redoc

### 4. Buka Frontend

Buka file `frontend/index.html` langsung di browser, atau gunakan live server:

```bash
# Opsi 1: Buka langsung
open frontend/index.html          # macOS
# xdg-open frontend/index.html   # Linux
# start frontend/index.html      # Windows

# Opsi 2: Gunakan Python HTTP server
cd frontend
python -m http.server 5500
# Lalu buka http://localhost:5500
```

---

## 📡 API Endpoints

| Method | Endpoint             | Deskripsi                                     | Analogi OS              |
|--------|----------------------|-----------------------------------------------|--------------------------|
| GET    | `/`                  | Info sistem                                   | System info              |
| POST   | `/dosen`             | Tambah dosen baru                             | Add resource to pool     |
| GET    | `/dosen`             | Lihat semua dosen                             | List available resources |
| POST   | `/ruang`             | Tambah ruang baru                             | Add resource to pool     |
| GET    | `/ruang`             | Lihat semua ruang                             | List available resources |
| POST   | `/sidang`            | Ajukan sidang baru (cek konflik + jadwalkan)  | Resource request         |
| GET    | `/jadwal`            | Lihat semua jadwal sidang                     | Process table            |
| GET    | `/jadwal?status=X`   | Filter berdasarkan status                     | Filter process by state  |
| GET    | `/dosen/{id}/jadwal` | Lihat jadwal seorang dosen                    | Resource utilization     |
| GET    | `/docs`              | Swagger UI (dokumentasi interaktif)           | -                        |

---

## 🧪 Data Demo (Seed Data)

Saat backend pertama kali dijalankan, sistem otomatis mengisi data demo:

### Dosen (Resource Pool)
1. Dr. Budi Santoso, M.Kom.
2. Prof. Siti Rahayu, Ph.D.
3. Dr. Ahmad Fauzi, M.T.

### Ruang (Resource Pool)
1. Ruang Sidang A (Lt. 3)
2. Ruang Sidang B (Lt. 4)

### Sidang Contoh (Process)
| # | Mahasiswa                    | Dosen              | Ruang    | Waktu               | Status      |
|---|------------------------------|---------------------|----------|----------------------|-------------|
| 1 | Andi Pratama                 | Dr. Budi, Prof. Siti| Ruang A  | 01/10 09:00-10:30   | ✅ TERJADWAL |
| 2 | Budi Setiawan                | Dr. Ahmad           | Ruang B  | 01/10 09:00-10:30   | ✅ TERJADWAL |
| 3 | Citra Dewi (CONTOH BENTROK)  | Dr. Budi, Dr. Ahmad | Ruang A  | 01/10 09:30-11:00   | ❌ GAGAL     |

> **Sidang #3 sengaja bentrok** karena:
> - Dr. Budi sudah menguji sidang Andi di waktu yang overlap (konflik dosen)
> - Ruang A sudah dipakai sidang Andi di waktu yang overlap (konflik ruang)
>
> Ini mendemonstrasikan **Deadlock Avoidance** — sistem menolak alokasi resource yang akan menyebabkan konflik.

---

## 🧠 Konsep OS yang Diimplementasikan

### 1. Resource Management
Dosen dan ruang sidang = **resource terbatas** yang harus dialokasikan secara bijak ke proses (sidang).

### 2. Process Scheduling
Sidang mahasiswa = **proses** yang masuk antrian dan membutuhkan alokasi resource. Status proses: PENDING → TERJADWAL / GAGAL.

### 3. Deadlock Avoidance
Fungsi `cek_konflik()` di `scheduler.py` = implementasi **Banker's Algorithm**. Memeriksa apakah alokasi resource aman sebelum dieksekusi.

### 4. Mutual Exclusion
Satu dosen tidak boleh menguji dua sidang bersamaan. Satu ruang tidak boleh dipakai dua sidang bersamaan. = **Critical section protection**.

### 5. Recovery & Rescheduling
Ketika sidang gagal, fungsi `cari_slot_alternatif()` menyarankan waktu lain = **Recovery mechanism** di OS.

---

## 🛠 Teknologi

- **Backend**: Python 3, FastAPI, SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (Vanilla, Fetch API)
- **Database**: SQLite (file-based, ringan untuk demo)

---

## 📝 Catatan

- Database SQLite akan otomatis dibuat di `backend/sidang_scheduler.db` saat pertama kali dijalankan.
- Untuk mereset data, hapus file `sidang_scheduler.db` dan restart backend.
- Frontend terhubung ke backend di `http://127.0.0.1:8000`. Ubah variabel `API_BASE` di `script.js` jika backend berjalan di port lain.
