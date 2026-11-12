import os
import time
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Path to the folder that contains the active property sub‑folders (e.g. "01_…")
PROPERTIES_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), "propiedades")

# Facebook Marketplace URL that lists the user's active posts.
# Adjust if a different URL is needed (e.g., "selling" vs "buying").
MARKETPLACE_URL = "https://www.facebook.com/marketplace/you/selling"

# Chrome user‑data directory – reuse the existing Chrome profile so we stay logged in.
CHROME_USER_DATA_DIR = os.path.expanduser("~/Library/Application Support/Google/Chrome")

# Output report file (written in the project root).
REPORT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "marketplace_deletion_report.md"))

# ---------------------------------------------------------------------------
# Helper: determine active property numbers from folder names
# ---------------------------------------------------------------------------
def get_active_numbers():
    active = set()
    if not os.path.isdir(PROPERTIES_ROOT):
        return active
    for entry in os.listdir(PROPERTIES_ROOT):
        entry_path = os.path.join(PROPERTIES_ROOT, entry)
        if os.path.isdir(entry_path):
            # Expect folder names like "01_colinas_san_javier_venta"
            prefix = entry.split("_")[0]
            if prefix.isdigit():
                active.add(prefix.lstrip('0') or '0')  # store without leading zeros for easy compare
    return active

# ---------------------------------------------------------------------------
# Main deletion routine
# ---------------------------------------------------------------------------
def main():
    active_numbers = get_active_numbers()
    print(f"Active property numbers: {sorted(active_numbers)}")

    # -----------------------------------------------------------------------
    # Launch Chrome (headless) re‑using the existing user profile
    # -----------------------------------------------------------------------
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Chrome >=109 headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
    # Keep the same language/locale as the user profile (optional)
    chrome_options.add_argument("--remote-debugging-port=9222")

    try:
        # Connect to the already‑running Chrome instance with remote debugging
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

    # -----------------------------------------------------------------------
    # Scroll to the bottom to load all posts (infinite scroll)
    # -----------------------------------------------------------------------
    SCROLL_PAUSE = 2.0
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # -----------------------------------------------------------------------
    # Locate each post card on the page
    # -----------------------------------------------------------------------
    # Facebook uses a "role='article'" attribute for each listing card.
    posts = driver.find_elements(By.XPATH, "//div[@role='article']")
    print(f"Found {len(posts)} posts on the page.")

    deleted = []
    failed = []

    for idx, post in enumerate(posts, start=1):
        try:
            # Try to extract a title or identifier that contains the property number.
            # The exact DOM may differ; we fall back to the whole text content.
            title_elem = post.find_element(By.XPATH, ".//span[contains(@class,'_1g5v')]")
            title_text = title_elem.text.strip()
        except NoSuchElementException:
            title_text = post.text.strip().split('\n')[0]

        # Extract a leading numeric token (the folder number).
        token = title_text.split('_')[0] if '_' in title_text else title_text.split(' ')[0]
        numeric = ''.join(ch for ch in token if ch.isdigit())
        numeric = numeric.lstrip('0') or '0'

        # If this post's number is **not** in the active set, delete it.
        if numeric and numeric not in active_numbers:
            print(f"[{idx}] Deleting post \"{title_text}\" (num={numeric}) …")
            try:
                # Click the three‑dot "Más opciones" button.
                more_btn = post.find_element(By.XPATH, ".//div[@aria-label='Más opciones']")
                driver.execute_script("arguments[0].click();", more_btn)
                time.sleep(1)
                # Click the "Eliminar publicación" menu entry.
                delete_btn = driver.find_element(By.XPATH, "//span[text()='Eliminar publicación']")
                driver.execute_script("arguments[0].click();", delete_btn)
                time.sleep(1)
                # Confirm the deletion dialog.
                confirm_btn = driver.find_element(By.XPATH, "//span[text()='Eliminar']")
                driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(2)
                deleted.append(title_text)
            except Exception as e:
                err_msg = f"Failed to delete \"{title_text}\": {e}"
                print(err_msg)
                failed.append(err_msg)
        else:
            print(f"[{idx}] Keeping post \"{title_text}\" (num={numeric})")

    # -----------------------------------------------------------------------
    # Write a markdown report
    # -----------------------------------------------------------------------
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Marketplace Deletion Report\n\n")
        f.write(f"Total posts scanned: {len(posts)}\n")
        f.write(f"Active property numbers retained: {sorted(active_numbers)}\n\n")
        f.write(f"## Deleted ({len(deleted)})\n")
        for t in deleted:
            f.write(f"- {t}\n")
        f.write("\n## Failed to delete ({len(failed)})\n")
        for e in failed:
            f.write(f"- {e}\n")

    print(f"Report written to {REPORT_PATH}")
    driver.quit()

if __name__ == "__main__":
    main()
