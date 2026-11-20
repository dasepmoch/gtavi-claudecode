# Format `campaigns.md`

`scripts/check.py` membaca seluruh file `campaigns.md` dengan regex, jadi:
jangan menaruh contoh angka/handle di `campaigns.md` — yang ditulis di sana
dianggap aturan untuk semua klip.

Di bawah bagian kampanye terkait, tulis baris seperti ini (pakai nilai asli):

```text
min_seconds: 15
max_seconds: 60
required_hashtags: #gta6 #gta6clips
required_mention: @streamer
```

- `min_seconds` / `max_seconds` → durasi klip harus di rentang itu.
- `required_hashtags` → semua tag wajib muncul di caption/hook saat check.
- `required_mention` → handle wajib muncul.
- Kalau file tidak ada, default check.py: 7–60 s, tanpa tag/handle wajib.

Baris tabel kampanye bebas formatnya; yang penting empat baris aturan di atas
ada di dekat kampanyenya.
