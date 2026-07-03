# Day 07 — Configuration Management dengan Ansible

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 06](../day-06-terraform/notes.md)

---

## ✅ Yang Dipelajari

- [x] Konsep Configuration Management dan bedanya dengan Infrastructure as Code (Terraform)
- [x] Install Ansible
- [x] Inventory — mendaftarkan target/mesin yang dikelola
- [x] Ad-hoc command — perintah cepat satu baris (`ping`, `command`, `file`)
- [x] Playbook — konfigurasi dalam file YAML (pendekatan proper/reusable)
- [x] Konsep **idempotency** — playbook aman dijalankan berkali-kali
- [x] Variables — konfigurasi yang fleksibel (`vars`, `--extra-vars`)
- [x] Handlers — aksi yang hanya dijalankan saat ada perubahan (`notify`)
- [x] Debugging: memahami perbedaan status `ok` vs `changed`, cek `systemd` di WSL

---

## 🧠 Konsep Kunci

| Konsep | Penjelasan Singkat |
|---|---|
| **Configuration Management** | Mengatur/konfigurasi isi dari server atau mesin yang sudah ada (install software, atur file konfigurasi, dll) |
| **Agentless** | Ansible tidak butuh software tambahan terinstall di target, cukup pakai SSH (atau koneksi lokal) |
| **Idempotent** | Menjalankan playbook yang sama berkali-kali menghasilkan kondisi akhir yang konsisten, tanpa duplikasi atau error |
| **Inventory** | Daftar mesin/target yang dikelola Ansible |
| **Module** | Unit fungsi Ansible untuk melakukan aksi tertentu (`apt`, `file`, `copy`, `service`, dll) |
| **Playbook** | File YAML berisi kumpulan task yang dijalankan berurutan terhadap target |
| **Handler** | Task khusus yang hanya dipanggil ketika ada task lain yang berstatus `changed` |

### Terraform vs Ansible

| | Terraform | Ansible |
|---|---|---|
| Fokus | Membuat infrastruktur (server, container, network) | Mengatur konfigurasi di dalam infrastruktur yang sudah ada |
| Analoginya | Tukang bangunan yang membuat rumah | Tukang yang mengatur isi rumah (listrik, furniture) |
| Biasa dipakai bersamaan | Terraform bikin server dulu → | Ansible setup software di dalamnya |

---

## 💻 Setup Awal

```bash
sudo apt update
sudo apt install ansible -y
ansible --version
```

---

## 📁 Inventory

```bash
nano inventory.ini
```
```ini
[local]
localhost ansible_connection=local
```

---

## 💻 Ad-hoc Commands

```bash
# Cek konektivitas
ansible -i inventory.ini local -m ping

# Jalankan perintah shell
ansible -i inventory.ini local -m command -a "uname -a"

# Bikin folder
ansible -i inventory.ini local -m file -a "path=/home/hamizan/test-ansible state=directory"
```

---

## 📄 Playbook Lengkap (dengan Variables & Handlers)

`setup-web-server.yml`:
```yaml
---
- name: Setup Web Server
  hosts: local
  become: yes

  vars:
    web_project_path: /home/hamizan/ansible-web-project
    site_title: "Halo dari Ansible Playbook!"
    nginx_package: nginx

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes

    - name: Install nginx
      apt:
        name: "{{ nginx_package }}"
        state: present

    - name: Pastikan folder project ada
      file:
        path: "{{ web_project_path }}"
        state: directory

    - name: Bikin file index.html sederhana
      copy:
        content: "<h1>{{ site_title }}</h1>"
        dest: "{{ web_project_path }}/index.html"
      notify: Restart nginx

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted
```

### Jalankan Playbook

```bash
ansible-playbook -i inventory.ini setup-web-server.yml --ask-become-pass
```

### Override Variable dari Command Line (tanpa edit file)

```bash
ansible-playbook -i inventory.ini setup-web-server.yml --ask-become-pass \
  --extra-vars "site_title='Halo dari Environment Berbeda!'"
```

---

## 🔬 Eksperimen: Membuktikan Idempotency

**Run pertama** (kondisi awal, belum ada apa-apa):
```
TASK [Install nginx] → changed
TASK [Pastikan folder project ada] → changed
TASK [Bikin file index.html sederhana] → changed
PLAY RECAP: ok=5  changed=3  failed=0
```

**Run kedua** (dijalankan ulang tanpa ada perubahan apapun):
```
TASK [Install nginx] → ok
TASK [Pastikan folder project ada] → ok
TASK [Bikin file index.html sederhana] → ok
PLAY RECAP: ok=5  changed=0  failed=0
```

**Insight:** Ansible mengecek dulu kondisi saat ini sebelum bertindak. Kalau sudah sesuai yang diinginkan, tidak melakukan apa-apa lagi (`ok`) — bukan menjalankan ulang instalasi/perintah dari nol. Ini yang membuatnya aman dijalankan berkali-kali, bahkan ke ratusan server sekaligus, tanpa risiko error "already installed" atau duplikasi konfigurasi.

---

## 🔬 Eksperimen: Handlers — Restart Hanya Saat Perlu

**Kondisi 1 — tidak ada perubahan pada isi `index.html`:**
Task "Bikin file index.html" berstatus `ok` → handler `Restart nginx` **tidak dipanggil** (tidak ada baris `RUNNING HANDLER` di output). Nginx tetap jalan tanpa gangguan.

**Kondisi 2 — `site_title` diubah, sehingga isi file berubah:**
Task "Bikin file index.html" berstatus `changed` → handler `Restart nginx` **otomatis dipanggil**:
```
RUNNING HANDLER [Restart nginx] ****
changed: [localhost]
```

**Insight:** Handler membuat proses lebih efisien — service hanya di-restart ketika benar-benar ada perubahan konfigurasi yang membutuhkan restart, bukan setiap kali playbook dijalankan.

---

## 🔧 Troubleshooting yang Dialami

| Masalah | Penyebab | Solusi |
|---|---|---|
| `[WARNING]: Unable to parse ... as an inventory source` | Typo nama file inventory (mis. `intentory.ini`) sehingga file yang dimaksud tidak ditemukan/kosong | Cek nama file dengan `ls -la`, pastikan nama pada perintah `-i` sesuai persis, verifikasi isi dengan `cat inventory.ini` |
| Handler tidak jalan meski sudah pakai `notify` | Task terkait berstatus `ok` (tidak ada perubahan nyata pada file), bukan `changed` — sehingga handler memang tidak dipicu, sesuai desain | Ubah value variable yang memengaruhi konten (misal `site_title`) agar task benar-benar `changed`, baru handler terpicu |
| Sempat curiga masalah `systemd` di WSL | WSL versi lama kadang tidak menjalankan `systemd` secara default | Cek dengan `ps -p 1` — kalau hasilnya `systemd`, artinya module `service` seharusnya berfungsi normal, bukan sumber masalah |

---

## 📌 Insight Penting

- Ansible dan Terraform sering dipakai berdampingan: Terraform membuat infrastruktur, Ansible mengonfigurasi isinya
- Sifat **agentless** membuat Ansible mudah diadopsi — cukup koneksi SSH (atau lokal), tanpa install software tambahan di setiap target
- Status `ok` vs `changed` adalah kunci untuk membaca output Ansible dengan benar — `ok` bukan berarti gagal, tapi berarti "kondisi sudah sesuai, tidak ada yang perlu diubah"
- Selalu cek isi/kondisi aktual sebelum menyimpulkan ada bug — banyak "masalah" yang sebenarnya adalah Ansible bekerja sesuai desain (idempotency, handler)

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 06](../day-06-terraform/notes.md)

