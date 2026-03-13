import logging
from datetime import datetime
import os

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs("logs", exist_ok=True)
log_filename = f"logs/{timestamp}_debug.txt"

class ContextFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'clientip'):
            record.clientip = 'SYSTEM'
        if not hasattr(record, 'useragent'):
            record.useragent = '-'
        return True

# Добавили %(useragent)s в формат
formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(clientip)-15s | %(useragent)-40s | %(message)s")

file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stream_handler])

logger = logging.getLogger("attendance_system")
logger.addFilter(ContextFilter())

logging.getLogger('aiosqlite').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)    