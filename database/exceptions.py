class DatabaseError(Exception):
    """
    Базовое исключение для всех ошибок, связанных с работой базы данных.
    Наследуется от стандартного Exception.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class SchemaInitializationError(DatabaseError):
    """
    Исключение, возникающее при ошибке чтения или выполнения SQL-скрипта 
    инициализации схемы (таблиц, индексов и т.д.).
    Наследуется от DatabaseError, чтобы можно было поймать любую ошибку БД, 
    если нужно.
    """
    def __init__(self, message: str, file_path: str | None = None):
        super().__init__(message)
        self.file_path = file_path  # Сохраняем путь к файлу для удобной отладки

    def __str__(self) -> str:
        """Переопределяем строковое представление для более информативного вывода."""
        if self.file_path:
            return f"{self.message} (Файл: {self.file_path})"
        return self.message
