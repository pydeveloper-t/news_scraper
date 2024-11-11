from datetime import date, datetime
from pydantic import BaseModel, AnyUrl, model_validator, field_validator, ConfigDict

from crawlers import supported_crawlers

class CrawlerTask(BaseModel):
    crawler_name: str
    crawling_aim: date  | str | None | AnyUrl
    
    model_config = ConfigDict(
        extra='allow',
    )    
    
    # Validate `crawler_name` against `supported_crawlers`
    @field_validator('crawler_name')
    def validate_crawler_name(cls, value):
        if value not in supported_crawlers:
            raise ValueError(f"'crawler_name' must be one of {supported_crawlers}")
        return value
    
   
    # Ensure the overall consistency of values based on `crawling_aim`
    @model_validator(mode="before")
    def check_aim_consistency(cls, values):
        
        aim = values.get('crawling_aim')

        try:
            values["crawling_url"] = AnyUrl(aim)     
        except ValueError:
            values["crawling_url"] = None
        if not values["crawling_url"]:
            try:
                values["crawling_date"] = datetime.strptime(aim, '%Y-%m-%d').date()
            except:
                values["crawling_date"] = date.today()
                
        
        return values
