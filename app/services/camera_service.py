"""
Camera service for managing camera devices and heartbeat tracking.

This service handles:
- Camera registration and provisioning
- Heartbeat monitoring and tracking
- Connection testing
- Camera status management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlmodel import Session, select

from ..models import Camera, CameraHeartbeat, CameraStatusEnum, Organization


class CameraService:
    """Service for managing camera devices."""
    
    @staticmethod
    def register_camera(
        serial_number: str,
        organization_id: int,
        firmware_version: Optional[str] = None,
        session: Session = None
    ) -> Camera:
        """
        Register a new camera device.
        
        Args:
            serial_number: Unique camera serial number
            organization_id: Organization ID this camera belongs to
            firmware_version: Optional firmware version
            session: Database session
        
        Returns:
            Created Camera instance
        """
        # Check if camera already exists
        existing = session.exec(
            select(Camera).where(Camera.serial_number == serial_number)
        ).first()
        
        if existing:
            return existing
        
        camera = Camera(
            serial_number=serial_number,
            organization_id=organization_id,
            firmware_version=firmware_version or "1.0.0",
            status=CameraStatusEnum.PROVISIONING.value
        )
        
        session.add(camera)
        session.commit()
        session.refresh(camera)
        
        return camera
    
    @staticmethod
    def record_heartbeat(
        serial_number: str,
        status_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        session: Session = None
    ) -> CameraHeartbeat:
        """
        Record a heartbeat from a camera device.
        
        Args:
            serial_number: Camera serial number
            status_data: Optional status data from camera
            ip_address: Camera's IP address
            session: Database session
        
        Returns:
            Created CameraHeartbeat instance
        """
        camera = session.exec(
            select(Camera).where(Camera.serial_number == serial_number)
        ).first()
        
        if not camera:
            raise ValueError(f"Camera with serial {serial_number} not found")
        
        # Update camera's last heartbeat
        camera.last_heartbeat = datetime.utcnow()
        
        # Update status to ACTIVE if it was OFFLINE or PROVISIONING
        if camera.status in [CameraStatusEnum.OFFLINE.value, CameraStatusEnum.PROVISIONING.value]:
            camera.status = CameraStatusEnum.ACTIVE.value
        
        session.add(camera)
        
        # Create heartbeat record
        heartbeat = CameraHeartbeat(
            camera_id=camera.id,
            ip_address=ip_address,
            status_json=str(status_data or {})
        )
        
        session.add(heartbeat)
        session.commit()
        session.refresh(heartbeat)
        
        return heartbeat
    
    @staticmethod
    def check_connection(
        serial_number: str,
        session: Session = None
    ) -> Dict[str, Any]:
        """
        Check if a camera is connected and responding.
        
        Args:
            serial_number: Camera serial number
            session: Database session
        
        Returns:
            Connection status dict with 'connected', 'last_seen', 'status'
        """
        camera = session.exec(
            select(Camera).where(Camera.serial_number == serial_number)
        ).first()
        
        if not camera:
            return {
                "connected": False,
                "last_seen": None,
                "status": "not_found",
                "error": "Camera not registered"
            }
        
        # Check if heartbeat is recent (within last 5 minutes)
        if camera.last_heartbeat:
            time_since_heartbeat = datetime.utcnow() - camera.last_heartbeat
            is_recent = time_since_heartbeat < timedelta(minutes=5)
            
            return {
                "connected": is_recent,
                "last_seen": camera.last_heartbeat.isoformat(),
                "status": camera.status,
                "seconds_since_heartbeat": time_since_heartbeat.total_seconds()
            }
        
        return {
            "connected": False,
            "last_seen": None,
            "status": camera.status,
            "error": "No heartbeat received"
        }
    
    @staticmethod
    def get_camera_status(
        serial_number: str,
        session: Session = None
    ) -> Optional[Camera]:
        """
        Get camera device information.
        
        Args:
            serial_number: Camera serial number
            session: Database session
        
        Returns:
            Camera instance or None
        """
        return session.exec(
            select(Camera).where(Camera.serial_number == serial_number)
        ).first()
    
    @staticmethod
    def update_camera_status(
        serial_number: str,
        status: CameraStatusEnum,
        session: Session = None
    ) -> Camera:
        """
        Update camera status.
        
        Args:
            serial_number: Camera serial number
            status: New status
            session: Database session
        
        Returns:
            Updated Camera instance
        """
        camera = session.exec(
            select(Camera).where(Camera.serial_number == serial_number)
        ).first()
        
        if not camera:
            raise ValueError(f"Camera with serial {serial_number} not found")
        
        camera.status = status.value
        session.add(camera)
        session.commit()
        session.refresh(camera)
        
        return camera
    
    @staticmethod
    def capture_test_image(serial_number: str) -> str:
        """
        Request a test image from the camera.
        
        NOTE: This is a placeholder implementation.
        In production, this would:
        1. Send API request to camera hardware
        2. Wait for image capture
        3. Download and save image
        4. Return local file path
        
        Args:
            serial_number: Camera serial number
        
        Returns:
            Path to captured image
        """
        # TODO: Implement actual camera API integration
        # For now, return a placeholder
        return f"/tmp/camera_{serial_number}_test.jpg"
