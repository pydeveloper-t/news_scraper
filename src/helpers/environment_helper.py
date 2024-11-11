import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_folders_tree(root_dir: str):
    for subfolder in ('tasks/new', 'tasks/done/ok', 'tasks/done/fail', "result", "profiles"):
        path = Path(root_dir) / subfolder
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Created folder - `%s`", path)