
import os
import shutil
from typing import BinaryIO
from pathlib import Path

class StorageService:
    def save(self, file_obj: BinaryIO, destination: str) -> str:
        raise NotImplementedError

class LocalStorageService(StorageService):
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, file_obj: BinaryIO, destination: str) -> str:
        """Saves file locally. Destination should include filename."""
        full_path = self.base_path / destination
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        return str(full_path)

# Mock S3 for later
class S3StorageService(StorageService):
    def save(self, file_obj: BinaryIO, destination: str) -> str:
        # Implementation for boto3 S3 upload would go here
        return f"s3://bucket/{destination}"
