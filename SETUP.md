# Детальна інструкція з налаштування

## Зміст

1. [Встановлення Python](#1-встановлення-python)
2. [Встановлення залежностей](#2-встановлення-залежностей)
3. [Налаштування Chrome](#3-налаштування-chrome)
4. [Налаштування Google Drive API](#4-налаштування-google-drive-api)
5. [Створення конфігурації](#5-створення-конфігурації)
6. [Перший запуск](#6-перший-запуск)

---

## 1. Встановлення Python

### Перевірка версії

```bash
python --version
# або
python3 --version
```

Потрібна версія **Python 3.8 або новіша**.

### Встановлення (якщо потрібно)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**Windows:**
Завантажте з [python.org](https://www.python.org/downloads/)

**macOS:**
```bash
brew install python3
```

---

## 2. Встановлення залежностей

### Створення віртуального середовища (рекомендовано)

```bash
cd webtoons-scraper
python3 -m venv venv

# Активація
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### Встановлення пакетів

```bash
pip install -r requirements.txt
```

Це встановить:
- `selenium` - автоматизація браузера
- `webdriver-manager` - автоматичне керування ChromeDriver
- `google-api-python-client` - Google Drive API
- `google-auth-oauthlib` - OAuth автентифікація
- `Pillow` - обробка зображень
- `requests` - HTTP запити

---

## 3. Налаштування Chrome

### Варіант A: Окремий профіль (рекомендовано)

Створіть новий профіль спеціально для скрипта:

```json
{
  "chrome": {
    "user_data_dir": "~/.config/google-chrome-selenium",
    "profile": "Default"
  }
}
```

**Переваги:**
- ✅ Не потребує закриття основного Chrome
- ✅ Ізольовані cookies та налаштування
- ✅ Безпечніше

**При першому запуску:**
1. Скрипт створить новий профіль
2. Вам потрібно увійти в translate.webtoons.com
3. Наступні запуски будуть автоматичними

### Варіант B: Використання існуючого профілю

Знайдіть шлях до вашого Chrome профілю:

**Linux:**
```bash
~/.config/google-chrome
```

**Windows:**
```
C:\Users\ВАШ_КОРИСТУВАЧ\AppData\Local\Google\Chrome\User Data
```

**macOS:**
```bash
~/Library/Application Support/Google/Chrome
```

**Знайдіть назву профілю:**

1. Відкрийте Chrome
2. Введіть в адресну строку: `chrome://version/`
3. Знайдіть рядок "Profile Path"
4. Назва профілю - остання частина шляху (напр. "Profile 1", "Default")

**Налаштуйте config.json:**

```json
{
  "chrome": {
    "user_data_dir": "/home/ВАШ_КОРИСТУВАЧ/.config/google-chrome",
    "profile": "Profile 1"
  }
}
```

⚠️ **ВАЖЛИВО:** При цьому варіанті Chrome має бути **повністю закритий** перед запуском скрипта!

```bash
# Linux: закрити всі процеси Chrome
pkill -9 -f chrome
```

---

## 4. Налаштування Google Drive API

### Крок 1: Створення проекту в Google Cloud Console

1. Перейдіть на [Google Cloud Console](https://console.cloud.google.com/)
2. Клікніть **"Select a Project"** → **"New Project"**
3. Введіть назву (напр. "Webtoons Scraper")
4. Клікніть **"Create"**

### Крок 2: Увімкнення Google Drive API

1. В меню зліва виберіть **"APIs & Services"** → **"Library"**
2. Знайдіть **"Google Drive API"**
3. Клікніть на нього
4. Натисніть **"Enable"**

### Крок 3: Створення OAuth 2.0 Credentials

1. Перейдіть в **"APIs & Services"** → **"Credentials"**
2. Клікніть **"Create Credentials"** → **"OAuth client ID"**

3. **Якщо з'явиться попередження "Configure consent screen":**
   - Клікніть **"Configure consent screen"**
   - User Type: **External**
   - Клікніть **"Create"**
   - App name: **"Webtoons Scraper"**
   - User support email: **ваш email**
   - Developer contact: **ваш email**
   - Натисніть **"Save and Continue"**
   - **Scopes**: пропустіть (Save and Continue)
   - **Test users**: пропустіть (Save and Continue)
   - Клікніть **"Back to Dashboard"**

4. **Поверніться до створення credentials:**
   - **"APIs & Services"** → **"Credentials"**
   - **"Create Credentials"** → **"OAuth client ID"**
   - Application type: **Desktop app**
   - Name: **"Webtoons Scraper Client"**
   - Клікніть **"Create"**

5. **Завантаження credentials:**
   - Клікніть **"Download JSON"**
   - **Перейменуйте** файл на `credentials.json`
   - **Помістіть** в папку зі скриптом

### Крок 4: Структура credentials.json

Файл має виглядати приблизно так:

```json
{
  "installed": {
    "client_id": "143633685933-...apps.googleusercontent.com",
    "project_id": "webtoons-scraper-...",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_secret": "GOCSPX-...",
    "redirect_uris": ["http://localhost"]
  }
}
```

---

## 5. Створення конфігурації

### Базова конфігурація

```bash
cp config.example.json config.json
```

Відредагуйте `config.json`:

```json
{
  "chrome": {
    "user_data_dir": "~/.config/google-chrome-selenium",
    "profile": "Default"
  },
  "image_filters": {
    "min_height": 1000,
    "min_width": 400,
    "min_aspect_ratio": 1.5,
    "min_file_size_kb": 100
  },
  "performance": {
    "max_parallel_downloads": 5
  },
  "google_drive": {
    "credentials_file": "credentials.json",
    "token_file": "token.json",
    "base_folder_name": "TOG",
    "subfolder_name": "нові розділи",
    "override_base_folder_id": null
  }
}
```

### Опціонально: Використання існуючої папки Google Drive

Якщо у вас вже є папка "TOG" на Drive і ви хочете уникнути дублікатів:

1. Відкрийте Google Drive в браузері
2. Знайдіть папку "TOG"
3. Клікніть правою кнопкою → **"Get link"** (або відкрийте папку)
4. Скопіюйте ID з URL:
   ```
   https://drive.google.com/drive/folders/0AItQ6yo4MeB-Uk9PVA
                                         ^^^^^^^^^^^^^^^^^^^^
                                         Це ID папки
   ```
5. Додайте в `config.json`:
   ```json
   {
     "google_drive": {
       "override_base_folder_id": "0AItQ6yo4MeB-Uk9PVA"
     }
   }
   ```

---

## 6. Перший запуск

### Перевірка налаштувань

```bash
# Перевірте, що всі файли на місці:
ls -la
# Має бути:
# - webtoons_scraper.py
# - config.json
# - credentials.json
# - requirements.txt
```

### Запуск скрипта

```bash
python webtoons_scraper.py
```

### Що відбудеться:

1. **Google OAuth (перший раз):**
   - Відкриється браузер
   - Виберіть ваш Google акаунт
   - Натисніть **"Allow"** для доступу до Google Drive
   - Створиться файл `token.json` (він буде використовуватись надалі)

2. **Chrome запуститься:**
   - Відкриється вікно Chrome
   - Якщо використовуєте новий профіль, браузер буде порожній

3. **Вхід в Webtoons (перший епізод):**
   ```
   ⚠️  НЕОБХІДНИЙ ВХІД В АКАУНТ
   ====================================
   1. Має відкритися вікно Chrome
   2. Увійдіть в акаунт на translate.webtoons.com
   3. Переконайтесь, що інтерфейс перекладу завантажився
   4. Натисніть Enter тут після входу
   ====================================
   👉 Натисніть Enter після входу...
   ```

4. **Автоматична обробка:**
   - Скрипт знайде скани
   - Завантажить на Google Drive
   - Перейде до наступного епізоду

### Очікуваний вивід:

```
======================================================================
WEBTOONS SCRAPER v3.0
======================================================================

Введіть номер Webtoon (напр. 174): 174
Введіть ПОЧАТКОВИЙ епізод (напр. 130): 130
Введіть КІНЦЕВИЙ епізод (напр. 135): 135
✓ Google Drive автентифіковано

Використання Chrome профілю: ~/.config/google-chrome-selenium/Default
Запуск Chrome драйвера...
✓ Chrome драйвер запущено успішно

======================================================================
ПАКЕТНЕ ЗАВАНТАЖЕННЯ: Епізоди 130-135
======================================================================

======================================================================
ОБРОБКА ЕПІЗОДУ 130
======================================================================
Налаштування папок для епізоду 130...
  ✓ Знайдено: TOG
  ✓ Знайдено: нові розділи
  ✓ Створено: 130
  ✓ Створено: scans
✓ Папка Google Drive готова

Завантаження сторінки: https://translate.webtoons.com/...
Очікування завершення завантаження (макс 30с)... ✓ Завершено за 3.2с (знайдено 155 зображень)
Всього унікальних зображень: 155
Аналіз зображень (паралельний режим, 5 потоків)...
[1/155] jPcDMzGRZYav54BZrzsZ.jpg      700x7616, 318.4KB ✓ СКАН
[2/155] sp_translate_svg.png           16x18, 0.2KB ✗ Пропуск
...

✓ Знайдено 9 скан(ів)
Завантаження на Google Drive...
  ✓ Завантажено: jPcDMzGRZYav54BZrzsZ.jpg
  ✓ Завантажено: SJ7OgcMG7RxJVuc2mLDt.jpg
  ...
✓ Епізод 130 успішно оброблено
```

---

## Вирішення проблем

### "credentials.json not found"

**Рішення:**
1. Завантажте credentials.json з Google Cloud Console
2. Перейменуйте на `credentials.json` (маленькими літерами)
3. Помістіть в папку зі скриптом

### "ChromeDriver version mismatch"

**Рішення:**
`webdriver-manager` має автоматично завантажити правильну версію. Якщо ні:

```bash
pip install --upgrade webdriver-manager
```

### "Chrome is already running" (тільки для існуючого профілю)

**Рішення:**

```bash
# Linux/Mac:
pkill -9 -f chrome

# Windows (Task Manager):
# Закрийте всі процеси chrome.exe
```

### "No images found"

**Причини:**
1. Не увійшли в акаунт
2. Епізод не має сканів
3. Занадто суворі фільтри

**Рішення:**
Знизьте пороги в `config.json`:

```json
{
  "image_filters": {
    "min_height": 500,           // було 1000
    "min_width": 300,            // було 400
    "min_aspect_ratio": 1.0,     // було 1.5
    "min_file_size_kb": 50       // було 100
  }
}
```

### "Invalid folder ID"

**Причина:** ID папки з `override_base_folder_id` недійсний

**Рішення:**
1. Перевірте ID папки на Google Drive
2. Або встановіть `"override_base_folder_id": null`

---

## Додаткові налаштування

### Зміна структури папок

```json
{
  "google_drive": {
    "base_folder_name": "Мої_Вебтуни",
    "subfolder_name": "архів"
  }
}
```

Результат: `Мої_Вебтуни/архів/130/scans/`

### Продуктивність

```json
{
  "performance": {
    "max_parallel_downloads": 10  // більше потоків = швидше (1-10)
  }
}
```

⚠️ **Увага:** Більше 10 потоків може спричинити rate limiting.

---

## Готово!

Тепер ви можете запускати скрипт коли завгодно:

```bash
python webtoons_scraper.py
```

Наступні запуски будуть автоматичними - логін не потрібен!

---

**Потрібна допомога?** Створіть [Issue на GitHub](https://github.com/ВАШ_USERNAME/webtoons-scraper/issues)
