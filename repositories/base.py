import logging
from utils.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self):
        self._db = DatabaseManager.get_instance()

    @property
    def db(self) -> DatabaseManager:
        self._db.connect()
        return self._db
