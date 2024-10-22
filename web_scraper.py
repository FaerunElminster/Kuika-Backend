from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_comments(url):
    # Start the Chrome browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)

    # Try to open the reviews section
    try:
        yorumlar_turu = driver.find_element(By.CLASS_NAME, 'js-review-trigger')
        yorumlar_turu.click()
    except Exception as e:
        print("Yorumlar bölümü açılamadı veya zaten açıktı.")

    # Scrape the comments
    yorumlar = driver.find_elements(By.CLASS_NAME, 'comment')
    product_name = driver.find_element(By.CLASS_NAME, 'product-name').text.strip()

    yorum_arr = []
    for yorum in yorumlar:
        yorum_metni = yorum.find_element(By.CLASS_NAME, 'comment-text').text.strip()
        yorum_tarihi = yorum.find_elements(By.CLASS_NAME, 'comment-info-item')[1].text.strip()
        if yorum_tarihi == "Elite Üye":
            yorum_tarihi = yorum.find_elements(By.CLASS_NAME, 'comment-info-item')[2].text.strip()
        yorum_arr.append({"text": yorum_metni, "date": yorum_tarihi})

    driver.quit()  # Close the browser
    return product_name, yorum_arr