"""Handler for resource related requests."""

import logging
from typing import Dict, Any, Optional, List

from care.facility.models import Facility
from care.facility.models.resources import ResourceRequest, RESOURCE_STATUS_CHOICES, RESOURCE_CATEGORY_CHOICES

from care_im.messaging.handlers.base import BaseHandler
from care_im.messaging.client import WhatsAppClient

logger = logging.getLogger(__name__)


class ResourceHandler(BaseHandler):
    """Handler for resource related functionality."""
    
    def get_resource_status(self, whatsapp_client: WhatsAppClient, facility_id: Optional[str] = None) -> str:
        """
        Get status of medical resources and resource requests.
        
        Args:
            whatsapp_client: WhatsApp client for sending messages
            facility_id: Optional facility ID to filter by
            
        Returns:
            Status message indicating whether the resource status was sent
        """
        try:
            if not self.user:
                return "Error: You don't have permission to view resource status."

            # Get facilities this user is associated with
            user_facilities = Facility.objects.filter(
                facilityuser__user=self.user,
            ).distinct()

            # If no facilities found
            if not user_facilities.exists():
                whatsapp_client.send_message(
                    self._format_phone_number(self.from_number),
                    "You are not associated with any facilities."
                )
                return "You are not associated with any facilities."

            # If no facility_id specified, show list of user's facilities
            if not facility_id:
                response = self._format_facilities_list(user_facilities)
                whatsapp_client.send_message(
                    self._format_phone_number(self.from_number),
                    response
                )
                return response

            # Get requested facility
            try:
                facility = user_facilities[int(facility_id)-1]
            except (IndexError, ValueError):
                whatsapp_client.send_message(
                    self._format_phone_number(self.from_number),
                    "Invalid facility number. Please try again."
                )
                return "Invalid facility number. Please try again."

            # Get resource information
            response = self._get_facility_resources(facility)
            
            whatsapp_client.send_message(
                self._format_phone_number(self.from_number),
                response
            )
            return "Resource status sent successfully"
            
        except Exception as e:
            return self._handle_error(e, "retrieving resource status")
            
    def _format_facilities_list(self, facilities) -> str:
        """Format list of facilities for display."""
        response = "🏥 *Your Facilities*\n\n"
        for i, facility in enumerate(facilities, 1):
            response += f"{i}. {facility.name}\n"

        response += "\n📝 *To view resources for a specific facility:*\n"
        response += "Type `/r <facility_number>`\n"
        response += "Example: `/r 2` for second facility"
        
        return response
        
    def _get_facility_resources(self, facility) -> str:
        """Get detailed resource status for a specific facility."""
        # Convert choices tuples to dictionaries for easier lookup
        status_dict = dict(RESOURCE_STATUS_CHOICES)
        category_dict = dict(RESOURCE_CATEGORY_CHOICES)

        # Get both incoming and outgoing resource requests
        incoming_requests_all = ResourceRequest.objects.filter(
            assigned_facility=facility
        ).select_related(
            'origin_facility',
            'assigned_to',
            'created_by'
        )

        incoming_requests_count_all = incoming_requests_all.count()
        incoming_requests_count_visible = incoming_requests_all.filter(deleted=False).count()

        incoming_requests = ResourceRequest.objects.filter(
            assigned_facility=facility,
            deleted=False
        ).select_related(
            'origin_facility',
            'assigned_to',
            'created_by'
        ).order_by('-created_date')[:20]

        outgoing_requests_all = ResourceRequest.objects.filter(
            origin_facility=facility
        ).select_related(
            'assigned_facility',
            'assigned_to',
            'created_by'
        )

        outgoing_requests_count_all = outgoing_requests_all.count()
        outgoing_requests_count_visible = outgoing_requests_all.filter(deleted=False).count()

        outgoing_requests = ResourceRequest.objects.filter(
            origin_facility=facility,
            deleted=False
        ).select_related(
            'assigned_facility',
            'assigned_to',
            'created_by'
        ).order_by('-created_date')[:20]

        # Debug information
        all_requests_count = incoming_requests_count_all + outgoing_requests_count_all
        visible_requests_count = incoming_requests_count_visible + outgoing_requests_count_visible
        deleted_requests_count = all_requests_count - visible_requests_count
        facility_info = f"Facility ID: {facility.id}, Name: {facility.name}"

        if not incoming_requests and not outgoing_requests:
            debug_info = self._format_debug_info(
                facility_info, 
                all_requests_count, 
                deleted_requests_count,
                incoming_requests_count_visible, 
                incoming_requests_count_all,
                outgoing_requests_count_visible, 
                outgoing_requests_count_all
            )
            return f"No active resource requests found for {facility.name}. {debug_info}"

        response = f"📊 *Resource Requests at {facility.name}*\n\n"

        # Process incoming requests
        if incoming_requests:
            response += self._format_incoming_requests(incoming_requests, status_dict, category_dict)

        # Process outgoing requests
        if outgoing_requests:
            response += self._format_outgoing_requests(outgoing_requests, status_dict, category_dict)

        # Add debug information
        debug_info = self._format_debug_info(
            facility_info, 
            all_requests_count, 
            deleted_requests_count,
            incoming_requests_count_visible, 
            incoming_requests_count_all,
            outgoing_requests_count_visible, 
            outgoing_requests_count_all
        )
        response += debug_info

        # Add bed capacity if available
        if hasattr(facility, 'total_bed_capacity') and hasattr(facility, 'current_bed_capacity'):
            response += "\n*Bed Availability:*\n"
            response += f" • Total Beds: {facility.total_bed_capacity or 0}\n"
            response += f" • Available Beds: {facility.current_bed_capacity or 0}\n\n"

        response += "📝 *To view another facility:*\n"
        response += "Type 'resource' to see your facilities"
        
        return response
        
    def _format_debug_info(self, facility_info, all_requests, deleted_requests, 
                          incoming_visible, incoming_total, outgoing_visible, outgoing_total) -> str:
        """Format debug information for resource requests."""
        return (
            f"\n*Debug Information:*\n"
            f"- {facility_info}\n"
            f"- Total requests found (including deleted): {all_requests}\n"
            f"- Active requests: {incoming_visible + outgoing_visible}\n"
            f"- Deleted requests: {deleted_requests}\n"
            f"- Incoming requests (visible/total): {incoming_visible}/{incoming_total}\n"
            f"- Outgoing requests (visible/total): {outgoing_visible}/{outgoing_total}\n"
        )
        
    def _format_incoming_requests(self, requests, status_dict, category_dict) -> str:
        """Format incoming resource requests."""
        response = "*Incoming Requests:*\n\n"

        for request in requests:
            status = request.status
            category = category_dict.get(request.category, "Unknown Category")

            request_info = {
                'title': request.title,
                'facility': request.origin_facility.name if request.origin_facility else "Unknown",
                'status': status_dict.get(status, "Unknown Status"),
                'category': category,
                'emergency': "🚨 EMERGENCY" if request.emergency else "",
                'date': request.created_date.strftime("%d-%m-%Y"),
                'assigned_to': request.assigned_to.get_full_name() if request.assigned_to else "Unassigned"
            }

            response += f" • {request_info['title']} ({request_info['category']})\n"
            response += f"   - From: {request_info['facility']}\n"
            response += f"   - Status: {request_info['status']}\n"
            if request_info['emergency']:
                response += f"   - {request_info['emergency']}\n"
            response += f"   - Date: {request_info['date']}\n"
            response += f"   - Assigned to: {request_info['assigned_to']}\n\n"
            
        return response
        
    def _format_outgoing_requests(self, requests, status_dict, category_dict) -> str:
        """Format outgoing resource requests."""
        response = "*Outgoing Requests:*\n\n"

        for request in requests:
            status = request.status
            category = category_dict.get(request.category, "Unknown Category")

            request_info = {
                'title': request.title,
                'facility': request.assigned_facility.name if request.assigned_facility else "Unassigned",
                'status': status_dict.get(status, "Unknown Status"),
                'category': category,
                'emergency': "🚨 EMERGENCY" if request.emergency else "",
                'date': request.created_date.strftime("%d-%m-%Y"),
                'assigned_to': request.assigned_to.get_full_name() if request.assigned_to else "Unassigned"
            }

            response += f" • {request_info['title']} ({request_info['category']})\n"
            response += f"   - To: {request_info['facility']}\n"
            response += f"   - Status: {request_info['status']}\n"
            if request_info['emergency']:
                response += f"   - {request_info['emergency']}\n"
            response += f"   - Date: {request_info['date']}\n"
            response += f"   - Assigned to: {request_info['assigned_to']}\n\n"
            
        return response