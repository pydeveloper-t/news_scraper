from enum import StrEnum
import aiofiles
import json
import random
import httpx
import ua_generator
from pydantic import AnyUrl, BaseModel
from pathlib import Path

class RequestTypes(StrEnum):
    GET = "GET"
    POST = 'POST'
    HEAD = 'HEAD'

class Response(BaseModel):
    successfull: bool 
    status_code: int
    response_text: str | None = None
    response_json: dict | None = None 
    error: str | None = None 

class RequestsBase:
    async def  request(self, request_type: RequestTypes, url: AnyUrl, params: dict | None = None, json: dict | None = None, headers: dict | None = None,) -> Response:
        successfull: bool = False 
        status_code: int | None = None
        response_text: str | None = None
        response_json: dict | None = None 
        error: str | None = None 
        response: Response
        try:
            match request_type:
                case RequestTypes.GET:
                    raw_response = await self.client.get(
                        url=url,
                        params=params,
                        headers=headers
                        )
                case RequestTypes.POST:
                    raw_response = await self.client.post(
                        url=url,
                        json=json,
                        headers=headers
                        )
                    
            status_code = raw_response.status_code
            if status_code == 200:
                response_text = raw_response.text
                try:
                    response_json = raw_response.json()
                except:
                    pass
                successfull = True   
        except Exception as exc:
            error = str(exc)
        finally:
            await self.client.aclose()
            response = Response(successfull=successfull, status_code=status_code, response_text=response_text, response_json=response_json, error=error)
        return response
    
    def  get_random_useragent(self, device: str | tuple[str] | None = None, browser: str | tuple[str] | None = None, platform: str | tuple[str] | None = None) -> dict:
        """
        device = ('desktop', 'mobile')
        platform = ('windows', 'macos', 'ios', 'linux', 'android')
        browser = ('chrome', 'edge', 'firefox', 'safari')
        """
        ua = ua_generator.generate(device=device, browser=browser, platform=platform)
        return ua.headers.get()
    
    async def get_random_crawler_bot_useragent(self) -> str:
        ua_json_path = Path(__file__).parent.parent.parent / "src/crawlers/helpers/crawler_user_agents/crawler_user_agents.json"
        async with aiofiles.open(ua_json_path, "r") as f:
            content = await f.read()
            ua_json_list = json.loads(content)
        bots =  [instance for item in ua_json_list for instance in item["instances"] if item["pattern"].replace("/", "").replace("\\", "").strip().lower() in ("googlebot", "bingbot")]
        return random.choice(bots)


http_request = RequestsBase()
