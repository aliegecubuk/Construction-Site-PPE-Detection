# REPORT-AI — Mimari Dokümantasyonu

Bu doküman, REPORT-AI projesinin mimari yapısını açıklar.

Detaylı mimari planı için `implementation_plan.md`'ye bakınız.

## Katman Yapısı

```
Controller (API Router)  →  İstekleri alır, Service'e delege eder
        ↓
Service (İş Mantığı)     →  Karar mekanizmaları ve iş kuralları
        ↓
Repository (Veri Erişimi) →  CRUD operasyonları (in-memory → PostgreSQL)
        ↓
Database (İleride)        →  PostgreSQL
```

## Bağımsız Modüller

- **`ai/`**: YOLO model inference, kamera yönetimi
- **`iot/`**: Sensör verisi simülasyonu ve toplama

## Hızlı Başlangıç

```bash
cd ai-service
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs
