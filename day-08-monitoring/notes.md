# Day 08 — Monitoring dengan Prometheus + Grafana (+ Eksplorasi Loki & ELK)

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 07](../day-07-ansible/notes.md)

---

## ✅ Yang Dipelajari

- [x] Konsep monitoring dan kenapa dibutuhkan setelah infrastruktur berjalan
- [x] Peran Prometheus (pengumpul metrik) vs Grafana (penyaji visual)
- [x] Setup Prometheus + Grafana via Docker Compose
- [x] Menghubungkan Grafana ke Prometheus sebagai data source
- [x] Membuat dashboard & panel visualisasi pertama
- [x] Alerting: Contact Point (webhook & email/SMTP Gmail)
- [x] Mengamankan credential dengan `.env` dan `.gitignore`
- [x] Persistent storage untuk Grafana & Prometheus (Volume)
- [x] Node Exporter — monitoring CPU/RAM host
- [x] Eksplorasi Prometheus UI (query langsung, Targets, Configuration)
- [x] Loki + Promtail — centralized logging terintegrasi dengan Grafana (LogQL)
- [x] Eksplorasi ELK Stack (Elasticsearch, Kibana, Filebeat) sebagai perbandingan
- [x] Memahami limitasi Docker Desktop di Windows/WSL2 untuk akses log container

---

## 🧠 Konsep Kunci

| Konsep | Penjelasan Singkat |
|---|---|
| **Prometheus** | Menarik ("scrape") metrik dari target secara berkala dan menyimpannya sebagai data time-series |
| **Grafana** | Visualisasi data dari berbagai sumber (Prometheus, Loki, dll) dalam bentuk dashboard |
| **Metrics vs Logs** | Metrics = data numerik terstruktur (cocok untuk Prometheus); Logs = teks detail kejadian (butuh tool khusus seperti Loki/ELK) |
| **Alert Rule & Contact Point** | Kondisi yang dipantau otomatis, dan tujuan notifikasi dikirim saat kondisi terpenuhi |
| **Node Exporter** | Agent yang mengekspos metrik hardware (CPU, RAM, disk) host agar bisa ditarik Prometheus |
| **Loki** | Database log ringan, terintegrasi langsung dengan Grafana, memakai bahasa query **LogQL** |
| **Promtail** | Agent yang menarik log dari container Docker dan mengirimkannya ke Loki |
| **ELK Stack** | Elasticsearch (index & search) + Logstash (pengolah data) + Kibana (visualisasi) — solusi logging yang lebih *powerful* tapi lebih berat resource |
| **Filebeat** | Agent pengumpul log untuk ELK Stack (setara Promtail di sisi Loki) |

---

## 💻 Setup Prometheus + Grafana via Docker Compose

### `prometheus.yml`
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

### `docker-compose.yml` (versi lengkap: Prometheus + Grafana + Node Exporter, dengan Volume & `.env`)
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_SMTP_ENABLED=true
      - GF_SMTP_HOST=${SMTP_HOST}
      - GF_SMTP_USER=${SMTP_USER}
      - GF_SMTP_PASSWORD=${SMTP_PASSWORD}
      - GF_SMTP_FROM_ADDRESS=${SMTP_FROM_ADDRESS}
      - GF_SMTP_FROM_NAME=Grafana Alert

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"

volumes:
  prometheus-data:
  grafana-data:
```

### `.env` (TIDAK di-commit ke Git)
```env
GRAFANA_ADMIN_PASSWORD=admin123
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=emailkamu@gmail.com
SMTP_PASSWORD=app_password_16_digit
SMTP_FROM_ADDRESS=emailkamu@gmail.com
```

### `.gitignore`
```
.env
terraform.tfstate
terraform.tfstate.backup
*.tfvars
```

### Jalankan
```bash
docker compose up -d
docker compose ps
```
Akses: Prometheus `http://localhost:9090` | Grafana `http://localhost:3000`

---

## 🔗 Menghubungkan Grafana ke Prometheus

1. Grafana → **Connections** → **Data sources** → **Add data source** → **Prometheus**
2. URL pakai **nama container**, bukan `localhost` (Docker Networking, Day 02):
   ```
   http://prometheus:9090
   ```
3. **Save & test** — berhasil jika muncul "Successfully queried the Prometheus API"

---

## 📊 Dashboard Pertama

1. **Dashboards** → **New** → **Add visualization** → pilih data source **Prometheus**
2. Query dasar:
   ```
   up
   ```
3. **Run queries** → **Save dashboard**

Data grafik hanya muncul mulai dari saat Prometheus pertama kali berjalan — bagian sebelumnya kosong karena memang belum ada data, ini normal.

---

## 🔔 Alerting dengan Email (Gmail SMTP)

### 1. Buat App Password Gmail
- Aktifkan 2-Step Verification di akun Google
- Buka [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- Buat App Password baru, copy 16 digit yang muncul

### 2. Set variabel SMTP di `.env` (lihat di atas), lalu restart
```bash
docker compose down
docker compose up -d
```

### 3. Buat Contact Point di Grafana
**Alerting** → **Contact points** → **Add contact point** → Integration: **Email** → isi alamat email → **Save** → klik **Test** untuk verifikasi

---

## 🔒 Persistent Storage (Volume) untuk Grafana & Prometheus

**Masalah yang dialami:** setelah `docker compose down` lalu `up` ulang (misalnya karena perbaikan konfigurasi `.env`), semua dashboard dan alert rule di Grafana **hilang total**. Ini karena Grafana menyimpan datanya di dalam filesystem container, dan container yang dihapus/dibuat ulang tidak membawa data lamanya — sama seperti eksperimen Redis di Day 02.

**Solusi:** tambahkan volume `grafana-data:/var/lib/grafana` dan `prometheus-data:/prometheus` (sudah termasuk di `docker-compose.yml` di atas). Setelah volume ditambahkan, `docker compose down` (**tanpa** flag `-v`) tidak akan lagi menghapus dashboard, alert rule, maupun history metrik.

**Peringatan penting:** `docker compose down -v` akan tetap menghapus volume — jangan gunakan flag `-v` kalau ingin data tetap aman.

---

## 📈 Node Exporter — Monitoring CPU/RAM Host

Ditambahkan sebagai service baru di `docker-compose.yml` (lihat di atas), lalu didaftarkan sebagai target scrape di `prometheus.yml`.

### Query Berguna
```promql
# RAM tersedia (bytes)
node_memory_MemAvailable_bytes

# Persentase RAM terpakai
100 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100)

# Persentase CPU sedang sibuk (bukan idle)
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

---

## 🔍 Eksplorasi Prometheus UI (Bukan Hanya Data Source untuk Grafana)

| Menu/Fitur | Kegunaan |
|---|---|
| Kolom query utama | Jalankan PromQL langsung, lihat hasil tabel/grafik sederhana |
| **Status → Targets** | Cek semua target yang dipantau beserta status `UP`/`DOWN` |
| **Status → Configuration** | Lihat isi `prometheus.yml` yang sedang aktif |
| `rate(metric[5m])` | Hitung laju perubahan suatu metrik dalam rentang waktu tertentu |

**Exporter lain yang umum dipakai di real-world:** Node Exporter (hardware server), cAdvisor (metrik container Docker), Blackbox Exporter (cek endpoint/website masih hidup).

---

## 📜 Loki + Promtail — Centralized Logging (Terintegrasi Grafana)

### Tambahan di `docker-compose.yml`
```yaml
  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./promtail-config.yaml:/etc/promtail/config.yaml
    command: -config.file=/etc/promtail/config.yaml
    depends_on:
      - loki
```

### `promtail-config.yaml`
```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
```

### Hubungkan Loki ke Grafana
Data source baru → **Loki** → URL: `http://loki:3100` → **Save & test**

Verifikasi Loki langsung dari browser (host):
```
http://localhost:3100/ready
```

### Query Log (LogQL) via Grafana **Explore**
```logql
# Semua log dari semua container
{container=~".+"}

# Mengandung kata tertentu
{container=~".+"} |= "error"

# Tidak mengandung kata tertentu
{container=~".+"} != "healthcheck"

# Regex — salah satu dari beberapa kata
{container=~".+"} |~ "error|warning|fail"

# Filter container spesifik + kata kunci
{container="grafana"} |= "error"

# Parsing log JSON
{container="nginx"} | json | status_code="500"
```

**Insight:** Loki sengaja tidak meng-index seluruh isi teks log (hanya label seperti nama container) — trade-off yang disengaja demi resource yang jauh lebih ringan dibanding Elasticsearch, cocok untuk homelab/skala kecil-menengah.

---

## 🔬 Eksplorasi ELK Stack (Elasticsearch, Kibana, Filebeat)

Dicoba sebagai perbandingan terhadap Loki. Dijalankan di folder terpisah (`~/devops-lab/elk-lab`) agar tidak membebani RAM bersamaan dengan stack Prometheus/Grafana/Loki yang sudah berjalan.

### `docker-compose.yml` (Elasticsearch + Kibana + Filebeat)
```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elastic-data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.15.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.15.0
    container_name: filebeat
    user: root
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: ["--strict.perms=false"]
    depends_on:
      - elasticsearch

volumes:
  elastic-data:
```

### `filebeat.yml`
```yaml
filebeat.autodiscover:
  providers:
    - type: docker
      hints.enabled: true

processors:
  - add_docker_metadata: ~

output.elasticsearch:
  hosts: ["http://elasticsearch:9200"]
  index: "filebeat-docker-%{+yyyy.MM.dd}"

setup.template.name: "filebeat"
setup.template.pattern: "filebeat-*"
```

### Perbandingan Loki vs ELK

| | Loki (Grafana) | ELK Stack |
|---|---|---|
| Bahasa query | LogQL | Query DSL / KQL |
| Full-text search | Terbatas, fokus label + filter teks | Sangat powerful, index penuh |
| Resource dibutuhkan | Ringan | Berat (Elasticsearch minimal disarankan 4GB+ RAM) |
| Integrasi | Native dengan Grafana (metrics + logs dalam satu tempat) | Perlu tool visual terpisah (Kibana) |
| Best untuk | Homelab, skala kecil-menengah | Analisis log kompleks, skala besar/enterprise |

---

## 🔧 Troubleshooting yang Dialami

| Masalah | Penyebab | Solusi |
|---|---|---|
| `Login failed: Invalid username or password` di Grafana | Nama variable di `.env` tidak cocok dengan yang dipanggil di `docker-compose.yml` (misal `.env` pakai `GF_SECURITY_ADMIN_PASSWORD`, padahal `docker-compose.yml` memanggil `${GRAFANA_ADMIN_PASSWORD}`) | Samakan nama variable persis antara `.env` dan pemanggilan `${...}` di `docker-compose.yml`; verifikasi dengan `docker compose config` (harus tanpa warning "variable is not set") |
| Dashboard & alert Grafana hilang setelah `docker compose down` + `up` | Grafana menyimpan data di filesystem container tanpa volume — ephemeral storage (konsep Day 02) | Tambahkan volume `grafana-data:/var/lib/grafana`; hindari flag `-v` saat `down` |
| `services.grafana additional properties 'node-exporter' not allowed` | Kesalahan indentasi YAML — service baru tertulis menjorok ke dalam service lain, bukan sejajar | Pastikan setiap service baru sejajar (indentasi sama) dengan service lain di bawah `services:` |
| `config file ("filebeat.yml") must be owned by ... root` | Filebeat memvalidasi ketat kepemilikan file config; di WSL2 + Docker Desktop kadang ownership terlihat benar dari sisi WSL (`stat`) namun tetap ditolak container akibat lapisan translasi filesystem WSL2↔Docker Desktop | Perbaiki dengan `sudo chown root file.yml` dan `sudo chmod go-w file.yml`; jika masih gagal, gunakan flag `--strict.perms=false` pada command container (valid untuk environment development) |
| `/var/lib/docker/containers` kosong di dalam container Promtail/Filebeat | **Limitasi arsitektur:** Docker Desktop di Windows (WSL2 backend) menjalankan Docker engine di distro WSL tersembunyi terpisah (`docker-desktop`/`docker-desktop-data`), bukan di distro Ubuntu yang dipakai sehari-hari — sehingga path container log yang sebenarnya tidak berada di lokasi yang di-mount | Tidak ada workaround sederhana dari sisi WSL Ubuntu biasa; solusi yang direncanakan: install Docker Engine langsung di WSL Ubuntu (bukan via Docker Desktop), agar `/var/lib/docker/containers` benar-benar merepresentasikan container yang berjalan |

---

## 📌 Insight Penting

- Monitoring melengkapi seluruh siklus DevOps: Terraform membuat infrastruktur, Ansible mengonfigurasi, Kubernetes menjalankan aplikasi, CI/CD mengotomasi deployment, monitoring memastikan semuanya berjalan sehat
- Selalu terapkan prinsip Secret/`.env` untuk credential (SMTP password, dll) — jangan pernah hardcode di file yang akan di-commit ke Git
- Volume itu sama pentingnya untuk tool monitoring (Grafana, Elasticsearch) seperti untuk database — tanpa volume, semua konfigurasi dan history data akan hilang setiap container dibuat ulang
- **Docker Desktop di Windows/Mac punya arsitektur berbeda dari Docker native di Linux** — beberapa hal yang berjalan mulus di server Linux produksi (seperti akses langsung ke `/var/lib/docker/containers`) tidak selalu berjalan sama di lingkungan development Windows/WSL2. Memahami batasan ini penting agar tidak salah menyimpulkan ada bug di konfigurasi sendiri
- Loki dan ELK Stack sama-sama valid untuk logging, dengan trade-off resource vs kemampuan search — pemilihan tergantung skala dan kebutuhan tim

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 07](../day-07-ansible/notes.md)

