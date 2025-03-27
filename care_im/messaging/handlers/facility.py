"""Handler for facility and asset related requests."""

import logging
from typing import Dict, Any, Optional, List

from care.facility.models import Facility
from care.facility.models.asset import Asset, AvailabilityStatus

from care_im.messaging.handlers.base import BaseHandler

logger = logging.getLogger(__name__)


class FacilityHandler(BaseHandler):
    """Handler for facility and asset related functionality."""
    
    def get_asset_status(self, facility_id: Optional[str] = None) -> str:
        """
        Get status of medical assets and equipment.
        
        Args:
            facility_id: Optional facility ID to filter by
            
        Returns:
            Formatted asset status message
        """
        try:
            if not self.user:
                return "Error: You don't have permission to view asset status."

            # Get facilities this user is associated with
            user_facilities = Facility.objects.filter(
                facilityuser__user=self.user,
            ).distinct()

            # If no facilities found
            if not user_facilities.exists():
                return "You are not associated with any facilities."

            # If no facility_id specified, show list of user's facilities
            if not facility_id:
                return self._format_facilities_list(user_facilities)

            # Get requested facility
            try:
                facility = user_facilities[int(facility_id)-1]
            except (IndexError, ValueError):
                return "Invalid facility number. Please try again."

            # Get facility assets
            return self._get_facility_assets(facility)
            
        except Exception as e:
            return self._handle_error(e, "retrieving asset status")
            
    def _format_facilities_list(self, facilities) -> str:
        """Format list of facilities for display."""
        response = "🏥 *Your Facilities*\n\n"
        for i, facility in enumerate(facilities, 1):
            response += f"{i}. {facility.name}\n"

        response += "\n📝 *To view assets for a specific facility:*\n"
        response += "Type `/a <facility_number>`\n"
        response += "Example: `/a 2` for second facility"
        
        return response
        
    def _get_facility_assets(self, facility) -> str:
        """Get detailed asset status for a specific facility."""
        # Get facility assets
        assets = Asset.objects.filter(
            current_location__facility=facility
        ).select_related(
            'current_location',
            'current_location__facility'
        )

        if not assets:
            return f"No monitored assets found at {facility.name}"

        response = f"📊 *Asset Status at {facility.name}*\n\n"

        # Group assets by status
        status_groups = self._group_assets_by_status(assets)
        
        # Format response by status
        response += self._format_operational_assets(status_groups)
        response += self._format_down_assets(status_groups)
        response += self._format_maintenance_assets(status_groups)

        # Add bed capacity if available
        if hasattr(facility, 'total_bed_capacity') and hasattr(facility, 'current_bed_capacity'):
            response += "*Bed Availability:*\n"
            response += f" • Total Beds: {facility.total_bed_capacity or 0}\n"
            response += f" • Available Beds: {facility.current_bed_capacity or 0}\n"

        response += "\n📝 *To view another facility:*\n"
        response += "Type 'asset' to see your facilities"

        return response
        
    def _group_assets_by_status(self, assets) -> Dict[str, List[Dict[str, Any]]]:
        """Group assets by their availability status."""
        status_groups = {
            AvailabilityStatus.OPERATIONAL: [],
            AvailabilityStatus.DOWN: [],
            AvailabilityStatus.UNDER_MAINTENANCE: [],
            AvailabilityStatus.NOT_MONITORED: []
        }

        for asset in assets:
            # Get latest availability record
            latest_record = asset.availability_records.order_by('-timestamp').first()
            status = latest_record.status if latest_record else AvailabilityStatus.NOT_MONITORED

            asset_info = {
                'name': asset.name,
                'location': asset.current_location.name if asset.current_location else 'Unknown',
                'class': asset.asset_class,
                'last_update': latest_record.timestamp.strftime("%d-%m-%Y %H:%M") if latest_record else 'Never'
            }
            status_groups[status].append(asset_info)
            
        return status_groups
        
    def _format_operational_assets(self, status_groups) -> str:
        """Format operational assets for display."""
        if not status_groups[AvailabilityStatus.OPERATIONAL]:
            return ""
            
        response = "✅ *Operational Assets:*\n"
        for asset in status_groups[AvailabilityStatus.OPERATIONAL]:
            response += f" • {asset['name']} ({asset['class']})\n"
            response += f"   - Location: {asset['location']}\n"
        response += "\n"
        
        return response
        
    def _format_down_assets(self, status_groups) -> str:
        """Format down assets for display."""
        if not status_groups[AvailabilityStatus.DOWN]:
            return ""
            
        response = "❌ *Down Assets:*\n"
        for asset in status_groups[AvailabilityStatus.DOWN]:
            response += f" • {asset['name']} ({asset['class']})\n"
            response += f"   - Location: {asset['location']}\n"
            response += f"   - Last Seen: {asset['last_update']}\n"
        response += "\n"
        
        return response
        
    def _format_maintenance_assets(self, status_groups) -> str:
        """Format maintenance assets for display."""
        if not status_groups[AvailabilityStatus.UNDER_MAINTENANCE]:
            return ""
            
        response = "🔧 *Under Maintenance:*\n"
        for asset in status_groups[AvailabilityStatus.UNDER_MAINTENANCE]:
            response += f" • {asset['name']} ({asset['class']})\n"
            response += f"   - Location: {asset['location']}\n"
        response += "\n"
        
        return response