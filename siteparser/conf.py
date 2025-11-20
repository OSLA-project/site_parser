from pathlib import Path
import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")


ROOT_DIR = Path(__file__).parent.parent
LOCAL_DIR = ROOT_DIR / "local"

