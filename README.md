# Report-AI: İnşaat Sahası İSG Tespit Sistemi

## Proje Hakkında
Report-AI, inşaat sahalarında iş güvenliğini artırmak için geliştirilmiş bir izleme sistemidir. YOLOv8 nesne tespit modelini kullanarak sahadaki kameralardan gelen görüntüleri analiz eder ve çalışanların kask, yelek, maske gibi koruyucu ekipmanları kullanıp kullanmadığını gerçek zamanlı olarak denetler.

## Sistem Mimarisi
Proje üç ana parçadan oluşmaktadır:

- Frontend: Angular ve TailwindCSS kullanılarak hazırlanan yönetim paneli. Kamera yayınlarını izlemek ve ihlalleri takip etmek için kullanılır.
- Backend: .NET (ASP.NET Core) ile yazılmış ana API. Tüm sistemin veri akışını ve servislerin birbiriyle konuşmasını yönetir.
- AI Servisi: FastAPI üzerinden çalışan Python servisidir. YOLOv8 modelini kullanarak görüntü işleme ve nesne tespiti yapar.

## Temel Özellikler
- Gerçek zamanlı nesne tespiti ve PPE denetimi.
- Kullanıcı paneli üzerinden aktif/pasif kamera yönetimi.
- AI tarafından işlenen görüntünün MJPEG formatında canlı yayını.
- Koruyucu ekipman ihlali yapan personelin anlık raporlanması.
- Python'un AI yetenekleri ile .NET'in kurumsal altyapısının entegrasyonu.

## Kurulum ve Çalıştırma

### 1. AI Servisi (Python)
ai-service klasörüne girip sanal ortamı kurun ve bağımlılıkları yükleyin:
```bash
cd ai-service
python -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python main.py
```

### 2. Backend (.NET)
backend klasöründe projeyi ayağa kaldırın:
```bash
cd backend
dotnet restore
dotnet run --project ReportAi.Orchestrator.Api
```

### 3. Frontend (Angular)
frontend klasöründe paketleri yükleyip uygulamayı başlatın:
```bash
cd frontend
npm install
npm start
```

## Katkıda Bulunma
Projeye yeni özellikler eklemek için ekibi collaborator olarak ekleyebilir ve değişiklikleri pushlayabilirsiniz.

## Lisans
Bu proje MIT lisansı altındadır.
