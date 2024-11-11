from pydantic import BaseModel, AnyUrl

class NYTimesPageScheme(BaseModel):
    article_url: AnyUrl
    article_title: str | None = None  
    article_authors_list: list[str] | None = None  
    article_created: str| None = None  
    article_summary: str | None = None
    article_images_list: list[AnyUrl]| None = None
    article_image_caption: str | None = None
    article_body:  str | None = None
