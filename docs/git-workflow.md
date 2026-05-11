# Git Workflow Guide

Dokumen ini digunakan sebagai panduan workflow Git dalam pengerjaan project tim agar proses development lebih terstruktur dan memudahkan kolaborasi antar anggota.

---

## 1. Branch Naming Convention

Setiap fitur atau perubahan wajib dikerjakan pada branch terpisah.

Format penamaan branch:

```bash
feature/nama-fitur
fix/nama-bug
docs/nama-dokumentasi
chore/nama-task
```

Contoh:

```bash
feature/dark-mode
feature/item-categories
feature/changelog
docs/git-workflow-guide
```

---

## 2. Commit Message Convention

Commit menggunakan format Conventional Commits agar riwayat perubahan lebih mudah dipahami.

Format:

```bash
type: deskripsi perubahan
```

Jenis commit yang digunakan:

| Type | Keterangan |
|------|-------------|
| feat | Menambahkan fitur baru |
| fix | Memperbaiki bug |
| docs | Perubahan dokumentasi |
| chore | Perubahan maintenance/setup |
| refactor | Perbaikan struktur kode |
| test | Penambahan atau perubahan testing |

Contoh commit:

```bash
feat: add dark mode feature
fix: repair category filter
docs: add git workflow guide
```

---

## 3. Workflow Pengerjaan

Berikut alur workflow yang digunakan oleh tim:

1. Pull/update branch `main`
2. Membuat branch baru sesuai tugas
3. Mengerjakan fitur pada branch masing-masing
4. Commit perubahan menggunakan conventional commits
5. Push branch ke GitHub
6. Membuat Pull Request (PR)
7. Meminta review dari anggota lain
8. Melakukan perbaikan jika diperlukan
9. Merge ke `main` menggunakan **Squash and Merge**
10. Menghapus branch setelah merge

---

## 4. Pull Request Rules

Setiap Pull Request wajib memenuhi ketentuan berikut:

- Menggunakan title dengan format Conventional Commits
- Memiliki deskripsi perubahan
- Memiliki minimal 1 reviewer
- Memiliki minimal 1 review comment
- Menggunakan metode **Squash and Merge**
- Branch dihapus setelah proses merge selesai

Contoh title PR:

```bash
feat: implement dark mode
```

---

## 5. Code Review Guidelines

Reviewer bertugas memastikan bahwa perubahan yang dibuat sudah sesuai dan tidak menimbulkan masalah pada project.

Hal yang diperiksa saat review:

- Fitur berjalan dengan baik
- Tidak merusak fitur lain
- Penulisan kode rapi dan mudah dipahami
- Tidak ada file yang tidak diperlukan
- Dokumentasi diperbarui jika diperlukan

Reviewer dapat memberikan:

- Approve
- Request Changes
- Comment atau saran perbaikan

---

## 6. CODEOWNERS Reference

Project menggunakan file `CODEOWNERS` untuk membantu pembagian review sesuai area masing-masing anggota.

Contoh:

```bash
/frontend @frontend-lead
/backend @backend-lead
/docs @qa-docs-lead
```

Dengan adanya CODEOWNERS, proses review menjadi lebih terarah dan terorganisir.

---

## 7. Struktur Workflow Branch

```bash
main
├── feature/dark-mode
├── feature/item-categories
├── feature/changelog
└── docs/git-workflow-guide
```

Setiap branch akan melalui proses Pull Request sebelum digabungkan ke branch `main`.

---

## 8. Penutup

Workflow Git yang terstruktur membantu tim dalam mengelola perubahan kode, mempermudah proses kolaborasi, serta mengurangi konflik saat development berlangsung.