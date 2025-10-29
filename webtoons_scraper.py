"""
Webtoons Scan Scraper - GitHub Release v3.1

Скрипт для завантаження сканів з translate.webtoons.com на Google Drive
"""

import os
import re
import time
import json
import requests
from io import BytesIO
from PIL import Image
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from webdriver_manager.chrome import ChromeDriverManager

# ============================================================================
# CONFIGURATION
# ============================================================================

def load_config():
    """Завантажує конфігурацію з config.json"""
    config_file = 'config.json'

    if not os.path.exists(config_file):
        if os.path.exists('config.example.json'):
            print("⚠ config.json не знайдено!")
            print("📝 Створюємо config.json з config.example.json...")
            with open('config.example.json', 'r', encoding='utf-8') as f:
                example = json.load(f)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(example, f, indent=2, ensure_ascii=False)
            print("✓ config.json створено!")
            print("\n⚠ УВАГА: Відредагуйте config.json перед запуском!")
            input("\nНатисніть Enter після редагування config.json...")
        else:
            raise FileNotFoundError(
                "config.json та config.example.json не знайдено!\n"
                "Створіть config.json на основі прикладу з документації."
            )

    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

CONFIG = load_config()

# Chrome налаштування
CHROME_USER_DATA_DIR = os.path.expanduser(CONFIG['chrome']['user_data_dir'])
CHROME_PROFILE = CONFIG['chrome']['profile']

# Фільтри зображень
MIN_IMAGE_HEIGHT = CONFIG['image_filters']['min_height']
MIN_IMAGE_WIDTH = CONFIG['image_filters']['min_width']
MIN_ASPECT_RATIO = CONFIG['image_filters']['min_aspect_ratio']
MIN_FILE_SIZE_KB = CONFIG['image_filters']['min_file_size_kb']

# Паралельна обробка
MAX_PARALLEL_DOWNLOADS = CONFIG['performance']['max_parallel_downloads']

# Google Drive налаштування
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = CONFIG['google_drive']['credentials_file']
TOKEN_FILE = CONFIG['google_drive']['token_file']

# ⭐ НОВА СПРОЩЕНА СТРУКТУРА
FOLDER_PATH = CONFIG['google_drive'].get('folder_path', 'скани')  # За замовчуванням "скани"

# ============================================================================
# WebDriver Setup
# ============================================================================

try:
    print("Ініціалізація webdriver-manager...")
    service = Service(ChromeDriverManager().install())
    print("✓ ChromeDriver готовий")
except Exception as e:
    print(f"✗ Помилка: {e}")
    service = None

# ============================================================================
# GOOGLE DRIVE FUNCTIONS
# ============================================================================

def get_google_drive_service():
    """Автентифікація та повернення Google Drive API service."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Файл '{CREDENTIALS_FILE}' не знайдено!\n"
                    f"Завантажте credentials.json з Google Cloud Console.\n"
                    f"Див. інструкцію в SETUP.md"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


def find_or_create_folder(service, folder_name, parent_id=None):
    """Знаходить або створює папку в Google Drive."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    else:
        query += " and 'root' in parents"

    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])

    if files:
        print(f"  ✓ Знайдено: {folder_name}")
        return files[0]['id']

    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"  ✓ Створено: {folder_name}")
    return folder['id']


def create_folder_structure(service, episode_no):
    """
    ⭐ СПРОЩЕНА ВЕРСІЯ: Створює структуру папок за шляхом з config.json

    Приклади шляхів:
    - "скани" -> створює папку "скани" в корені
    - "TOG/скани" -> створює TOG/скани
    - "TOG/нові розділи/скани" -> створює TOG/нові розділи/скани

    Завжди додає підпапку з номером епізоду: шлях/{episode_no}/
    """
    print(f"Налаштування папок для епізоду {episode_no}...")

    # Розбиваємо шлях на частини
    path_parts = [part.strip() for part in FOLDER_PATH.split('/') if part.strip()]

    if not path_parts:
        # Якщо шлях порожній, використовуємо корінь
        parent_id = None
    else:
        # Створюємо/знаходимо кожну папку в шляху
        parent_id = None
        for folder_name in path_parts:
            parent_id = find_or_create_folder(service, folder_name, parent_id)

    # Створюємо папку з номером епізоду
    episode_folder_id = find_or_create_folder(service, str(episode_no), parent_id)

    return episode_folder_id


def verify_uploaded_file(service, file_id, original_size):
    """
    ⭐ НОВА ФУНКЦІЯ: Перевіряє правильність завантаженого файлу

    Returns:
        bool: True якщо файл валідний
    """
    try:
        # Отримуємо метадані файлу з Drive
        file_metadata = service.files().get(fileId=file_id, fields='size,md5Checksum').execute()

        uploaded_size = int(file_metadata.get('size', 0))

        # Перевіряємо розмір (допускаємо відхилення 1%)
        size_diff = abs(uploaded_size - original_size) / original_size
        if size_diff > 0.01:
            print(f"    ⚠ Розмір не співпадає: {uploaded_size} != {original_size}")
            return False

        return True

    except Exception as e:
        print(f"    ⚠ Помилка перевірки: {e}")
        return False


def upload_to_drive(service, file_data, filename, folder_id):
    """Завантажує файл на Google Drive з перевіркою."""
    file_metadata = {'name': filename, 'parents': [folder_id]}

    mimetype = 'image/png'
    if file_data.startswith(b'\xff\xd8'):
        mimetype = 'image/jpeg'

    media = MediaIoBaseUpload(BytesIO(file_data), mimetype=mimetype, resumable=True)

    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,size'
        ).execute()

        file_id = file.get('id')
        original_size = len(file_data)

        # ⭐ Перевірка завантаження
        if verify_uploaded_file(service, file_id, original_size):
            print(f"  ✓ Завантажено: {filename} ({original_size/1024:.1f} KB)")
        else:
            print(f"  ⚠ Завантажено з попередженням: {filename}")

        return file_id

    except Exception as e:
        print(f"  ✗ Помилка завантаження {filename}: {e}")
        raise


# ============================================================================
# WEB SCRAPING FUNCTIONS
# ============================================================================

def setup_selenium_driver():
    """Налаштування Selenium WebDriver."""
    chrome_options = Options()

    chrome_options.add_argument(f"user-data-dir={CHROME_USER_DATA_DIR}")
    chrome_options.add_argument(f"profile-directory={CHROME_PROFILE}")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")

    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    if not service:
        raise Exception("ChromeDriver не ініціалізовано")

    print(f"Використання Chrome профілю: {CHROME_USER_DATA_DIR}/{CHROME_PROFILE}")
    print("Запуск Chrome драйвера...")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("✓ Chrome драйвер запущено успішно")
    return driver


def wait_for_network_idle_and_collect_images(driver, timeout=30, idle_time=2):
    """Очікує завершення Network запитів та збирає URLs зображень."""
    print(f"Очікування завершення завантаження (макс {timeout}с)...", end=" ", flush=True)

    import json

    start_time = time.time()
    last_request_time = start_time
    previous_count = 0

    image_urls = []
    seen_urls = set()

    while time.time() - start_time < timeout:
        logs = driver.get_log('performance')
        current_count = len(logs)

        for entry in logs:
            try:
                log = entry.get('message', '')

                if 'Network.responseReceived' in log:
                    log_data = json.loads(log)
                    response = log_data.get('message', {}).get('params', {}).get('response', {})
                    url = response.get('url', '')
                    mime_type = response.get('mimeType', '')

                    if 'image' in mime_type and 'pstatic.net' in url:
                        if url not in seen_urls:
                            seen_urls.add(url)
                            image_urls.append(url)

            except:
                continue

        if current_count > previous_count:
            last_request_time = time.time()
            previous_count = current_count

        if time.time() - last_request_time >= idle_time:
            elapsed = time.time() - start_time
            print(f"✓ Завершено за {elapsed:.1f}с (знайдено {len(image_urls)} зображень)")
            return image_urls

        time.sleep(0.5)

    elapsed = time.time() - start_time
    print(f"⚠ Timeout через {elapsed:.1f}с (знайдено {len(image_urls)} зображень)")
    return image_urls


def extract_filename_from_url(url):
    """Витягує оригінальну назву файлу з URL."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)

    if not filename or len(filename) < 5:
        match = re.search(r'/([a-zA-Z0-9_-]{10,})\.(jpg|jpeg|png|gif)', url, re.IGNORECASE)
        if match:
            filename = f"{match.group(1)}.{match.group(2)}"
        else:
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            filename = f"scan_{url_hash}.jpg"

    return filename


def get_image_dimensions_and_size(img_url, cookies_dict):
    """Завантажує зображення та отримує його властивості."""
    try:
        response = requests.get(img_url, cookies=cookies_dict, timeout=20)

        if response.status_code == 200:
            img_data = response.content

            try:
                img = Image.open(BytesIO(img_data))
                width, height = img.size
                size_kb = len(img_data) / 1024
                filename = extract_filename_from_url(img_url)

                return width, height, size_kb, img_data, filename
            except:
                return None

    except:
        pass
    return None


def analyze_single_image(img_url, cookies_dict, index, total):
    """Аналізує одне зображення (для паралельної обробки)."""
    result = get_image_dimensions_and_size(img_url, cookies_dict)

    if result:
        width, height, size_kb, img_data, filename = result
        is_scan = is_likely_scan(width, height, size_kb)

        return {
            'url': img_url,
            'width': width,
            'height': height,
            'size_kb': size_kb,
            'img_data': img_data,
            'filename': filename,
            'is_scan': is_scan,
            'index': index
        }

    return None


def is_likely_scan(width, height, size_kb):
    """Визначає, чи є зображення сканом."""
    if height < MIN_IMAGE_HEIGHT and size_kb < MIN_FILE_SIZE_KB:
        return False
    if width < MIN_IMAGE_WIDTH:
        return False

    aspect_ratio = height / width if width > 0 else 0

    if height >= MIN_IMAGE_HEIGHT or size_kb >= MIN_FILE_SIZE_KB:
        if aspect_ratio >= MIN_ASPECT_RATIO:
            return True

    return False


def scrape_scan_images(driver, url, wait_for_login=False):
    """Збирає скани зображень зі сторінки."""
    print(f"Завантаження сторінки: {url}")
    driver.get(url)

    if wait_for_login:
        print("\n" + "=" * 70)
        print("⚠️  НЕОБХІДНИЙ ВХІД В АКАУНТ")
        print("=" * 70)
        print("1. Має відкритися вікно Chrome")
        print("2. Увійдіть в акаунт на translate.webtoons.com")
        print("3. Переконайтесь, що інтерфейс перекладу завантажився")
        print("4. Натисніть Enter тут після входу")
        print("=" * 70)
        input("👉 Натисніть Enter після входу...")
        print("✓ Продовжуємо...\n")

    image_urls = wait_for_network_idle_and_collect_images(driver, timeout=30, idle_time=2)

    print("Прокручування для завантаження всіх зображень...")
    for i in range(2):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    driver.execute_script("window.scrollTo(0, 0);")

    additional_urls = wait_for_network_idle_and_collect_images(driver, timeout=15, idle_time=1.5)

    all_urls = image_urls + [url for url in additional_urls if url not in image_urls]

    if not all_urls:
        print("⚠ Зображення не знайдено. Переконайтесь, що ви увійшли в акаунт!")
        return []

    print(f"Всього унікальних зображень: {len(all_urls)}")

    selenium_cookies = driver.get_cookies()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}

    print(f"Аналіз зображень (паралельний режим, {MAX_PARALLEL_DOWNLOADS} потоків)...")

    scan_images = []

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
        futures = {
            executor.submit(analyze_single_image, url, cookies_dict, idx, len(all_urls)): url
            for idx, url in enumerate(all_urls, 1)
        }

        for future in as_completed(futures):
            result = future.result()

            if result:
                idx = result['index']
                width = result['width']
                height = result['height']
                size_kb = result['size_kb']
                filename = result['filename']
                is_scan = result['is_scan']

                display_name = filename[:30] if len(filename) > 30 else filename
                print(f"[{idx}/{len(all_urls)}] {display_name:30s} {width}x{height}, {size_kb:.1f}KB", end=" ")

                if is_scan:
                    print("✓ СКАН")
                    scan_images.append({
                        'data': result['img_data'],
                        'filename': filename,
                        'index': idx
                    })
                else:
                    print("✗ Пропуск")

    scan_images.sort(key=lambda x: x['index'])

    return scan_images


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def process_episode(driver, drive_service, webtoon_no, episode_no, is_first_episode=False):
    """Обробляє один епізод."""
    print("\n" + "=" * 70)
    print(f"ОБРОБКА ЕПІЗОДУ {episode_no}")
    print("=" * 70)

    url = f"https://translate.webtoons.com/translate/tool?webtoonNo={webtoon_no}&episodeNo={episode_no}&language=UKR&teamVersion=0"

    try:
        folder_id = create_folder_structure(drive_service, episode_no)
        print(f"✓ Папка Google Drive готова: {FOLDER_PATH}/{episode_no}/\n")
    except Exception as e:
        print(f"✗ Помилка налаштування папок: {e}")
        import traceback
        traceback.print_exc()
        return False

    try:
        scan_images = scrape_scan_images(driver, url, wait_for_login=is_first_episode)

        print(f"\n✓ Знайдено {len(scan_images)} скан(ів)")

        if not scan_images:
            print("⚠ Скани не знайдено.")
            print("  → Переконайтесь, що ви увійшли в акаунт")
            print("  → Перевірте, чи є скани в цьому епізоді")
            return True

        print("Завантаження на Google Drive...")
        successful_uploads = 0

        for scan in scan_images:
            img_data = scan['data']
            filename = scan['filename']

            try:
                upload_to_drive(drive_service, img_data, filename, folder_id)
                successful_uploads += 1
            except Exception as upload_err:
                print(f"  ✗ Помилка завантаження {filename}: {upload_err}")

        print(f"\n✓ Епізод {episode_no}: завантажено {successful_uploads}/{len(scan_images)} файлів")
        return True

    except Exception as e:
        print(f"✗ Помилка: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Головна функція виконання."""
    print("=" * 70)
    print("WEBTOONS SCRAPER v3.1")
    print("=" * 70)
    print()

    try:
        webtoon_no = input("Введіть номер Webtoon (напр. 174): ").strip()
        start_episode = int(input("Введіть ПОЧАТКОВИЙ епізод (напр. 130): ").strip())
        end_episode = int(input("Введіть КІНЦЕВИЙ епізод (напр. 135): ").strip())

        if not webtoon_no or start_episode <= 0 or end_episode < start_episode:
            print("✗ Невалідні дані")
            return

    except (ValueError, KeyboardInterrupt):
        print("\n✗ Скасовано")
        return

    try:
        drive_service = get_google_drive_service()
        print("✓ Google Drive автентифіковано")
        print(f"✓ Структура папок: {FOLDER_PATH}/[номер_епізоду]/\n")
    except Exception as e:
        print(f"✗ Помилка Google Drive: {e}")
        return

    driver = None
    try:
        driver = setup_selenium_driver()

        print("\n" + "=" * 70)
        print(f"ПАКЕТНЕ ЗАВАНТАЖЕННЯ: Епізоди {start_episode}-{end_episode}")
        print("=" * 70)

        total_success = 0
        total_failed = 0

        for idx, ep_num in enumerate(range(start_episode, end_episode + 1)):
            is_first = (idx == 0)

            success = process_episode(
                driver,
                drive_service,
                webtoon_no,
                ep_num,
                is_first_episode=is_first
            )

            if success:
                total_success += 1
            else:
                total_failed += 1
                print(f"⚠ Помилка обробки епізоду {ep_num}, продовжуємо...")

            if ep_num < end_episode:
                time.sleep(1)

        print("\n" + "=" * 70)
        print("✓ ПАКЕТНЕ ЗАВАНТАЖЕННЯ ЗАВЕРШЕНО!")
        print("=" * 70)
        print(f"Успішно оброблено: {total_success}")
        print(f"З помилками: {total_failed}")
        print(f"Всього: {total_success + total_failed}")

    except KeyboardInterrupt:
        print("\n\n⚠ Перервано користувачем (Ctrl+C)")

    except Exception as e:
        print(f"\n✗ Критична помилка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            print("\nЗакриття браузера...")
            driver.quit()


if __name__ == "__main__":
    main()