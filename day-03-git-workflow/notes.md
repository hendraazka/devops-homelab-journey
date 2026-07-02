# Day 03 — Git & GitHub Workflow (Branching & Pull Request)

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 02](../day-02-networking-volumes/notes.md)

---

## ✅ Yang Dipelajari

- [x] Konsep branching — kenapa gak langsung kerja di `main`
- [x] Membuat branch baru (`git checkout -b`)
- [x] Commit perubahan di branch terpisah
- [x] Push branch ke GitHub
- [x] Membuat Pull Request (PR) dari GitHub
- [x] Review perubahan lewat "Files changed" (diff view)
- [x] Merge PR ke `main`
- [x] Sinkronisasi branch lokal setelah merge (`git pull`)
- [x] Membersihkan branch yang sudah tidak dipakai

---

## 🧠 Konsep Kunci

| Konsep | Penjelasan Singkat |
|---|---|
| **Branch** | Salinan terpisah dari kode, tempat eksperimen/perubahan dilakukan tanpa mengganggu `main` |
| **`main`** | Branch utama yang dianggap "versi stabil/final" dari project |
| **Pull Request (PR)** | Permintaan resmi untuk menggabungkan perubahan dari satu branch ke branch lain, biasanya disertai proses review |
| **Merge** | Proses menggabungkan perubahan dari satu branch ke branch lain |
| **Diff (Files changed)** | Tampilan perbandingan sebelum & sesudah perubahan — hijau (ditambah), merah (dihapus) |
| **Conflict** | Terjadi saat dua branch mengubah baris kode yang sama, sehingga Git tidak bisa otomatis menggabungkannya |

---

## 💻 Alur Kerja Lengkap (Branch → PR → Merge)

### 1. Cek posisi branch saat ini
```bash
git status
git branch
```

### 2. Buat branch baru untuk perubahan/fitur baru
```bash
git checkout -b day-03-git-workflow
```
`-b` artinya membuat branch baru sekaligus berpindah ke branch tersebut.

### 3. Buat perubahan, lalu commit
```bash
git add <nama-file>
git commit -m "pesan commit yang deskriptif"
```

### 4. Push branch (bukan main!) ke GitHub
```bash
git push -u origin day-03-git-workflow
```

### 5. Buat Pull Request di GitHub
- Buka repo di GitHub → klik **"Compare & pull request"**
- Base: `main`, Compare: branch kamu
- Isi judul & deskripsi PR
- Klik **"Create pull request"**

### 6. Review "Files changed"
Cek tab **Files changed** di halaman PR untuk melihat diff — bagian mana yang ditambah (hijau) dan dihapus (merah).

### 7. Merge PR
- Klik **"Merge pull request"** → **"Confirm merge"**
- (Opsional) Klik **"Delete branch"** untuk membersihkan branch yang sudah selesai tugasnya

### 8. Sinkronkan branch lokal
```bash
git checkout main
git pull origin main
```

### 9. Hapus branch lokal yang sudah tidak dipakai
```bash
git branch -d day-03-git-workflow
```

---

## 📌 Insight Penting

- `main` sebaiknya selalu dalam kondisi "bersih/siap pakai" — perubahan eksperimental selalu lewat branch terpisah
- **"No conflicts with base branch"** di GitHub artinya perubahan bisa digabung otomatis tanpa bentrokan
- Setelah PR di-merge di GitHub, branch **lokal** `main` tidak otomatis update — wajib `git pull` manual
- Alur `branch → commit → push → PR → review → merge → sync` ini adalah standar kolaborasi tim di dunia kerja nyata, bukan cuma latihan
- Butuh repetisi berkali-kali sebelum alur ini terasa natural — wajar kalau masih perlu latihan lebih banyak

---

[⬅️ Kembali ke index](../README.md) | [⬅️ Day 02](../day-02-networking-volumes/notes.md)

