# Release Notes — Milestone 3

**Project:** SiCure Procurement System
**Version:** 1.0.0
**Release Date:** June 2026

---

# Overview

Milestone 3 berfokus pada penyelesaian implementasi sistem procurement berbasis microservices, peningkatan keamanan aplikasi, monitoring layanan, serta penyempurnaan alur bisnis Purchase Requisition (PR), Purchase Order (PO), dan Goods Receipt Note (GRN).

Pada milestone ini seluruh layanan inti berhasil diintegrasikan dan siap digunakan melalui API Gateway.

---

# New Features

## Authentication Service

Fitur yang berhasil ditambahkan:

* User Authentication menggunakan JWT
* Refresh Token Mechanism
* Logout dan Token Revocation
* User Profile Endpoint
* Token Verification Endpoint
* Health Check Endpoint
* Metrics Endpoint

---

## Purchase Requisition Module

Fitur yang berhasil ditambahkan:

* Pembuatan Purchase Requisition
* Melihat daftar Purchase Requisition
* Detail Purchase Requisition
* Update Purchase Requisition
* Delete Purchase Requisition
* Kategori Item Management
* Filtering dan Pagination

---

## Purchase Requisition Review

Fitur admin:

* Melihat seluruh Purchase Requisition
* Filter berdasarkan status
* Filter berdasarkan requester
* Filter berdasarkan kategori
* Approve Purchase Requisition
* Reject Purchase Requisition

---

## Purchase Order Module

Fitur yang berhasil ditambahkan:

* Generate Purchase Order dari PR yang telah disetujui
* Alokasi budget otomatis
* Validasi satu Purchase Order untuk satu PR
* Daftar Purchase Order
* View Purchase Order oleh requester

---

## Goods Receipt Note (GRN)

Fitur yang berhasil ditambahkan:

* Upload Commercial Invoice
* Upload Goods Photo
* Validasi ukuran file
* Validasi tipe file
* Penyimpanan dokumen GRN
* View dokumen GRN

---

## GRN Verification

Fitur admin:

* Verifikasi dokumen GRN
* Workflow status VERIFIED
* Workflow status CLOSED
* Catatan verifikasi (verification note)

---

# Security Improvements

Peningkatan keamanan yang diterapkan:

* JWT Authentication
* Role Based Access Control (RBAC)
* Token Verification antar Service
* Token Revocation saat Logout
* File Type Validation
* File Size Validation
* Request Body Size Limitation
* Input Validation
* CORS Configuration

---

# Monitoring & Reliability

Fitur monitoring dan reliability:

* Health Check Endpoint
* Aggregated Service Health Monitoring
* Database Connectivity Check
* Auth Service Availability Check
* Circuit Breaker Monitoring
* Metrics Endpoint
* Structured API Response

---

# Procurement Workflow

```text
Requester
    ↓
Create Purchase Requisition
    ↓
SUBMITTED
    ↓
Admin Review
    ↓
APPROVED / REJECTED
    ↓
Purchase Order Issued
    ↓
PO_ISSUED
    ↓
Requester Upload GRN
    ↓
DOC_SUBMITTED
    ↓co
    
Admin Verification
    ↓
VERIFIED
    ↓
CLOSED
```

---

# Technical Stack

## Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* JWT Authentication

## Infrastructure

* Docker
* Docker Compose
* Railway Deployment

## Monitoring

* Health Checks
* Metrics Endpoint
* Circuit Breaker Pattern

---

# Known Limitations

* Dashboard analytics belum tersedia
* Export laporan procurement belum tersedia
* Notifikasi email belum tersedia
* Audit logging masih dapat dikembangkan lebih lanjut

---

# Release Summary

Milestone 3 berhasil menyelesaikan implementasi sistem procurement end-to-end mulai dari pengajuan Purchase Requisition, persetujuan oleh admin, penerbitan Purchase Order, pengunggahan dokumen Goods Receipt Note, hingga proses verifikasi dan penutupan transaksi. Sistem telah dilengkapi dengan mekanisme keamanan, monitoring, serta dokumentasi yang mendukung proses deployment dan operasional aplikasi.
