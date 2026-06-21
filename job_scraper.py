import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger("easyapplier.scraper")

def search_linkedin_jobs(job_title: str, limit: int = 35) -> list[dict]:
    """
    Scrapes public guest LinkedIn job postings for the given job title.
    Returns a list of dicts containing title, company, location, link, and posted date.
    """
    jobs = []
    start = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    encoded_title = urllib.parse.quote(job_title)
    
    while len(jobs) < limit:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_title}&sortBy=DD&start={start}"
        logger.info(f"Scraping LinkedIn jobs: {url}")
        
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read()
        except Exception as e:
            logger.error(f"Failed to scrape page starting at {start}: {e}")
            break
            
        soup = BeautifulSoup(html, 'html.parser')
        list_items = soup.find_all('li')
        
        if not list_items:
            logger.info("No more job elements found in response HTML.")
            break
            
        for li in list_items:
            if len(jobs) >= limit:
                break
                
            title_tag = li.find('h3', class_='base-search-card__title')
            company_tag = li.find('h4', class_='base-search-card__subtitle')
            location_tag = li.find('span', class_='job-search-card__location')
            link_tag = li.find('a', class_='base-card__full-link')
            time_tag = li.find('time', class_=lambda x: x and 'listdate' in x)
            
            title = title_tag.text.strip() if title_tag else "N/A"
            company = company_tag.text.strip() if company_tag else "N/A"
            location = location_tag.text.strip() if location_tag else "N/A"
            link = link_tag['href'].split('?')[0] if link_tag else "N/A"
            
            # Post date parsing
            posted_date = time_tag.text.strip() if time_tag else "Recent"
            posted_datetime = time_tag.get('datetime', '') if time_tag else ""
            
            jobs.append({
                'title': title,
                'company': company,
                'location': location,
                'link': link,
                'posted_date': posted_date,
                'posted_datetime': posted_datetime
            })
            
        start += 25
        # Throttle to respect LinkedIn endpoints
        time.sleep(1.0)
        
    return jobs
