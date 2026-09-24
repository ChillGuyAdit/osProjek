"""
main.py - FastAPI Application & Endpoints
==========================================

Modul ini adalah ENTRY POINT dari sistem, menyediakan REST API endpoints
yang menjadi antarmuka antara pengguna (frontend) dan sistem penjadwalan.

Analogi OS:
- API Endpoints = System Calls
  Seperti system call di OS yang menjadi antarmuka antara user space
  dan kernel space, endpoint ini menjadi antarmuka antara frontend
  dan logika penjadwalan di backend.

- Seed Data = Initial Process & Resource Pool
  Data awal yang di-load saat sistem boot, mirip proses init dan
  daftar resource yang tersedia saat OS pertama kali berjalan.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import init_db, get_db, DosenDB, RuangDB, SidangDB
from models import StatusSidang
from scheduler import jadwalkan_sidang


# ============================================================
# Inisialisasi Aplikasi FastAPI
# ============================================================
app = FastAPI(
    title="Sistem Penjadwalan Sidang Tugas Akhir Terotomasi",
    description=(
        "Sistem penjadwalan sidang skripsi yang menerapkan konsep Sistem Operasi: "
        "manajemen proses, penjadwalan resource, dan deadlock avoidance. "
        "Dosen & ruang = resource terbatas, sidang = proses yang membutuhkan resource."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI otomatis dari FastAPI
    redoc_url="/redoc",     # ReDoc UI alternatif
)

# CORS middleware agar frontend bisa mengakses backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Pydantic Schemas (Request/Response Models)
# ============================================================
class DosenCreate(BaseModel):
    nama: str = Field(..., min_length=1, examples=["Dr. Budi Santoso"])


class DosenResponse(BaseModel):
    id: int
    nama: str

    class Config:
        from_attributes = True


class RuangCreate(BaseModel):
    nama: str = Field(..., min_length=1, examples=["Ruang Sidang A"])


class RuangResponse(BaseModel):
    id: int
    nama: str

    class Config:
        from_attributes = True


class SidangCreate(BaseModel):
    """
    Schema untuk request pembuatan sidang baru.
    Analogi: Resource Request dari proses ke OS.
    Proses harus menyebutkan resource apa saja yang dibutuhkan.
    """
    nama_mahasiswa: str = Field(..., min_length=1, examples=["Andi Pratama"])
    dosen_penguji_ids: List[int] = Field(..., min_length=1, examples=[[1, 2]])
    ruang_id: int = Field(..., examples=[1])
    waktu_mulai: datetime = Field(..., examples=["2026-10-01T09:00:00"])
    waktu_selesai: datetime = Field(..., examples=["2026-10-01T10:30:00"])


class SlotAlternatif(BaseModel):
    waktu_mulai: str
    waktu_selesai: str


class SidangResponse(BaseModel):
    id: int
    nama_mahasiswa: str
    dosen_penguji: List[DosenResponse]
    ruang: RuangResponse
    waktu_mulai: datetime
    waktu_selesai: datetime
    status: str
    konflik: Optional[List[str]] = None
    slot_alternatif: Optional[List[SlotAlternatif]] = None

    class Config:
        from_attributes = True


# ============================================================
# EVENT HANDLERS
# ============================================================
@app.on_event("startup")
def on_startup():
    """
    Dipanggil saat aplikasi pertama kali berjalan.
    Analogi OS: Boot sequence - inisialisasi resource dan proses awal.
    """
    init_db()
    seed_data()


def seed_data():
    """
    ============================================================
    SEED DATA - Data Dummy untuk Demo
    ============================================================

    Mengisi database dengan data awal:
    - 3 Dosen (resource pool)
    - 2 Ruang (resource pool)
    - 3 Sidang contoh, termasuk 1 skenario yang SENGAJA BENTROK

    Analogi OS: Initial resource pool dan proses-proses awal yang
    di-load saat sistem boot.
    """
    db = next(get_db())

    # Cek apakah sudah ada data (hindari duplikasi saat restart)
    if db.query(DosenDB).count() > 0:
        db.close()
        return

    # --- Tambah 3 Dosen (Resource Pool) ---
    dosen1 = DosenDB(nama="Dr. Budi Santoso, M.Kom.")
    dosen2 = DosenDB(nama="Prof. Siti Rahayu, Ph.D.")
    dosen3 = DosenDB(nama="Dr. Ahmad Fauzi, M.T.")
    db.add_all([dosen1, dosen2, dosen3])
    db.flush()

    # --- Tambah 2 Ruang (Resource Pool) ---
    ruang1 = RuangDB(nama="Ruang Sidang A (Lt. 3)")
    ruang2 = RuangDB(nama="Ruang Sidang B (Lt. 4)")
    db.add_all([ruang1, ruang2])
    db.flush()

    # --- Sidang 1: Normal, tidak bentrok ---
    sidang1 = SidangDB(
        nama_mahasiswa="Andi Pratama",
        ruang_id=ruang1.id,
        waktu_mulai=datetime(2026, 10, 1, 9, 0),
        waktu_selesai=datetime(2026, 10, 1, 10, 30),
        status=StatusSidang.TERJADWAL,
    )
    sidang1.dosen_penguji = [dosen1, dosen2]
    db.add(sidang1)

    # --- Sidang 2: Normal, ruang berbeda ---
    sidang2 = SidangDB(
        nama_mahasiswa="Budi Setiawan",
        ruang_id=ruang2.id,
        waktu_mulai=datetime(2026, 10, 1, 9, 0),
        waktu_selesai=datetime(2026, 10, 1, 10, 30),
        status=StatusSidang.TERJADWAL,
    )
    sidang2.dosen_penguji = [dosen3]
    db.add(sidang2)

    # --- Sidang 3: SENGAJA BENTROK dengan Sidang 1 ---
    # Dosen1 (Dr. Budi) sudah dijadwalkan di Sidang 1 pada jam yang sama.
    # Ruang1 juga sudah dipakai Sidang 1.
    # Ini akan menghasilkan status GAGAL karena konflik resource.
    sidang3 = SidangDB(
        nama_mahasiswa="Citra Dewi (CONTOH BENTROK)",
        ruang_id=ruang1.id,
        waktu_mulai=datetime(2026, 10, 1, 9, 30),
        waktu_selesai=datetime(2026, 10, 1, 11, 0),
        status=StatusSidang.GAGAL,
    )
    sidang3.dosen_penguji = [dosen1, dosen3]
    db.add(sidang3)

    db.commit()
    db.close()


# ============================================================
# ENDPOINTS - System Calls ke Kernel Penjadwalan
# ============================================================

# ----------------------------------------------------------
# POST /dosen - Tambah Resource Baru (Dosen)
# Analogi: Menambah resource baru ke resource pool OS
# ----------------------------------------------------------
@app.post("/dosen", response_model=DosenResponse, tags=["Dosen (Resource)"])
def tambah_dosen(data: DosenCreate, db: Session = Depends(get_db)):
    """
    Menambahkan dosen baru ke sistem.
    Analogi OS: Menambah resource baru ke pool (seperti menambah printer baru).
    """
    dosen_baru = DosenDB(nama=data.nama)
    db.add(dosen_baru)
    db.commit()
    db.refresh(dosen_baru)
    return dosen_baru


# ----------------------------------------------------------
# GET /dosen - Lihat Semua Dosen
# ----------------------------------------------------------
@app.get("/dosen", response_model=List[DosenResponse], tags=["Dosen (Resource)"])
def lihat_semua_dosen(db: Session = Depends(get_db)):
    """Menampilkan daftar semua dosen (resource) yang tersedia."""
    return db.query(DosenDB).all()


# ----------------------------------------------------------
# POST /ruang - Tambah Resource Baru (Ruang)
# Analogi: Menambah resource baru ke resource pool OS
# ----------------------------------------------------------
@app.post("/ruang", response_model=RuangResponse, tags=["Ruang (Resource)"])
def tambah_ruang(data: RuangCreate, db: Session = Depends(get_db)):
    """
    Menambahkan ruang sidang baru ke sistem.
    Analogi OS: Menambah resource baru ke pool (seperti menambah CPU core).
    """
    ruang_baru = RuangDB(nama=data.nama)
    db.add(ruang_baru)
    db.commit()
    db.refresh(ruang_baru)
    return ruang_baru


# ----------------------------------------------------------
# GET /ruang - Lihat Semua Ruang
# ----------------------------------------------------------
@app.get("/ruang", response_model=List[RuangResponse], tags=["Ruang (Resource)"])
def lihat_semua_ruang(db: Session = Depends(get_db)):
    """Menampilkan daftar semua ruang sidang (resource) yang tersedia."""
    return db.query(RuangDB).all()


# ----------------------------------------------------------
# POST /sidang - Ajukan Jadwal Sidang Baru
# Analogi: Process melakukan Resource Request ke OS
# Ini adalah system call utama yang menjalankan:
# 1. cek_konflik() -> Safety check (Banker's Algorithm)
# 2. jadwalkan_sidang() -> Resource allocation
# ----------------------------------------------------------
@app.post("/sidang", response_model=SidangResponse, tags=["Sidang (Process)"])
def ajukan_sidang(data: SidangCreate, db: Session = Depends(get_db)):
    """
    Mengajukan jadwal sidang baru.

    Alur (mirip Resource Request Algorithm di OS):
    1. Proses (mahasiswa) me-request resource (dosen + ruang + waktu)
    2. Sistem menjalankan safety check (cek_konflik)
    3. Jika aman -> resource dialokasikan (TERJADWAL)
    4. Jika tidak aman -> request ditolak (GAGAL) + saran slot alternatif
    """
    # Validasi waktu
    if data.waktu_mulai >= data.waktu_selesai:
        raise HTTPException(
            status_code=400,
            detail="Waktu mulai harus lebih awal dari waktu selesai."
        )

    # Jalankan resource allocation dengan safety check
    sidang, konflik, alternatif = jadwalkan_sidang(
        db=db,
        nama_mahasiswa=data.nama_mahasiswa,
        dosen_ids=data.dosen_penguji_ids,
        ruang_id=data.ruang_id,
        waktu_mulai=data.waktu_mulai,
        waktu_selesai=data.waktu_selesai,
    )

    # Bangun response
    response = SidangResponse(
        id=sidang.id,
        nama_mahasiswa=sidang.nama_mahasiswa,
        dosen_penguji=[DosenResponse.model_validate(d) for d in sidang.dosen_penguji],
        ruang=RuangResponse.model_validate(sidang.ruang),
        waktu_mulai=sidang.waktu_mulai,
        waktu_selesai=sidang.waktu_selesai,
        status=sidang.status.value,
        konflik=konflik if konflik else None,
        slot_alternatif=[SlotAlternatif(**s) for s in alternatif] if alternatif else None,
    )

    return response


# ----------------------------------------------------------
# GET /jadwal - Lihat Semua Jadwal Sidang
# Analogi: Melihat process table dan status semua proses
# ----------------------------------------------------------
@app.get("/jadwal", response_model=List[SidangResponse], tags=["Sidang (Process)"])
def lihat_semua_jadwal(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Menampilkan semua jadwal sidang (process table).
    Bisa difilter berdasarkan status: PENDING, TERJADWAL, GAGAL.
    """
    query = db.query(SidangDB)

    if status:
        try:
            status_enum = StatusSidang(status.upper())
            query = query.filter(SidangDB.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Status tidak valid. Gunakan: PENDING, TERJADWAL, atau GAGAL."
            )

    sidang_list = query.order_by(SidangDB.waktu_mulai).all()

    return [
        SidangResponse(
            id=s.id,
            nama_mahasiswa=s.nama_mahasiswa,
            dosen_penguji=[DosenResponse.model_validate(d) for d in s.dosen_penguji],
            ruang=RuangResponse.model_validate(s.ruang),
            waktu_mulai=s.waktu_mulai,
            waktu_selesai=s.waktu_selesai,
            status=s.status.value,
        )
        for s in sidang_list
    ]


# ----------------------------------------------------------
# GET /dosen/{id}/jadwal - Lihat Jadwal Seorang Dosen
# Analogi: Melihat resource utilization - proses apa saja yang
# sedang menggunakan resource tertentu
# ----------------------------------------------------------
@app.get("/dosen/{dosen_id}/jadwal", response_model=List[SidangResponse],
         tags=["Dosen (Resource)"])
def lihat_jadwal_dosen(dosen_id: int, db: Session = Depends(get_db)):
    """
    Menampilkan jadwal sidang untuk dosen tertentu.
    Analogi OS: Melihat daftar proses yang sedang menggunakan resource tertentu
    (resource utilization view).
    """
    dosen = db.query(DosenDB).filter(DosenDB.id == dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan.")

    sidang_list = (
        db.query(SidangDB)
        .filter(SidangDB.dosen_penguji.any(DosenDB.id == dosen_id))
        .filter(SidangDB.status == StatusSidang.TERJADWAL)
        .order_by(SidangDB.waktu_mulai)
        .all()
    )

    return [
        SidangResponse(
            id=s.id,
            nama_mahasiswa=s.nama_mahasiswa,
            dosen_penguji=[DosenResponse.model_validate(d) for d in s.dosen_penguji],
            ruang=RuangResponse.model_validate(s.ruang),
            waktu_mulai=s.waktu_mulai,
            waktu_selesai=s.waktu_selesai,
            status=s.status.value,
        )
        for s in sidang_list
    ]


# ============================================================
# Root endpoint
# ============================================================
@app.get("/", tags=["Info"])
def root():
    return {
        "nama_sistem": "Sistem Penjadwalan Sidang Tugas Akhir Terotomasi",
        "versi": "1.0.0",
        "konsep_os": {
            "resource": "Dosen & Ruang Sidang",
            "proses": "Sidang Mahasiswa",
            "deadlock_avoidance": "Cek konflik sebelum alokasi resource",
            "mutual_exclusion": "Satu resource hanya untuk satu proses per waktu",
        },
        "dokumentasi": "/docs",
    }
