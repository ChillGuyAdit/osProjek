"""
database.py - Setup Database SQLite dengan SQLAlchemy
=====================================================

Database di sini berfungsi sebagai PERSISTENT STORAGE untuk:
- Resource Table (tabel dosen, ruang) = menyimpan daftar resource yang tersedia
- Process Table (tabel sidang)        = menyimpan daftar proses dan statusnya
- Allocation Table (relasi sidang-dosen) = mencatat alokasi resource ke proses

Menggunakan SQLite sebagai database ringan yang sesuai untuk demo.
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Table, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from models import StatusSidang

# ============================================================
# Konfigurasi Database
# ============================================================
DATABASE_URL = "sqlite:///./sidang_scheduler.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Diperlukan untuk SQLite + FastAPI
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================
# Tabel Asosiasi Many-to-Many: Sidang <-> Dosen
# Analogi: Allocation Matrix dalam Banker's Algorithm
# Mencatat dosen mana saja yang dialokasikan untuk sidang tertentu
# ============================================================
sidang_dosen_table = Table(
    "sidang_dosen",
    Base.metadata,
    Column("sidang_id", Integer, ForeignKey("sidang.id"), primary_key=True),
    Column("dosen_id", Integer, ForeignKey("dosen.id"), primary_key=True),
)


# ============================================================
# Model SQLAlchemy - Tabel Dosen (Resource)
# ============================================================
class DosenDB(Base):
    """
    Tabel Dosen - Merepresentasikan RESOURCE dalam sistem.
    Setiap dosen adalah resource yang bisa di-request oleh proses (sidang).
    """
    __tablename__ = "dosen"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nama = Column(String(100), nullable=False)

    # Relasi ke sidang (resource -> proses yang menggunakan resource ini)
    sidang_list = relationship(
        "SidangDB", secondary=sidang_dosen_table, back_populates="dosen_penguji"
    )


# ============================================================
# Model SQLAlchemy - Tabel Ruang (Resource)
# ============================================================
class RuangDB(Base):
    """
    Tabel Ruang - Merepresentasikan RESOURCE bertipe ruangan.
    Hanya satu proses (sidang) yang boleh menggunakan ruang pada satu waktu
    (prinsip Mutual Exclusion).
    """
    __tablename__ = "ruang"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nama = Column(String(100), nullable=False)

    # Relasi ke sidang
    sidang_list = relationship("SidangDB", back_populates="ruang")


# ============================================================
# Model SQLAlchemy - Tabel Sidang (Process)
# ============================================================
class SidangDB(Base):
    """
    Tabel Sidang - Merepresentasikan PROCESS dalam sistem.
    Setiap sidang adalah proses yang membutuhkan alokasi beberapa resource
    (dosen + ruang) pada slot waktu tertentu.

    Status merepresentasikan state proses:
    - PENDING    = Ready (menunggu alokasi)
    - TERJADWAL  = Running (resource berhasil dialokasikan)
    - GAGAL      = Blocked (konflik resource / deadlock avoidance)
    """
    __tablename__ = "sidang"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nama_mahasiswa = Column(String(200), nullable=False)
    ruang_id = Column(Integer, ForeignKey("ruang.id"), nullable=False)
    waktu_mulai = Column(DateTime, nullable=False)
    waktu_selesai = Column(DateTime, nullable=False)
    status = Column(SAEnum(StatusSidang), default=StatusSidang.PENDING, nullable=False)

    # Relasi
    ruang = relationship("RuangDB", back_populates="sidang_list")
    dosen_penguji = relationship(
        "DosenDB", secondary=sidang_dosen_table, back_populates="sidang_list"
    )


# ============================================================
# Fungsi Inisialisasi Database
# ============================================================
def init_db():
    """Membuat semua tabel di database jika belum ada."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency untuk mendapatkan session database.
    Menggunakan pola context manager agar session selalu ditutup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
