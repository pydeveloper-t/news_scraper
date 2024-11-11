import asyncio
import logging
import random

import httpx
import zendriver as zd
from pathlib import Path

logger = logging.getLogger(__name__)

class WebBase:
    predefined_browser_args = [
        "--hide-crash-restore-bubble",
        "--disable-notifications",
        "--disable-save-password-bubble",
        "--disable-password-manager",
        "--no-service-autorun",
        "--password-store=basic"
        
        ]

    def __init__(self, workdir: Path, profile_path: Path, browser_args: list[str] | None = None, timeout: float = 15):
        self.browser = None
        self.workdir = workdir
        self.profile_path = profile_path
        self.timeout = timeout
        self.browser_args = WebBase.predefined_browser_args + (browser_args  if browser_args else {})

    @staticmethod
    async def random_delay(from_: int = 1, to_: int = 5) -> None:
        await asyncio.sleep(random.randint(from_, to_))

    async def init_browser(self):
        # '/home/android/.config/google-chrome/AppProfile'
        if not self.browser:
            self.browser = await zd.start(headless=False, browser_args=self.browser_args, user_data_dir=self.profile_path)

    async def stop_browser(self)-> None:
        if self.browser:
            await self.browser.stop()

    async def open_url(self, url: str, new_tab: bool=False) ->zd.Tab:
        return await self.browser.get(url, new_tab=new_tab)    

    async def get_element(self, page: zd.Tab, selector: str, timeout: float | None = None) -> zd.Element | None:
        item: zd.Element | None  = None
        try:
            item: zd.Element | None  = await page.find(selector, timeout=timeout if timeout else self.timeout)
        except TimeoutError:
            pass
        except:
            pass
        return item


    async def get_texts_by_xpath(self, page: zd.Tab, xpath_selector: str, timeout: float | None = None) -> list[str]:
        result_str_list: list[str] = []
        try:
            result_list: list[zd.Element] | None  = await page.find_all(xpath_selector, timeout=timeout if timeout else self.timeout)
            if result_list:
                result_str_list = [item.text.strip() for item in result_list] 
        except TimeoutError:
            pass
        except:
            pass
        return result_str_list    
    

    async def get_data_by_selectors(self, page: zd.Tab, selectors: dict, ignore_errors: bool = True) -> tuple[bool, dict]:
        result: list[dict] = {}
        errors: int = -1
        await page
        for xpath_code, xpath_expression in selectors.items():
            try:
                result_list: list[str] = await self.get_texts_by_xpath(page=page, xpath_selector=xpath_expression, timeout=2)
                result_list = [v.strip() for v in result_list if v.strip()]
                if result_list:
                    result[xpath_code.lower()] = result_list if xpath_code.upper().endswith("LIST") else ' '.join(result_list)
                else:
                    result[xpath_code.lower()] = None
            except Exception as exc:
                errors -= 1
                logger.error("Error `%s` receiving data by XPATH `%s` : `%s`", str(exc), xpath_code, xpath_expression)
            if not ignore_errors and errors:
                result = None
                raise ValueError("Error receiving data by XPATH `%s` : `%s`", xpath_code, xpath_expression)
        
        # An errors are present if the `errors`` not equal 0                   
        errors += 1 
        return bool(errors), result


