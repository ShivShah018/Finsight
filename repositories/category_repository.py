import logging
from typing import Optional
from repositories.base import BaseRepository
from utils.db_manager import Category

logger = logging.getLogger(__name__)


class CategoryRepository(BaseRepository):
    def find_by_user(self, user_id: int, cat_type: Optional[str] = None) -> list[Category]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            if cat_type:
                cursor.execute(
                    "SELECT id, name, type, icon, color FROM categories WHERE user_id = %s AND type = %s ORDER BY name",
                    (user_id, cat_type),
                )
            else:
                cursor.execute(
                    "SELECT id, name, type, icon, color FROM categories WHERE user_id = %s ORDER BY type, name",
                    (user_id,),
                )
            return [Category(**r) for r in cursor.fetchall()]
        finally:
            cursor.close()
