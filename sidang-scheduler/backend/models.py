"""
models.py - Definisi Model Data (Analogi Entitas Sistem Operasi)
================================================================

Konsep Sistem Operasi yang diterapkan:
- Dosen & Ruang  = RESOURCE (sumber daya terbatas dalam OS)
  Seperti CPU, printer, atau memory yang harus dialokasikan ke proses.
- Sidang          = PROCESS (proses yang membutuhkan resource)
  Setiap sidang membutuhkan alokasi dosen (penguji) dan ruang secara bersamaan,
  mirip proses yang membutuhkan beberapa resource sekaligus.
- jadwal_terisi   = RESOURCE ALLOCATION TABLE
  Mencatat kapan resource sedang dialokasikan, mirip tabel alokasi di OS.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class StatusSidang(str, Enum):
    """
    Status sidang merepresentasikan STATE dari sebuah proses di OS:
    - PENDING    = Proses dalam antrian (Ready Queue)
    - TERJADWAL  = Proses berhasil mendapat alokasi resource (Running)
    - GAGAL      = Proses gagal mendapat resource karena konflik (Blocked/Deadlock)
    """
    PENDING = "PENDING"
    TERJADWAL = "TERJADWAL"
    GAGAL = "GAGAL"


@dataclass
class SlotWaktu:
    """
    Representasi slot waktu pemakaian resource.
    Mirip time quantum dalam penjadwalan CPU.
    """
    waktu_mulai: datetime
    waktu_selesai: datetime


@dataclass
class Dosen:
    """
    Dosen = Resource bertipe 'penguji'.
    Satu dosen bisa menguji banyak sidang, tetapi TIDAK BISA di waktu bersamaan.
    Analogi: Printer yang hanya bisa melayani satu job pada satu waktu (mutual exclusion).
    """
    id: Optional[int] = None
    nama: str = ""
    jadwal_terisi: List[SlotWaktu] = field(default_factory=list)


@dataclass
class Ruang:
    """
    Ruang = Resource bertipe 'ruangan'.
    Satu ruang hanya bisa digunakan satu sidang pada satu waktu.
    Analogi: Critical section yang hanya boleh diakses satu proses pada satu waktu.
    """
    id: Optional[int] = None
    nama: str = ""
    jadwal_terisi: List[SlotWaktu] = field(default_factory=list)


@dataclass
class Sidang:
    """
    Sidang = Process yang membutuhkan alokasi resource.
    Setiap sidang membutuhkan:
    - Minimal 1 dosen penguji (resource tipe 1)
    - 1 ruang sidang (resource tipe 2)
    - Slot waktu tertentu (time slice)

    Jika semua resource tersedia -> TERJADWAL (proses berjalan)
    Jika ada konflik -> GAGAL (proses di-block, analogi deadlock avoidance)
    """
    id: Optional[int] = None
    nama_mahasiswa: str = ""
    dosen_penguji_ids: List[int] = field(default_factory=list)
    ruang_id: Optional[int] = None
    waktu_mulai: Optional[datetime] = None
    waktu_selesai: Optional[datetime] = None
    status: StatusSidang = StatusSidang.PENDING
