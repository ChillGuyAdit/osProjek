"""
scheduler.py - Logika Penjadwalan & Deteksi Konflik
====================================================

Modul ini adalah INTI dari sistem penjadwalan yang menerapkan konsep OS:

1. cek_konflik()      = DEADLOCK AVOIDANCE / SINKRONISASI RESOURCE
   Sebelum mengalokasikan resource (dosen/ruang) ke proses (sidang),
   sistem memeriksa apakah alokasi tersebut akan menyebabkan konflik.
   Ini mirip dengan Banker's Algorithm yang memeriksa apakah state aman
   sebelum mengabulkan permintaan resource.

2. jadwalkan_sidang()  = RESOURCE ALLOCATION dengan SAFETY CHECK
   Jika cek_konflik() mengembalikan state aman (tidak ada konflik),
   maka resource dialokasikan ke proses. Jika tidak aman, proses ditolak
   dan sistem menyarankan slot alternatif.

3. cari_slot_alternatif() = PREEMPTIVE SCHEDULING SUGGESTION
   Ketika proses gagal mendapat resource, sistem mencari slot waktu
   alternatif terdekat di mana semua resource tersedia.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from database import SidangDB, DosenDB, RuangDB
from models import StatusSidang


def waktu_overlap(mulai_a: datetime, selesai_a: datetime,
                  mulai_b: datetime, selesai_b: datetime) -> bool:
    """
    Memeriksa apakah dua interval waktu saling overlap.
    Digunakan sebagai utility untuk deteksi konflik resource.

    Analogi OS: Memeriksa apakah dua proses membutuhkan resource
    yang sama pada time slice yang saling tumpang tindih.

    Dua interval overlap jika: mulai_a < selesai_b DAN mulai_b < selesai_a
    """
    return mulai_a < selesai_b and mulai_b < selesai_a


def cek_konflik(db: Session, dosen_ids: List[int], ruang_id: int,
                waktu_mulai: datetime, waktu_selesai: datetime,
                exclude_sidang_id: Optional[int] = None) -> List[str]:
    """
    ============================================================
    DEADLOCK AVOIDANCE / RESOURCE CONFLICT DETECTION
    ============================================================

    Fungsi ini mengimplementasikan konsep DEADLOCK AVOIDANCE dari OS.
    Sebelum resource (dosen/ruang) dialokasikan ke proses (sidang baru),
    sistem memeriksa apakah alokasi tersebut akan menyebabkan konflik.

    Mirip dengan Banker's Algorithm di OS:
    1. Periksa apakah resource yang di-request sedang dipakai proses lain
    2. Jika ya, tolak request (hindari deadlock)
    3. Jika tidak, izinkan alokasi (state aman)

    Juga menerapkan konsep MUTUAL EXCLUSION:
    - Satu dosen tidak boleh menguji dua sidang bersamaan
    - Satu ruang tidak boleh dipakai dua sidang bersamaan

    Parameter:
        db              : Database session
        dosen_ids       : List ID dosen yang di-request
        ruang_id        : ID ruang yang di-request
        waktu_mulai     : Waktu mulai yang di-request
        waktu_selesai   : Waktu selesai yang di-request
        exclude_sidang_id: ID sidang yang dikecualikan (untuk update)

    Return:
        List pesan konflik. Kosong jika tidak ada konflik (state aman).
    """
    konflik_list: List[str] = []

    # --------------------------------------------------------
    # 1. CEK KONFLIK DOSEN (Resource Type: Penguji)
    #    Mutual Exclusion: satu dosen hanya boleh di satu sidang per waktu
    # --------------------------------------------------------
    for dosen_id in dosen_ids:
        dosen = db.query(DosenDB).filter(DosenDB.id == dosen_id).first()
        if not dosen:
            konflik_list.append(f"Dosen dengan ID {dosen_id} tidak ditemukan dalam sistem.")
            continue

        # Cari sidang lain yang sudah TERJADWAL dan melibatkan dosen ini
        sidang_dosen = (
            db.query(SidangDB)
            .filter(SidangDB.dosen_penguji.any(DosenDB.id == dosen_id))
            .filter(SidangDB.status == StatusSidang.TERJADWAL)
        )

        if exclude_sidang_id:
            sidang_dosen = sidang_dosen.filter(SidangDB.id != exclude_sidang_id)

        for sidang_existing in sidang_dosen.all():
            if waktu_overlap(waktu_mulai, waktu_selesai,
                             sidang_existing.waktu_mulai, sidang_existing.waktu_selesai):
                konflik_list.append(
                    f"⚠️ KONFLIK DOSEN: {dosen.nama} sudah dijadwalkan menguji "
                    f"sidang '{sidang_existing.nama_mahasiswa}' "
                    f"pada {sidang_existing.waktu_mulai.strftime('%d/%m/%Y %H:%M')} - "
                    f"{sidang_existing.waktu_selesai.strftime('%H:%M')}. "
                    f"(Mutual Exclusion: Resource sedang digunakan proses lain)"
                )

    # --------------------------------------------------------
    # 2. CEK KONFLIK RUANG (Resource Type: Ruangan)
    #    Mutual Exclusion: satu ruang hanya boleh dipakai satu sidang per waktu
    # --------------------------------------------------------
    ruang = db.query(RuangDB).filter(RuangDB.id == ruang_id).first()
    if not ruang:
        konflik_list.append(f"Ruang dengan ID {ruang_id} tidak ditemukan dalam sistem.")
    else:
        sidang_ruang = (
            db.query(SidangDB)
            .filter(SidangDB.ruang_id == ruang_id)
            .filter(SidangDB.status == StatusSidang.TERJADWAL)
        )

        if exclude_sidang_id:
            sidang_ruang = sidang_ruang.filter(SidangDB.id != exclude_sidang_id)

        for sidang_existing in sidang_ruang.all():
            if waktu_overlap(waktu_mulai, waktu_selesai,
                             sidang_existing.waktu_mulai, sidang_existing.waktu_selesai):
                konflik_list.append(
                    f"⚠️ KONFLIK RUANG: {ruang.nama} sudah digunakan untuk "
                    f"sidang '{sidang_existing.nama_mahasiswa}' "
                    f"pada {sidang_existing.waktu_mulai.strftime('%d/%m/%Y %H:%M')} - "
                    f"{sidang_existing.waktu_selesai.strftime('%H:%M')}. "
                    f"(Mutual Exclusion: Critical section sedang diakses proses lain)"
                )

    return konflik_list


def cari_slot_alternatif(db: Session, dosen_ids: List[int], ruang_id: int,
                         waktu_mulai_asal: datetime,
                         durasi_menit: int = 90,
                         jumlah_saran: int = 3) -> List[dict]:
    """
    ============================================================
    ALTERNATIVE RESOURCE SCHEDULING / RECOVERY SUGGESTION
    ============================================================

    Ketika proses (sidang) gagal mendapatkan resource karena konflik,
    fungsi ini mencari slot waktu alternatif terdekat di mana semua
    resource (dosen + ruang) tersedia secara bersamaan.

    Analogi OS: Ketika request resource ditolak, OS menyarankan waktu
    lain di mana resource tersedia (preemptive scheduling hint).

    Algoritma:
    1. Mulai dari waktu asal yang diminta
    2. Geser slot waktu per 30 menit ke depan
    3. Untuk setiap slot, cek apakah semua resource kosong
    4. Kumpulkan hingga 'jumlah_saran' slot alternatif

    Parameter:
        db              : Database session
        dosen_ids       : List ID dosen penguji
        ruang_id        : ID ruang
        waktu_mulai_asal: Waktu mulai asal yang diminta (sebagai titik awal pencarian)
        durasi_menit    : Durasi sidang dalam menit (default 90)
        jumlah_saran    : Jumlah slot alternatif yang disarankan (default 3)

    Return:
        List dict berisi slot alternatif {waktu_mulai, waktu_selesai}
    """
    alternatif: List[dict] = []
    kandidat_waktu = waktu_mulai_asal

    # Cari dalam rentang 7 hari ke depan, geser per 30 menit
    batas_pencarian = waktu_mulai_asal + timedelta(days=7)

    while kandidat_waktu < batas_pencarian and len(alternatif) < jumlah_saran:
        kandidat_selesai = kandidat_waktu + timedelta(minutes=durasi_menit)

        # Hanya cari slot di jam kerja (08:00 - 17:00)
        if 8 <= kandidat_waktu.hour < 17 and kandidat_selesai.hour <= 17:
            konflik = cek_konflik(db, dosen_ids, ruang_id,
                                  kandidat_waktu, kandidat_selesai)
            if not konflik:
                alternatif.append({
                    "waktu_mulai": kandidat_waktu.isoformat(),
                    "waktu_selesai": kandidat_selesai.isoformat()
                })

        # Geser 30 menit ke depan
        kandidat_waktu += timedelta(minutes=30)

    return alternatif


def jadwalkan_sidang(db: Session, nama_mahasiswa: str, dosen_ids: List[int],
                     ruang_id: int, waktu_mulai: datetime,
                     waktu_selesai: datetime) -> Tuple[SidangDB, List[str], List[dict]]:
    """
    ============================================================
    RESOURCE ALLOCATION dengan SAFETY CHECK
    ============================================================

    Fungsi utama penjadwalan yang menggabungkan:
    1. Safety Check (cek_konflik) - Banker's Algorithm analogy
    2. Resource Allocation - mengalokasikan dosen+ruang ke sidang
    3. Recovery - jika gagal, cari slot alternatif

    Alur (mirip Resource Request Algorithm di OS):
    1. Proses (sidang) me-request resource (dosen + ruang)
    2. Sistem memeriksa apakah alokasi aman (cek_konflik)
    3a. Jika AMAN -> alokasikan resource, status = TERJADWAL
    3b. Jika TIDAK AMAN -> tolak request, status = GAGAL
    4. Jika GAGAL -> cari slot alternatif (recovery/rescheduling)

    Parameter:
        db              : Database session
        nama_mahasiswa  : Nama mahasiswa
        dosen_ids       : List ID dosen penguji
        ruang_id        : ID ruang
        waktu_mulai     : Waktu mulai sidang
        waktu_selesai   : Waktu selesai sidang

    Return:
        Tuple(SidangDB, List[str], List[dict])
        - Objek sidang yang dibuat
        - List pesan konflik (kosong jika berhasil)
        - List slot alternatif (kosong jika berhasil atau tidak ditemukan)
    """
    # --------------------------------------------------------
    # STEP 1: SAFETY CHECK - Cek apakah alokasi resource aman
    # (Analogi: Banker's Algorithm - cek safe state)
    # --------------------------------------------------------
    konflik_list = cek_konflik(db, dosen_ids, ruang_id, waktu_mulai, waktu_selesai)

    # Ambil objek dosen dari database
    dosen_objects = db.query(DosenDB).filter(DosenDB.id.in_(dosen_ids)).all()

    # Buat objek sidang baru
    sidang_baru = SidangDB(
        nama_mahasiswa=nama_mahasiswa,
        ruang_id=ruang_id,
        waktu_mulai=waktu_mulai,
        waktu_selesai=waktu_selesai,
    )

    alternatif: List[dict] = []

    if not konflik_list:
        # --------------------------------------------------------
        # STEP 2a: STATE AMAN - Alokasikan resource ke proses
        # Resource berhasil di-assign, proses masuk state RUNNING
        # --------------------------------------------------------
        sidang_baru.status = StatusSidang.TERJADWAL
        sidang_baru.dosen_penguji = dosen_objects
        db.add(sidang_baru)
        db.commit()
        db.refresh(sidang_baru)
    else:
        # --------------------------------------------------------
        # STEP 2b: STATE TIDAK AMAN - Tolak alokasi resource
        # Proses masuk state BLOCKED/GAGAL (deadlock avoidance)
        # --------------------------------------------------------
        sidang_baru.status = StatusSidang.GAGAL
        sidang_baru.dosen_penguji = dosen_objects
        db.add(sidang_baru)
        db.commit()
        db.refresh(sidang_baru)

        # --------------------------------------------------------
        # STEP 3: RECOVERY - Cari slot alternatif
        # Mirip rescheduling di OS ketika proses gagal mendapat resource
        # --------------------------------------------------------
        durasi = int((waktu_selesai - waktu_mulai).total_seconds() / 60)
        alternatif = cari_slot_alternatif(
            db, dosen_ids, ruang_id, waktu_mulai, durasi
        )

    return sidang_baru, konflik_list, alternatif
