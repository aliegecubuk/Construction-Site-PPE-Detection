#!/bin/bash
# =================================================================
# REPORT-AI — Geliştirme Sunucusunu Başlat
# =================================================================
# Kullanım: bash scripts/start_dev.sh

echo "🚀 REPORT-AI Geliştirme Sunucusu Başlatılıyor..."

# Proje kök dizinine git
cd "$(dirname "$0")/.." || exit 1

# .env dosyası yoksa .env.example'dan oluştur
if [ ! -f .env ]; then
    echo "📋 .env dosyası bulunamadı, .env.example kopyalanıyor..."
    cp .env.example .env
fi

# Sunucuyu başlat
echo "🌐 http://localhost:8000/docs adresinde Swagger UI açılacak"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
