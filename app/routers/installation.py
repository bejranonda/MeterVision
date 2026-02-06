"""Installation management API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlmodel import Session
from pydantic import BaseModel

from ..database import get_session
from ..models import User, Meter, InstallationSession
from ..auth import get_current_user
from ..services.installation_service import InstallationService
from ..services.camera_service import CameraService

router = APIRouter(prefix="/api/installations", tags=["installations"])


# --- Request/Response Models ---

class StartInstallationRequest(BaseModel):
    """Request to start an installation session."""
    camera_serial: str
    meter_serial: str
    meter_type: str
    meter_unit: str
    meter_location: Optional[str] = None
    expected_reading: Optional[float] = None
    organization_id: int


class InstallationResponse(BaseModel):
    """Installation session response."""
    session_id: int
    status: str
    message: str


class CompleteInstallationRequest(BaseModel):
    """Request to complete installation."""
    installer_confirmed: bool
    expected_reading: Optional[float] = None
    serial_number: Optional[str] = None
    meter_type: Optional[str] = None


# --- Installation Endpoints ---

@router.post("/start", response_model=InstallationResponse)
async def start_installation(
    request: StartInstallationRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new installation session.
    
    This endpoint:
    1. Creates or retrieves the meter
    2. Registers the camera
    3. Starts an installation session
    4. Returns session ID for tracking
    """
    try:
        # Check if user has access to this organization
        from ..services.rbac_service import RBACService
        from ..models import UserRoleEnum
        
        user_role = RBACService.get_user_role_in_org(
            current_user.id, request.organization_id, session
        )
        
        if not user_role and current_user.platform_role not in [
            UserRoleEnum.SUPER_ADMIN.value,
            UserRoleEnum.PLATFORM_MANAGER.value
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this organization"
            )
        
        # Create or get meter
        from ..models import Meter, MeterBase
        from sqlmodel import select
        
        meter = session.exec(
            select(Meter).where(Meter.serial_number == request.meter_serial)
        ).first()
        
        if not meter:
            # Create new meter
            meter = Meter(
                serial_number=request.meter_serial,
                meter_type=request.meter_type,
                unit=request.meter_unit,
                location=request.meter_location,
                expected_reading=request.expected_reading,
                organization_id=request.organization_id,
                place_id=None  # Can be set later
            )
            session.add(meter)
            session.commit()
            session.refresh(meter)
        
        # Start installation session
        installation = InstallationService.start_installation(
            camera_serial=request.camera_serial,
            meter_id=meter.id,
            installer_user_id=current_user.id,
            organization_id=request.organization_id,
            session=session
        )
        
        return InstallationResponse(
            session_id=installation.id,
            status=installation.status,
            message="Installation session started successfully"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/analyze-image")
async def analyze_installation_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Beta: Use AI to discover meter information from an image.
    Returns suggested meter_type, serial_number, and initial reading.
    """
    import os
    import uuid
    from ..services.ocr import SmartMeterReader, save_upload_file
    
    # Save temporary file
    file_ext = file.filename.split(".")[-1]
    temp_path = f"uploads/temp_{uuid.uuid4()}.{file_ext}"
    save_upload_file(file, temp_path)
    
    try:
        reader = SmartMeterReader()
        discovery = reader.discover_meter(temp_path)
        
        # Keep temp file for verification if needed, or delete
        # os.remove(temp_path) 
        
        return {
            "suggestions": discovery,
            "temp_image_path": temp_path
        }
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"AI Discovery failed: {str(e)}")


@router.post("/{session_id}/validate")
async def run_validation(
    session_id: int,
    db_session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Run the validation pipeline for an installation session.
    
    Executes:
    1. Connection test
    2. FOV validation
    3. Glare detection
    4. Initial OCR reading
    
    Returns validation results for all checks.
    """
    try:
        # Verify installation session exists and user has access
        installation = db_session.get(InstallationSession, session_id)
        
        if not installation:
            raise HTTPException(status_code=404, detail="Installation session not found")
        
        # Check if user is the installer or has org access
        if installation.installer_user_id != current_user.id:
            from ..services.rbac_service import RBACService
            from ..models import UserRoleEnum
            
            user_role = RBACService.get_user_role_in_org(
                current_user.id, installation.organization_id, db_session
            )
            
            if not user_role and current_user.platform_role not in [
                UserRoleEnum.SUPER_ADMIN.value,
                UserRoleEnum.PLATFORM_MANAGER.value
            ]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to validate this installation"
                )
        
        # Run validation pipeline
        results = await InstallationService.run_validation_pipeline(
            installation_session_id=session_id,
            session=db_session
        )
        
        return {
            "session_id": session_id,
            "validation_results": results,
            "status": installation.status
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{session_id}/status")
async def get_installation_status(
    session_id: int,
    db_session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current status of an installation session.
    
    Returns:
    - Session status
    - Validation check results
    - Timestamps
    """
    try:
        status_info = InstallationService.get_installation_status(session_id, db_session)
        return status_info
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{session_id}/complete")
async def complete_installation(
    session_id: int,
    request: CompleteInstallationRequest,
    db_session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Complete an installation session.
    
    If confirmed:
    - Marks installation as COMPLETED
    - Activates the camera
    - Links camera to meter
    
    If not confirmed:
    - Marks installation as FAILED
    """
    try:
        installation = InstallationService.complete_installation(
            installation_session_id=session_id,
            installer_confirmed=request.installer_confirmed,
            session=db_session
        )

        # Handle calibration if confirmed
        if request.installer_confirmed and request.expected_reading is not None:
             # Update meter with metadata and calibrate
             meter = db_session.get(Meter, installation.meter_id)
             if meter:
                 if request.serial_number:
                     meter.serial_number = request.serial_number
                 if request.meter_type:
                     meter.meter_type = request.meter_type
                 
                 meter.expected_reading = request.expected_reading
                 
                 # Optimization: Modify prompt if reading was off
                 # In a real scenario, we'd compare the last validation reading with expected
                 # For now, we'll set a hint prompt
                 meter.custom_prompt = f"Read the numeric value from this {meter.meter_type} meter. Note: This specific meter usually shows values around {request.expected_reading}. Ensure the decimal point is correctly placed. Return ONLY the number."
                 
                 db_session.add(meter)
                 db_session.commit()

        return {
            "session_id": installation.id,
            "status": installation.status,
            "message": "Installation completed and calibrated successfully" if request.installer_confirmed
                      else "Installation marked as failed"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# --- Camera Heartbeat Endpoint ---

class HeartbeatRequest(BaseModel):
    """Camera heartbeat request."""
    serial_number: str
    ip_address: Optional[str] = None
    status_data: Optional[dict] = None


@router.post("/cameras/heartbeat")
async def camera_heartbeat(
    request: HeartbeatRequest,
    session: Session = Depends(get_session)
):
    """
    Record a heartbeat from a camera device.
    
    This endpoint should be called periodically by cameras to indicate they are online.
    
    NOTE: In production, this should use API key authentication instead of JWT.
    """
    try:
        heartbeat = CameraService.record_heartbeat(
            serial_number=request.serial_number,
            status_data=request.status_data,
            ip_address=request.ip_address,
            session=session
        )
        
        return {
            "message": "Heartbeat recorded",
            "timestamp": heartbeat.timestamp.isoformat(),
            "camera_status": "ok"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
