import os
import re
import sys
import time
import requests
from urllib.parse import urlparse, unquote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = "التقييمات_الوزارية"
os.makedirs(BASE_DIR, exist_ok=True)

_CONTENT_PDF_RE = re.compile(
    r"https?://elearnningcontent\.blob\.core\.windows\.net/[^\s<>\"']+\.pdf",
    re.IGNORECASE,
)

# مسار الرابط يحتوي على التنظيم الكامل:
# /elearnningcontent/2026/Primary/Primary4/Term2/ClassrHomeAssessmentsTest/filename.pdf
# نستخرج منه: stage_folder / grade_folder / term_folder / type_folder / filename.pdf
_PATH_PREFIX = "/elearnningcontent/"


def _folder_and_name_from_url(url: str):
    """يستخرج مسار المجلد واسم الملف من URL الـ Azure."""
    path = unquote(urlparse(url).path)
    idx = path.lower().find(_PATH_PREFIX.lower())
    if idx != -1:
        rel = path[idx + len(_PATH_PREFIX):]  # e.g. 2026/Primary/Primary4/Term2/.../file.pdf
    else:
        rel = path.lstrip("/")
    parts = rel.replace("\\", "/").split("/")
    if len(parts) >= 2:
        folder = os.path.join(*parts[:-1])
        fname = parts[-1]
    else:
        folder = ""
        fname = parts[0] if parts else "unknown.pdf"
    if fname.lower().endswith(".pdf"):
        fname = fname[:-4]
    return folder, fname


def download_pdf(session, url, save_dir, file_name):
    file_path = os.path.join(save_dir, f"{file_name}.pdf")
    if os.path.exists(file_path):
        return False
    try:
        resp = session.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        it = resp.iter_content(chunk_size=8192)
        first = next(it, b"") or b""
        if not first:
            return False
        os.makedirs(save_dir, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(first)
            for chunk in it:
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"❌ خطأ: {file_name} ← {e}")
        return False


# ───── تهيئة المتصفح ─────
options = webdriver.ChromeOptions()
if os.environ.get("CHA_HEADLESS", "").strip().lower() in ("1", "true", "yes"):
    options.add_argument("--headless=new")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
if os.environ.get("CHA_NO_SANDBOX", "").strip().lower() in ("1", "true", "yes"):
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

try:
    driver = webdriver.Chrome(options=options)
except Exception:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

dl_session = requests.Session()

try:
    driver.get("https://ellibrary.moe.gov.eg/cha/")
    time.sleep(3)

    try:
        dl_session.headers["User-Agent"] = driver.execute_script("return navigator.userAgent")
    except Exception:
        pass
    dl_session.headers["Accept"] = "application/pdf,*/*;q=0.9"
    for c in driver.get_cookies():
        dl_session.cookies.set(c["name"], c["value"], domain=c.get("domain"), path=c.get("path") or "/")

    total_files = 0

    stage_select = Select(wait.until(EC.presence_of_element_located((By.ID, "stage-select"))))
    stage_options = [opt.text for opt in stage_select.options if opt.get_attribute("value") != ""]

    for stage in stage_options:
        stage_select = Select(wait.until(EC.presence_of_element_located((By.ID, "stage-select"))))
        stage_select.select_by_visible_text(stage)
        print(f"\n📂 مرحلة: {stage}")

        # انتظار ظهور روابط الـ PDF بعد اختيار المرحلة
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "a[href*='elearnningcontent.blob.core.windows.net'][href$='.pdf']",
                ))
            )
        except TimeoutException:
            print(f"  ⚠️ لم يتم العثور على ملفات لمرحلة: {stage}")
            continue

        time.sleep(2)

        # سحب كل روابط elearnningcontent PDF من الصفحة دفعة واحدة
        html = (driver.page_source or "").replace("\\/", "/")
        urls = list(dict.fromkeys(_CONTENT_PDF_RE.findall(html)))
        print(f"  📊 عدد الروابط الفريدة: {len(urls)}")

        stage_count = 0
        for url in urls:
            folder_rel, fname = _folder_and_name_from_url(url)
            save_dir = os.path.join(BASE_DIR, folder_rel)
            dl_session.headers["Referer"] = driver.current_url
            if download_pdf(dl_session, url, save_dir, fname):
                stage_count += 1
                if stage_count % 20 == 0:
                    print(f"  ✅ تم تحميل {stage_count} ملف حتى الآن...")

        print(f"  ✅ مرحلة {stage}: تم تحميل {stage_count} ملف جديد")
        total_files += stage_count

    print(f"\n📊 إجمالي الملفات المحمّلة: {total_files}")

finally:
    print("\n🎉 انتهت عملية الفحص والتحميل!")
    driver.quit()
