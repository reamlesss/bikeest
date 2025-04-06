from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import requests
from bs4 import BeautifulSoup
import csv
from selenium.common.exceptions import TimeoutException  # Add this import

def accept_consent(driver):
    """Přijme consent modal, pokud existuje."""
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.fc-button.fc-cta-consent.fc-primary-button[aria-label="Consent"]'))
        )
        accept_button.click()
        print("Consent úspěšně přijat.")
    except Exception as e:
        print(f"Consent modal nebyl nalezen nebo došlo k chybě: {str(e)}")

def scrape_bike_links(base_url):
    """Najde všechny odkazy na kola na mtbdatabase.com."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Spustí prohlížeč v režimu bez GUI
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    all_links = []

    try:
        driver.get(base_url)

        # Přijetí consent modalu (pokud existuje)
        accept_consent(driver)

        # Počkej na načtení hlavní stránky
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#bike_results_container a"))
        )

        # Najdi všechny odkazy na kola
        bike_cards = driver.find_elements(By.CSS_SELECTOR, "#bike_results_container a")
        for card in bike_cards:
            link = card.get_attribute("href")
            if link and link.startswith("http") and link not in all_links:
                all_links.append(link)

        # Navigace na další stránky (pokud existují)
        while True:
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn-pagination[data-value]"))
                )
                next_button.click()
                time.sleep(2)  # Počkej na načtení další stránky

                # Najdi odkazy na další stránce
                bike_cards = driver.find_elements(By.CSS_SELECTOR, "#bike_results_container a")
                for card in bike_cards:
                    link = card.get_attribute("href")
                    if link and link.startswith("http") and link not in all_links:
                        all_links.append(link)
            except Exception as e:
                print("Další stránka nenalezena nebo konec stránek.")
                break

    except TimeoutException as e:
        print(f"Timeout při načítání stránky: {str(e)}")

    finally:
        driver.quit()

    return all_links

def get_all_urls_from_site(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    bike_results_container = soup.find(id="bike_results_container")
    if not bike_results_container:
        return []

    urls = []
    for a_tag in bike_results_container.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('https://'):
            urls.append(href)

    return urls

def save_urls_to_csv(urls, filename="ebike_urls.csv"):
    """Uloží seznam URL do CSV souboru."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["URL"])  # Záhlaví sloupce
        for url in urls:
            writer.writerow([url])
    print(f"URL byly úspěšně uloženy do souboru {filename}")

def scrape_all_pages(base_url):
    """Scrapes all bike URLs from all pages of the site."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Spustí prohlížeč v režimu bez GUI
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    all_links = set()  # Use a set to avoid duplicates

    try:
        driver.get(base_url)

        # Přijetí consent modalu (pokud existuje)
        accept_consent(driver)

        while True:
            # Počkej na načtení hlavní stránky
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#bike_results_container a"))
            )

            # Najdi všechny odkazy na kola na aktuální stránce
            bike_cards = driver.find_elements(By.CSS_SELECTOR, "#bike_results_container a")
            for card in bike_cards:
                link = card.get_attribute("href")
                if link and link.startswith("http"):
                    all_links.add(link)

            # Najdi tlačítko "Next" a přejdi na další stránku
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/section[3]/div/div/div[3]/div[3]/div/a[8]'))
                )
                next_button.click()
                time.sleep(2)  # Počkej na načtení další stránky
            except Exception:
                print("Další stránka nenalezena nebo konec stránek.")
                break

    except TimeoutException as e:
        print(f"Timeout při načítání stránky: {str(e)}")

    finally:
        driver.quit()

    return list(all_links)

def get_riding_style_links(base_url):
    """Scrapes all riding style links from the main page."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    riding_style_links = []

    try:
        driver.get(base_url)

        # Přijetí consent modalu (pokud existuje)
        accept_consent(driver)

        # Počkej na načtení seznamu stylů jízdy
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#riding_styles_list a"))
        )

        # Najdi všechny odkazy na styly jízdy
        style_links = driver.find_elements(By.CSS_SELECTOR, "#riding_styles_list a")
        for link in style_links:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                riding_style_links.append(href)

    finally:
        driver.quit()

    return riding_style_links

def scrape_all_pages_for_style(style_url):
    """Scrapes all bike URLs for a specific riding style by iterating through pages."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    all_links = set()
    page_number = 1

    try:
        while True:
            # Construct the URL for the current page
            paginated_url = f"{style_url}&prod_mtbdb%5Bpage%5D={page_number}"
            print(f"Scraping page {page_number} of {style_url}")
            driver.get(paginated_url)

            # Wait for bike results to load or break if no results are found
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#bike_results_container a"))
                )
            except TimeoutException:
                print(f"No bikes found on page {page_number}. Stopping pagination for {style_url}.")
                break

            # Scrape bike links on the current page
            bike_cards = driver.find_elements(By.CSS_SELECTOR, "#bike_results_container a")
            for card in bike_cards:
                link = card.get_attribute("href")
                if link and link.startswith("http"):
                    all_links.add(link)

            # Increment the page number for the next iteration
            page_number += 1

    finally:
        driver.quit()

    return list(all_links)

def scrape_all_riding_styles(base_url):
    """Scrapes all bike URLs for each riding style."""
    riding_style_links = get_riding_style_links(base_url)
    all_bike_links = set()

    for style_link in riding_style_links:
        print(f"Scraping riding style: {style_link}")
        try:
            bike_links = scrape_all_pages_for_style(style_link)
            all_bike_links.update(bike_links)
        except Exception as e:
            print(f"Error while scraping {style_link}: {e}. Moving to the next riding style.")

    return list(all_bike_links)

if __name__ == "__main__":
    base_url = "https://mtbdatabase.com/bikes/"
    all_bike_links = scrape_all_riding_styles(base_url)

    print(f"Nalezeno {len(all_bike_links)} odkazů na kola:")
    for link in all_bike_links:
        print(link)

    # Uložení URL do CSV
    save_urls_to_csv(all_bike_links)

    site_url = "https://mtbdatabase.com"
    urls = get_all_urls_from_site(site_url)
    for url in urls:
        print(url)
