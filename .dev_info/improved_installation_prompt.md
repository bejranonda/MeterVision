# Mobile Installation Workflow & UX Optimization Request

**Context:**
MeterVision is a multi-tenant B2B SaaS platform for "Meter Reading as a Service". We currently have a basic mobile-web installer application (`/installer`) that allows users (Installers) to provision camera devices, link them to meters, and validate the installation.

**Current Tech Stack:**
- **Frontend:** Vanilla JavaScript, HTML5, CSS3 (Mobile-first design)
- **Backend:** FastAPI, SQLModel
- **Current Flow:** Login -> Select Org -> Scan QR -> Enter Meter Details -> Validation -> Complete

**Objective:**
We need to refine the installation procedure to be the "Gold Standard" for field deployment. The primary goal is speed and simplicity: an installer should be able to complete a setup using *only* their mobile phone, often in challenging environments (basements, utility closets).

**Task:**
Please research and propose an optimal User Experience (UX) and User Flow for the installation process.

## 1. Analysis & Strategy
- **Quick Actions:** Upon login, how can we reduce friction? Should the "New Installation" action be immediate?
- **Field Conditions:** specific UX strategies for:
  - Low light / Glare (common on meter faces).
  - Poor network connectivity (offline syncing?).
  - Awkward physical access (one-handed operation).
- **Validation Feedback:** How to best communicate complex validation failures (e.g., "FOV bad" vs "Glare detected") to a non-technical installer in real-time?

## 2. Proposed User Flow
Provide a detailed, step-by-step user flow. Consider the following stages:
1.  **Authentication & Context:** Quick login and Organization context switching.
2.  **Device Identification:** QR Scanning (Optimizing for speed/accuracy).
3.  **Asset Association:** Linking the camera to a specific Meter (Creating new vs. Selecting existing).
4.  **Physical Installation & Validation:** The critical "Feedback Loop" where the user adjusts the camera based on real-time validation checks (FOV, Glare, OCR).
5.  **Completion:** Success confirmation and transition to the next task.

## 3. UI/UX Recommendations
- **Mobile-First Design:** Suggestions for touch targets, layout, and visual hierarchy.
- **Admin vs. Installer:** How should the view differ? (e.g., Admins might need to override validation failures).
- **Visual Aids:** Where can we use animations, haptics, or specific iconography to guide the user?

**Deliverables:**
- A comprehensive text-based description of the **Ideal User Flow**.
- **UX Wireframe descriptions** for key screens (Dashboard, Scanner, Validation).
- A list of **Actionable Improvements** for our current codebase (`static/installer.html`, `static/installer.js`).
