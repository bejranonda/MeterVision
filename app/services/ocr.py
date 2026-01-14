import shutil
import os
from abc import ABC, abstractmethod
from typing import Optional

import pytesseract
from PIL import Image
import easyocr
import re

class MeterReader(ABC):
    @abstractmethod
    def read_meter(self, image_path: str, expected_value: Optional[str] = None) -> float:
        pass

class MockMeterReader(MeterReader):
    def read_meter(self, image_path: str, expected_value: Optional[str] = None) -> float:
        # Simulate processing time or just return a static value
        if expected_value:
             return float(expected_value)
        return 12345.67

class TesseractMeterReader(MeterReader):
    def read_meter(self, image_path: str, expected_value: Optional[str] = None) -> float:
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, config='--psm 7')
            
            # Calibration: Check if expected value is present
            if expected_value:
                # Basic fuzzy match: remove spaces and check existence
                clean_ocr = text.replace(" ", "").replace(",", ".")
                clean_expected = expected_value.replace(" ", "").replace(",", ".")
                if clean_expected in clean_ocr:
                    return float(expected_value)

            cleaned_text = "".join([c for c in text if c.isdigit() or c in ['.', ',']])
            cleaned_text = cleaned_text.replace(',', '.')
            if not cleaned_text:
                return 0.0
            return float(cleaned_text)
        except Exception as e:
            print(f"Error processing image with Tesseract: {e}")
            return 0.0

class EasyOCRMeterReader(MeterReader):
    def __init__(self):
        self.reader = easyocr.Reader(['en'])

    def read_meter(self, image_path: str, expected_value: Optional[str] = None) -> float:
        try:
            results = self.reader.readtext(image_path, detail=0)
            
            # Calibration: Check if expected value is present in any segment
            if expected_value:
                clean_expected = expected_value.replace(" ", "").replace(",", ".")
                for text in results:
                    clean_ocr = text.replace(" ", "").replace(",", ".")
                    # Allow fuzzy match or exact contained match
                    if clean_expected in clean_ocr:
                        return float(expected_value)
            
            best_candidate = 0.0
            max_digits = 0
            
            for text in results:
                cleaned_text = "".join([c for c in text if c.isdigit() or c in ['.', ',']])
                cleaned_text = cleaned_text.replace(',', '.')
                if not cleaned_text or cleaned_text.count('.') > 1:
                    continue
                try:
                    val = float(cleaned_text)
                    num_digits = len(cleaned_text.replace('.', ''))
                    score = num_digits
                    if '.' in cleaned_text:
                        score += 2 
                    
                    if score > max_digits and val < 1000000:
                        max_digits = score
                        best_candidate = val
                except ValueError:
                    continue

            return best_candidate
        except Exception as e:
            print(f"Error processing image with EasyOCR: {e}")
            return 0.0

import google.generativeai as genai

class GeminiMeterReader(MeterReader):
    def __init__(self, model_name="gemini-1.5-flash-latest"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL_VERSION", model_name)

        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            print(f"Initializing GeminiMeterReader with model: {self.model_name}")
            self.model = genai.GenerativeModel(self.model_name)

    def read_meter(self, image_path: str, expected_value: Optional[str] = None) -> float:
        if not self.model:
             return 0.0
        
        try:
            image = Image.open(image_path)
            prompt = "Read the numeric value from this meter. Return ONLY the number. If you are unsure, return 0. Ignore any non-numeric text."
            if expected_value:
                prompt += f" The expected value is close to {expected_value}."
            
            response = self.model.generate_content([prompt, image])
            text = response.text.strip()
            
            # Basic cleanup
            cleaned_text = "".join([c for c in text if c.isdigit() or c in ['.', ',']])
            cleaned_text = cleaned_text.replace(',', '.')
            
            if not cleaned_text:
                return 0.0
            
            return float(cleaned_text)
        except Exception as e:
            print(f"Error processing image with Gemini ({self.model_name}): {e}")
            return 0.0

class SmartMeterReader(MeterReader):
    def __init__(self):
        self.tesseract = TesseractMeterReader()
        self.easyocr = EasyOCRMeterReader()
        self.gemini_1_5 = GeminiMeterReader(model_name="gemini-1.5-flash-latest")
        self.gemini_2_0 = GeminiMeterReader(model_name="gemini-2.0-flash-exp")

    def read_meter(self, image_path: str, expected_value: Optional[str] = None) -> float:
        val_easy = self.easyocr.read_meter(image_path, expected_value)
        val_tess = self.tesseract.read_meter(image_path, expected_value)
        val_gemini_1_5 = self.gemini_1_5.read_meter(image_path, expected_value)
        val_gemini_2_0 = self.gemini_2_0.read_meter(image_path, expected_value)

        
        print(f"OCR Results - Tesseract: {val_tess}, EasyOCR: {val_easy}, Gemini 1.5: {val_gemini_1_5}, Gemini 2.0: {val_gemini_2_0}")
        
        # If expected value was matched by any, verify and return it
        if expected_value:
            try:
                exp_float = float(expected_value.replace(",", "."))
                results = [val_easy, val_tess, val_gemini_1_5, val_gemini_2_0]
                if exp_float > 0 and exp_float in results:
                    return exp_float
            except:
                pass

        # Voting / Consensus Logic
        # 1. If Gemini models agree, trust them
        if val_gemini_1_5 == val_gemini_2_0 and val_gemini_1_5 > 0:
            return val_gemini_1_5

        # 2. If a Gemini model agrees with a local OCR, that's a strong signal
        if val_gemini_2_0 > 0 and (val_gemini_2_0 == val_easy or val_gemini_2_0 == val_tess):
            return val_gemini_2_0
        if val_gemini_1_5 > 0 and (val_gemini_1_5 == val_easy or val_gemini_1_5 == val_tess):
            return val_gemini_1_5

        # 3. If local OCRs agree, trust them
        if val_easy == val_tess and val_easy > 0:
            return val_easy
        
        # 4. If no consensus, trust the "smartest" model that returned a value. Prioritize 2.0.
        if val_gemini_2_0 > 0:
            return val_gemini_2_0
        if val_gemini_1_5 > 0:
            return val_gemini_1_5

        # 5. Fallback to local models if Gemini failed
        if val_easy > 0:
            return val_easy
        elif val_tess > 0:
            return val_tess
        else:
            return 0.0

class BasicMeterReader(MeterReader):
    def read_meter(self, image_path: str, expected_value: Optional[str] = None) -> float:
        return 0.0

def save_upload_file(upload_file, destination: str):
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
