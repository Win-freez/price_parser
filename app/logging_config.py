import logging
from pathlib import Path
def setup_logging(log_file: str = "errors.log"):
    BASE_DIR = Path(__file__).parent.parent.parent
    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(BASE_DIR / log_file, encoding="utf-8")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

