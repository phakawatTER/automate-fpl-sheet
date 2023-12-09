import fpl_service
from loguru import logger

for i in range(38):
    gw = i + 1
    logger.info(f"processing game week {gw}")
    fpl_service.update_fpl_table(gw)
