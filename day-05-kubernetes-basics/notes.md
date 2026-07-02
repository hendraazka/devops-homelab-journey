# Day 05 — Kubernetes Dasar (kind)

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 04](../day-04-github-actions/notes.md)

---

## ✅ Yang Dipelajari

- [x] Konsep dasar Kubernetes — kenapa dibutuhkan setelah Docker
- [x] Install `kind` (Kubernetes in Docker) dan `kubectl`
- [x] Membuat cluster Kubernetes lokal
- [x] Deploy aplikasi via command line (`kubectl create`, `kubectl expose`)
- [x] Konsep **self-healing** — Pod otomatis dibuat ulang saat dihapus/crash
- [x] Konsep **scaling** — menambah/mengurangi jumlah Pod
- [x] Deploy aplikasi via file **YAML** (pendekatan deklaratif)
- [x] Environment variable di dalam Pod
- [x] Resource requests & limits (CPU/RAM)
- [x] Kubernetes **Secret** untuk data sensitif (password, API key)

---

## 🧠 Konsep Kunci

| Istilah | Analogi | Penjelasan |
|---|---|---|
| **Cluster** | Seluruh restoran | Kumpulan mesin (node) yang menjalankan Kubernetes |
| **Node** | Satu dapur/cabang | Satu mesin (fisik/virtual) dalam cluster |
| **Pod** | Satu piring makanan siap saji | Unit terkecil di Kubernetes, biasanya membungkus 1 container |
| **Deployment** | Resep + aturan jumlah porsi | Mengatur berapa banyak Pod yang harus selalu jalan, dan cara update-nya |
| **Service** | Nomor meja/alamat pemesanan | Cara Pod diakses dari luar/Pod lain, walau Pod-nya berganti-ganti |
| **Secret** | Brankas kecil | Tempat menyimpan data sensitif (password, token) secara terpisah dari konfigurasi utama |

**Kenapa butuh Kubernetes setelah Docker?**
Docker cocok untuk menjalankan 1–2 container secara manual. Tapi aplikasi production butuh: otomatis mengganti container yang crash, otomatis scaling saat traffic naik, dan update tanpa downtime — semua ini yang dihandle Kubernetes.

---

## 💻 Setup Awal

```bash
# Install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.29.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Buat cluster
kind create cluster --name lab-cluster

# Cek cluster
kubectl cluster-info --context kind-lab-cluster
kubectl get nodes
```

**Insight:** `kind` sebenarnya menjalankan seluruh cluster Kubernetes **di dalam 1 container Docker** (`lab-cluster-control-plane`). Ini kenapa `kind` ringan dijalankan di laptop — dari sisi `docker ps`, cuma keliatan 1 container biasa, padahal di dalamnya ada komponen Kubernetes lengkap.

---

## 💻 Perintah Dasar — Cara Imperatif (Command Line)

```bash
kubectl create deployment nginx-app --image=nginx:alpine   # buat deployment
kubectl get pods                                            # lihat semua pod
kubectl get deployments                                     # lihat semua deployment
kubectl expose deployment nginx-app --port=80 --type=NodePort  # buat service
kubectl get services                                         # lihat semua service
kubectl port-forward service/nginx-app 8090:80               # akses dari browser (localhost:8090)
```

## 🔬 Eksperimen: Self-Healing

```bash
kubectl get pods                    # catat nama pod
kubectl delete pod <nama-pod>       # hapus paksa (simulasi crash)
kubectl get pods                    # -> muncul pod BARU otomatis, tanpa perintah tambahan
```

## 🔬 Eksperimen: Scaling

```bash
kubectl scale deployment nginx-app --replicas=3   # tambah jadi 3 pod
kubectl get pods                                    # -> 3 pod jalan
kubectl scale deployment nginx-app --replicas=1     # kembali ke 1 pod
```

---

## 💻 Cara Deklaratif — via YAML (Pendekatan Real-World)

Kenapa YAML lebih dipakai di production dibanding command line langsung:
- Bisa disimpan & di-versioning di Git (seperti Dockerfile)
- Reproducible — orang lain bisa deploy persis sama
- Deklaratif — cukup definisikan "kondisi yang diinginkan", Kubernetes yang urus caranya

### Contoh `nginx-deployment.yaml` Lengkap

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-app
  template:
    metadata:
      labels:
        app: nginx-app
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
          env:
            - name: APP_ENV
              value: "development"
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: DB_USER
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: DB_PASSWORD
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "250m"
              memory: "128Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-app
spec:
  selector:
    app: nginx-app
  ports:
    - port: 80
      targetPort: 80
  type: NodePort
```

### Penjelasan Bagian-bagian Penting

| Bagian | Fungsi |
|---|---|
| `apiVersion`, `kind` | Jenis dan versi API object Kubernetes |
| `metadata.name` | Nama object |
| `spec.replicas` | Jumlah Pod yang diinginkan |
| `selector` & `labels` | Cara Deployment/Service mengenali Pod miliknya — harus cocok satu sama lain |
| `env` (langsung `value`) | Environment variable non-sensitif |
| `env` (`valueFrom.secretKeyRef`) | Environment variable yang diambil dari Secret (untuk data sensitif) |
| `resources.requests` | Resource minimal yang dijamin tersedia |
| `resources.limits` | Resource maksimal yang boleh dipakai (lebih dari ini, container bisa di-kill) |
| `---` | Pemisah antar-object dalam 1 file YAML |

### Perintah untuk YAML

```bash
kubectl apply -f nginx-deployment.yaml    # deploy / update sesuai isi file
kubectl get pods                          # cek hasil
kubectl get services
kubectl delete -f nginx-deployment.yaml   # hapus semua resource dari file ini
```

**Insight penting:** `kubectl apply` itu pintar — dia membandingkan kondisi cluster saat ini dengan yang didefinisikan di YAML, lalu otomatis menyesuaikan (tambah/kurang/update Pod) tanpa perlu hapus manual dulu.

---

## 🔒 Kubernetes Secret — Menyimpan Data Sensitif dengan Aman

### Masalah: `env` biasa itu tidak aman untuk data sensitif

```yaml
env:
  - name: DB_PASSWORD
    value: "password123"   # BAHAYA! Tersimpan plain text, bisa dilihat siapa saja
                            # dan akan ter-expose kalau file di-commit ke Git
```

### Solusi: Secret

```bash
# Buat Secret
kubectl create secret generic db-credentials \
  --from-literal=DB_USER=admin \
  --from-literal=DB_PASSWORD=SuperSecret123

# Cek Secret
kubectl get secrets
kubectl get secret db-credentials -o yaml   # data ter-encode base64, tidak plain text
```

Lalu hubungkan ke Deployment lewat `valueFrom.secretKeyRef` (lihat contoh YAML di atas).

### Verifikasi Secret Masuk ke Pod

```bash
kubectl exec -it <nama-pod> -- env | grep DB_
# Output:
# DB_USER=admin
# DB_PASSWORD=SuperSecret123
```

### ⚠️ Catatan Keamanan Penting

- Base64 encoding **bukan enkripsi sungguhan** — cuma "penyamaran". Untuk production sungguhan biasanya dikombinasikan dengan tool tambahan seperti *Sealed Secrets* atau *HashiCorp Vault*
- File Deployment yang **mereferensikan** Secret (`secretKeyRef`) aman di-commit ke Git, karena tidak berisi value asli
- File YAML yang **mendefinisikan** Secret secara langsung (dengan value asli) **jangan pernah** di-commit ke Git — biasanya di-exclude lewat `.gitignore`

---

## 🔧 Troubleshooting yang Dialami

| Masalah | Penyebab | Solusi |
|---|---|---|
| `error: unknown flag: --env` saat `kubectl exec` | Salah sintaks — menulis `--env` (tanpa spasi) padahal maksudnya menjalankan perintah `env` di dalam container | Gunakan `kubectl exec -it <pod> -- env` (perhatikan spasi setelah `--`) |

---

## 📌 Insight Penting

- Kubernetes = "manajer" yang otomatis menjaga kondisi aplikasi sesuai yang diinginkan (self-healing, scaling)
- `kind` menjalankan cluster Kubernetes di dalam 1 container Docker — cocok untuk latihan di laptop dengan resource terbatas
- Pendekatan **deklaratif** (YAML + `kubectl apply`) adalah standar di dunia kerja, dibanding pendekatan **imperatif** (`kubectl create` langsung)
- Selalu pisahkan data sensitif menggunakan **Secret**, jangan pernah hardcode password/API key di file YAML yang akan di-commit ke Git

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 04](../day-04-github-actions/notes.md)

