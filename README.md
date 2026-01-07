# 👁️ MeterVision

**Automated Hierarchical Meter Infrastructure & AI-Powered Reading Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![OCR Ensemble](https://img.shields.io/badge/OCR-Ensemble-green)](https://github.com/tesseract-ocr/tesseract)
[![Gemini AI](https://img.shields.io/badge/Gemini-1.5%20Flash-violet?logo=google-gemini)](https://deepmind.google/technologies/gemini/)

MeterVision is a robust, end-to-end solution designed to manage complex meter infrastructures and automate the process of collecting readings through advanced computer vision. Whether you're managing industrial parks, residential buildings, or utility networks, MeterVision provides the tools to organize, monitor, and scale your operations.

---

## ✨ Key Features

### 🏢 Hierarchical Asset Management
Organize your infrastructure with a flexible, five-layer hierarchy:
*   **Projects**: Top-level containers for large-scale operations.
*   **Customers**: Manage clients or tenants individually.
*   **Buildings**: Physical assets associated with customers.
*   **Places**: Specific locations within buildings (e.g., "Basement", "Kitchen").
*   **Meters**: The leaf nodes supporting various types (Electricity, Gas, Heat).

### 🤖 Intelligent OCR Ensemble
MeterVision doesn't rely on a single model. It uses a sophisticated **voting ensemble** to ensure maximum accuracy:
1.  **Google Gemini 1.5 Flash**: State-of-the-art vision-language model for complex environments.
2.  **EasyOCR**: Deep learning-based OCR for high-accuracy text extraction.
3.  **Tesseract OCR**: The industry standard for reliable text processing.
*Includes a calibration system that uses expected values to improve confidence.*

### 🎨 Modern Dashboard
*   **Card-Based Interface**: Elegant, dark-mode-ready design using the Outfit typeface.
*   **Real-Time Status**: Instant overview of active meters and monitoring status.
*   **Mobile Friendly**: Designed for field technicians to upload readings directly from their devices.

---

## 🛠️ Tech Stack

*   **Backend**: FastAPI, SQLModel (SQLAlchemy + Pydantic)
*   **Database**: SQLite (default), extensible to PostgreSQL
*   **OCR Engine**: Tesseract, EasyOCR, Google Generative AI (Gemini)
*   **Frontend**: Vanilla JavaScript + Modern CSS (no heavy frameworks required)
*   **Icons**: Phosphor Icons

---

## ⚡ Quick Start

### 1. Prerequisites
*   Python 3.10+
*   Tesseract OCR installed on your system (`sudo apt install tesseract-ocr`)

### 2. Installation
```bash
git clone https://github.com/bejranonda/MeterVision.git
cd MeterVision
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env.local` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword123
```

### 4. Run it
```bash
uvicorn app.main:app --reload
```
Visit `http://localhost:8000` for the dashboard and `http://localhost:8000/docs` for the API documentation.

---

## 🧪 Verification & Testing
Ensure everything is running correctly with our automated script:
```bash
python verify_setup.py
```
This script validates the entire pipeline from hierarchy creation to OCR reading processing.

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

---

## ⚖️ License
This project is licensed under the MIT License - see the LICENSE file for details.
