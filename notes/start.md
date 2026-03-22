# 📌 **Judul Terpilih**

**“Enhancing Microservices API Security using JWT and Rate Limiting: A Performance Evaluation”**

---

## 🧠 **Inti Ide Penelitian**

Penelitian ini bertujuan untuk:

* Meningkatkan **keamanan API pada arsitektur microservices**
* Menggunakan:

  * **JWT (JSON Web Token)** untuk autentikasi
  * **Rate limiting** untuk mitigasi request berlebih / abuse
* Mengevaluasi:

  * Dampak terhadap **performa sistem**
  * Efektivitas dalam menghadapi **request burst / attack sederhana**

---

## 🎯 **Kontribusi Utama**

* Pendekatan **lightweight security** (mudah diimplementasikan)
* Evaluasi **security vs performance**
* Studi kasus berbasis **microservices sederhana**

---

## ⚙️ **Gambaran Sistem**

* 2–3 microservices (contoh: user, product, order)
* API gateway (opsional, tapi disarankan)
* JWT-based authentication
* Rate limiting mechanism

---

## 🧪 **Metodologi Singkat**

Bandingkan 2 kondisi:

1. Tanpa security mechanism
2. Dengan JWT + rate limiting

Metrik evaluasi:

* Response time (latency)
* Throughput
* Error rate saat high traffic

---

## 📊 **Output yang Diharapkan**

* Ada trade-off kecil (latency naik sedikit)
* Tapi sistem lebih stabil & aman
* Insight praktis untuk implementasi microservices

---

# 🚀 **Next Steps (yang akan kita kerjakan)**

Nanti kita breakdown satu per satu:

## 1. 🔧 Step-by-step implementasi

* Setup microservices
* Implement JWT
* Tambah rate limiting
* Setup environment testing

## 2. 🧪 Template eksperimen & load testing

* Cara generate traffic (normal vs attack)
* Tools (misal: k6 / JMeter)
* Format pengambilan data

## 3. 📝 Outline paper IEEE

* Abstract
* Introduction
* Methodology
* Results & Discussion
* Conclusion
