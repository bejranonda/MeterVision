import shutil
import os
from abc import ABC, abstractmethod
from typing import Optional

class MeterReader(ABC):
    @abstractmethod
    def read_meter(self, image_path: str) -> float:
        pass

class MockMeterReader(MeterReader):
    def read_meter(self, image_path: str) -> float:
        # Simulate processing time or just return a static value
        return 12345.67

class BasicMeterReader(MeterReader):
    # Placeholder for real OCR implementation
    def read_meter(self, image_path: str) -> float:
        # TODO: Implement actual OCR logic here
        return 0.0

def save_upload_file(upload_file, destination: str):
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
