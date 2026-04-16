#!/bin/bash

# ===================================================================
# REPORT-AI — Otomatik Başlatma Betiği
# ===================================================================

echo "🚀 REPORT-AI başlatılıyor..."

# 1. Sanal ortam (venv) kontrolü ve oluşturma
if [ ! -d "venv" ]; then
    echo "📦 Sanal ortam oluşturuluyor (venv)..."
    python3 -m venv venv
fi

# 2. Sanal ortamı aktif et
source venv/bin/activate

# 3. Bağımlılıkları kontrol et/güncelle
echo "🛠️ Bağımlılıklar kontrol ediliyor..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. .env dosyası kontrolü
if [ ! -f ".env" ]; then
    echo "⚠️ .env dosyası bulunamadı, .env.example'dan oluşturuluyor..."
    cp .env.example .env
fi

# 5. Sunucuyu başlat
echo "✅ Sistem hazır! API başlatılıyor..."
echo "🔗 Dokümantasyon: http://localhost:8000/docs"
echo "-------------------------------------------------------"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
