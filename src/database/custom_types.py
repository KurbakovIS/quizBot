import os
from typing import Any
from fastapi_storages.integrations.sqlalchemy import FileType as _FileType
from fastapi_storages import FileSystemStorage

class FileType(_FileType):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if os.getenv('DOCKER', 'False').lower() == 'true':  # Проверка, выполняется ли код внутри Docker
            path = '/data'
        elif os.name == 'nt':  # Windows
            path = 'C:\\temp'  # Убедитесь, что путь существует и имеет правильные разрешения
        else:  # Unix-like (Linux, macOS, etc.)
            path = '/tmp'

        storage = FileSystemStorage(path=path)
        super().__init__(storage=storage, *args, **kwargs)
