# Day 02 — Docker Networking & Volumes

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 01](../day-01-linux-docker-basics/notes.md)

---

## ✅ Yang Dipelajari

- [x] Memahami sifat *ephemeral storage* — data di container hilang saat container dihapus
- [x] Membuktikan langsung masalah data hilang (percobaan dengan Redis)
- [x] Menggunakan **Docker Volume** agar data persistent walau container dihapus & dibuat ulang
- [x] Membuat **Docker Network** custom
- [x] Membuktikan 2 container bisa saling terhubung menggunakan **nama container** (DNS resolution otomatis antar container)

---

## 🧠 Konsep Kunci

| Konsep | Penjelasan Singkat |
|---|---|
| **Ephemeral Storage** | Data yang ditulis di dalam container bersifat sementara — hilang permanen saat container di-`rm` |
| **Volume** | Storage yang dikelola Docker secara terpisah dari container, sehingga data tetap ada walau container dihapus & dibuat ulang |
| **Docker Network** | Jaringan virtual yang menghubungkan container-container agar bisa saling berkomunikasi |
| **DNS Resolution antar Container** | Docker otomatis "menerjemahkan" nama container menjadi IP internal, sehingga container bisa saling connect cukup pakai nama, tanpa perlu tahu IP |

---

## 🔬 Eksperimen: Bukti Data Hilang Tanpa Volume

```bash
docker run -d --name redis-test redis:alpine
docker exec -it redis-test redis-cli
# SET nama "Hendra"
# GET nama   -> "Hendra"
# exit

docker stop redis-test
docker rm redis-test

# Buat ulang container dengan nama sama
docker run -d --name redis-test redis:alpine
docker exec -it redis-test redis-cli
# GET nama   -> (nil)  <-- data hilang!
```

---

## 💻 Perintah Penting — Volume

```bash
docker run -d --name redis-test -v redis-data:/data redis:alpine   # jalankan container dengan volume
docker volume ls                                                    # lihat semua volume
docker volume inspect redis-data                                    # lihat detail volume
docker volume rm redis-data                                         # hapus volume (permanen!)
docker volume prune                                                 # hapus semua volume yang tidak terpakai
```

**Hasil setelah pakai volume:** container dihapus & dibuat ulang → data **tetap ada** (`GET nama` → `"Hendra"`), karena volume hidup terpisah dari siklus hidup container.

---

## 💻 Perintah Penting — Networking

```bash
docker network create lab-network                                          # buat network custom
docker run -d --name redis-server --network lab-network redis:alpine       # jalankan container di network tsb
docker run -it --network lab-network --name test-client alpine sh          # container lain di network yang sama

# Di dalam test-client:
apk add redis
redis-cli -h redis-server ping    # -> PONG (berhasil connect pakai nama container!)

docker network ls              # lihat semua network
docker network rm lab-network  # hapus network
```

---

## 📌 Insight Penting

- Container = sementara (disposable), aman untuk dihapus & dibuat ulang kapan saja
- Volume = permanen, harus dipakai untuk data penting (database, file upload, dll)
- Ini juga menjelaskan kenapa Docker Compose "otomatis jalan" saat menghubungkan beberapa service — Compose secara default membuat network sendiri dan mendaftarkan tiap service agar bisa saling memanggil lewat nama service

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 01](../day-01-linux-docker-basics/notes.md)

