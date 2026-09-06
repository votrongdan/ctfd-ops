import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def visit(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # FLAG: The bot injects the flag into its cookies for the challenge domain
    flag = os.environ.get("FLAG", "flag{xss_test_flag_123}")
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(10)
        
        # We must visit the domain first to set a cookie.
        # Since the bot is in the same container, we can visit localhost.
        driver.get("http://127.0.0.1/")
        driver.add_cookie({"name": "flag", "value": flag})
        
        # Now visit the user-provided URL
        driver.get(url)
        time.sleep(3) # Wait for XSS payload to execute
    except Exception as e:
        pass
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        visit(sys.argv[1])
