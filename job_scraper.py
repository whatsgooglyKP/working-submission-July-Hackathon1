import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import time
import logging
import re

logger = logging.getLogger("easyapplier.scraper")

def get_linkedin_job_description(job_url: str) -> str:
    """
    Scrapes the full job description text from a guest LinkedIn job page.
    Attempts view URL and falls back to guest API endpoint if needed.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    # Clean the URL
    job_url = job_url.split('?')[0].strip()
    logger.info(f"Scraping job description: {job_url}")
    
    html = None
    req = urllib.request.Request(job_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read()
    except Exception as e:
        logger.error(f"Failed to fetch job view URL {job_url}: {e}")
        
    # Fallback to Guest Job API endpoint if the main view page fails or redirects
    if not html:
        # Link typically has ID like .../view/job-title-12345678 or .../view/12345678
        match = re.search(r'/view/.*?(\d+)', job_url)
        if not match:
            match = re.search(r'/view/(\d+)', job_url)
        if match:
            job_id = match.group(1)
            api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPostings/{job_id}"
            logger.info(f"Attempting Guest API fallback: {api_url}")
            req = urllib.request.Request(api_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    html = response.read()
            except Exception as ex:
                logger.error(f"Failed to fetch job description from guest API {api_url}: {ex}")
                return ""
        else:
            return ""
            
    if not html:
        return ""
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Standard classes for job descriptions on public LinkedIn pages
    desc_div = (
        soup.find('div', class_='description__text') or 
        soup.find('div', class_='show-more-less-html__markup') or 
        soup.find('section', class_='description') or
        soup.find('div', class_='jobs-box__html-content')
    )
    
    if desc_div:
        # Extract and clean text formatting
        return desc_div.get_text('\n').strip()
        
    # Final generic fallback to get clean text paragraphs
    text_content = soup.get_text('\n').strip()
    if len(text_content) > 2000:
        return text_content[:2000]
    return text_content


def search_linkedin_jobs(job_title: str, limit: int = 20) -> list[dict]:
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
            
            # Parse Easy Apply
            easy_apply = False
            li_text_lower = li.get_text().lower()
            if "easy apply" in li_text_lower:
                easy_apply = True
            else:
                easy_apply_tag = li.find(class_=lambda x: x and 'easy-apply' in x.lower())
                if easy_apply_tag:
                    easy_apply = True
            
            # Parse workplace type (Remote, Hybrid, Onsite)
            workplace_type = "Onsite"
            combined_text = f"{title} {location} {li_text_lower}".lower()
            if "remote" in combined_text or "telecommute" in combined_text or "anywhere" in combined_text:
                workplace_type = "Remote"
            elif "hybrid" in combined_text:
                workplace_type = "Hybrid"
            else:
                workplace_type = "Onsite"
            
            jobs.append({
                'title': title,
                'company': company,
                'location': location,
                'link': link,
                'posted_date': posted_date,
                'posted_datetime': posted_datetime,
                'easy_apply': easy_apply,
                'workplace_type': workplace_type
            })
            
        start += 25
        # Throttle to respect LinkedIn endpoints
        time.sleep(1.0)
        
    return jobs
