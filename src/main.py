from logger import init_logger
init_logger()

import asyncio

from helpers.environment_helper import create_folders_tree
from helpers.tasks_helper import task_dispatcher
from settings import settings



async def main(scan_interval: int = 10):
    create_folders_tree(root_dir=settings.WORKDIR)
    await task_dispatcher(scan_interval=scan_interval)

if __name__ == "__main__":
    asyncio.run(main())