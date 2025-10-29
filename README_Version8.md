# Webtoons Scraper

🇺🇦 Скрипт для автоматичного завантаження сканів (оригінальних сторінок комікса) з translate.webtoons.com на Google Drive.

## ⚡ Основні можливості

- ✅ **Автоматичний вхід** через існуючий Chrome профіль
- ✅ **Розумне очікування** - автоматично визначає, коли завантаження завершено
- ✅ **Паралельна обробка** - аналізує 5 зображень одночасно
- ✅ **Оригінальні назви файлів** - зберігає назви з сайту
- ✅ **Пакетне завантаження** - завантажує діапазон епізодів автоматично
- ✅ **Структуровані папки** - автоматично створює `TOG/нові розділи/[епізод]/scans/`

## 📋 Вимоги

- Python 3.8+
- Google Chrome
- Google Cloud Console аккаунт (для Google Drive API)

## 🚀 Швидкий старт

### 1. Клонування репозиторію

```bash
git clone https://github.com/ВАШ_USERNAME/webtoons-scraper.git
cd webtoons-scraper
```

### 2. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 3. Налаштування

#### 3.1 Створення config.json

```bash
cp config.example.json config.json
```

Відредагуйте `config.json`:

```json
{
  "chrome": {
    "user_data_dir": "~/.config/google-chrome-selenium",  // Ваш шлях
    "profile": "Default"
  },
  "google_drive": {
    "base_folder_name": "TOG",  // Назва базової папки
    "subfolder_name": "нові розділи",
    "override_base_folder_id": null  // ID існуючої папки (опціонально)
  }
}
```

#### 3.2 Налаштування Google Drive API

Дивіться детальну інструкцію в [SETUP.md](SETUP.md)

### 4. Запуск

```bash
python webtoons_scraper.py
```

## 📖 Використання

```
Введіть номер Webtoon (напр. 174): 174
Введіть ПОЧАТКОВИЙ епізод (напр. 130): 130
Введіть КІНЦЕВИЙ епізод (напр. 135): 135
```

Скрипт:
1. Відкриє Chrome
2. Попросить увійти в акаунт (тільки перший раз)
3. Автоматично завантажить скани для епізодів 130-135
4. Завантажить їх на Google Drive у структуру: `TOG/нові розділи/130/scans/`

## ⚙️ Конфігурація

### Фільтри зображень

Якщо скрипт не знаходить скани або знаходить зайві файли, налаштуйте фільтри в `config.json`:

```json
{
  "image_filters": {
    "min_height": 1000,          // Мінімальна висота (px)
    "min_width": 400,            // Мінімальна ширина (px)
    "min_aspect_ratio": 1.5,     // Мінімальне співвідношення висота/ширина
    "min_file_size_kb": 100      // Мінімальний розмір файлу (KB)
  }
}
```

### Продуктивність

```json
{
  "performance": {
    "max_parallel_downloads": 5  // Кількість одночасних завантажень (1-10)
  }
}
```

## 🗂️ Структура файлів

```
webtoons-scraper/
├── webtoons_scraper.py      # Головний скрипт
├── config.json              # Ваша конфігурація (НЕ комітити!)
├── config.example.json      # Приклад конфігурації
├── credentials.json         # Google API credentials (НЕ комітити!)
├── token.json              # Google OAuth token (НЕ комітити!)
├── requirements.txt         # Python залежності
├── .gitignore              # Git ignore
├── README.md               # Цей файл
└── SETUP.md                # Детальна інструкція з налаштування
```

## 🔒 Безпека

**ВАЖЛИВО:** Ніколи не комітьте ці файли в Git:
- `config.json` (може містити шляхи до вашої системи)
- `credentials.json` (містить API ключі Google)
- `token.json` (містить OAuth токен)

Вони вже додані в `.gitignore`.

## 🐛 Вирішення проблем

### Chrome не запускається

```bash
# Linux: переконайтесь, що Chrome закритий
pkill -9 -f chrome
```

### "No images found"

1. Переконайтесь, що ви увійшли в акаунт
2. Перевірте, чи є скани в цьому епізоді
3. Знизьте пороги фільтрів у `config.json`

### "File not found: credentials.json"

Завантажте `credentials.json` з Google Cloud Console. Див. [SETUP.md](SETUP.md)

## 📊 Швидкість роботи

- **Один епізод**: ~30-45 секунд
- **10 епізодів**: ~5-7 хвилин
- **Аналіз 150+ зображень**: ~30 секунд (паралельно)

## 📝 Ліцензія

MIT License - використовуйте вільно!

## 🤝 Внесок

Pull requests вітаються! Для великих змін спочатку створіть issue.

## ⭐ Подяки

Створено для збереження контенту з translate.webtoons.com перед закриттям сервісу.

---

**Disclaimer:** Використовуйте тільки для архівування власного перекладацького контенту. Поважайте авторські права.