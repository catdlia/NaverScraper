import os
import re
import time
import json
import requests
from io import BytesIO
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ============================================================================
# CONFIG
# ============================================================================

def load_config():
    config_file = 'config.json'
    if not os.path.exists(config_file):
        raise FileNotFoundError("config.json не знайдено!")
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

CONFIG = load_config()

# Chrome Paths
CHROME_USER_DATA_DIR = os.path.expanduser(CONFIG['chrome']['user_data_dir'])
CHROME_PROFILE = CONFIG['chrome']['profile']

# Drive Paths
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = CONFIG['google_drive']['credentials_file']
TOKEN_FILE = CONFIG['google_drive']['token_file']
BASE_FOLDER_PATH = CONFIG['google_drive'].get('folder_path', 'Bato_Scans')

# ============================================================================
# DRIVE HELPER FUNCTIONS
# ============================================================================

def get_google_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def find_folder(service, folder_name, parent_id=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    else:
        query += " and 'root' in parents"

    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def create_folder(service, folder_name, parent_id=None):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder['id']

def ensure_path_exists(service, series_name, chapter_name):
    # 1. Base path
    path_parts = [part.strip() for part in BASE_FOLDER_PATH.split('/') if part.strip()]
    parent_id = None
    for part in path_parts:
        found = find_folder(service, part, parent_id)
        if found:
            parent_id = found
        else:
            parent_id = create_folder(service, part, parent_id)

    # 2. Series folder
    if series_name:
        found = find_folder(service, series_name, parent_id)
        if found:
            parent_id = found
        else:
            parent_id = create_folder(service, series_name, parent_id)

    # 3. Chapter folder
    found_chapter = find_folder(service, chapter_name, parent_id)
    if found_chapter:
        return found_chapter, False
    else:
        new_id = create_folder(service, chapter_name, parent_id)
        return new_id, True

def upload_to_drive(service, file_data, filename, folder_id):
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaIoBaseUpload(BytesIO(file_data), mimetype='image/webp', resumable=True)
    try:
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True
    except:
        return False

# ============================================================================
# SCRAPER LOGIC
# ============================================================================

def setup_driver():
    options = Options()
    print(f"Запуск Chrome профілю: {CHROME_PROFILE}")
    options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
    options.add_argument(f"--profile-directory={CHROME_PROFILE}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.page_load_strategy = 'eager'

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def clean_url(url):
    """Видаляє якорі (#) та зайві параметри."""
    if not url: return ""
    return url.split('#')[0].strip()

def parse_url_info(url):
    try:
        path = urlparse(url).path.strip('/')
        parts = path.split('/')

        series_name = "Unknown_Series"
        chapter_name = parts[-1]

        if 'title' in parts:
            idx = parts.index('title')
            if len(parts) > idx + 1:
                series_name = parts[idx + 1]

        match = re.search(r'^\d+-(.+)$', chapter_name)
        if match:
            chapter_name = match.group(1)

        chapter_name = chapter_name.replace('_', '')
        return series_name, chapter_name
    except:
        return "Unknown", f"ch_{int(time.time())}"

def get_safe_src(element):
    """Безпечно отримує src, ігноруючи помилки зникнення елементу."""
    try:
        return element.get_attribute('src')
    except StaleElementReferenceException:
        return None

def scroll_and_wait(driver):
    """Безпечний скролінг з обробкою StaleElementReferenceException."""
    print("  ⏳ Скролінг для прогрузки...")
    last_count = 0
    stable_ticks = 0

    driver.execute_script("window.scrollTo(0, 0);")

    for _ in range(40):
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(0.5)

        # --- FIX: Безпечний підрахунок картинок ---
        images = driver.find_elements(By.TAG_NAME, 'img')
        current_valid_count = 0

        for img in images:
            src = get_safe_src(img)
            if src and ('.webp' in src or 'bato' in src):
                current_valid_count += 1
        # ------------------------------------------

        if current_valid_count > 0 and current_valid_count == last_count:
            stable_ticks += 1
        else:
            stable_ticks = 0

        if stable_ticks >= 4:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            return current_valid_count

        last_count = current_valid_count

        if driver.execute_script("return (window.innerHeight + window.scrollY) >= document.body.scrollHeight"):
            if stable_ticks >= 2: return current_valid_count

    return last_count

def find_next_link(driver, current_url):
    clean_current = clean_url(current_url)
    candidates = []

    # 1. Primary buttons
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-primary")
        for btn in btns:
            try:
                href = clean_url(btn.get_attribute('href'))
                text = btn.text.lower()

                if href and href != clean_current:
                    if 'next' in text or 'chapter' in text or not text:
                        candidates.append(href)
            except StaleElementReferenceException:
                continue
    except: pass

    # 2. Fallback text search
    if not candidates:
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            for a in links:
                try:
                    text = a.text.lower()
                    if "next" in text and "chapter" in text:
                        href = clean_url(a.get_attribute('href'))
                        if href and href != clean_current:
                            candidates.append(href)
                except StaleElementReferenceException:
                    continue
        except: pass

    if candidates:
        return candidates[-1]

    return None

def main():
    print("=== BATO SCRAPER v4 (STABLE) ===")
    start_url = input("Link to first chapter: ").strip()
    if not start_url: return

    try:
        drive_service = get_google_drive_service()
        print("✓ Drive API OK")
    except Exception as e:
        print(f"✗ Drive Error: {e}")
        return

    try:
        driver = setup_driver()
        session = requests.Session()
    except Exception as e:
        print(f"✗ Browser Error: {e}")
        return

    current_url = clean_url(start_url)
    visited_urls = set()

    while True:
        # Перевірка на дублікати URL
        if current_url in visited_urls:
            print(f"🛑 Зупинка: Вже були тут {current_url}")
            break

        visited_urls.add(current_url)

        print(f"\n🌍 Перехід на: {current_url}")
        driver.get(current_url)

        series_name, chapter_name = parse_url_info(current_url)
        print(f"📂 Тайтл: {series_name} | Розділ: {chapter_name}")

        folder_id, is_new = ensure_path_exists(drive_service, series_name, chapter_name)

        if not is_new:
            print(f"⏩ Папка '{chapter_name}' вже існує. Пропускаємо завантаження...")
            time.sleep(2)
        else:
            print(f"📥 Починаємо завантаження розділу...")
            count = scroll_and_wait(driver)

            # --- FIX: Безпечний збір посилань для скачування ---
            img_elements = driver.find_elements(By.TAG_NAME, 'img')
            img_urls = []
            seen_src = set()

            for img in img_elements:
                src = get_safe_src(img)
                if src and '.webp' in src and 'avatar' not in src and src not in seen_src:
                    img_urls.append(src)
                    seen_src.add(src)
            # ---------------------------------------------------

            print(f"Знайдено {len(img_urls)} сканів.")

            uploaded = 0
            for i, u in enumerate(img_urls, 1):
                print(f"Upload {i}/{len(img_urls)}", end='\r')
                try:
                    r = session.get(u, headers={'Referer': current_url}, timeout=15)
                    if r.status_code == 200 and b'<svg' not in r.content[:100]:
                        upload_to_drive(drive_service, r.content, f"{i:03d}.webp", folder_id)
                        uploaded += 1
                except: pass
            print(f"\n✅ Завантажено {uploaded} файлів.")

        next_url = find_next_link(driver, current_url)

        if not next_url:
            print("🏁 Кнопку 'Next' не знайдено.")
            break

        current_url = next_url

    driver.quit()

if __name__ == "__main__":
    main()