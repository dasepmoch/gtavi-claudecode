# Setup GTA 6 Clip Desk — status nyata di mesin ini

Semua di bawah ini sudah dijalankan dan diverifikasi di `/home/dasepmoch/gta6-clip`, bukan estimasi.

## 1. Yang terpasang

| Komponen | Versi | Catatan |
|---|---|---|
| Ubuntu | 26.04 LTS | 4 core, 11 GB RAM, tanpa GPU NVIDIA |
| Python | 3.14.4 | di `.venv/` (venv lokal, bukan sistem) |
| ffmpeg / ffprobe | 8.0.1 | libass + libx264 tersedia |
| yt-dlp | 2026.10.26 | dipakai via `python -m yt_dlp` |
| faster-whisper | 1.2.1 | model `small`, int8 di CPU (462 MB di `~/.cache/huggingface`) |
| ctranslate2 | 4.9.0 | `cuda_devices = 0` → transkripsi jalan di CPU |
| opencv-python-headless | 5.1.0 | deteksi webcam (YuNet) |
| edge-tts / deep-translator | 7.3.1 / 1.11.4 | untuk klip 5 bahasa |
| numpy, requests, onnxruntime, truststore | — | dependensi pendukung |

Install ulang kalau perlu:

```bash
cd /home/dasepmoch/gta6-clip
python3 -m venv .venv
.venv/bin/pip install -r gtavi-claudecode/requirements.txt
```

## 2. Struktur folder

Repo ini sekarang berisi script asli **dan** perkakas tambahan, jadi dua layout sama-sama jalan:

```text
repo/  (mis. /home/dasepmoch/gta6-clip/gtavi-claudecode)
├── scripts/             13 script asli (moments.py sudah dipatch)
├── skills/              16 skill Claude Code
├── tools/publish.py     packager klip -> cover + caption per platform + queue.csv
├── clipdesk             wrapper: layout-aware, jalan dari repo root atau dari workspace
├── extras/              alias fontconfig untuk caption ASS
├── patches/             diff patch moments.py (untuk re-apply)
├── SETUP.md             dokumen ini
└── FORK-NOTES.md        status salinan + lisensi
```

Workspace (default `<root>/desk`, bisa dipindah lewat `CLIP_DESK_HOME`):

```text
desk/
├── jobs/<id>/           source.mp4, audio.wav, transcript.json, candidates.md, edits/
├── trends.md            hasil trend-radar
├── streams.md           hasil stream-finder
├── campaigns.md         daftar campaign (diisi manual dari halaman live)
├── scoreboard.csv       log performa posting
├── log.md
└── publish/             paket siap-posting + queue.csv
```

Wrapper mencari python di `<workspace>/.venv` lalu `<repo>/.venv`, dan script di
`scripts/` (repo root) atau `gtavi-claudecode/scripts` (clone di dalam workspace).

## 3. Perintah harian

```bash
cd /home/dasepmoch/gta6-clip

./clipdesk streams --query "gta 6"                  # siapa yang live + jumlah penonton
./clipdesk trends --query "gta 6" --hours 24        # video 24 jam terakhir, diurut views/jam
./clipdesk moments "<url youtube/vod>" --top 6      # unduh + transkrip + skor momen → candidates.md
./clipdesk cut jobs/<id> --pick 1 --layout blur \
    --hook "Nobody noticed this in GTA 6" --credit "@creator"
./clipdesk check jobs/<id>/edits/clip_1.mp4 --campaign campaigns.md
.venv/bin/python tools/publish.py jobs/<id>/edits/clip_1.mp4 \
    --platforms all --credit "@creator" --hook "Nobody noticed this"
```

Layout `cut.py`: `fill` (crop penuh), `blur` (video utuh + background blur, default), `facecam` (muka di atas), `react` (muka + game + judul; pakai `--title`, `--title-style box|outline`).

## 4. Bukti uji (semua dijalankan hari ini)

| Uji | Hasil |
|---|---|
| `streams.py` | 20+ stream GTA 6 live dari Twitch + YouTube, `caseoh_` ±93k penonton |
| `trends.py` | 11 video 24 jam terakhir, teratas 256k views/jam |
| `moments.py` (video ber-narasi) | 3 menit "Hardware Unboxed" → 612 kata, 4 kandidat, VAD normal |
| `moments.py` (gameplay musik) | "GameV" 9 menit → VAD kosong, fallback aktif, 14 kata, 6 kandidat |
| `cut.py` | output 1080x1920, 30 fps, 48 kHz, **−14.0 LUFS** (sesuai target) |
| burn-in caption | OCR frame: hook ("Stealing a HYDRA from the army"), caption, `clip: @GameV` terbaca |
| `check.py` | 6/6 PASS (resolusi, fps, audio, durasi, credit, banned terms) |
| `publish.py` | cover.jpg 1080x1920 + caption 4 platform + `queue.csv` |

Klip contoh yang dihasilkan: `desk/jobs/9gahxscaboe-4f09fc9f/edits/clip_4.mp4` (15 s, 10 MB)
dan paket postingnya di `desk/publish/2026-11-19-stealing-a-hydra-from-the-army/`.

Catatan dari uji nyata:
- Video gameplay murni (tanpa narasi) isinya musik + SFX; transkripnya tipis, jadi caption
  otomatis juga tipis. Untuk klip ber-caption padat, pilih sumber yang ada narasi/komentar.
- Caption ikut membakar kata kasar yang ada di audio ("fuck you!"). TikTok/IG bisa membatasi
  jangkauan klip seperti itu — pilih momen lain atau matikan caption (`--captions none`).
- `desk/jobs/` menyimpan `source.mp4` penuh (140 MB per video). Bersihkan dengan
  `rm -rf desk/jobs/<id>` atau `find desk/jobs -name 'source.mp4' -delete` setelah klip jadi.


## 5. Patch lokal (2 hal, wajib tahu)

**(a) `scripts/moments.py` — fallback VAD.** Tanpa patch ini, video gameplay yang penuh musik
menghasilkan transkrip **kosong** (`transcript.json` = `[]`), jadi caption tidak muncul.
Terbukti pada video uji: `vad_filter=True` → 0 kata; tanpa VAD → ada kata sungguhan.
Patch: kalau hasil VAD kosong, ulangi tanpa VAD lalu buang label efek suara
(`MUSIC`, `GUNFIRE`, `[Applause]`, …) dan segmen dengan `no_speech_prob ≥ 0.5`.

**(b) Font caption.** ASS-nya minta `Arial Black`; di Linux itu jatuh ke fallback reguler
(caption tipis). Sudah ditambahkan alias fontconfig di
`~/.config/fontconfig/conf.d/99-clipdesk-fonts.conf` (Arial Black → DejaVu Sans,
Arial → Liberation Sans). Hasil ukur: tinta caption naik 16.128 → 27.434 piksel (+70%).

Kembalikan ke asli: `cd gtavi-claudecode && git checkout scripts/moments.py` dan hapus file fontconfig itu.

## 6. Soal auto-upload

**Repo ini tidak punya auto-upload.** README-nya eksplisit: *"Nothing is uploaded automatically.
You approve every post."* Semua script berhenti di MP4 lokal. Jadi jawabannya:
tidak bisa "tinggal jalan" — perlu ditambahkan, dan tiap platform punya syarat sendiri (§7 di bawah).

Yang sudah disiapkan sebagai jembatan: `tools/publish.py` membuat satu folder per klip berisi
`clip.mp4`, `cover.jpg`, `caption_<platform>.txt`, `caption.txt`, `meta.json`, plus baris
`pending` di `publish/queue.csv`. Artinya uploader apa pun tinggal membaca queue itu.

## 7. Kalau mau benar-benar auto-upload

Semua jalur resmi butuh akun + kredensial kamu, bukan sekadar kode:

| Platform | Jalur resmi | Syarat | Catatan |
|---|---|---|---|
| YouTube Shorts | Data API v3 `videos.insert` | OAuth client (Google Cloud), verifikasi app | kuota 10.000/hari; 1 upload ≈ 1.600 unit → ±6 klip/hari gratis |
| TikTok | Content Posting API | app TikTok for Developers + audit | sebelum diaudit, post terkunci `SELF_ONLY` (private) |
| Instagram Reels | Graph API (container → publish) | akun Business/Creator + app Meta + review izin | butuh halaman FB terhubung |
| X | API v2 (media + tweet) | paket berbayar di atas free tier | free tier sangat terbatas |
| Whop / clip.tech | — | submit link manual di dashboard | tidak ada API publik untuk submit klip |

Risiko yang perlu kamu tahu: otomatisasi via browser bukan API resmi rawan ban akun;
credit wajib; klip streamer tanpa izin/campaign bisa kena takedown; judul clickbait palsu
melanggar aturan `rule-check` dan aturan platform.

## 8. Batasan yang tersisa

- `campaign-finder` tidak otomatis: halaman Whop/clip.tech berat JS dan sering di balik login → isi `campaigns.md` manual.
- Tanpa GPU: transkripsi ±3,5× lebih cepat dari realtime (video 9 menit ≈ 2,5–3 menit). Model `medium` bisa dicoba kalau akurasi kurang, tapi ±2× lebih lambat.
- Repo ini v0.1.0, 1 author, tanpa test/CI — anggap prototipe yang berfungsi, bukan produk.
- Semua angka pendapatan bergantung campaign; tidak ada jaminan.
