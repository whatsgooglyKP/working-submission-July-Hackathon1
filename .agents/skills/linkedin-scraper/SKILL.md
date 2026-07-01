---
name: linkedin-scraper
description: Best practices and code patterns for public LinkedIn guest job posting scraping using BeautifulSoup4.
---

# LinkedIn Guest Job Scraper Development Skill

Use this skill when developing, testing, or updating web-scraping features for LinkedIn guest listings located in `job_scraper.py`.

## Core Guidelines & Principles

1. **Be Respectful & Throttled**:
   - Always implement explicit sleep timings (e.g., `time.sleep(1.0)`) inside search pagination loops to avoid hitting rate limits or triggering IP blocks.

2. **Accurate User-Agents**:
   - Set realistic `User-Agent` string headers that mirror standard browser environments:
     ```python
     headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
     }
     ```

3. **Robust Selector Engineering**:
   - Because public LinkedIn layouts can shift, utilize robust BeautifulSoup selectors with explicit fallback values (`"N/A"` or `"Recent"`).
   - Target the custom search card class structures:
     - Card container: `li` tags
     - Job Title: `h3` with class `base-search-card__title`
     - Company Subtitle: `h4` with class `base-search-card__subtitle`
     - Job Location: `span` with class `job-search-card__location`
     - Application Link: `a` with class `base-card__full-link` (strip URL parameters after the `?` sign)
     - Posted Time Tag: `time` with class containing `listdate`

4. **Iterative Search Pagination**:
   - Public LinkedIn guest endpoints utilize a `start` query parameter representing the result offset (incremented in steps of 25).
   - Continue crawling until the target sample limit (default 35) is fulfilled or no additional `li` elements are found in the response HTML.

---

## Code Patterns

### Robust Scraping Pagination and HTML Parsing
```python
import urllib.request
import urllib.parse
import time
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("easyapplier.scraper")

def search_linkedin_jobs(job_title: str, limit: int = 35) -> list[dict]:
    jobs = []
    start = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    encoded_title = urllib.parse.quote(job_title)
    
    while len(jobs) < limit:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_title}&sortBy=DD&start={start}"
        
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
        time.sleep(1.0) # Respectful throttle limit
        
    return jobs
```
