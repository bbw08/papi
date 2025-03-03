import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler
from urllib.parse import urlencode
from bs4 import BeautifulSoup

app = FastAPI()

class LinkedInJobRequest(BaseModel):
    job_title: str
    location: str

@app.post("/scrape-jobs/")
async def scrape_jobs_endpoint(req: LinkedInJobRequest):
    """
    1) Build LinkedIn seeMoreJobPostings URL with the given job_title + location.
    2) Use AsyncWebCrawler to fetch the page.
    3) Parse the HTML with BeautifulSoup.
    4) Extract data-entity-urn from 'body > li:nth-child(n) > div'.
    """
    try:
        base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        
        # Build query params (?keywords=job_title&location=location)
        query_params = {
            "keywords": req.job_title,
            "location": req.location
        }
        full_url = f"{base_url}?{urlencode(query_params)}"
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=full_url)
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(result.html, "html.parser")
        
        # Select all <div> elements that are direct children of <li> elements under <body>
        # Note: You might also try 'li > div[data-entity-urn]' or 'body li div[data-entity-urn]'
        # depending on actual HTML structure
        divs = soup.select("body > li > div")
        
        # Extract the 'data-entity-urn' attribute from each matched <div>
        urn_list = []
        for div in divs:
            data_urn = div.get("data-entity-urn")
            if data_urn:
                urn_list.append(data_urn)
        
        return {
            "status": "success",
            "url_requested": full_url,
            "total_urns_found": len(urn_list),
            "urns": urn_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
