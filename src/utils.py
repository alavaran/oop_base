import uuid
# ============ UUID Generator (Single Responsibility) ============
class UUIDGenerator:
    """Генерация уникальных идентификаторов"""

    @staticmethod
    def generate() -> str:
        return str(uuid.uuid4())