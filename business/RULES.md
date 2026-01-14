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

- **Automatic Verification**: OCR readings with confidence > 95% are automatically marked as `Verified`.
- **Manual Review**: Readings with lower confidence are marked as `Pending` for manual review by an `Org Manager` or `Org Viewer`.
- **Ensemble Voting**: The system uses a weighted voting mechanism (Gemini 2.0 Flash > Gemini 1.5 Flash > EasyOCR > Tesseract) to determine the most likely reading.
