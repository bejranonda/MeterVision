# GitHub "About" settings

These are the values to set on the repository home page. They are kept here as
the source of truth; update GitHub from this file when it changes.

> Apply them in **Settings → General → Description** and via the **gear icon
> next to "About"** on the repo home page (Description, Website, Topics).

## Description

Use this as the repository description (under GitHub's 350-character limit):

```
Read electricity, gas, water, and heat meters from photos. Multi-tenant FastAPI platform with a voting OCR ensemble (Gemma 3, Qwen 2.5 VL, EasyOCR, Tesseract), role-based access control, and an MQTT camera pipeline for automatic meter reading.
```

## Topics

Paste these into the Topics field (GitHub allows up to 20):

```
meter-reading
automatic-meter-reading
smart-metering
ocr
ocr-ensemble
computer-vision
multi-tenant
saas
fastapi
python
sqlmodel
energy-management
utility
iot
mqtt
tesseract
easyocr
gemma
generative-ai
dashboard
```

## Why these

- The description leads with the concrete job ("read meters from photos") and
  the meter types people actually search for, then names the stack. It drops the
  earlier "Gemini" reference, which was wrong — the ensemble uses Gemma 3 and
  Qwen, not Gemini.
- Topics cover the problem (`meter-reading`, `automatic-meter-reading`,
  `smart-metering`), the method (`ocr`, `ocr-ensemble`, `computer-vision`), the
  stack (`fastapi`, `python`, `sqlmodel`, `mqtt`), and the domain (`utility`,
  `energy-management`, `iot`), which is the spread that surfaces a repo across
  different searches.
