# REPORT-AI Lokal Çalıştırma

Bu dosya Angular, .NET Orchestrator ve Python FastAPI katmanlarını birlikte ayağa kaldırmak için eklendi.

Başlatma:

```bash
bash start.sh
```

veya

```bash
bash infrastructure/scripts/run_report_ai_stack.sh
```

Durdurma:

```bash
bash stop.sh
```

veya

```bash
bash infrastructure/scripts/stop_report_ai_stack.sh
```

Adresler:

- Angular UI: `http://localhost:4200`
- .NET API: `http://localhost:8080/api/cameras`
- SignalR Hub: `http://localhost:8080/hubs/alerts`
- Python Swagger: `http://localhost:8000/docs`
- Python MJPEG örneği: `http://localhost:8000/api/v1/stream/mjpeg/camera_1`

Notlar:

- Python katmanı `ai-service/venv` içindeki sanal ortamı kullanır.
- Angular katmanı `frontend/node_modules` hazır değilse önce `npm install` çalıştırılmalıdır.
- Python kamera kaynakları `ai-service/ai/config/camera_class_map.json` içinden okunur ve şu an `data/videos/` klasöründeki 4 farklı MP4 dosyasına bağlanır.
