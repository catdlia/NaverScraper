# Bato.si Scraper

🇺🇦 Скрипт для автоматичного завантаження манги/манхви з Bato.si на Google Drive.

## ⚡ Основні можливості

- ✅ **Розумна навігація** - автоматично знаходить кнопку "Next" і переходить до наступного розділу.
- ✅ **Resume Capability** - пропускає вже завантажені розділи (перевіряє наявність папки на Drive).
- ✅ **Anti-Loop** - захист від зациклення на одній сторінці.
- ✅ **Webp Support** - завантажує оригінальні `.webp` файли.
- ✅ **Безпечний скролінг** - чекає повного завантаження зображень ("ліниве завантаження").
- ✅ **Структура папок** - Автоматично створює: `Тайтл / Розділ / Файли`.

## 📋 Вимоги

- Python 3.8+
- Google Chrome
- Обліковий запис Google Cloud (для Drive API)
- Linux (Ubuntu) або Windows

## 🚀 Швидкий старт

### 1. Встановлення

```bash
git clone [https://github.com/ВАШ_USERNAME/bato-scraper.git](https://github.com/ВАШ_USERNAME/bato-scraper.git)
cd bato-scraper
pip install -r requirements.txt
