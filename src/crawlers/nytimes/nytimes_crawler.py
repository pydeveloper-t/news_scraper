import asyncio
import logging
import os
import re
import random
from datetime import date, datetime
from crawlers import WebBase, RequestTypes, RequestsBase, Response
from crawlers.helpers.sitemap_helper import parse_sitemap
from .nytimes_schemes import NYTimesPageScheme
from .nytimes_selectors import NYTimesSelectors
from settings import settings

import aiofiles
import httpx
import zendriver as zd
from zendriver import Element, cdp
from zendriver.cdp.dom import Node
from zendriver.core import element

from pathlib import Path
from pydantic import AnyUrl



logger = logging.getLogger(__name__)


class NYTimes(WebBase, RequestsBase, NYTimesSelectors):
    URL = "https://www.nytimes.com/"
    _instances = {}

    crawler_specific_browser_args = []

    def __new__(cls, *args, **kwargs):
        if email:=kwargs.get("email") in cls._instances:
            return cls._instances[email]

        isinstance = super().__new__(cls)
        cls._instances[email] = isinstance
        return isinstance

    def __init__(self, *, email: str, password: str, workdir: Path, browser_args: list[str] | None = None, timeout: float = 15):
        # Avoid Reinitialization
        if not hasattr(self, 'initialized'):
            full_path_to_profile = workdir / f"profiles/{email.strip().lower()}"
            full_path_to_profile.mkdir(parents=True, exist_ok=True)
            browser_args = self.predefined_browser_args + [f"--profile-directory={email.strip().lower()}"]
            super().__init__(workdir, full_path_to_profile, browser_args, timeout)
            self.email = email
            self.password = password
            self.page = None        
            self.initialized = True
            self.client = httpx.AsyncClient()

    async def open_main_page(self) -> zd.Tab:
        page: zd.Tab | None = None 
        try:
            if not self.browser:
                await self.init_browser()
            page: zd.Tab = await self.open_url(url=self.URL)
            await self.random_delay()
        except Exception as exc:
            logger.error("Error opening the main page `%s`", str(exc))
        return page

    async def _updated_terms(self, page: zd.Tab) -> bool:
        '''
            Accept the agreement on the general terms and 
            conditions of use of the website        
        '''
        if (updated_terms:=await self.get_element(page=page, selector=self.SELECTORS_SETUP["UPDATE_TERMS"], timeout=3)):
            await updated_terms.click()
            return True
        return False

    async def login(self, page: zd.Tab) -> bool:
        '''
            The method logs into your NYTimes account if not already done 
            for the current browser profile
        '''
        logged: bool  =  False
        try:
            if await self.get_element(page=page, selector=self.SELECTORS_LOGIN["ACCOUNT"], timeout=5):
                logger.info("Already logged into NYTimes account")
                return True
            
            if (accept_all_cookies:=await self.get_element(page=page, selector=self.SELECTORS_SETUP["ACCEPT_ALL"], timeout=5)):
                await accept_all_cookies.click()
            await self._updated_terms(page)
            
            if not (login:= await self.get_element(page=page, selector=self.SELECTORS_LOGIN["LOG_IN"])):
                raise ValueError("Not found element `%s`, 'LOG_IN'")
            await login.click()
            await self.random_delay()

            if not (email:= await self.get_element(page=page, selector=self.SELECTORS_LOGIN["EMAIL"])):
                raise ValueError("Not found element `%s`, 'EMAIL'")
            await  email.send_keys(text=self.email)

            if not (email_continue:= await self.get_element(page=page, selector=self.SELECTORS_LOGIN["EMAIL_CONTINUE"])):
                raise ValueError("Not found element `%s`, 'EMAIL_CONTINUE'")
            await email_continue.click()
            await self.random_delay()

            if not (password:= await self.get_element(page=page, selector=self.SELECTORS_LOGIN["PASSWORD"])):
                raise ValueError("Not found element `%s`, 'PASSWORD'")
            await password.send_keys(text=self.password)
            if not (login_button:= await self.get_element(page=page, selector=self.SELECTORS_LOGIN["LOGIN_BUTTON"])):
                raise ValueError("Not found element `%s`, 'LOGIN_BUTTON'")
            await login_button.click()            
            await self.random_delay()

            if (without_subscribing:= await self.get_element(page=page, selector=self.SELECTORS_LOGIN["WITHOUT_SUBSCRIBING"], timeout=5)):
                await without_subscribing.click()            

            await self._updated_terms(page)
            logged = True
        except ValueError as verr:
            logger.error(str(verr))
            logged = False
        except Exception as exc:
            logger.error("General exception `%s`", str(exc))
            raise exc

        return logged

    def get_selectors_for_url(self, url: str) -> dict | None:
        ''' The set of selectors used depends on the second element of the URL (after the base URL)
            https://www.nytimes.com/2024/11/12/world/europe/archbishop-canterbury-resigns-abuse-scandal.html  - DEFAULT - set
            https://www.nytimes.com/athletic/5917697/2024/11/12/jeff-landry-louisiana-governor-live-tiger-lsu-alabama-comments/ - ATHLETIC set
        '''
        try:
            second_url_parameter = (url.replace(self.URL, "").split('/')[0]).upper()
        except:
            second_url_parameter = None
        return  self.SELECTORS_PAGE[second_url_parameter] if second_url_parameter in self.SELECTORS_PAGE else self.SELECTORS_PAGE["DEFAULT"]
    

    async def accept_cookies(self, page: zd.Tab)-> bool:
        accepted: bool = False
        shadow_div:zd.Element
        try:
            await self.random_delay(from_=1, to_=3)
            if (shadow_div:= await self.get_element(page=page, selector=self.SELECTORS_COOKIES["ACCEPT_FRAME"], timeout=3)):
                shadow_roots: Node = shadow_div.shadow_roots[0]
                div: Node = shadow_roots.children[0]
                iframe: Element = element.create(div, page, div.content_document)
                if (button:= await iframe.query_selector(self.SELECTORS_COOKIES["ACCEPT_ALL"])):
                    await button.click()
                    accepted = True
        except TimeoutError:
            pass            
        except Exception as exc:            
            logger.error("Failed to validate cookie `%s`",exc)
        return accepted    
            

    async def parse_page(self, page_url: AnyUrl) -> NYTimesPageScheme | None:
        '''
            Parses the page and returns the result 
        '''
        page: zd.Tab | None = None
        page_data: dict
        result: NYTimesPageScheme | None = None
        try:
            errors: int
            page_data: dict | None
            if not (selectors:= self.get_selectors_for_url(page_url)):
                ValueError("Page `%s` has unsupported format", page_url)
            page= await self.open_url(url=page_url, new_tab=True)
            await self.accept_cookies(page)
            errors, page_data = await self.get_data_by_selectors(page=page, selectors=selectors)
            if errors:
                raise Exception
            result = NYTimesPageScheme.model_validate(page_data | {"article_url": page_url})
                
        except Exception as exc:    
            logger.error("Page `%s` parsing error `%s` ", page_url, str(exc))
        finally:
            await self.random_delay()
            await page.close()
        return result    
        

    async def get_urls_from_sitemap(self, sitemap_date: date) -> list[tuple[str, datetime]] | None:
        '''
        Opens a sitemap file based on the date of parsing (sitemap files are stored monthly, 
        like  `https://www.nytimes.com/sitemaps/new/sitemap-2024-11.xml.gz`) 
        and retrieves a list of links for parsing from it
        '''
        sitemap_list: list[tuple[str, datetime]] | None = None
        try:
            year = sitemap_date.year
            month = sitemap_date.month
            url = f"https://www.nytimes.com/sitemaps/new/sitemap-{year}-{month}.xml.gz"
            headers = {
                "user-agent" : (await self.get_random_crawler_bot_useragent()).strip()
            }
            response: Response = await self.request(request_type=RequestTypes.GET, url=url, headers=headers)
            if response.successfull and response.response_text:
                sitemap_list =  parse_sitemap(sitemap_content=response.response_text)
        except Exception as exc:    
            logger.error("Sitemap `%s` parsing parsing error `%s` ", url, str(exc))
        return sitemap_list

    async def set_result_file(self, work_date: date) -> Path | None :
        '''
            Sets the output file name based on the parsing date
        '''
        result_file: Path | None = None
        try:
            # The script will store result into output folder depends on the current user account(email)
            result_folder = Path(settings.WORKDIR) / 'result' / self.email.strip().lower() 
            result_folder.mkdir(parents=True, exist_ok=True)
            
            # For every working date separate file for storing the articles data
            result_file = result_folder / f'{work_date.strftime("%Y%m%d")}.json' 
            logger.info("The result will be written to a file ’%s’ ", result_file)
        except Exception as exc:    
            logger.error("Error `%s raised duiring building output data file - '%s' ", exc, result_file)
        return result_file    



    async def prepare_urls_list_for_scraping(self, sitemap_list: list[tuple[str, datetime]], already_scrapped_list: list[str]) -> list[str] | None:
        urls_list: list[str] | None  = None

        # We'll only collect articles that haven't been scrapped yet
        urls_list = list(set(item[0] for item in sitemap_list) - set(already_scrapped_list))

        # Randomize urls list
        random.shuffle(urls_list)
        urls_list.sort(key=lambda x: x[1])
        return urls_list    

    async def login_into_news_site(self) ->zd.Tab:
        page: zd.Tab | None = None 
        try:
            await self.init_browser()
            await asyncio.sleep(3)
            page = await self.open_url(url=NYTimes.URL, new_tab=True)
            await asyncio.sleep(5)
            await self.login(page=page)
        except Exception as exc:
            logger.error("An error `%s` occurred during the initialisation(login) of the scraping process", exc)
        return page    


    async def crawler(self, news_date: date | None = None , news_url: AnyUrl | None = None ) -> bool:
        result_file: Path
        errors = 0
        if (not news_date and not news_url) or (news_date and news_url):
            logger.error("Must be set or `date` or `url` parameters")
            return False
        try:

            work_date = news_date if news_date else date.today()
            # Define name(with full path) for saving a crawling result
            if not (result_file:= await self.set_result_file(work_date)):
                raise FileNotFoundError("Can't create an output file")

            if news_url:
                # Build URLs list based on the one particulary news url 
                urls_list = [news_url] 
            else:    
                # In case of repeated crawlers starts, get list of the urls already scraped articles (for work date)
                already_scrapped_urls = await self.restore_urls_from_result_file(result_file=result_file)
                logger.info("Found ’%s’ records already collected", len(already_scrapped_urls))

                sitemap_urls_list: list[tuple[str, datetime]] = await self.get_urls_from_sitemap(sitemap_date=work_date)
                logger.info("The sitemap file for a date ’%s’ contains `%s` records", work_date, len(sitemap_urls_list))

                # We'll only collect articles that haven't been scrapped yet
                urls_list: list[str] =  await self.prepare_urls_list_for_scraping(sitemap_list=sitemap_urls_list, already_scrapped_list=already_scrapped_urls)
            
            logger.info("’%s’ new news articles will be collected", len(urls_list))
            if urls_list:
                if not (page:= await self.login_into_news_site()):
                    logger.fatal("The scraping process cannot be continued")
                    return False

            for url_ind, url in enumerate(urls_list, 1):
                if (article:= await self.parse_page(page_url=url)):
                    logger.info("[%s/%s] - `%s` - success", url_ind, len(urls_list), url)
                    await self.append_record_to_json_file(filename=result_file, json_data=article.model_dump_json(indent=4))
                else:
                    logger.error("[%s/%s] - `%s`- fail", url_ind, len(urls_list), url)  
                    errors += 1
        except Exception as exc:
            errors += 1
            logger.error("Crawler error `%s - '%s' : '%s'`", exc, news_date, news_url)
        finally:
            await self.stop_browser()    
        return not bool(errors)

    
    async def restore_urls_from_result_file(self, result_file: Path, block_size=1024*10) -> list[str]:
        """
            Get list of URLs already gathered news articles
        """
        buffer: str = ""
        urls_list: list[str] = []
        url_pattern = re.compile(r'"article_url":\s*"(http[s]?://[^\"]+)"')
        if result_file.exists():
            async with aiofiles.open(result_file, 'r') as file:
                while chunk := await file.read(block_size):
                    buffer += chunk
                    for match in url_pattern.finditer(buffer):
                        url = match.group(1)
                        end_position_in_buffer = match.end()
                        urls_list.append(url)
                    
                    buffer = buffer[end_position_in_buffer:]

        return urls_list


    async def append_record_to_json_file(self, filename: Path, json_data: str):
        '''
            In order to minimise memory consumption when adding a new record to the result file, 
            the record is added to the end of the file, without fully loading the json file 
        '''
        if filename.exists():
            # Open the file in read-plus mode (r+)
            async with aiofiles.open(filename, 'r+') as file:
                # Move the cursor to the end of the file and backtrack to remove the last character `]`
                await file.seek(0, os.SEEK_END)
                pos = await file.tell()
                pos = pos -1 if pos > 0 else 0
                await file.seek( pos, os.SEEK_SET)
                
                # Write a comma to separate the last item from the new item and the closing bracket `]`
                await file.write(",\n" + json_data + "]")
        else:
            # If the file doesn't exist or is empty, create it as a new JSON array
            async with aiofiles.open(filename, 'w') as json_file:
                await json_file.write("[" + json_data + "]")