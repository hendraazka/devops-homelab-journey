# 🚀 DevOps Homelab Journey

Catatan progress belajar DevOps di homelab pribadi (Windows + WSL2), sebagai persiapan karir di bidang DevOps.

**Environment:** Windows + WSL2 (Ubuntu 24.04) + Docker Desktop
**RAM:** 16GB

---

## 📅 Day 1 — Fondasi Linux CLI & Docker Basics

### ✅ Yang Sudah Dipelajari

- [x] Setup & verifikasi WSL2 (`wsl --list --verbose`)
- [x] Navigasi dasar Linux (`cd`, `ls`, `mkdir`, `touch`, `pwd`)
- [x] Text editor di terminal (`nano`)
- [x] Konsep permission & `chmod` (execute permission untuk shell script)
- [x] Instalasi Docker Desktop + integrasi WSL2
- [x] Menjalankan container pertama (`docker run hello-world`)
- [x] Menjalankan long-running container dengan port mapping (Nginx)
- [x] Membuat **Dockerfile** custom & build image sendiri
- [x] Docker Compose — menjalankan multi-container app sekaligus

### 🧠 Konsep Kunci

| Konsep | Penjelasan Singkat |
|---|---|
| **WSL2** | Layer kompatibilitas untuk menjalankan Linux di Windows tanpa dual-boot |
| **Image** | Blueprint/template read-only berisi aplikasi + dependencies |
| **Container** | Instance yang berjalan dari sebuah image |
| **Dockerfile** | Instruksi tertulis untuk membangun image custom |
| **Docker Compose** | Tool untuk mendefinisikan & menjalankan multi-container app dalam satu file YAML |
| **Port Mapping** (`-p`) | Menghubungkan port di host (laptop) ke port di dalam container |

### 💻 Perintah Penting yang Dipelajari

**Linux CLI**
```bash
mkdir -p folder1/folder2      # bikin folder (nested)
touch file.txt                 # bikin file kosong
nano file.txt                  # edit file di terminal
chmod +x script.sh             # kasih izin execute
ls -la                         # list isi folder + hidden files + detail permission
```

**Docker — Container Management**
```bash
docker run hello-world                          # jalankan container sekali jalan
docker run -d -p 8080:80 --name web nginx        # jalankan container di background + port mapping
docker ps                                        # lihat container yang sedang berjalan
docker logs <container_name>                     # lihat log container
docker stop <container_name>                     # hentikan container
docker start <container_name>                    # jalankan ulang container
docker rm <container_name>                       # hapus container
docker images                                    # lihat semua image lokal
docker rmi <image_name>                          # hapus image
```

**Docker — Build Custom Image**
```bash
docker build -t nama-image .                     # build image dari Dockerfile di folder saat ini
docker run -d -p 8081:80 --name app nama-image    # jalankan container dari image custom
```

**Docker Compose**
```bash
docker compose up -d          # jalankan semua service di background
docker compose ps             # cek status semua service
docker compose down           # matikan & hapus semua service
```

### 📁 Contoh Dockerfile

```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
```

### 📁 Contoh docker-compose.yml

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8082:80"
  cache:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 📸 Hasil Praktik

- Berhasil menjalankan `hello-world` container
- Berhasil menjalankan Nginx via `docker run` dengan port mapping (`localhost:8080`)
- Berhasil membangun & menjalankan custom image dari Dockerfile sendiri (`localhost:8081`)
- Berhasil menjalankan multi-container (Nginx + Redis) via Docker Compose (`localhost:8082`)

---

## 🗺️ Roadmap Selanjutnya

- [ ] Docker networking & volumes (persistent data)
- [ ] Git & GitHub workflow (branching, PR)
- [ ] CI/CD pipeline dengan GitHub Actions
- [ ] Kubernetes dasar (kind / Minikube)
- [ ] Infrastructure as Code — Terraform
- [ ] Configuration management — Ansible
- [ ] Monitoring — Prometheus + Grafana

---

## 📚 Referensi

- [Docker Documentation](https://docs.docker.com/)
- [WSL2 + Docker Desktop Setup](https://docs.docker.com/go/wsl2/)

---

*Catatan pribadi — belajar DevOps dari nol, homelab di laptop Windows.*
