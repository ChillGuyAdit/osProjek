/**
 * script.js - Frontend Logic (Fetch API Only, No Business Logic)
 * ==============================================================
 *
 * File ini HANYA bertugas:
 * 1. Mengirim request ke backend via fetch()
 * 2. Menampilkan response dari backend ke UI
 *
 * Semua business logic (cek konflik, penjadwalan, dll) ada di BACKEND.
 * Frontend hanya sebagai "user interface" / "shell" dalam analogi OS.
 */

// ============================================================
// KONFIGURASI
// ============================================================
const API_BASE = "http://127.0.0.1:8000";


// ============================================================
// UTILITAS
// ============================================================

/**
 * Menampilkan toast notification
 */
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icons = {
        success: "✅",
        error: "❌",
        info: "ℹ️",
    };

    toast.innerHTML = `<span>${icons[type] || "ℹ️"}</span><span>${message}</span>`;
    container.appendChild(toast);

    // Hapus toast setelah animasi selesai
    setTimeout(() => toast.remove(), 4000);
}

/**
 * Format datetime untuk tampilan
 */
function formatDateTime(isoString) {
    const date = new Date(isoString);
    const options = {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    };
    return date.toLocaleDateString("id-ID", options);
}

/**
 * Format waktu saja (HH:MM)
 */
function formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", hour12: false });
}


// ============================================================
// NAVIGASI TAB
// ============================================================
document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        // Deactivate semua tab
        document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".section").forEach((s) => s.classList.remove("active"));

        // Activate tab yang diklik
        btn.classList.add("active");
        const targetId = btn.dataset.tab;
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
            targetSection.classList.add("active");
        }

        // Refresh data jadwal ketika tab jadwal dibuka
        if (targetId === "jadwal-section") {
            fetchJadwal();
        }
    });
});


// ============================================================
// FETCH DATA: DOSEN (Resource)
// ============================================================
async function fetchDosen() {
    try {
        const response = await fetch(`${API_BASE}/dosen`);
        if (!response.ok) throw new Error("Gagal memuat data dosen");
        const dosenList = await response.json();

        const container = document.getElementById("dosen-checkboxes");
        if (dosenList.length === 0) {
            container.innerHTML = '<div class="loading-placeholder">Belum ada data dosen.</div>';
            return;
        }

        container.innerHTML = dosenList
            .map(
                (dosen) => `
                <div class="checkbox-item">
                    <input type="checkbox" id="dosen-${dosen.id}" name="dosen_penguji" value="${dosen.id}">
                    <label for="dosen-${dosen.id}">${dosen.nama}</label>
                </div>
            `
            )
            .join("");
    } catch (error) {
        console.error("Error fetching dosen:", error);
        document.getElementById("dosen-checkboxes").innerHTML =
            '<div class="loading-placeholder" style="color: #ef4444;">Gagal memuat data dosen. Pastikan backend berjalan.</div>';
    }
}


// ============================================================
// FETCH DATA: RUANG (Resource)
// ============================================================
async function fetchRuang() {
    try {
        const response = await fetch(`${API_BASE}/ruang`);
        if (!response.ok) throw new Error("Gagal memuat data ruang");
        const ruangList = await response.json();

        const select = document.getElementById("ruang_id");
        select.innerHTML = '<option value="">-- Pilih Ruang Sidang --</option>';

        ruangList.forEach((ruang) => {
            const option = document.createElement("option");
            option.value = ruang.id;
            option.textContent = ruang.nama;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Error fetching ruang:", error);
        const select = document.getElementById("ruang_id");
        select.innerHTML = '<option value="">Gagal memuat data ruang</option>';
    }
}


// ============================================================
// FETCH DATA: JADWAL SIDANG (Process Table)
// ============================================================
let currentFilter = "all";

async function fetchJadwal(statusFilter) {
    if (statusFilter !== undefined) {
        currentFilter = statusFilter;
    }

    try {
        let url = `${API_BASE}/jadwal`;
        if (currentFilter && currentFilter !== "all") {
            url += `?status=${currentFilter}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error("Gagal memuat jadwal");
        const jadwalList = await response.json();

        renderJadwalTable(jadwalList);
    } catch (error) {
        console.error("Error fetching jadwal:", error);
        const tbody = document.getElementById("jadwal-tbody");
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <p style="color: #ef4444;">Gagal memuat jadwal. Pastikan backend berjalan di ${API_BASE}</p>
                </td>
            </tr>
        `;
    }
}

/**
 * Render tabel jadwal sidang
 */
function renderJadwalTable(jadwalList) {
    const tbody = document.getElementById("jadwal-tbody");

    if (jadwalList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
                        <rect x="3" y="4" width="18" height="18" rx="2"/>
                        <line x1="3" y1="10" x2="21" y2="10"/>
                    </svg>
                    <p>Tidak ada jadwal sidang ditemukan.</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = jadwalList
        .map((sidang, index) => {
            const dosenChips = sidang.dosen_penguji
                .map((d) => `<span class="dosen-chip">${d.nama}</span>`)
                .join("");

            const statusClass = sidang.status.toLowerCase();
            const statusText = sidang.status;

            return `
                <tr>
                    <td style="color: var(--text-muted); font-weight: 600;">${index + 1}</td>
                    <td style="color: var(--text-primary); font-weight: 500;">${sidang.nama_mahasiswa}</td>
                    <td><div class="dosen-chips">${dosenChips}</div></td>
                    <td>${sidang.ruang.nama}</td>
                    <td>
                        <div style="font-size: 0.82rem;">
                            ${formatDateTime(sidang.waktu_mulai)}<br>
                            <span style="color: var(--text-muted);">s/d ${formatTime(sidang.waktu_selesai)}</span>
                        </div>
                    </td>
                    <td>
                        <span class="status-badge ${statusClass}">
                            <span class="status-dot status-${statusClass}"></span>
                            ${statusText}
                        </span>
                    </td>
                </tr>
            `;
        })
        .join("");
}


// ============================================================
// FILTER JADWAL
// ============================================================
document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        fetchJadwal(btn.dataset.status);
    });
});

// Tombol refresh
document.getElementById("btn-refresh").addEventListener("click", () => {
    fetchJadwal();
    showToast("Data jadwal diperbarui", "info");
});


// ============================================================
// SUBMIT FORM: AJUKAN SIDANG (Resource Request)
// ============================================================
document.getElementById("sidang-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const btn = document.getElementById("btn-ajukan");
    const resultContainer = document.getElementById("result-container");
    const resultContent = document.getElementById("result-content");

    // Ambil data form
    const namaMahasiswa = document.getElementById("nama_mahasiswa").value.trim();
    const ruangId = parseInt(document.getElementById("ruang_id").value);
    const waktuMulai = document.getElementById("waktu_mulai").value;
    const waktuSelesai = document.getElementById("waktu_selesai").value;

    // Ambil dosen yang dipilih (checkbox)
    const dosenCheckboxes = document.querySelectorAll('input[name="dosen_penguji"]:checked');
    const dosenIds = Array.from(dosenCheckboxes).map((cb) => parseInt(cb.value));

    // Validasi minimal
    if (dosenIds.length === 0) {
        showToast("Pilih minimal 1 dosen penguji!", "error");
        return;
    }

    if (!ruangId) {
        showToast("Pilih ruang sidang!", "error");
        return;
    }

    if (!waktuMulai || !waktuSelesai) {
        showToast("Isi waktu mulai dan waktu selesai!", "error");
        return;
    }

    if (new Date(waktuMulai) >= new Date(waktuSelesai)) {
        showToast("Waktu mulai harus lebih awal dari waktu selesai!", "error");
        return;
    }

    // Loading state
    btn.classList.add("loading");
    btn.disabled = true;
    btn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        Memproses...
    `;

    try {
        // Kirim request ke backend
        const response = await fetch(`${API_BASE}/sidang`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nama_mahasiswa: namaMahasiswa,
                dosen_penguji_ids: dosenIds,
                ruang_id: ruangId,
                waktu_mulai: waktuMulai + ":00",
                waktu_selesai: waktuSelesai + ":00",
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Terjadi kesalahan pada server");
        }

        // Tampilkan hasil
        resultContainer.classList.remove("hidden");

        if (data.status === "TERJADWAL") {
            // ====== BERHASIL ======
            showToast("Sidang berhasil dijadwalkan! ✨", "success");

            const dosenNames = data.dosen_penguji.map((d) => d.nama).join(", ");

            resultContent.innerHTML = `
                <div class="result-card success">
                    <h3>
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                        Sidang Berhasil Dijadwalkan!
                    </h3>
                    <div class="result-detail">
                        <div class="result-item">
                            <span class="label">Mahasiswa</span>
                            <span class="value">${data.nama_mahasiswa}</span>
                        </div>
                        <div class="result-item">
                            <span class="label">Status</span>
                            <span class="value"><span class="badge badge-success">TERJADWAL</span></span>
                        </div>
                        <div class="result-item">
                            <span class="label">Dosen Penguji</span>
                            <span class="value">${dosenNames}</span>
                        </div>
                        <div class="result-item">
                            <span class="label">Ruang</span>
                            <span class="value">${data.ruang.nama}</span>
                        </div>
                        <div class="result-item">
                            <span class="label">Waktu Mulai</span>
                            <span class="value">${formatDateTime(data.waktu_mulai)}</span>
                        </div>
                        <div class="result-item">
                            <span class="label">Waktu Selesai</span>
                            <span class="value">${formatTime(data.waktu_selesai)}</span>
                        </div>
                    </div>
                    <p style="font-size: 0.82rem; color: var(--accent-success);">
                        ✅ Resource (dosen + ruang) berhasil dialokasikan ke proses (sidang). State: RUNNING.
                    </p>
                </div>
            `;
        } else {
            // ====== GAGAL (KONFLIK) ======
            showToast("Sidang gagal dijadwalkan karena konflik resource!", "error");

            let konflikHTML = "";
            if (data.konflik && data.konflik.length > 0) {
                konflikHTML = `
                    <ul class="konflik-list">
                        ${data.konflik.map((k) => `<li>${k}</li>`).join("")}
                    </ul>
                `;
            }

            let alternatifHTML = "";
            if (data.slot_alternatif && data.slot_alternatif.length > 0) {
                alternatifHTML = `
                    <div class="alternatif-section">
                        <h4>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <polyline points="12 6 12 12 16 14"/>
                            </svg>
                            Saran Slot Alternatif (Resource Tersedia):
                        </h4>
                        <div class="alternatif-list">
                            ${data.slot_alternatif
                                .map(
                                    (slot) => `
                                <span class="alternatif-chip">
                                    📅 ${formatDateTime(slot.waktu_mulai)} - ${formatTime(slot.waktu_selesai)}
                                </span>
                            `
                                )
                                .join("")}
                        </div>
                    </div>
                `;
            }

            resultContent.innerHTML = `
                <div class="result-card error">
                    <h3>
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="15" y1="9" x2="9" y2="15"/>
                            <line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                        Sidang Gagal Dijadwalkan — Konflik Resource Terdeteksi!
                    </h3>
                    <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px;">
                        Proses (sidang) ditolak karena resource yang diminta sedang dialokasikan ke proses lain.
                        Ini adalah implementasi <strong>Deadlock Avoidance</strong> — sistem mendeteksi unsafe state.
                    </p>
                    ${konflikHTML}
                    ${alternatifHTML}
                </div>
            `;
        }

        // Scroll ke hasil
        resultContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (error) {
        console.error("Error submitting sidang:", error);
        showToast(error.message || "Terjadi kesalahan. Pastikan backend berjalan.", "error");

        resultContainer.classList.remove("hidden");
        resultContent.innerHTML = `
            <div class="result-card error">
                <h3>
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                    </svg>
                    Error
                </h3>
                <p style="font-size: 0.85rem; color: var(--text-secondary);">${error.message}</p>
            </div>
        `;
    } finally {
        // Reset tombol
        btn.classList.remove("loading");
        btn.disabled = false;
        btn.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 2L11 13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
            Ajukan Sidang
        `;
    }
});


// ============================================================
// SET DEFAULT WAKTU pada form
// ============================================================
function setDefaultWaktu() {
    const now = new Date();
    // Set ke besok jam 09:00
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);

    const selesai = new Date(tomorrow);
    selesai.setHours(10, 30, 0, 0);

    // Format ke datetime-local (YYYY-MM-DDTHH:MM)
    const formatForInput = (d) => {
        const pad = (n) => n.toString().padStart(2, "0");
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    };

    document.getElementById("waktu_mulai").value = formatForInput(tomorrow);
    document.getElementById("waktu_selesai").value = formatForInput(selesai);
}


// ============================================================
// INISIALISASI
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    fetchDosen();
    fetchRuang();
    fetchJadwal();
    setDefaultWaktu();
});
