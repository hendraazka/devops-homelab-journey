# Day 09 — Kubernetes Lanjutan: Helm, Ingress Controller, StatefulSet

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 08](../day-08-monitoring/notes.md)

---

## ✅ Yang Dipelajari

- [x] Helm — package manager untuk Kubernetes (install, upgrade, rollback, history)
- [x] Ingress Controller — setup NGINX Ingress di `kind`
- [x] Ingress Resource — routing traffic berdasarkan domain
- [x] StatefulSet — identitas Pod yang stabil + persistent storage per-Pod
- [x] Headless Service dan `volumeClaimTemplates`
- [x] Troubleshooting kubeconfig/context yang stale setelah cluster dibuat ulang
- [x] Insight: sifat *disposable* cluster `kind` dan implikasinya terhadap data

---

## 🧠 Konsep Kunci

| Konsep | Penjelasan Singkat |
|---|---|
| **Helm** | "Package manager" untuk Kubernetes — membungkus banyak file YAML menjadi satu paket (Chart) yang bisa di-install/upgrade/rollback dengan satu perintah |
| **Chart** | Paket konfigurasi Kubernetes siap pakai (mirip package di `apt`/`npm`) |
| **Ingress** | "Resepsionis" yang menerima semua traffic dari satu pintu masuk, lalu mengarahkan ke Service yang tepat berdasarkan domain/path |
| **Ingress Controller** | Komponen yang benar-benar menjalankan logika routing Ingress (contoh: NGINX Ingress Controller) |
| **StatefulSet** | Mirip Deployment, tapi memberi setiap Pod nama stabil-berurutan dan storage sendiri yang tetap menempel walau Pod dihapus/dibuat ulang |
| **Headless Service** | Service dengan `clusterIP: None`, wajib untuk StatefulSet agar tiap Pod bisa diakses langsung by nama |
| **volumeClaimTemplates** | Membuat PersistentVolumeClaim otomatis dan terpisah untuk **setiap** Pod di StatefulSet |

---

## 💻 Bagian 1: Helm

### Setup
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

### Install & Kelola Aplikasi
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo bitnami/nginx

helm install my-nginx bitnami/nginx
helm list
helm upgrade my-nginx bitnami/nginx --set replicaCount=3
helm history my-nginx
helm rollback my-nginx 1
helm uninstall my-nginx
```

**Insight:** Helm otomatis mencatat setiap perubahan sebagai *revision*. Kalau upgrade bermasalah, tinggal `helm rollback` ke revisi sebelumnya — jauh lebih cepat dibanding memperbaiki manual lewat banyak file YAML.

---

## 💻 Bagian 2: Ingress Controller

### Install NGINX Ingress Controller (khusus provider `kind`)
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s
```

### Ingress Resource (`nginx-ingress.yaml`)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: nginx-app.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-app
                port:
                  number: 80
```

### Terapkan & Akses
```bash
kubectl apply -f nginx-ingress.yaml
kubectl get ingress
```

Tambahkan domain palsu ke `hosts` file Windows (`C:\Windows\System32\drivers\etc\hosts`, edit sebagai Administrator):
```
127.0.0.1 nginx-app.local
```

Port-forward Ingress Controller ke port lokal:
```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```

Akses: `http://nginx-app.local:8080`

---

## 💻 Bagian 3: StatefulSet

### `redis-statefulset.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-headless
spec:
  clusterIP: None
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis-headless
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:alpine
          ports:
            - containerPort: 6379
          volumeMounts:
            - name: redis-data
              mountPath: /data
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
```

```bash
kubectl apply -f redis-statefulset.yaml
kubectl get pods
kubectl get pvc
```

**Hasil:** Pod bernama `redis-0`, `redis-1`, `redis-2` (berurutan dan stabil) — berbeda dari Deployment yang menghasilkan nama acak seperti `nginx-app-557b9c48bb-jq724`. Masing-masing punya PVC sendiri (`redis-data-redis-0`, dst).

### 🔬 Eksperimen: Identitas & Data Tetap Menempel

```bash
kubectl exec -it redis-0 -- redis-cli
# SET pod_id "saya-adalah-redis-0"
# GET pod_id   -> "saya-adalah-redis-0"
# exit

kubectl delete pod redis-0
kubectl get pods    # -> Pod baru terbuat dengan nama TETAP "redis-0"

kubectl exec -it redis-0 -- redis-cli
# GET pod_id   -> "saya-adalah-redis-0"  (data tetap ada!)
```

**Insight:** Ini pembuktian gabungan konsep *self-healing* (Day 05) dan *persistent storage* (Day 02), tapi kali ini terikat secara spesifik per-Pod individual — sesuatu yang tidak dijamin oleh Deployment biasa.

---

## 🔧 Troubleshooting yang Dialami

| Masalah | Penyebab | Solusi |
|---|---|---|
| `connection refused` saat `kubectl get nodes` | Container cluster `kind` sempat mati (misal karena Docker Desktop restart) atau terhapus | Cek `docker ps -a`, nyalakan ulang dengan `docker start <nama-container>`; jika kubeconfig masih menunjuk ke port lama, jalankan `kind export kubeconfig --name <nama-cluster>` |
| Pod status `Pending` lama, lalu ternyata `Running` setelah ditunggu | Image Ingress Controller cukup besar (~116MB), butuh waktu pull lebih dari timeout default `kubectl wait` (120s) | Tunggu lebih lama, atau gunakan `kubectl get pods -n ingress-nginx -w` untuk memantau real-time alih-alih `kubectl wait` dengan timeout pendek |
| `CreateContainerConfigError` pada Pod, `Endpoints` Service kosong, hasil 503 di Ingress | Secret (`db-credentials`) yang direferensikan Deployment tidak ditemukan — karena dibuat di cluster lama, sedangkan Pod berjalan di cluster baru yang berbeda | Buat ulang Secret di cluster yang aktif saat ini; Kubernetes akan otomatis retry Pod begitu Secret tersedia |
| Banyak context menumpuk di `kubectl config get-contexts`, nama cluster jadi aneh (`lab-cluster-helm-control-plane-control-plane`) | Tidak sengaja menjalankan `kind create cluster` dengan nama yang sudah mengandung "-control-plane", sehingga `kind` menambah suffix lagi; sebelumnya juga sempat membuat cluster baru tanpa sadar cluster lama masih "tercatat" di kubeconfig meski container aslinya sudah tidak ada | Selalu cek `kind get clusters` (bukan hanya `kubectl config get-contexts`) untuk melihat cluster yang benar-benar hidup; gunakan `docker ps -a` untuk verifikasi container aslinya; pastikan context aktif benar dengan `kubectl config current-context` sebelum menjalankan perintah penting |
| Semua Pod, Secret, dan PVC hilang meski PVC sebelumnya "Bound" | Cluster `kind` bersifat *disposable* — jika container cluster diganti/dibuat ulang (bukan sekadar di-restart), seluruh isi cluster (termasuk PVC yang tersimpan di dalam container tersebut) ikut hilang | Pahami bahwa `kind` cocok untuk latihan, bukan produksi; untuk kebutuhan data yang benar-benar persisten lintas re-create cluster, dibutuhkan storage eksternal di luar container `kind` itu sendiri |

---

## 📌 Insight Penting

- Helm sangat mempercepat pekerjaan yang sebelumnya butuh banyak file YAML manual — terutama untuk aplikasi kompleks yang sudah tersedia sebagai Chart komunitas (Bitnami, dll)
- Ingress adalah cara standar production untuk expose banyak aplikasi lewat satu pintu masuk (satu IP/port), dibanding `LoadBalancer` per-aplikasi yang boros dan `NodePort` yang tidak rapi
- StatefulSet penting untuk workload yang butuh identitas & data unik per instance (database cluster, message queue, dll) — Deployment biasa tidak menjamin hal ini
- **Cluster `kind` sepenuhnya disposable**, persis seperti container biasa — pemahaman ini penting agar tidak kaget kehilangan data saat bereksperimen. Di dunia kerja nyata, cluster production tidak "dibuat ulang" sembarangan seperti homelab, dan data critical selalu disimpan di storage yang independen dari siklus hidup cluster
- Kebiasaan mengecek `kind get clusters`, `docker ps -a`, dan `kubectl config current-context` sebelum bekerja adalah kebiasaan baik untuk menghindari kebingungan saat mengelola banyak cluster lokal sekaligus

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 08](../day-08-monitoring/notes.md)

