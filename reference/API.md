# MeterVision API Reference Guide

This document provides a comprehensive reference for the MeterVision Enterprise API.

## Authentication

All protected routes require a Bearer token.
- **Login**: `POST /token` (form-data: `username`, `password`)
- **Header**: `Authorization: Bearer <token>`

## Organization Management

### Organizations
- `POST /api/organizations/`: Create a new organization (Super Admin only).
- `GET /api/organizations/`: List all organizations (Platform Manager+).
- `GET /api/organizations/my-organizations`: List organizations current user belongs to.
- `GET /api/organizations/{org_id}`: Get organization details.

### User Management
- `POST /api/organizations/{org_id}/users`: Assign a user to an organization with a specific role.
- `GET /api/organizations/{org_id}/users`: List users in an organization.
- `DELETE /api/organizations/{org_id}/users/{user_id}`: Remove a user from an organization.

## Asset Hierarchy

All asset creation/retrieval requires `organization_id` for isolation.

### Projects
- `POST /projects/`: Create a project.
- `GET /projects/`: List projects (filtered by organization membership).

### Customers
- `POST /customers/`: Create a customer.

### Buildings
- `POST /buildings/`: Create a building.

### Places
- `POST /places/`: Create a place.

### Meters
- `POST /meters/`: Create a meter.
- `GET /meters_list/`: List all meters.
- `GET /meters/{serial_number}`: Get meter by serial.

### Readings
- `POST /meters/{serial}/reading`: Upload a reading (Multipart form with `file`).

## Installation Workflow

### Workflow Management
- `POST /api/installations/start`: Start a new installation session.
- `POST /api/installations/{session_id}/validate`: Trigger the 4-stage validation pipeline.
- `GET /api/installations/{session_id}/status`: Get current status and validation checks.
- `POST /api/installations/{session_id}/complete`: Finalize installation (marks active or failed).

### Device Integration
- `POST /api/installations/cameras/heartbeat`: Camera heartbeat endpoint (records connectivity).

## Administrative
- `GET /users/me`: Get current user profile.
- `GET /`: Dashboard homepage.
- `http://localhost:8000/docs`: Interactive OpenAPI documentation.
