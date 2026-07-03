# Day 06 — Infrastructure as Code dengan Terraform

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 05](../day-05-kubernetes-basics/notes.md)

---

## ✅ Yang Dipelajari

- [x] Konsep Infrastructure as Code (IaC) dan kenapa dibutuhkan
- [x] Install Terraform
- [x] Alur kerja dasar: `init` → `plan` → `apply` → `destroy`
- [x] Konsep state management (`terraform.tfstate`)
- [x] Variables — membuat konfigurasi fleksibel (`variables.tf`, `.tfvars`)
- [x] Multi-environment: perbandingan pola `.tfvars` vs folder terpisah per environment
- [x] Terraform **modules** — blueprint reusable untuk banyak environment
- [x] Perintah pendukung: `terraform fmt`, `terraform validate`, `terraform show`, `terraform output`
- [x] Praktik best practice review sebelum apply ke "production"

---

## 🧠 Konsep Kunci

| Konsep | Penjelasan Singkat |
|---|---|
| **Infrastructure as Code (IaC)** | Mendefinisikan infrastruktur dalam kode, bukan setup manual — reproducible dan bisa di-versioning di Git |
| **Provider** | Plugin yang menghubungkan Terraform ke platform target (Docker, AWS, Azure, GCP, dll) |
| **Resource** | Satu unit infrastruktur yang dikelola Terraform (container, image, server, dll) |
| **State** (`terraform.tfstate`) | "Buku catatan" Terraform tentang kondisi infrastruktur yang sudah dibuat |
| **Variable** | Nilai yang bisa diubah tanpa mengedit kode inti, membuat konfigurasi reusable |
| **Module** | Blueprint konfigurasi yang bisa dipanggil berulang kali dengan value berbeda |
| **Plan** | Preview perubahan sebelum benar-benar dieksekusi |

---

## 💻 Alur Kerja Dasar

```bash
terraform init      # download provider yang dibutuhkan (sekali di awal project)
terraform plan       # preview perubahan sebelum eksekusi
terraform apply      # eksekusi perubahan sungguhan (minta konfirmasi "yes")
terraform destroy    # hapus semua resource yang dikelola Terraform
```

### Contoh `main.tf` Dasar (mengelola Docker)

```hcl
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "nginx" {
  name = "nginx:alpine"
}

resource "docker_container" "web" {
  name  = "nginx-terraform"
  image = docker_image.nginx.image_id
  ports {
    internal = 80
    external = 8095
  }
}
```

---

## 🔧 Variables — Konfigurasi Fleksibel

### `variables.tf`

```hcl
variable "container_name" {
  description = "Nama container yang akan dibuat"
  type        = string
  default     = "nginx-terraform"
}

variable "external_port" {
  description = "Port di laptop yang akan dipetakan ke container"
  type        = number
  default     = 8095
}

variable "image_name" {
  description = "Image Docker yang dipakai"
  type        = string
  default     = "nginx:alpine"
}
```

### Memakai variable di `main.tf`

```hcl
resource "docker_image" "nginx" {
  name = var.image_name
}

resource "docker_container" "web" {
  name  = var.container_name
  image = docker_image.nginx.image_id
  ports {
    internal = 80
    external = var.external_port
  }
}
```

### Cara Override Value

```bash
# Lewat command line
terraform apply -var="external_port=9000"

# Lewat file .tfvars (lebih umum dipakai)
terraform apply -var-file="dev.tfvars"
```

---

## 🌍 Pola Multi-Environment

### Pola 1: File `.tfvars` Terpisah (Simpel, untuk project kecil)

```bash
terraform apply -var-file="dev.tfvars"
terraform apply -var-file="staging.tfvars"
```

**Kekurangan yang terbukti lewat eksperimen:** semua environment berbagi 1 `terraform.tfstate` yang sama. Apply ke `staging` setelah `dev` menyebabkan container `dev` **dihapus** — karena dari sudut pandang Terraform, keduanya dianggap "1 kondisi yang sama" yang harus disesuaikan.

### Pola 2: Terraform Workspaces (Built-in)

```bash
terraform workspace new dev
terraform workspace select dev
terraform apply -var-file="dev.tfvars"
```
State otomatis terpisah per workspace, tapi kode konfigurasi tetap sama.

### Pola 3: Folder Terpisah per Environment (Standar Perusahaan Besar) ⭐

```
terraform-project/
├── modules/
│   └── web-app/
│       ├── main.tf         (blueprint reusable)
│       └── variables.tf
├── environments/
│   ├── dev/
│   │   └── main.tf         (memanggil module, state terpisah)
│   ├── staging/
│   │   └── main.tf
│   └── production/
│       └── main.tf
```

**Module** (`modules/web-app/main.tf`):
```hcl
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

resource "docker_image" "nginx" {
  name = var.image_name
}

resource "docker_container" "web" {
  name  = var.container_name
  image = docker_image.nginx.image_id
  ports {
    internal = 80
    external = var.external_port
  }
}

output "container_id" {
  value = docker_container.web.id
}

output "container_url" {
  value = "http://localhost:${var.external_port}"
}
```

**Environment** (`environments/dev/main.tf`):
```hcl
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

module "web_app" {
  source = "../../modules/web-app"

  container_name = "nginx-dev"
  external_port  = 8091
  image_name     = "nginx:alpine"
}

output "dev_url" {
  value = module.web_app.container_url
}
```

**Deploy tiap environment** (masing-masing folder, state terpisah):
```bash
cd environments/dev
terraform init
terraform apply

cd ../staging
terraform init
terraform apply
```

**Hasilnya:** semua environment (dev, staging, production) bisa hidup **bersamaan** tanpa saling menghapus, karena masing-masing folder punya `terraform.tfstate` sendiri.

**Kelebihan pola ini:**
- State benar-benar terpisah per environment (paling aman)
- Kode inti tidak duplikat (DRY — Don't Repeat Yourself), cukup didefinisikan sekali di module
- Bisa diatur akses berbeda per folder (misal hanya senior engineer yang boleh apply ke `production`)

---

## 🔒 Praktik Production yang Lebih Hati-hati

Production diperlakukan lebih ketat karena dampaknya langsung ke pengguna nyata:

1. **Selalu `terraform plan` dulu dan direview** sebelum apply — idealnya oleh orang lain (code review)
2. **Melalui CI/CD pipeline**, bukan dijalankan manual dari laptop sembarang orang
3. **Akses terbatas** — biasanya hanya senior engineer/lead yang punya izin apply ke production
4. **State disimpan di remote backend** (misal AWS S3, Terraform Cloud) — bukan file lokal, agar aman dan bisa diakses tim

### Checklist review `terraform plan` sebelum apply

- Cek ringkasan `Plan: X to add, Y to change, Z to destroy` — waspada kalau ada `destroy` yang tidak diharapkan (potensi downtime)
- Cek value penting (nama, port, versi image) sesuai yang direncanakan, tidak bentrok dengan resource lain
- Untuk plan yang sudah direview dan disetujui, kunci dengan:
  ```bash
  terraform plan -out=tfplan
  terraform apply tfplan
  ```
  Ini memastikan `apply` menjalankan persis plan yang sudah di-review, bukan generate plan baru yang mungkin sudah berubah.

---

## 💻 Perintah Pendukung Lainnya

### `terraform fmt` — Rapikan format kode

```bash
terraform fmt
```
Otomatis merapikan indentasi dan format penulisan `.tf` sesuai standar resmi HashiCorp. Biasa dijalankan sebelum commit ke Git agar style kode konsisten di seluruh tim.

### `terraform validate` — Cek sintaks kode

```bash
terraform validate
```
Mengecek validitas sintaks/struktur kode **tanpa** perlu koneksi ke provider — lebih cepat dari `plan`. Sering dijadikan gerbang pertama di CI/CD pipeline sebelum lanjut ke `plan`/`apply`.

### `terraform show` — Lihat detail state saat ini

```bash
terraform show
```
Menampilkan kondisi lengkap resource yang dikelola (dibaca dari `terraform.tfstate`) dalam format yang mudah dibaca manusia — berguna untuk audit/debugging tanpa membuka file state mentah.

### `terraform output` — Tampilkan nilai output

Didefinisikan dulu di kode:
```hcl
output "container_url" {
  value = "http://localhost:${var.external_port}"
}
```
Lalu ditampilkan dengan:
```bash
terraform output
```
Berguna untuk mengambil informasi hasil deploy (URL, ID, connection string) yang mungkin dibutuhkan komponen/script lain.

---

## 📌 Ringkasan Perintah

| Perintah | Fungsi | Kapan Dipakai |
|---|---|---|
| `terraform fmt` | Rapikan format kode | Sebelum commit ke Git |
| `terraform validate` | Cek sintaks/struktur kode | Awal CI/CD pipeline, cepat |
| `terraform plan` | Preview perubahan sungguhan | Sebelum apply, butuh koneksi provider |
| `terraform show` | Lihat detail state saat ini | Audit/debugging |
| `terraform output` | Tampilkan nilai yang didefinisikan | Ambil info hasil deploy |
| `terraform apply` | Eksekusi perubahan | Setelah plan direview |
| `terraform destroy` | Hapus semua resource | Cleanup |

---

## 🔧 Troubleshooting yang Dialami

| Masalah | Penyebab | Solusi |
|---|---|---|
| `Error: Reference to undeclared input variable` | File `variables.tf` belum tersimpan dengan benar (lupa `Ctrl+O` sebelum keluar nano) | Buat ulang file, pastikan save dengan benar, verifikasi dengan `cat variables.tf` |
| `Unable to remove Docker image: conflict ... container is using its referenced image` saat `terraform destroy` | Ada container lain (dibuat manual, di luar kendali Terraform) yang masih memakai image yang sama | Bersihkan container nganggur dengan `docker container prune`, lalu ulangi `terraform destroy` |
| Container environment sebelumnya hilang saat apply environment baru | Semua environment berbagi 1 `terraform.tfstate` (pola `.tfvars` tanpa folder terpisah) | Gunakan pola folder terpisah per environment (masing-masing dengan state sendiri) |

---

## 📌 Insight Penting

- Terraform sebaiknya jadi satu-satunya cara mengelola resource tertentu — mencampur manual (`docker run`) dengan Terraform pada resource yang sama bisa menyebabkan konflik
- `terraform plan` adalah kebiasaan wajib sebelum `apply` — bedakan sikap "hati-hati cek dulu" vs "langsung eksekusi tanpa lihat dampaknya"
- Untuk skenario multi-environment yang serius, folder terpisah per environment (dengan module sebagai blueprint bersama) adalah standar yang dipakai di perusahaan besar — bukan sekadar file `.tfvars` yang berbagi state
- Production selalu diperlakukan lebih hati-hati: review berlapis, akses terbatas, dan state disimpan di remote backend

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 05](../day-05-kubernetes-basics/notes.md)

