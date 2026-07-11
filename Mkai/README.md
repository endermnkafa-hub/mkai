# MKAI

MKAI, geleceğe hazır bir AI asistanı platformu için kurulan production-grade temel projedir. FastAPI tabanlı bir backend, Next.js tabanlı bir frontend, SQLAlchemy tabanlı veri katmanı ve modüler bir mimari sunar.

## Mimari Özeti

- Backend: FastAPI, Pydantic, SQLAlchemy, Uvicorn
- Frontend: Next.js, TypeScript, Tailwind CSS
- Güvenlik: CORS, yapılandırma yönetimi ve hata işleme
- Ölçeklenebilirlik: servis, şema, model, API ve bileşen katmanları ayrılmıştır

## Özellikler

- Yerel geliştirme ortamında çalışan chat arayüzü
- Async servis katmanı
- SQLAlchemy tabanlı mesaj modeli ve veri erişim katmanı
- Merkezi exception ve validation yönetimi
- Frontend bileşenleri ile yeniden kullanılabilir UI yapısı

## Hızlı Başlangıç

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
node .\node_modules\next\dist\bin\next dev -p 3001
```

### Testler

```powershell
cd backend
python -m pytest -q
```

## Yapı

- backend/app/api/v1: API rotaları
- backend/app/core: yapılandırma, veritabanı, exception ve ortak yardımcılar
- backend/app/models: SQLAlchemy modelleri
- backend/app/schemas: Pydantic şemaları
- backend/app/services: iş mantığı hizmetleri
- frontend/src/app: Next.js sayfa yapısı
- frontend/src/components: yeniden kullanılabilir UI bileşenleri
- frontend/src/lib: API yardımcıları
