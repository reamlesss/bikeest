import csv
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import re

def parse_suspension(label, value):
    """Zpracování specifikací vidlice a tlumiče."""
    result = {}
    if 'Fork' in label:
        result['fork_brand'] = value.split()[0] if value else None
        result['fork_model'] = re.sub(r'^\S+\s*', '', value.split(',')[0]).strip() if ',' in value else None
        travel_match = re.search(r'(\d+mm)\s+travel', value)
        result['fork_travel'] = travel_match.group(1) if travel_match else None
        damper_match = re.search(r'(GRIP\d?|Fit\d+|Charger\d+)', value)
        result['fork_damper'] = damper_match.group(1) if damper_match else None
        offset_match = re.search(r'(\d+mm)\s+offset', value)
        result['fork_offset'] = offset_match.group(1) if offset_match else None
    elif 'Shock' in label:
        result['shock_brand'] = value.split()[0] if value else None
        result['shock_model'] = re.sub(r'^\S+\s*', '', value.split(',')[0]).strip() if ',' in value else None
        dimensions = value.split('x') if 'x' in value else []
        if len(dimensions) == 2:
            length_match = re.search(r'(\d+mm)', dimensions[0])
            stroke_match = re.search(r'(\d+mm)', dimensions[1])
            result['shock_length'] = length_match.group(1) if length_match else None
            result['shock_stroke'] = stroke_match.group(1) if stroke_match else None
    return result

def accept_consent(driver):
    """Přijme consent modal, pokud existuje."""
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.fc-button.fc-cta-consent.fc-primary-button[aria-label="Consent"]'))
        )
        accept_button.click()
        print("Consent úspěšně přijat.")
    except Exception as e:
        print(f"Consent modal nebyl nalezen nebo došlo k chybě: {str(e)}")

def scrape_page(url):
    """Scrapuje data z jedné URL."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        driver.get(url)
        result = {
            'url': url,
            'title': None,
            'price': None,
            'year': None,
            'brand': None,
            'frame_material': None,
            'wheel_size': None,
            'drivetrain_brand': None,
            'fork_brand': None,
            'fork_model': None,
            'fork_travel': None,
            'fork_damper': None,
            'fork_offset': None,
            'shock_brand': None,
            'shock_model': None,
            'shock_length': None,
            'shock_stroke': None
        }

        # Značka z URL
        match = re.search(r'/bikes/\d{4}/([^/]+)/', url)
        if match:
            result['brand'] = match.group(1).capitalize()

        accept_consent(driver)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section.specifications"))
        )

        # Základní informace
        result['title'] = driver.find_element(By.TAG_NAME, 'h1').text
        result['price'] = driver.find_element(By.CSS_SELECTOR, '#final_price').text
        result['year'] = driver.find_element(By.CSS_SELECTOR, 'div.col-md-5.col-12 > b').text

        # Specifikace
        specs_section = driver.find_element(By.CSS_SELECTOR, 'section.specifications')
        
        for item in specs_section.find_elements(By.CLASS_NAME, 'list-group-item'):
            try:
                label = item.find_element(By.CLASS_NAME, 'font-weight-bold').text.strip().lower()
                value = item.find_element(By.CLASS_NAME, 'text-muted').text.strip().lower()
                if "frame" in label:
                    result['frame_material'] = 'carbon' if 'carbon' in value else 'aluminium'
                elif "wheel size" in label:
                    result['wheel_size'] = value
                elif "drivetrain" in label:
                    result['drivetrain_brand'] = value.split()[0]
                elif "fork" in label or "shock" in label:
                    suspension_data = parse_suspension(label, value)
                    result.update(suspension_data)
            except Exception as e:
                print(f"Chyba při zpracování položky: {str(e)}")

        return result

    finally:
        driver.quit()

def process_urls(input_file, output_file):
    """Zpracuje URL ze souboru CSV a uloží výsledky do jiného CSV."""
    fieldnames = [
        'url', 'title', 'price', 'year', 'brand', 
        'frame_material', 'wheel_size', 'drivetrain_brand',
        'fork_brand', 'fork_model', 'fork_travel', 
        'fork_damper', 'fork_offset', 
        'shock_brand', 'shock_model',
        'shock_length', 'shock_stroke'
    ]

    with open(input_file, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Přeskočí hlavičku

        urls = [row[0] for row in csv_reader]

    with open(output_file, mode='w', newline='', encoding='utf-8') as output_csv:
        writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
        writer.writeheader()

        def process_url(url):
            scraped_data = scrape_page(url)
            if scraped_data:
                writer.writerow(scraped_data)  # Save each bike immediately

        with ThreadPoolExecutor(max_workers=5) as executor:  # Paralelizace s 5 vlákny
            executor.map(process_url, urls)

if __name__ == "__main__":
    input_file = "ebike_urls.csv"
    output_file = "scraped.csv"
    
    process_urls(input_file, output_file)
