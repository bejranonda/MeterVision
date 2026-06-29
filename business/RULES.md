# MeterVision Multi-Tenant Business Rules

This document outlines the core business logic and rules governing the MeterVision platform.

## 1. Multi-Tenant Data Isolation

- **Strict Isolation**: All data entities (Project, Customer, Building, Place, Meter, Reading, Camera, InstallationSession) MUST have an `organization_id`.
- **Query Filtering**: Every API request must verify that the `current_user` has access to the requested `organization_id`.
- **Middleware Enforcement**: The `get_current_user_org_context` middleware is used to validate membership before processing organization-scoped requests.

## 2. Role-Based Access Control (RBAC)

MeterVision defines 5 hierarchical roles:

| Role | Scope | Permissions |
| :--- | :--- | :--- |
| **Super Admin** | Global | Full system access, create organizations, manage platform config. |
| **Platform Manager** | Global | Manage installers across organizations, list all organizations. |
| **Org Manager** | Organization | Manage projects, customers, buildings, and users within their organization. |
| **Org Viewer** | Organization | Read-only access to organization assets and readings. |
| **Installer** | Organization | Perform meter installations and validations in assigned organizations. |

## 3. Installation Workflow Rules

- **Pre-requisites**:
    - Camera must be registered (provisioning status).
    - Meter must exist or will be created during session start.
- **Validation Pipeline**:
    - **Step 1: Connection**: Camera must have sent a heartbeat within the last 5 minutes.
    - **Step 2: FOV (Field of View)**: Meter face must be fully visible and centered.
    - **Step 3: Glare**: Lighting must be sufficient for OCR without major reflections.
    - **Step 4: Initial OCR**: A test reading must be obtained with >70% confidence.
- **Completion**:
    - Installation can only be `COMPLETED` if the installer manually confirms after validation.
    - Upon completion, camera status moves to `ACTIVE` and is linked to the `meter_id`.

## 4. Reading Verification Rules

- **Ensemble Voting**: The system uses a weighted voting mechanism over
  **Gemma 3 27B (Google) > Gemma 3 12B (OpenRouter) > Qwen 2.5 VL (OpenRouter)**,
  corroborated by **EasyOCR** and **Tesseract**, to determine the most likely
  reading. See `docs/KNOWLEDGE_BASE.md` for the exact priority order.
- **Verification status**: A reading is stored as `Verified` when the ensemble
  produced a value and `Failed` when every engine returned no reading (`0.0`).
- **Target rule (not yet implemented):** Confidence-threshold auto-verification
  (e.g. auto-verify above 95%, queue lower-confidence readings as `Pending` for
  manual review) requires a real confidence score from the ensemble, which is a
  known TODO — see `docs/KNOWN_ISSUES.md`.
