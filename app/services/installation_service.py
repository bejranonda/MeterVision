"""
Installation service for orchestrating meter installation workflow.

This service manages:
- Installation session lifecycle
- Validation pipeline execution
- Workflow state transitions
- Installation completion
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlmodel import Session, select
import json

from ..models import (
    InstallationSession, ValidationCheck,
    InstallationStatusEnum, ValidationTypeEnum,
    Camera, Meter, User
)
from .camera_service import CameraService
from .validation_service import ImageValidationService


class InstallationService:
    """Service for managing installation workflows."""
    
    @staticmethod
    def start_installation(
        camera_serial: str,
        meter_id: int,
        installer_user_id: int,
        organization_id: int,
        session: Session
    ) -> InstallationSession:
        """
        Start a new installation session.
        
        Args:
            camera_serial: Camera serial number
            meter_id: Meter ID to install camera for
            installer_user_id: ID of the installer user
            organization_id: Organization ID
            session: Database session
        
        Returns:
            Created InstallationSession
        """
        # Get or create camera
        camera = CameraService.get_camera_status(camera_serial, session)
        
        if not camera:
            camera = CameraService.register_camera(
                serial_number=camera_serial,
                organization_id=organization_id,
                session=session
            )
        
        # Create installation session
        installation = InstallationSession(
            camera_id=camera.id,
            meter_id=meter_id,
            installer_user_id=installer_user_id,
            organization_id=organization_id,
            status=InstallationStatusEnum.STARTED.value,
            started_at=datetime.utcnow(),
            validation_results_json="{}"
        )
        
        session.add(installation)
        session.commit()
        session.refresh(installation)
        
        return installation
    
    @staticmethod
    async def run_validation_pipeline(
        installation_session_id: int,
        session: Session
    ) -> Dict[str, Any]:
        """
        Run the complete validation pipeline for an installation.
        
        Pipeline steps:
        1. Connection test
        2. FOV validation
        3. Glare detection
        4. Initial OCR reading
        
        Args:
            installation_session_id: Installation session ID
            session: Database session
        
        Returns:
            Validation results dictionary
        """
        installation = session.get(InstallationSession, installation_session_id)
        
        if not installation:
            raise ValueError(f"Installation session {installation_session_id} not found")
        
        camera = session.get(Camera, installation.camera_id)
        # Initialize all results with a default "not_run" state to prevent frontend crashes
        results = {
            "connection": {"passed": False, "message": "Waiting..."},
            "fov": {"passed": False, "message": "Waiting..."},
            "glare": {"passed": False, "message": "Waiting..."},
            "ocr": {"passed": False, "message": "Waiting..."}
        }
        
        # Step 1: Connection Test
        connection_check = InstallationService._run_connection_test(
            camera, installation, session
        )
        results["connection"] = connection_check
        
        if not connection_check["passed"]:
            installation.status = InstallationStatusEnum.FAILED.value
            installation.validation_results_json = json.dumps(results)
            session.add(installation)
            session.commit()
            return results
        
        installation.status = InstallationStatusEnum.CONNECTION_TEST_PASSED.value
        session.add(installation)
        session.commit()
        
        # Step 2: FOV Validation
        test_image_path = CameraService.capture_test_image(camera.serial_number)
        
        fov_check = InstallationService._run_fov_validation(
            test_image_path, installation, session
        )
        results["fov"] = fov_check
        
        if not fov_check["passed"]:
            installation.status = InstallationStatusEnum.FAILED.value
            installation.validation_results_json = json.dumps(results)
            session.add(installation)
            session.commit()
            return results
        
        installation.status = InstallationStatusEnum.FOV_VALIDATED.value
        session.add(installation)
        session.commit()
        
        # Step 3: Glare Detection
        glare_check = InstallationService._run_glare_detection(
            test_image_path, installation, session
        )
        results["glare"] = glare_check
        
        installation.status = InstallationStatusEnum.GLARE_CHECK_PASSED.value
        session.add(installation)
        session.commit()
        
        # Step 4: Initial OCR Reading
        ocr_check = InstallationService._run_ocr_validation(
            test_image_path, installation, session
        )
        results["ocr"] = ocr_check
        
        if not ocr_check["passed"]:
            installation.status = InstallationStatusEnum.FAILED.value
        else:
            installation.status = InstallationStatusEnum.OCR_VALIDATED.value
        
        # Store all results
        installation.validation_results_json = json.dumps(results)
        session.add(installation)
        session.commit()
        
        return results
    
    @staticmethod
    def _run_connection_test(
        camera: Camera,
        installation: InstallationSession,
        session: Session
    ) -> Dict[str, Any]:
        """Run connection test validation."""
        check_result = CameraService.check_connection(camera.serial_number, session)
        
        validation_check = ValidationCheck(
            installation_session_id=installation.id,
            check_type=ValidationTypeEnum.CONNECTION.value,
            status="PASSED" if check_result["connected"] else "FAILED",
            result_json=json.dumps(check_result),
            checked_at=datetime.utcnow()
        )
        
        session.add(validation_check)
        session.commit()
        
        return {
            "passed": check_result["connected"],
            "message": "Camera connected successfully" if check_result["connected"] else "Camera not responding",
            "details": check_result
        }
    
    @staticmethod
    def _run_fov_validation(
        image_path: str,
        installation: InstallationSession,
        session: Session
    ) -> Dict[str, Any]:
        """Run FOV validation."""
        fov_result = ImageValidationService.validate_fov(image_path)
        
        validation_check = ValidationCheck(
            installation_session_id=installation.id,
            check_type=ValidationTypeEnum.FOV.value,
            status="PASSED" if fov_result.passed else "FAILED",
            result_json=json.dumps(fov_result.to_dict()),
            checked_at=datetime.utcnow()
        )
        
        session.add(validation_check)
        session.commit()
        
        return {
            "passed": fov_result.passed,
            "message": fov_result.message,
            "confidence": fov_result.confidence,
            "details": fov_result.details
        }
    
    @staticmethod
    def _run_glare_detection(
        image_path: str,
        installation: InstallationSession,
        session: Session
    ) -> Dict[str, Any]:
        """Run glare detection."""
        glare_result = ImageValidationService.detect_glare(image_path)
        
        validation_check = ValidationCheck(
            installation_session_id=installation.id,
            check_type=ValidationTypeEnum.GLARE.value,
            status="PASSED" if glare_result.passed else "FAILED",
            result_json=json.dumps(glare_result.to_dict()),
            checked_at=datetime.utcnow()
        )
        
        session.add(validation_check)
        session.commit()
        
        return {
            "passed": glare_result.passed,
            "message": glare_result.message,
            "confidence": glare_result.confidence,
            "details": glare_result.details
        }
    
    @staticmethod
    def _run_ocr_validation(
        image_path: str,
        installation: InstallationSession,
        session: Session
    ) -> Dict[str, Any]:
        """Run OCR validation."""
        ocr_result = ImageValidationService.validate_initial_reading(image_path)
        
        validation_check = ValidationCheck(
            installation_session_id=installation.id,
            check_type=ValidationTypeEnum.INITIAL_OCR.value,
            status="PASSED" if ocr_result.passed else "FAILED",
            result_json=json.dumps(ocr_result.to_dict()),
            checked_at=datetime.utcnow()
        )
        
        session.add(validation_check)
        session.commit()
        
        return {
            "passed": ocr_result.passed,
            "message": ocr_result.message,
            "confidence": ocr_result.confidence,
            "details": ocr_result.details
        }
    
    @staticmethod
    def complete_installation(
        installation_session_id: int,
        installer_confirmed: bool,
        session: Session
    ) -> InstallationSession:
        """
        Complete an installation session.
        
        Args:
            installation_session_id: Installation session ID
            installer_confirmed: Whether installer confirmed installation
            session: Database session
        
        Returns:
            Updated InstallationSession
        """
        installation = session.get(InstallationSession, installation_session_id)
        
        if not installation:
            raise ValueError(f"Installation session {installation_session_id} not found")
        
        if installer_confirmed:
            installation.status = InstallationStatusEnum.COMPLETED.value
            installation.completed_at = datetime.utcnow()
            
            # Update camera status to ACTIVE and link to meter
            camera = session.get(Camera, installation.camera_id)
            if camera:
                from ..models import CameraStatusEnum
                camera.status = CameraStatusEnum.ACTIVE.value
                camera.meter_id = installation.meter_id
                session.add(camera)
        else:
            installation.status = InstallationStatusEnum.FAILED.value
            installation.completed_at = datetime.utcnow()
        
        session.add(installation)
        session.commit()
        session.refresh(installation)
        
        return installation
    
    @staticmethod
    def get_installation_status(
        installation_session_id: int,
        session: Session
    ) -> Dict[str, Any]:
        """
        Get the current status of an installation session.
        
        Args:
            installation_session_id: Installation session ID
            session: Database session
        
        Returns:
            Installation status dictionary
        """
        installation = session.get(InstallationSession, installation_session_id)
        
        if not installation:
            raise ValueError(f"Installation session {installation_session_id} not found")
        
        # Get all validation checks
        validation_checks = session.exec(
            select(ValidationCheck)
            .where(ValidationCheck.installation_session_id == installation_session_id)
            .order_by(ValidationCheck.checked_at)
        ).all()
        
        return {
            "session_id": installation.id,
            "status": installation.status,
            "started_at": installation.started_at.isoformat(),
            "completed_at": installation.completed_at.isoformat() if installation.completed_at else None,
            "validation_checks": [
                {
                    "type": check.check_type,
                    "status": check.status,
                    "checked_at": check.checked_at.isoformat(),
                    "result": json.loads(check.result_json)
                }
                for check in validation_checks
            ]
        }
