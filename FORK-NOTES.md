# Tentang salinan ini

Repo ini adalah salinan kerja dari **gtavi-claudecode** karya
[Bodila51](https://github.com/Bodila51) (MIT, © 2026 Bodila51), plus beberapa perbaikan dan
perkakas tambahan di mesin lokal.

Riwayat commit asli (9 commit, 2026-11-18) tetap utuh dan tercantum atas nama penulis aslinya.
Upstream `github.com/Bodila51/gtavi-claudecode` sudah tidak tersedia saat salinan ini dibuat,
jadi repo ini bukan GitHub fork resmi — hanya salinan dengan histori yang dipertahankan.

## Yang ditambahkan di sini

| Path | Isi |
|---|---|
| `scripts/moments.py` | patch: fallback VAD saat transkrip kosong + filter label efek suara (lihat `patches/`) |
| `tools/publish.py` | packager klip → `cover.jpg`, caption per platform, `queue.csv` |
| `clipdesk` | wrapper bash: menjalankan script dengan venv + folder kerja `desk/` |
| `SETUP.md` | status pemasangan, perintah harian, hasil uji, batasan |
| `patches/0001-moments-vad-fallback.patch` | diff patch di atas, untuk re-apply |
| `extras/99-clipdesk-fonts.conf` | alias fontconfig agar caption ASS tidak jatuh ke font tipis |
| `campaign-format.md` | format aturan kampanye yang dibaca `scripts/check.py` |

## Lisensi

Kode asli tetap MIT (lihat `LICENSE`). Tambahan di atas mengikuti lisensi yang sama.
Proyek ini tidak berafiliasi dengan Rockstar Games, Take-Two, Anthropic, atau penulis asli.
