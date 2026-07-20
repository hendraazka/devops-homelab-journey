# Day 11 — Deploy Aplikasi ke Production (GitLab → Vercel)

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 10](../day-10-cicd-advanced/notes.md)

---

## ✅ Yang Dipelajari

- [x] Perbandingan opsi hosting: PaaS (Render/Railway), VPS + Terraform/Ansible, Kubernetes Cloud
- [x] Realita kebijakan free tier platform (verifikasi kartu, trial terbatas) yang sering berubah
- [x] Deploy aplikasi Flask ke **Vercel** menggunakan **GitLab** sebagai sumber repo (bukan GitHub)
- [x] Perbedaan model Vercel (serverless function) vs Docker container biasa
- [x] Restrukturisasi static files (`static/` → `public/`) sesuai requirement Vercel
- [x] Autentikasi GitLab dengan Personal Access Token (mirip PAT GitHub)
- [x] Membangun fitur pencarian kota dengan autocomplete dari data wilayah Indonesia (500+ kabupaten/kota)
- [x] Pola **backend sebagai proxy** untuk menghindari masalah CORS pada API pihak ketiga
- [x] Debugging sistematis: JavaScript syntax error, CSS layout overflow, data source yang tidak akurat
- [x] Custom desain UI dengan tema kontekstual (bukan dark-mode generik)
- [x] Live production URL: **https://prayer-time-app-two.vercel.app/**

---

## 🌐 Eksplorasi Opsi Hosting

Sebelum memilih Vercel, dieksplorasi 3 opsi:

| Opsi | Kompleksitas | Biaya | Relevansi ke skill DevOps |
|---|---|---|---|
| PaaS (Render/Railway) | Rendah | Gratis-murah, kebijakan berubah-ubah | Rendah |
| VPS + Terraform + Ansible | Menengah | ~$4-6/bulan | **Tinggi** — memakai seluruh skill Day 06-07 |
| Kubernetes Cloud | Tinggi | ~$12+/bulan | Tinggi — memakai skill Day 05, 09 |

**Catatan dari pengalaman nyata:** Render meminta verifikasi kartu kredit meski instance dipilih "Free" (kemungkinan kebijakan anti-fraud yang tidak selalu konsisten diberitahukan di awal). Railway ternyata sudah menghapus free tier permanennya sejak Agustus 2024, kini hanya trial credit terbatas. Ini pengingat penting: **kebijakan platform gratis sering berubah**, jangan berasumsi dari dokumentasi lama.

**Keputusan akhir:** mencoba **Vercel** dengan sumber repo di **GitLab** (bukan GitHub) — kombinasi yang jarang dibahas di tutorial kebanyakan, sekaligus latihan tambahan menggunakan platform Git selain GitHub.

---

## 🔀 Setup Repo Terpisah di GitLab

Aplikasi dipisahkan ke repo baru dan berdiri sendiri (terpisah dari `journal` yang berisi dokumentasi belajar):

```bash
mkdir -p ~/devops-lab/prayer-time-app-vercel
cp -r ~/devops-lab/journal/day-10-cicd-advanced/app/* ~/devops-lab/prayer-time-app-vercel/
cd ~/devops-lab/prayer-time-app-vercel
git init
git add .
git commit -m "initial commit for vercel deploy"
git branch -M main
git remote add origin https://gitlab.com/USERNAME/prayer-time-app.git
git push -u origin main
```

### Autentikasi GitLab

GitLab (seperti GitHub) tidak menerima password akun biasa untuk `git push` via HTTPS jika akun terautentikasi lewat SSO — solusinya sama dengan pola Personal Access Token yang sudah dipelajari di Day 03:

1. [gitlab.com/-/user_settings/personal_access_tokens](https://gitlab.com/-/user_settings/personal_access_tokens)
2. Scope minimal: `write_repository`
3. Gunakan token sebagai password saat `git push`

---

## 🧩 Penyesuaian untuk Vercel

Vercel memperlakukan Flask sebagai **serverless function**, bukan container yang berjalan terus — implikasinya:

- `Dockerfile` dan `gunicorn` yang sudah disiapkan di Day 10 **tidak dipakai** oleh Vercel
- Static file (CSS/JS) harus disajikan dari folder **`public/`**, bukan `static_folder` Flask standar

### Menyatukan Sumber Static File

Supaya tidak perlu sinkron manual dua folder (`static/` untuk lokal, `public/` untuk Vercel), Flask dikonfigurasi membaca langsung dari `public/`:

```python
app = Flask(__name__, static_folder='public', static_url_path='')
```

Referensi di `templates/index.html` diubah ke path absolut:
```html
<link rel="stylesheet" href="/css/style.css" />
<script src="/js/app.js"></script>
```

---

## 🔍 Fitur: Pencarian Kota dengan Autocomplete (500+ Kabupaten/Kota)

### Percobaan Awal: Fetch Langsung dari Browser (Gagal — CORS)

Percobaan pertama memanggil API publik data wilayah Indonesia langsung dari JavaScript sisi klien:
```js
fetch("https://emsifa.github.io/api-wilayah-indonesia/api/provinces.json")
```
Muncul error:
```
Access to fetch ... has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header
GET .../provinces.json net::ERR_FAILED 301 (Moved Permanently)
```
Root cause: endpoint tersebut redirect (301) ke domain custom yang tidak konsisten mengirim header CORS yang dibutuhkan browser.

### Solusi: Backend sebagai Proxy

Alih-alih fetch API pihak ketiga langsung dari browser, Flask bertindak sebagai perantara — fetch dilakukan **server-to-server** (tidak terkena aturan CORS sama sekali), lalu backend menyajikan data itu lewat endpoint miliknya sendiri:

```python
_cities_cache = {"data": None, "ts": 0}
CITIES_CACHE_TTL = 60 * 60 * 24  # 24 jam

@app.route("/api/all-cities")
def api_all_cities():
    now = time.time()
    if _cities_cache["data"] and (now - _cities_cache["ts"] < CITIES_CACHE_TTL):
        return jsonify(_cities_cache["data"])
    try:
        prov_res = requests.get("https://ihsaninh.github.io/wilayah-indonesia/provinces.json", timeout=10)
        provinces = prov_res.json()
        all_cities = []
        for p in provinces:
            reg_res = requests.get(
                f"https://ihsaninh.github.io/wilayah-indonesia/{p['id']}/regencies.json", timeout=10
            )
            for r in reg_res.json():
                all_cities.append({"name": r["value"], "province": p["value"]})
        # dedup & sort, simpan ke cache in-memory 24 jam
        ...
        return jsonify(deduped)
    except Exception:
        return jsonify([]), 502
```

Frontend (JavaScript) cukup memanggil endpoint **sesama origin**:
```js
const res = await fetch("/api/all-cities");
```
CORS tidak lagi menjadi masalah karena request browser hanya menuju domain sendiri.

**Insight penting:** ini pola arsitektur yang lebih tepat secara umum — proxy melalui backend sendiri untuk data pihak ketiga, bukan hanya solusi darurat untuk CORS. Manfaat tambahan: caching terpusat (semua pengguna berbagi cache 24 jam yang sama, mengurangi beban ke API eksternal).

### Caching di Sisi Klien

Hasil fetch juga disimpan di `localStorage` browser (TTL 24 jam) supaya kunjungan berikutnya tidak perlu fetch ulang sama sekali.

---

## 🔧 Troubleshooting yang Dialami

| Masalah | Penyebab | Solusi |
|---|---|---|
| CSS tidak ter-load di halaman deploy (`404`) | Path `href="/css/style.css"` tidak cocok dengan struktur folder Flask default saat testing lokal | Set `static_folder='public', static_url_path=''` di inisialisasi Flask agar satu struktur folder berlaku untuk lokal maupun Vercel |
| `Uncaught TypeError: Cannot read properties of null` | File JavaScript versi lama (mencari elemen `id="city"` yang sudah tidak ada di HTML) belum benar-benar tersimpan setelah proses edit sebelumnya | Tulis ulang seluruh file dengan `cat > file << 'EOF'` (bukan edit parsial berulang) untuk memastikan seluruh isi konsisten |
| `Uncaught SyntaxError: Missing catch or finally after try` | Kurung kurawal `{ }` tidak seimbang akibat beberapa kali edit manual sebagian pada blok `try {}` | Validasi sintaks dengan `node -c nama_file.js` **sebelum** menyimpan ke repo — mencegah bug sintaks sampai ke production |
| Fetch API wilayah gagal karena CORS + redirect 301 | Endpoint publik redirect ke domain custom tanpa header CORS yang konsisten | Pindahkan proses fetch ke backend Flask (server-to-server, tidak terkena CORS), frontend hanya memanggil endpoint sendiri |
| Nama kota di bagian bawah halaman selalu menampilkan "Jakarta" meski kota lain dipilih | Nama kota yang ditampilkan diambil dari `city` hasil parsing *timezone* API cuaca (banyak kota di sekitar Jakarta berbagi timezone `Asia/Jakarta`, sehingga API selalu mengembalikan "Jakarta") | Simpan nama kota yang **dipilih pengguna** di variabel terpisah (`currentCityLabel`) dan prioritaskan itu untuk ditampilkan, bukan hasil parsing dari API |
| Dropdown pencarian kota "bocor" keluar dari kotak (label provinsi tumpang tindih) | `float: right` pada elemen label provinsi tidak ter-*contain* dengan baik di lebar kotak yang sempit | Sederhanakan tampilan opsi dropdown — hapus label provinsi dari tampilan, cukup nama kota saja |
| Perubahan CSS terlihat di lokal tapi tidak muncul di production | Perubahan sempat hanya disimpan lokal untuk diuji, belum di-`git add`/`commit`/`push` ke GitLab | Selalu cek `git status` sebelum menyimpulkan ada masalah deployment — banyak "bug production" yang sebenarnya karena perubahan belum benar-benar terkirim |

---

## 🎨 Desain Ulang UI

![Tampilan Final Aplikasi Jadwal Sholat](./assets/prayer-app-final.png)

Desain awal (dark generik: background nyaris hitam + aksen kuning polos) diganti dengan tema yang lebih intentional bernama **"Serambi Masjid"**:

- Palet warna: indigo malam hangat + emas antik + teal lembut (bukan hitam pekat + kuning neon)
- Tipografi: font `Amiri` (serif dengan dukungan aksara Arab) untuk judul dan nama waktu sholat
- Kartu utama (`hero`) berbentuk lengkung asimetris menyerupai mihrab, dengan aksen bulat emas di puncaknya
- Pola geometris bintang Islami sebagai tekstur latar belakang yang subtle
- Transisi halus (`0.45s ease`) saat toggle dark/light mode, dengan penyesuaian kontras warna khusus untuk mode terang
- Sapaan bahasa Arab (السَّلَامُ عَلَيْكُمْ...) ditambahkan di header dengan ukuran dan warna yang disesuaikan agar tetap menonjol di kedua mode tema

---

## 📌 Insight Penting

- Kebijakan free tier platform hosting berubah-ubah — jangan berasumsi dari dokumentasi/tutorial lama, selalu verifikasi kondisi terkini sebelum berkomitmen ke satu platform
- Vercel + Flask memakai model serverless function, bukan container Docker biasa — arsitektur aplikasi (terutama static file) perlu disesuaikan, tidak bisa "asal deploy" dari setup Docker yang sudah ada
- CORS adalah masalah level **browser**, bukan level server — memindahkan pemanggilan API pihak ketiga ke backend (server-to-server) adalah solusi yang jauh lebih andal dibanding mencoba "mengakali" CORS dari sisi klien
- Validasi sintaks (`node -c file.js`) sebelum commit adalah kebiasaan kecil yang menghemat banyak waktu debugging berulang
- Selalu telusuri **sumber data** sebuah nilai yang ditampilkan (dalam kasus ini, nama kota dari parsing timezone) — bug yang terlihat sederhana di UI kadang berakar dari asumsi yang salah tentang API pihak ketiga
- `git status` adalah langkah pertama yang wajib dicek setiap kali ada perbedaan antara lokal dan production — mayoritas kasus "tidak update di production" bukan karena Vercel/CI gagal, tapi karena perubahan belum benar-benar di-push

---

**Live demo:** [https://prayer-time-app-two.vercel.app/](https://prayer-time-app-two.vercel.app/)

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 10](../day-10-cicd-advanced/notes.md)
