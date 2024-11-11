import asyncio
import logging
from pathlib import Path
from crawlers.schemes.crawlers_task import CrawlerTask
from crawlers import NYTimes
from settings import settings


logger = logging.getLogger(__name__)

def move_file_with_increment(source: Path, destination: Path) -> Path:
    '''
        The method moves the task file to the destination directory, 
        renaming the existing file by adding an incremental number to the file name
    '''
    if destination.is_file():
        destination = destination.parent
    destination_file = destination / source.name    
    # If the destination file exists, increment index until an available filename is found
    if destination_file.exists():
        counter = 1
        while True:
            # Create a new filename with an incremented counter
            new_destination = destination_file.with_stem(f"{destination_file.stem}_{counter}")
            if not new_destination.exists():
                destination_file = new_destination
                break
            counter += 1

    # Move the file to the new (or original if no conflict) destination
    source.rename(destination_file)
    return destination_file


async def task_dispatcher(scan_interval: int = 10):
    '''
        The method periodically scans the input directory for the presence of a file with a crawling job, 
        starts crawling and after crawling is completed (either successfully or unsuccessfully) moves the job file 
        from the input directory to the corresponding output directory.
        Format of the task file:
        {
            "crawler_name": "NYTIMES" (...)
            "crawling_aim": "DAY" or "URL"
            "crawling_date": null or  "CURRENT_DAY" or date YYYY-MM-DD (2024-10=25)
            "crawling_url": null or url ("https://www.nytimes.com/2024/11/12/world/middleeast/israel-north-gaza-hamas-war.html")
        }

        if crawling_aim = "DAY" must be set 

{
    "crawler_name": "NYTIMES",
    "crawling_aim": "CURRENT_DAY",
    "crawling_date": null,
    "crawling_url": "https://www.nytimes.com/interactive/2024/11/05/us/elections/results-alabama-us-house-2.html"
}

    '''
    task_in = Path(settings.WORKDIR) /  "tasks/new" 
    task_done = Path(settings.WORKDIR) / "tasks/done" 

    while True:
        for file in list(task_in.iterdir()):
            try:
                task: CrawlerTask = CrawlerTask.model_validate_json(open(file, 'r').read())
            except ValueError as ve:
                logger.error("Wrong task in file `%s` - `%s`", file, ve)
            else:
                match task.crawler_name:
                    case 'NYTIMES':
                        nytimes_crawler = NYTimes(email=settings.NYTIMES_EMAIL, password=settings.NYTIMES__PASSWORD, workdir=Path(settings.WORKDIR))
                        success: bool = await nytimes_crawler.crawler(news_date=task.crawling_date, news_url=task.crawling_url)
                    case _ :
                        pass
                destination = move_file_with_increment(source=file, destination=task_done / ("ok" if success else "fail"))
                logger.info("Task file moved to: `%s`", destination)
        await asyncio.sleep(scan_interval)