# Report-AI: İnşaat Sahası İSG PPE Tespit Sistemi

![Report-AI Banner](docs/assets/videoconstruc2.gif)

## 🏢 Proje Hakkında
**Report-AI**, inşaat sahalarında iş sağlığı ve güvenliğini (İSG) artırmak için geliştirilmiş, yapay zeka destekli bir karar destek sistemidir. Sistem, kameralardan gelen görüntüleri gerçek zamanlı olarak analiz ederek kask, yelek ve maske gibi kişisel koruyucu donanımların (PPE) kullanımını denetler.

---

## 🚀 Sistem Mimarisi
Proje, her biri modern teknolojilerle geliştirilmiş 3 ana servisten oluşan bir **Monorepo** yapısındadır:

| Servis | Teknoloji | Görevi |
| :--- | :--- | :--- |
| **Frontend Dashboard** | Angular + TailwindCSS | Canlı kamera izleme, ihlal logları ve kamera yönetimi. |
| **Orchestrator Backend** | .NET (ASP.NET Core) | Veri yönetimi, API orkestrasyonu ve iş mantığı. |
| **AI Processing Service** | FastAPI + YOLOv8 | Görüntü işleme, nesne tespiti ve MJPEG yayını. |

---

## 🛠️ Temel Özellikler
- 🛡️ **Gerçek Zamanlı Tespit:** YOLOv8n modeli ile yüksek doğrulukta PPE denetimi.
- 📹 **Kamera Yönetimi:** Aktif/Pasif kamera durum kontrolü (Passive Alerts).
- ⚡ **MJPEG Streaming:** AI tarafından işlenmiş görüntünün doğrudan tarayıcı üzerinden izlenmesi.
- 🚨 **İhlal Takibi:** Kask veya yelek takmayan işçilerin anlık olarak sistem üzerinde raporlanması.
- 📊 **Hibrit Mimari:** Python'un AI gücü ile .NET'in kurumsal gücünün entegrasyonu.

---

## 📂 Kurulum Notları

### 1. AI Servisi (Python)
```bash
cd ai-service
python -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python main.py
```

### 2. Backend (.NET)
```bash
cd backend
dotnet restore
dotnet run --project ReportAi.Orchestrator.Api
```

### 3. Frontend (Angular)
```bash
cd frontend
npm install
npm start
```

---

## 👤 Geliştirici & Katkıda Bulunma
Bu proje **Report-AI** ekibi tarafından geliştirilmiştir. İş birliği yapmak için arkadaşınızı Collaborator olarak ekleyebilir ve `git pull`/`git push` ile ortak çalışmaya başlayabilirsiniz.

---

## 📝 Lisans
Bu proje MIT lisansı ile korunmaktadır.
