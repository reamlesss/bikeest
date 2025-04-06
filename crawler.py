import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import re
import os 

def parse_suspension(label, value):
    result = {}
    
    if 'Fork' in label:
        # Zpracování vidlice
        result['fork_brand'] = value.split()[0] if value else None
        result['fork_model'] = re.sub(r'^\S+\s*', '', value.split(',')[0]).strip() if ',' in value else None
        
        # Hledání parametrů pomocí regulárních výrazů
        travel_match = re.search(r'(\d+mm)\s+travel', value)
        result['fork_travel'] = travel_match.group(1) if travel_match else None
        
        damper_match = re.search(r'(GRIP\d?|Fit\d+|Charger\d+)', value)
        result['fork_damper'] = damper_match.group(1) if damper_match else None
        
        offset_match = re.search(r'(\d+mm)\s+offset', value)
        result['fork_offset'] = offset_match.group(1) if offset_match else None

    elif 'Shock' in label:
        # Zpracování tlumiče
        result['shock_brand'] = value.split()[0] if value else None
        result['shock_model'] = re.sub(r'^\S+\s*', '', value.split(',')[0]).strip() if ',' in value else None
        
        # Rozdělení rozměrů
        if 'x' in value:
            dimensions = value.split('x')
            length_match = re.search(r'(\d+mm)', dimensions[0])
            stroke_match = re.search(r'(\d+mm)', dimensions[1])
            result['shock_length'] = length_match.group(1) if length_match else None
            result['shock_stroke'] = stroke_match.group(1) if stroke_match else None
        else:
            result['shock_length'] = re.search(r'(\d+mm)\s+length', value).group(1) if re.search(r'(\d+mm)\s+length', value) else None
            result['shock_stroke'] = re.search(r'(\d+mm)\s+stroke', value).group(1) if re.search(r'(\d+mm)\s+stroke', value) else None

    return result

def accept_consent(driver):
    try:
        accept_button = WebDriverWait(driver, 10).until(  # Reduce wait time from 15 to 10 seconds
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.fc-button.fc-cta-consent.fc-primary-button[aria-label="Consent"]'))
        )
        accept_button.click()
        print("Consent úspěšně přijat pomocí CSS selektoru")
        return True
    except Exception as e:
        print(f"Chyba při klikání na consent tlačítko: {str(e)}")
        return False

def scrape_page(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
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
            'title': None,
            'price': None,
            'year': None,
            'brand': None,
            'frame_material': None,
            'suspension': {},
            'wheel_size': None,
            'drivetrain_brand': None
        }

        # Extract brand from the URL
        match = re.search(r'/bikes/\d{4}/([^/]+)/', url)
        if match:
            result['brand'] = match.group(1).capitalize()

        if accept_consent(driver):
            WebDriverWait(driver, 15).until(  # Reduce wait time from 30 to 15 seconds
                EC.presence_of_element_located((By.CSS_SELECTOR, "section.specifications"))
            )

            # Základní informace
            result['title'] = driver.find_element(By.TAG_NAME, 'h1').text
            result['price'] = driver.find_element(By.CSS_SELECTOR, '#final_price').text
            result['year'] = driver.find_element(By.CSS_SELECTOR, 'div.col-md-5.col-12 > b').text
            
            # Zpracování specifikací
            specs_section = driver.find_element(By.CSS_SELECTOR, 'section.specifications')
            
            for item in specs_section.find_elements(By.CLASS_NAME, 'list-group-item'):
                try:
                    label = item.find_element(By.CLASS_NAME, 'font-weight-bold').text.strip().lower()
                    value = item.find_element(By.CLASS_NAME, 'text-muted').text.strip().lower()


                    
                    if "Frame" in label:
                        result['frame_material'] = 'carbon' if 'carbon' in value else 'aluminium'
                    elif "wheel size" in label:
                        result['wheel_size'] = value
                    elif "drivetrain" in label:
                        result['drivetrain_brand'] = value.split()[0]
                    elif "fork" in label or "shock" in label:
                        suspension_data = parse_suspension(label, value)
                        result['suspension'].update(suspension_data)

                except Exception as e:
                    print(f"Chyba při zpracování položky: {str(e)}")

            return result

        return None

    finally:
        driver.quit()

if __name__ == "__main__":
    input_file = "ebike_urls.csv"
    output_file = "scraped_bike_data.csv"

    try:
        fieldnames = [
            'url', 'title', 'price', 'year', 'brand', 'frame_material', 
            'wheel_size', 'drivetrain_brand', 'fork_brand', 'fork_model', 
            'fork_travel', 'fork_damper', 'fork_offset', 'shock_brand', 
            'shock_model', 'shock_length', 'shock_stroke'
        ]
        write_header = not os.path.exists(output_file)

        with open(output_file, mode='a', newline='', encoding='utf-8') as output_csv:
            writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()

            with open(input_file, mode='r') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)  # Skip the header row if present

                for row in csv_reader:
                    url = row[0]
                    print(f"Scraping URL: {url}")
                    result = scrape_page(url)

                    if result:
                        print("\nÚspěšně scrapováno:")
                        print(f"Název: {result['title']}")
                        print(f"Cena: {result['price']}")
                        print(f"Rok: {result['year']}")
                        print(f"Značka: {result['brand']}")
                        print(f"Materiál rámu: {result['frame_material']}")
                        print(f"Velikost kol: {result['wheel_size']}")
                        print(f"Značka pohonu: {result['drivetrain_brand']}")
                        
                        print("\nDetaily odpružení:")
                        for key, value in result['suspension'].items():
                            print(f"{key.replace('_', ' ').title()}: {value}")

                        # Flatten suspension data into the result dictionary
                        suspension_data = result.pop('suspension', {})
                        result.update(suspension_data)

                        # Add the URL to the result
                        result['url'] = url

                        # Replace None values with the string 'None'
                        result = {key: (value if value is not None else 'None') for key, value in result.items()}

                        # Write the result to the output CSV immediately
                        writer.writerow(result)
                        print("Výsledek uložen do CSV.")
                    else:
                        print("Scrapování selhalo")
    except FileNotFoundError:
        print(f"Soubor {input_file} nebyl nalezen.")
    except Exception as e:
        print(f"Chyba při čtení souboru: {str(e)}")
