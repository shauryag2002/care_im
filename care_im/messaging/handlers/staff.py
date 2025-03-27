"""Handler for staff schedule related requests."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from django.utils import timezone

from care.facility.models import Facility, FacilityUser
from care.emr.models.scheduling.schedule import SchedulableUserResource, Schedule, Availability
from care.emr.models import AvailabilityException
from care.emr.resources.scheduling.schedule.spec import SlotTypeOptions

from care_im.messaging.handlers.base import BaseHandler
from care_im.messaging.client import WhatsAppClient

logger = logging.getLogger(__name__)


class StaffHandler(BaseHandler):
    """Handler for staff schedule related functionality."""
    
    def get_staff_schedule(self, whatsapp_client: WhatsAppClient, facility_id: Optional[str] = None) -> str:
        """
        Get staff schedule information.
        
        Args:
            whatsapp_client: WhatsApp client for sending messages
            facility_id: Optional facility ID to filter by
            
        Returns:
            Status message indicating whether the schedule was sent
        """
        try:
            if not self.user:
                return "Error: You don't have permission to view staff schedules."

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
                return "Invalid facility number. Please try again."

            # Get schedule information
            response = self._get_facility_staff_schedule(facility)
            
            whatsapp_client.send_message(
                self._format_phone_number(self.from_number),
                response
            )
            return "Staff schedule sent successfully"
            
        except Exception as e:
            return self._handle_error(e, "retrieving staff schedule")
            
    def _format_facilities_list(self, facilities) -> str:
        """Format list of facilities for display."""
        response = "🏥 *Your Facilities*\n\n"
        for i, facility in enumerate(facilities, 1):
            response += f"{i}. {facility.name}\n"

        response += "\n📝 *To view schedule for a specific facility:*\n"
        response += "Type `/s <facility_number>`\n"
        response += "Example: `/s 2` for second facility"
        
        return response
        
    def _get_facility_staff_schedule(self, facility) -> str:
        """Get detailed staff schedule for a specific facility."""
        # Get all active facility users for this facility
        staff = FacilityUser.objects.filter(
            facility=facility,
        ).select_related('user')

        response = f"👥 *Staff Schedule at {facility.name}*\n\n"
        today = timezone.now().date()
        next_week = today + timedelta(days=7)

        for staff_member in staff:
            user = staff_member.user
            response += f"*{user.get_full_name()}*\n"

            # Get schedulable resource for this user
            resource = SchedulableUserResource.objects.filter(
                facility=facility,
                user=user
            ).first()

            if not resource:
                response += "   No schedule configured\n\n"
                continue

            # Get active schedules
            schedules = Schedule.objects.filter(
                resource=resource,
                valid_from__lte=next_week,
                valid_to__gte=today
            )

            if not schedules:
                response += "   No active schedules\n\n"
                continue

            # Get availabilities for each schedule
            availabilities = Availability.objects.filter(
                schedule__in=schedules,
                slot_type=SlotTypeOptions.appointment.value
            )

            # Get exceptions
            exceptions = AvailabilityException.objects.filter(
                resource=resource,
                valid_from__lte=next_week,
                valid_to__gte=today
            )

            # Format availability by day
            response += self._format_availability_by_day(availabilities, exceptions)
            response += "\n"

        response += "\n📝 *To view another facility:*\n"
        response += "Type 'schedule' to see your facilities"
        return response
        
    def _format_availability_by_day(self, availabilities, exceptions) -> str:
        """Format staff availability by day of week."""
        # Initialize all days with empty lists
        days = {i: [] for i in range(7)}
        
        # Process availabilities
        for avail in availabilities:
            for slot in avail.availability:
                try:
                    day = int(slot['day_of_week'])
                    # Ensure time strings are properly formatted
                    start_time = slot.get('start_time', '')
                    end_time = slot.get('end_time', '')

                    # Clean and validate time formats
                    start_time = self._clean_time_format(start_time)
                    end_time = self._clean_time_format(end_time)

                    if start_time and end_time:
                        days[day].append({
                            'start': start_time,
                            'end': end_time
                        })
                except (ValueError, KeyError, TypeError) as e:
                    logger.error(f"Error processing slot {slot}: {e}")
                    continue
        
        # Format days with times
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result = ""
        
        for day_num in range(7):
            result += f"   {day_names[day_num]}:\n"
            if days[day_num]:  # If there are slots for this day
                for slot in sorted(days[day_num], key=lambda x: x['start']):
                    try:
                        # Parse time in 24h format and convert to 12h format
                        start = datetime.strptime(slot['start'], '%H:%M')
                        end = datetime.strptime(slot['end'], '%H:%M')
                        result += f"      {start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}\n"
                    except ValueError as e:
                        logger.error(f"Error parsing time slot {slot}: {e}")
                        continue
            else:
                result += "      No scheduled hours\n"
            result += "\n"

        # Add exceptions if any
        if exceptions:
            result += "   *Exceptions:*\n"
            for exc in exceptions:
                date = exc.valid_from.strftime('%d %b')
                start = exc.start_time.strftime('%I:%M %p')
                end = exc.end_time.strftime('%I:%M %p')
                result += f"      {date}: {start} - {end}\n"
                
        return result
        
    def _clean_time_format(self, time_str: str) -> Optional[str]:
        """Clean and validate time formats."""
        if not time_str:
            return None
            
        # Remove any seconds if present
        if len(time_str.split(':')) > 2:
            time_str = ':'.join(time_str.split(':')[:2])
            
        # Add minutes if missing
        if ':' not in time_str:
            time_str = f"{time_str}:00"
            
        return time_str