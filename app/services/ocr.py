import shutil
import os
from abc import ABC, abstractmethod
from typing import Optional
import requests
import base64

import pytesseract
from PIL import Image
import easyocr
import re
import google.generativeai as genai

class MeterReader(ABC):
    @abstractmethod
    def read_meter(self, image_path: str, expected_value: Optional[str] = None, custom_prompt: Optional[str] = None) -> float:
        pass

class MockMeterReader(MeterReader):
    def read_meter(self, image_path: str, expected_value: Optional[str] = None, custom_prompt: Optional[str] = None) -> float:
        # Simulate processing time or just return a static value
        if expected_value:
             return float(expected_value)
        return 12345.67

class TesseractMeterReader(MeterReader):
    def read_meter(self, image_path: str, expected_value: Optional[str] = None, custom_prompt: Optional[str] = None) -> float:
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

    def read_meter(self, image_path: str, expected_value: Optional[str] = None, custom_prompt: Optional[str] = None) -> float:
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



class GemmaGoogleMeterReader(MeterReader):
    """Gemma 3 27B using Google Generative AI API (Google API Key)"""
    def __init__(self, model_name="models/gemma-3-27b-it"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model_name

        if not self.api_key:
            print("Warning: GEMINI_API_KEY (for Gemma Google) not found in environment variables.")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            print(f"Initializing GemmaGoogleMeterReader with model: {self.model_name}")
            self.model = genai.GenerativeModel(self.model_name)

    def read_meter(self, image_path: str, expected_value: Optional[str] = None, custom_prompt: Optional[str] = None) -> float:
        if not self.model:
             return 0.0
        
        try:
            image = Image.open(image_path)
            prompt = custom_prompt if custom_prompt else "Read the numeric value from this meter. Return ONLY the number. If you are unsure, return 0. Ignore any non-numeric text."
            if expected_value:
                prompt += f" The expected value is close to {expected_value}."
            
            response = self.model.generate_content([prompt, image])
            text = response.text.strip()
            
            # Basic cleanup
            cleaned_text = "".join([c for c in text if c.isdigit() or c in ['.', ',']])
            cleaned_text = cleaned_text.replace(',', '.')
            
            if not cleaned_text:
                # More aggressive regex for Gemma
                match = re.search(r'(\d+[.,]\d+|\d+)', text)
                if match:
                    cleaned_text = match.group(1).replace(',', '.')
                else:
                    return 0.0
            
            return float(cleaned_text)
        except Exception as e:
            print(f"Error processing image with Gemma Google ({self.model_name}): {e}")
            return 0.0

class OpenRouterMeterReader(MeterReader):
    def __init__(self, model_name="google/gemma-3-12b-it:free"):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            print("Warning: OPENROUTER_API_KEY not found in environment variables.")

    def read_meter(self, image_path: str, expected_value: Optional[str] = None, custom_prompt: Optional[str] = None) -> float:
        if not self.api_key:
            return 0.0

        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = custom_prompt if custom_prompt else "Read the numeric value from this meter. Return ONLY the number. If you are unsure, return 0. Ignore any non-numeric text."
            if expected_value:
                prompt += f" The expected value is close to {expected_value}."

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://metervision.local",
                "X-Title": "MeterVision"
            }

            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_string}"
                                }
                            }
                        ]
                    }
                ]
            }

            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result_json = response.json()
            if 'choices' in result_json and len(result_json['choices']) > 0:
                text = result_json['choices'][0]['message']['content'].strip()
                
                # Basic cleanup
                cleaned_text = "".join([c for c in text if c.isdigit() or c in ['.', ',']])
                cleaned_text = cleaned_text.replace(',', '.')
                
                if not cleaned_text:
                    match = re.search(r'(\d+[.,]\d+|\d+)', text)
                    if match:
                        cleaned_text = match.group(1).replace(',', '.')
                    else:
                        return 0.0
                return float(cleaned_text)
            else:
                return 0.0

        except Exception as e:
            print(f"Error processing image with OpenRouter ({self.model_name}): {e}")
            return 0.0

class SmartMeterReader(MeterReader):
    def __init__(self):
        self.tesseract = TesseractMeterReader()
        self.easyocr = EasyOCRMeterReader()

        # Gemma 3 27B via Google API
        self.gemma_27b = GemmaGoogleMeterReader(model_name="models/gemma-3-27b-it")
        # Gemma 3 12B via OpenRouter
        self.gemma_12b = OpenRouterMeterReader(model_name="google/gemma-3-12b-it:free")
        # Qwen via OpenRouter
        self.qwen_vl = OpenRouterMeterReader(model_name="qwen/qwen-2.5-vl-7b-instruct:free")

    def read_meter(self, image_path: str, expected_value: Optional[str] = None, custom_prompt: Optional[str] = None) -> float:
        val_easy = self.easyocr.read_meter(image_path, expected_value, custom_prompt)
        val_tess = self.tesseract.read_meter(image_path, expected_value, custom_prompt)

        val_gemma_27b = self.gemma_27b.read_meter(image_path, expected_value, custom_prompt)
        val_gemma_12b = self.gemma_12b.read_meter(image_path, expected_value, custom_prompt)
        val_qwen = self.qwen_vl.read_meter(image_path, expected_value, custom_prompt)
        
        print(f"OCR Results - Tesseract: {val_tess}, EasyOCR: {val_easy}, Gemma 27B (Google): {val_gemma_27b}, Gemma 12B (OR): {val_gemma_12b}, Qwen2.5-VL: {val_qwen}")
        
        # If expected value was matched by any, verify and return it
        if expected_value:
            try:
                exp_float = float(expected_value.replace(",", "."))
                results = [val_easy, val_tess, val_gemma_27b, val_gemma_12b, val_qwen]
                if exp_float > 0 and exp_float in results:
                    return exp_float
            except:
                pass

        # Voting / Consensus Logic
        
        # 0. Collect all positive results from AI models
        ai_results = [v for v in [val_gemma_27b, val_gemma_12b, val_qwen] if v > 0]
        
        # If all agree (highly unlikely)

            
        # If any 2 AI models agree
        if val_gemma_27b > 0 and (val_gemma_27b == val_gemma_12b):
            return val_gemma_27b
        if val_gemma_12b > 0 and (val_gemma_12b == val_qwen):
            return val_gemma_12b

        # 1. If Gemma 27B agrees with a local OCR
        if val_gemma_27b > 0 and (val_gemma_27b == val_easy or val_gemma_27b == val_tess):
            return val_gemma_27b



        # 3. If local OCRs agree
        if val_easy == val_tess and val_easy > 0:
            return val_easy
        
        # 4. If no consensus, trust the "smartest" model that returned a value. 
        # Prioritize Gemma 3 27B.
        if val_gemma_27b > 0:
            return val_gemma_27b
        if val_gemma_12b > 0:
            return val_gemma_12b
        if val_qwen > 0:
            return val_qwen


        # 5. Fallback to local models
        if val_easy > 0:
            return val_easy
        elif val_tess > 0:
            return val_tess
        else:
            return 0.0

    def discover_meter(self, image_path: str) -> dict:
        """
        Analyze meter image to suggest type, serial number, and initial reading.
        Returns: {meter_type: str, serial_number: str, reading: float}
        """
        if not self.gemma_27b.model:
            return {"meter_type": "Electricity", "serial_number": "UNKNOWN", "reading": 0.0}

        try:
            image = Image.open(image_path)
            prompt = """
            Analyze this meter image and return a JSON object with:
            1. 'meter_type': One of ['Electricity', 'Gas', 'Water', 'Heat']
            2. 'serial_number': The serial number or ID printed on the meter
            3. 'reading': The current numeric value shown on the display/dial (as a number)
            
            Return ONLY the valid JSON object. Example: {"meter_type": "Gas", "serial_number": "123456", "reading": 102.5}
            """
            
            response = self.gemma_27b.model.generate_content([prompt, image])
            text = response.text.strip()
            
            # Clean possible markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            import json
            data = json.loads(text)
            return {
                "meter_type": data.get("meter_type", "Electricity"),
                "serial_number": data.get("serial_number", "UNKNOWN"),
                "reading": float(data.get("reading", 0.0))
            }
        except Exception as e:
            print(f"Discovery error: {e}")
            return {"meter_type": "Electricity", "serial_number": "UNKNOWN", "reading": 0.0}

class BasicMeterReader(MeterReader):
    def read_meter(self, image_path: str, expected_value: Optional[str] = None) -> float:
        return 0.0

def save_upload_file(upload_file, destination: str):
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()