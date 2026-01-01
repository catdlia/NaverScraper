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
    "folder_path": "скани"
  }
}
```

### Налаштування структури папок Google Drive

Параметр `folder_path` визначає, де зберігатимуться файли:

#### Приклад 1: Проста папка в корені

```json
{
  "google_drive": {
    "folder_path": "скани"
  }
}
```

**Результат:** `My Drive/скани/130/`, `My Drive/скани/131/`, ...

#### Приклад 2: Вкладена структура

```json
{
  "google_drive": {
    "folder_path": "TOG/нові розділи/скани"
  }
}
```

**Результат:** `My Drive/TOG/нові розділи/скани/130/`, ...

#### Приклад 3: Збереження в корені

```json
{
  "google_drive": {
    "folder_path": ""
  }
}
```

**Результат:** `My Drive/130/`, `My Drive/131/`, ... (прямо в корені)

#### Приклад 4: Використання існуючої структури

Якщо у вас вже є папка "мої вебтуни/архів":

```json
{
  "google_drive": {
    "folder_path": "мої вебтуни/архів"
  }
}
```

**Результат:** `My Drive/мої вебтуни/архів/130/`, ...

**Важливо:** 
- Скрипт автоматично створить папки, якщо їх не існує
- Номер епізоду завжди додається як окрема підпапка
- Всі скани епізоду зберігаються разом у папці з номером

---

## 6. Перший запуск

### Перевірка налаштувань

```bash
# Перевірте, що всі файли на місці:
ls -la
# Має бути:
# - bato_scraper.py
# - config.json
# - credentials.json
# - requirements.txt
```

### Запуск скрипта

```bash
python bato_scraper.py
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
   - Перевірить кожне зображення
   - Завантажить на Google Drive
   - Перевірить цілісність файлів
   - Перейде до наступного епізоду

### Очікуваний вивід:

```
======================================================================
WEBTOONS SCRAPER v3.1
======================================================================

Введіть номер Webtoon (напр. 174): 174
Введіть ПОЧАТКОВИЙ епізод (напр. 130): 130
Введіть КІНЦЕВИЙ епізод (напр. 135): 135
✓ Google Drive автентифіковано
✓ Структура папок: скани/[номер_епізоду]/

======================================================================
ПАКЕТНЕ ЗАВАНТАЖЕННЯ: Епізоди 130-135
======================================================================

======================================================================
ОБРОБКА ЕПІЗОДУ 130
======================================================================
Налаштування папок для епізоду 130...
  ✓ Знайдено: скани
  ✓ Створено: 130
✓ Папка Google Drive готова: скани/130/

Завантаження сторінки: https://translate.webtoons.com/...
Очікування завершення завантаження (макс 30с)... ✓ Завершено за 3.2с (знайдено 155 зображень)
Прокручування для завантаження всіх зображень...
Очікування завершення завантаження (макс 15с)... ✓ Завершено за 1.5с (знайдено 0 зображень)
Всього унікальних зображень: 155
Аналіз зображень (паралельний режим, 5 потоків)...
[1/155] jPcDMzGRZYav54BZrzsZ.jpg      700x7616, 318.4KB ✓ СКАН
[2/155] sp_translate_svg.png           16x18, 0.2KB ✗ Пропуск
...

✓ Знайдено 9 скан(ів)
Завантаження на Google Drive...
  ✓ Завантажено: jPcDMzGRZYav54BZrzsZ.jpg (318.4 KB)
  ✓ Завантажено: SJ7OgcMG7RxJVuc2mLDt.jpg (391.8 KB)
  ...

✓ Епізод 130: завантажено 9/9 файлів

======================================================================
ОБРОБКА ЕПІЗОДУ 131
======================================================================
...

======================================================================
✓ ПАКЕТНЕ ЗАВАНТАЖЕННЯ ЗАВЕРШЕНО!
======================================================================
Успішно оброблено: 6
З помилками: 0
Всього: 6
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

### "⚠ Завантажено з попередженням"

**Що це означає:**
Розмір файлу на Google Drive відрізняється від оригінального більше ніж на 1%.

**Рішення:**
1. Зазвичай це не критично - Google Drive може трохи стискати файли
2. Якщо хочете перевірити - завантажте файл з Drive і порівняйте візуально
3. Якщо проблема повторюється часто - повідомте в Issues

### Папки створюються не там, де потрібно

**Приклад проблеми:**
Хочете `TOG/скани/130/`, але створюється `скани/130/`

**Рішення:**
Перевірте `folder_path` в `config.json`:

```json
{
  "google_drive": {
    "folder_path": "TOG/скани"  // Не "скани"!
  }
}
```

---

## Додаткові налаштування

### Зміна структури папок

Можете змінити структуру в будь-який момент:

```json
{
  "google_drive": {
    "folder_path": "мої комікси/Tower of God/оригінали"
  }
}
```

Результат: `мої комікси/Tower of God/оригінали/130/`

### Продуктивність

```json
{
  "performance": {
    "max_parallel_downloads": 10  // більше потоків = швидше (1-10)
  }
}
```

⚠️ **Увага:** Більше 10 потоків може спричинити rate limiting.

### Більш м'які фільтри

Якщо пропускає деякі скани:

```json
{
  "image_filters": {
    "min_height": 800,
    "min_width": 300,
    "min_aspect_ratio": 1.2,
    "min_file_size_kb": 80
  }
}
```

---

## Готово!

Тепер ви можете запускати скрипт коли завгодно:

```bash
python bato_scraper.py
```

Наступні запуски будуть автоматичними - логін не потрібен!

Файли зберігатимуться на Google Drive у структурі, яку ви налаштували в `folder_path`.

---

**Потрібна допомога?** Створіть [Issue на GitHub](https://github.com/ВАШ_USERNAME/webtoons-scraper/issues)