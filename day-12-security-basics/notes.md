# Day 12 — Security Dasar: Container Scanning & Secret Management dengan Vault

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 11](../day-11-deploy-vercel/notes.md)

---

## ✅ Yang Dipelajari

- [x] Container scanning dengan Trivy — instalasi CLI, cara membaca hasil scan
- [x] Perbedaan vulnerability di level base image (OS) vs level dependency aplikasi
- [x] Dampak nyata pemilihan base image terhadap jumlah vulnerability (`slim` vs `alpine`)
- [x] Menaikkan standar CI/CD agar pipeline gagal saat ada CVE CRITICAL/HIGH
- [x] Konsep dan keterbatasan Kubernetes Secret dibanding secret management sungguhan
- [x] Instalasi dan penggunaan dasar HashiCorp Vault (KV secrets engine)
- [x] Fitur versioning secret di Vault
- [x] Integrasi Vault dengan Kubernetes: Kubernetes Auth Method, Policy, Role
- [x] Vault Agent Injector — Pod otomatis mendapat secret tanpa `kubectl create secret` manual

---

## 🧠 Konsep Kunci

| Konsep | Penjelasan Singkat |
|---|---|
| **Container Scanning** | Proses otomatis mendeteksi vulnerability (CVE) yang sudah diketahui publik di dalam layer-layer image Docker |
| **CVE** | Kode identifikasi unik untuk sebuah celah keamanan yang sudah didokumentasikan |
| **Attack Surface** | Seberapa banyak komponen/kode yang berpotensi dieksploitasi — semakin sedikit komponen dalam image, semakin kecil attack surface |
| **HashiCorp Vault** | Tool khusus untuk menyimpan, mengelola, dan mendistribusikan secret secara aman, dengan enkripsi asli, audit trail, dan kontrol akses granular |
| **Vault Agent Injector** | Komponen yang otomatis menyisipkan sidecar container ke Pod Kubernetes untuk mengambil secret dari Vault saat Pod start |
| **Dynamic Secrets** | Secret yang dibuat sesuai permintaan dan bisa expire otomatis, alih-alih credential statis yang hidup selamanya |

---

## 🔍 Bagian 1: Container Scanning dengan Trivy

### Instalasi

```bash
sudo apt-get install wget gnupg -y
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo gpg --dearmor -o /usr/share/keyrings/trivy.gpg
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy -y
```

### Scan Image

```bash
docker build -t prayer-time-app:local .
trivy image --severity CRITICAL,HIGH prayer-time-app:local
```

### Cara Membaca Hasil Scan

| Kolom | Artinya |
|---|---|
| Package | Komponen yang terdeteksi (bisa dari OS dasar, bukan hanya kode aplikasi sendiri) |
| CVE ID | Kode identifikasi celah keamanan, detail bisa dicek di `avd.aquasec.com` |
| Severity | `CRITICAL` → `HIGH` → `MEDIUM` → `LOW`, urutan tingkat keparahan |
| Status | `affected` = benar-benar terdampak; `fix_deferred` = ada perbaikan tapi sengaja ditunda oleh vendor OS |

**Insight penting:** vulnerability yang muncul sering kali berasal dari **base image OS** (misalnya `perl-base`, `util-linux` bawaan Debian), bukan dari kode aplikasi yang ditulis sendiri.

### 🔬 Eksperimen: Dampak Memilih Base Image yang Lebih Minimal

**Sebelum** (`python:3.12-slim`): ditemukan beberapa CVE CRITICAL/HIGH dari package OS bawaan (`perl-base`, `util-linux`) yang sebenarnya tidak pernah dipakai langsung oleh aplikasi.

**Sesudah** (`python:3.12-alpine`):
```
prayer-time-app:alpine-test (alpine 3.24.1) → 0 Vulnerabilities
```
Seluruh Python package (`flask`, `requests`, `jinja2`, dll) juga berstatus **clean**. Dalam kasus ini, dependency yang dipakai (Flask, requests) sudah tersedia sebagai pre-compiled wheel untuk Alpine, sehingga tidak perlu menambahkan compiler (`gcc`/`musl-dev`) — image menjadi lebih ramping sekaligus lebih aman.

**Dockerfile final:**
```dockerfile
FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates/ templates/
COPY static/ static/
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD python -c "import requests; requests.get('http://localhost:5000/')" || exit 1
CMD ["python", "app.py"]
```

**Insight:** memilih base image yang minimal adalah langkah security paling efektif dan efisien — jauh lebih sederhana dibanding menambal satu per satu CVE yang muncul dari komponen OS yang bahkan tidak dipakai aplikasi.

### Menaikkan Standar di CI/CD (Day 10)

Sebelumnya pipeline dikonfigurasi tetap lolos meski ada temuan (`exit-code: '0'`). Setelah image dipastikan bersih, standar dinaikkan agar pipeline **gagal** jika ada CVE baru CRITICAL/HIGH:

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: prayer-time-app:${{ github.sha }}
    format: 'table'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'
```

---

## 🔐 Bagian 2: Secret Management dengan HashiCorp Vault

### Keterbatasan Kubernetes Secret (Day 05)

- Base64 bukan enkripsi sungguhan, hanya "penyamaran"
- Tidak ada audit log (siapa mengakses secret apa, kapan)
- Tidak ada rotasi otomatis
- Tidak ada dynamic secrets (mis. password database yang expire otomatis)

### Setup Vault (Mode Dev, via Docker)

```bash
docker run -d --name vault-dev \
  --cap-add=IPC_LOCK \
  -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=myroot' \
  hashicorp/vault
```

### Instalasi Vault CLI

```bash
wget -qO - https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install vault -y

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='myroot'
vault status
```

### Operasi Dasar Secret (KV Engine)

```bash
# Simpan secret
vault kv put secret/prayer-app db_user="admin" db_password="SuperSecret123"

# Ambil secret
vault kv get secret/prayer-app
vault kv get -field=db_password secret/prayer-app

# Update — otomatis membuat versi baru
vault kv put secret/prayer-app db_user="admin" db_password="PasswordBaru456"

# Lihat metadata & history versi
vault kv metadata get secret/prayer-app

# Ambil versi lama secara spesifik
vault kv get -version=1 secret/prayer-app
```

**Insight:** Vault otomatis menyimpan **setiap versi** dari sebuah secret. Kubernetes Secret standar tidak memiliki kemampuan ini — begitu di-update, versi lama hilang tanpa jejak. Fitur ini penting untuk audit dan troubleshooting saat rotasi credential.

---

## ☸️ Integrasi Vault dengan Kubernetes (Vault Agent Injector)

### Instalasi via Helm

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Konfigurasi Auth Method, Policy, dan Role

Dijalankan di dalam Pod `vault-0` (`kubectl exec -it vault-0 -- /bin/sh`):

```sh
vault kv put secret/prayer-app db_user="admin" db_password="RahasiaDariVault123"

vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

vault policy write prayer-app-policy - <<EOF
path "secret/data/prayer-app" {
  capabilities = ["read"]
}
EOF

vault write auth/kubernetes/role/prayer-app-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=prayer-app-policy \
  ttl=1h
```

### Deployment dengan Anotasi Vault Injector

`vault-demo-app.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prayer-app-vault-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prayer-app-vault-demo
  template:
    metadata:
      labels:
        app: prayer-app-vault-demo
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "prayer-app-role"
        vault.hashicorp.com/agent-inject-secret-db-creds.txt: "secret/data/prayer-app"
    spec:
      serviceAccountName: default
      containers:
        - name: app
          image: nginx:alpine
          command: ["/bin/sh", "-c"]
          args:
            - "sleep infinity"
```

```bash
kubectl apply -f vault-demo-app.yaml
kubectl get pods
```

**Hasil kunci:** Pod menunjukkan status **`2/2`** (bukan `1/1`) — Vault Injector otomatis menambahkan 1 sidecar container yang bertugas menarik secret dari Vault, tanpa campur tangan manual sama sekali.

### Verifikasi Secret Berhasil Ter-inject

```bash
kubectl exec -it deploy/prayer-app-vault-demo -c app -- cat /vault/secrets/db-creds.txt
```

Output:
```
data: map[db_password:RahasiaDariVault123 db_user:admin]
metadata: map[created_time:... version:1]
```

Pod ini **tidak pernah** menerima secret lewat `kubectl create secret` — seluruhnya didapat otomatis lewat rangkaian: Pod start dengan identitas Service Account → Vault Agent (sidecar) autentikasi ke Vault → Vault mencocokkan Role & Policy → token terbit → secret ditulis ke file di dalam Pod.

---

## 📊 Perbandingan: Kubernetes Secret vs Vault Injector

| | Kubernetes Secret (Day 05) | Vault Injector (Day 12) |
|---|---|---|
| Cara secret masuk ke Pod | Manual `kubectl create secret` | Otomatis saat Pod start |
| Siapa yang tahu isi secret | Siapa pun dengan akses `kubectl get secret -o yaml` | Hanya Pod dengan Role yang cocok |
| Audit log | Tidak ada | Tercatat siapa mengakses apa, kapan |
| Rotasi / expire | Manual | Token auth Pod bisa auto-expire (`ttl`) |
| Versioning | Tidak ada | Ada, bisa melihat & mengambil history |

---

## 🔧 Troubleshooting yang Dialami

| Masalah | Penyebab | Solusi |
|---|---|---|
| Warning "Role does not have an audience configured" saat membuat Vault Role | Saran best-practice tambahan dari Vault (opsional), bukan error | Diabaikan dengan aman — role tetap terbentuk dan berfungsi normal |

---

## 📌 Insight Penting

- Banyak vulnerability yang ditemukan container scanning berasal dari base image OS, bukan kode aplikasi sendiri — memilih base image yang minimal (Alpine) seringkali jauh lebih efektif daripada menambal CVE satu per satu
- `exit-code` pada tahap security scan di CI/CD sebaiknya dinaikkan menjadi tegas (gagal jika ada temuan serius) setelah baseline image sudah bersih — ini memastikan regresi keamanan di masa depan langsung terdeteksi
- Vault menyelesaikan masalah mendasar yang tidak bisa diatasi Kubernetes Secret sendirian: audit trail, versioning, dan pemberian akses berbasis identitas (bukan sekadar "siapa saja yang punya akses ke namespace")
- Vault Agent Injector mendemonstrasikan pola **zero-touch secret delivery** — aplikasi tidak pernah menyimpan credential secara statis, melainkan "meminta" secret setiap kali dibutuhkan berdasarkan identitasnya sendiri
- Environment security seperti Vault mode dev bersifat sengaja tidak persisten — cocok untuk latihan, tapi di production Vault dijalankan dalam mode HA dengan storage backend yang tepat dan proses unseal yang aman

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 11](../day-11-deploy-vercel/notes.md)
