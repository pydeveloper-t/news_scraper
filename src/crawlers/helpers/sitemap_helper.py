import logging
import xml.etree.ElementTree as ET
from datetime import datetime

from ..base_requests import http_request, Response, RequestTypes
from urllib.parse import urljoin

from pydantic import AnyUrl

logger = logging.getLogger(__name__)

async def get_robots(site_url: AnyUrl) -> str | None :
    robots_url = urljoin(site_url + "/", "robots.txt")
    robots_txt: str | None = None 
    try:
        response: Response = await http_request.request(request_type=RequestTypes.GET, url=robots_url)
        robots_txt = response.response_text
    except Exception as exc: 
        logger.error("Error ’%s’ receiving robots.txt by link `%s`", exc), robots_url
    return robots_txt



def get_disallowed_user_agents(file_content: str) -> list[str] | None:
    user_agents = []
    current_user_agent = None
    disallow_all = "Disallow: /"
    
    for line in file_content.splitlines():
        # Remove any leading/trailing whitespace from the line
        line = line.strip()
        
        # Check if the line specifies a user-agent
        if line.startswith("User-agent:"):
            current_user_agent = line.split(":", 1)[1].strip()
        
        # Check if the line contains `Disallow: /`
        elif line == disallow_all and current_user_agent:
            user_agents.append(current_user_agent)
            current_user_agent = None  # Reset after recording

    return user_agents if user_agents else None

 
def parse_sitemap(sitemap_content: str) -> list[tuple[str, datetime]]:
    # Parse XML content
    root = ET.fromstring(sitemap_content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    # Initialize a list to store results
    result: list[tuple[str, datetime]] = []

    # Iterate over each <url> element in the sitemap
    for url in root.findall("ns:url", namespaces=namespace):
        # Get the <loc> and <lastmod> text
        loc = url.find('ns:loc', namespaces=namespace).text
        lastmod = url.find('ns:lastmod', namespaces=namespace).text
        
        # Convert lastmod to datetime object
        lastmod_dt = datetime.strptime(lastmod, "%Y-%m-%dT%H:%M:%SZ")
        
        # Append the tuple (URL, lastmod as datetime) to result list
        result.append((loc, lastmod_dt))
    
    return result
