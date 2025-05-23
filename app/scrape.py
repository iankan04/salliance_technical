from fastapi import HTTPException
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_linkedin_profile(profile_url: str):
    # Configure Selenium
    options = Options()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(profile_url)
        
        # Wait for skills section to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".skills-section"))
        )
        
        # Scroll to load all content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Allow time for loading
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract skills
        skills = []
        skill_elements = soup.select(".skills-section .pv-skill-category-entity")
        
        for skill in skill_elements:
            name = skill.select_one(".pv-skill-category-entity__name").get_text(strip=True)
            
            # Extract years if available
            years_element = skill.select_one(".pv-skill-category-entity__skill-proficiency")
            years = years_element.get_text(strip=True) if years_element else "Not specified"
            
            skills.append({"skill": name, "experience": years})
        
        return skills[:10]  # Return top 10 skills
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scraping failed: {str(e)}")
    finally:
        driver.quit()