# MeterVision Concepts

## 🌟 Project Vision
MeterVision is designed as a **B2B SaaS "Meter Reading as a Service"** platform. Its primary goal is to provide utility companies and facility managers with a robust, automated way to collect meter readings (Electricity, Gas, Water, Heat) using low-cost camera devices and high-accuracy AI.

## 🏢 Multi-Tenancy & Data Isolation
The project is built from the ground up to support multiple independent organizations (tenants).

### Hierarchical Data Model
To represent complex real-world facilities, MeterVision uses a 6-layer hierarchy:
1.  **Organization**: The top-level tenant (e.g., "City Power & Light").
2.  **Project**: A container for related assets (e.g., "Smart Grid Hub").
3.  **Customer**: The end-client (e.g., "Downtown Apartments").
4.  **Building**: A physical structure.
5.  **Place**: A specific location within a building (e.g., "Basement North").
6.  **Meter**: The actual physical device.

### Security Isolation
- **Automatic Filtering**: All API queries are implicitly scoped to the user's current organization.
- **Cross-Org Prevention**: Users cannot access or modify data belonging to other organizations unless they are a Super Admin.

## 🤖 AI-Powered OCR (The "Voting Ensemble")
Reliability is the biggest challenge in automated meter reading. MeterVision solves this by using a **Voting Ensemble** architecture.

### How it Works:
1.  **Multiple Experts**: When an image is uploaded, it is sent to multiple AI models:
    - **Gemma 3 (27B & 12B)**: High-level reasoning and visual understanding.
    - **Qwen 2.5 VL**: Specialized visual-language model.
    - **EasyOCR / Tesseract**: Traditional deep-learning and statistical OCR.
2.  **Consensus Mechanism**: The system compares results. If the advanced models agree, the confidence is high.
3.  **Calibration**: Users can provide an "Expected Reading" (current physical value) during installation. The AI uses this as a hint to "focus" its recognition, significantly increasing accuracy for difficult-to-read meters.

## 📷 Professional Installation Workflow
Installing a camera to read a meter is a precision task. MeterVision provides a guided **Installer App** to ensure every camera is set up correctly.

### Validation Pipeline:
- **Connection**: Verifies the camera can communicate with the server.
- **FOV (Field of View)**: AI checks if the meter is fully visible and not cut off.
- **Glare Detection**: Detects reflections that might obscure digits.
- **Initial OCR**: Confirms the AI can successfully read the value before the installer leaves the site.

## 🛡️ Role-Based Access Control (RBAC)
The system distinguishes between platform-level and organization-level roles:
- **Platform Roles**: Super Admin, Platform Manager (global control).
- **Organization Roles**: Org Manager, Org Viewer, Installer (tenant-level control).

This allows a single platform instance to be managed by a service provider while giving customers complete control over their own data and staff.
