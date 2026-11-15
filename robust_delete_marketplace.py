import os
import sys
import time
import json
import re
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Path to the folder that contains the active property sub‑folders (e.g. "01_…")
PROPERTIES_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), "propiedades")

# Facebook Marketplace URL that lists the user's active posts.
MARKETPLACE_URL = "https://www.facebook.com/marketplace/you/selling"

# Chrome user‑data directory – reuse the existing Chrome profile so we stay logged in.
CHROME_USER_DATA_DIR = os.path.expanduser("~/Library/Application Support/Google/Chrome")

# Output report file (written in the project root).
REPORT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "marketplace_deletion_report.md"))

# Regex patterns for safe prefix detection and false-positive prevention
PREFIX_PATTERN = re.compile(r"^(\d{1,2})[\s_\.\-]+(.*)$", re.IGNORECASE)
PRICE_OR_UNIT_PATTERN = re.compile(
    r"(\$|mxn|usd|m2|m²|rec[aá]mara|habitaci[oó]n|ba[nñ]o|caj[oó]n|nivel|piso|estacionamiento)",
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Pure Helper Functions (Testable & Safe)
# ---------------------------------------------------------------------------
def get_active_numbers(properties_root=PROPERTIES_ROOT):
    """
    Determine active property numbers from folder names.
    Expects folder names like '01_colinas_san_javier_casa_venta'.
    Returns a set of integer strings without leading zeros (e.g., {'1', '2'}).
    """
    active = set()
    if not os.path.isdir(properties_root):
        return active
    for entry in os.listdir(properties_root):
        entry_path = os.path.join(properties_root, entry)
        if os.path.isdir(entry_path):
            prefix = entry.split("_")[0]
            if prefix.isdigit():
                active.add(prefix.lstrip('0') or '0')
    return active


def extract_property_number(title_text):
    """
    Safely extract property number from a listing title.
    Enforces strict safeguards to avoid matching prices, square meters, or bedroom counts.
    
    Examples:
      '01_Colinas de San Javier' -> '1'
      '02 - Country Club'        -> '2'
      '08 Americana Estudio'     -> '8'
      '$13,800,000 Residencia'   -> None (protected from deletion)
      '3 recámaras en Country'   -> None (protected from deletion)
      '200m2 departamento'       -> None (protected from deletion)
    """
    if not title_text or not isinstance(title_text, str):
        return None

    cleaned = title_text.strip()
    if not cleaned:
        return None

    # Never treat prices as property number
    if cleaned.startswith("$") or cleaned.lower().startswith("mxn") or cleaned.lower().startswith("usd"):
        return None

    # Check for prefix like '01_', '01 - ', '01. ', or '01 '
    match = PREFIX_PATTERN.match(cleaned)
    if not match:
        return None

    num_str = match.group(1)
    remainder = match.group(2).strip()

    # Guard against units immediately following (e.g., '3 recámaras', '200 m2')
    first_word_of_remainder = remainder.split()[0] if remainder.split() else ""
    if PRICE_OR_UNIT_PATTERN.search(first_word_of_remainder):
        return None

    num_val = int(num_str)
    if num_val < 1 or num_val > 99:
        return None

    return str(num_val)


def evaluate_deletion_candidate(title_text, active_numbers):
    """
    Evaluate whether a post should be deleted or kept.
    Fail-safe rule: If the title cannot be reliably linked to a property number,
    KEEP it to prevent accidental data loss of active listings.
    
    Returns:
        (should_delete: bool, reason: str, property_num: str | None)
    """
    prop_num = extract_property_number(title_text)

    if prop_num is None:
        return False, "Sin prefijo de propiedad reconocible (conservado por seguridad)", None

    if prop_num in active_numbers:
        return False, f"Propiedad activa confirmada (#{prop_num})", prop_num

    return True, f"Propiedad obsoleta/inactiva (#{prop_num} no está en catálogo activo)", prop_num


# ---------------------------------------------------------------------------
# Main deletion routine
# ---------------------------------------------------------------------------
def main(dry_run=True):
    active_numbers = get_active_numbers()
    mode_str = "DRY-RUN (Simulación segura)" if dry_run else "EN VIVO (Eliminación real)"
    print(f"=== DEPURADOR DE MARKETPLACE [{mode_str}] ===")
    print(f"Números de propiedad activos detectados: {sorted(active_numbers, key=lambda x: int(x) if x.isdigit() else 999)}")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
    chrome_options.add_argument("--remote-debugging-port=9222")

    try:
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
    except WebDriverException as e:
        print("Failed to start Chrome driver:", e)
        return

    driver.set_page_load_timeout(60)
    try:
        driver.get(MARKETPLACE_URL)
        print("Marketplace page loaded")
    except Exception as e:
        print("Could not load Marketplace page:", e)
        driver.quit()
        return

    SCROLL_PAUSE = 2.0
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    posts = driver.find_elements(By.XPATH, "//div[@role='article']")
    print(f"Found {len(posts)} posts on the page.")

    deleted = []
    retained = []
    failed = []

    for idx, post in enumerate(posts, start=1):
        try:
            title_elem = post.find_element(By.XPATH, ".//span[contains(@class,'_1g5v')]")
            title_text = title_elem.text.strip()
        except NoSuchElementException:
            title_text = post.text.strip().split('\n')[0]

        should_del, reason, prop_num = evaluate_deletion_candidate(title_text, active_numbers)

        if should_del:
            if dry_run:
                print(f"[{idx}] [DRY-RUN] Candidato a eliminar: \"{title_text}\" -> {reason}")
                deleted.append(f"[DRY-RUN] {title_text} ({reason})")
            else:
                print(f"[{idx}] Eliminando publicación \"{title_text}\" -> {reason} …")
                try:
                    more_btn = post.find_element(By.XPATH, ".//div[@aria-label='Más opciones']")
                    driver.execute_script("arguments[0].click();", more_btn)
                    time.sleep(1)
                    delete_btn = driver.find_element(By.XPATH, "//span[text()='Eliminar publicación']")
                    driver.execute_script("arguments[0].click();", delete_btn)
                    time.sleep(1)
                    confirm_btn = driver.find_element(By.XPATH, "//span[text()='Eliminar']")
                    driver.execute_script("arguments[0].click();", confirm_btn)
                    time.sleep(2)
                    deleted.append(title_text)
                except Exception as e:
                    err_msg = f"Failed to delete \"{title_text}\": {e}"
                    print(err_msg)
                    failed.append(err_msg)
        else:
            print(f"[{idx}] Conservando publicación \"{title_text}\" -> {reason}")
            retained.append(f"{title_text} ({reason})")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Marketplace Deletion Report ({mode_str})\n\n")
        f.write(f"Total posts scanned: {len(posts)}\n")
        f.write(f"Active property numbers retained: {sorted(active_numbers, key=lambda x: int(x) if x.isdigit() else 999)}\n\n")
        f.write(f"## Deleted / Marked for Deletion ({len(deleted)})\n")
        for t in deleted:
            f.write(f"- {t}\n")
        f.write(f"\n## Retained ({len(retained)})\n")
        for r in retained:
            f.write(f"- {r}\n")
        f.write(f"\n## Failed ({len(failed)})\n")
        for e in failed:
            f.write(f"- {e}\n")

    print(f"Report written to {REPORT_PATH}")
    driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Depuración segura de Marketplace")
    parser.add_argument("--confirm-live-delete", action="store_true", help="Ejecutar eliminación real (por defecto es simulación segura)")
    args = parser.parse_args()
    main(dry_run=not args.confirm_live_delete)
