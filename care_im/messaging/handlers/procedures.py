"""Handler for patient procedures related requests."""

import logging
from typing import Dict, Any, List
from datetime import timedelta

from django.utils import timezone

from care.emr.models import Encounter

from care_im.messaging.handlers.base import BaseHandler
from care_im.messaging.template_sender import WhatsAppSender

logger = logging.getLogger(__name__)


class ProceduresHandler(BaseHandler):
    """Handler for patient procedures related functionality."""
    
    def get_procedures(self, template_sender: WhatsAppSender, is_template: bool = False) -> str:
        """
        Get and format procedures for the patient.
        
        Args:
            template_sender: WhatsApp template sender instance
            is_template: Whether this is being called for template formatting
            
        Returns:
            Status message indicating whether the procedures were sent
        """
        try:
            if not self.patient:
                return "🚫 Error: Could not find your patient records. Please contact support."

            # Get recent procedures from encounters
            recent_encounters = Encounter.objects.filter(
                patient=self.patient,
            )
            
            # No encounters found
            if not recent_encounters:
                upcoming_encounters = self._get_upcoming_encounters()
                
                if not upcoming_encounters:
                    template_sender.send_template(
                        to_number=self.from_number,
                        template_name="care_procedures",
                        params={
                            "body": [
                                {"type": "text", "text": "🚫 No recent or upcoming procedures found."}
                            ]
                        }
                    )
                    return "No recent or upcoming procedures found."

                # Format upcoming procedures
                response = self._format_upcoming_procedures(upcoming_encounters)
                
                # Send via template
                template_sender.send_template(
                    to_number=self.from_number,
                    template_name="care_procedures",
                    params={
                        "body": [
                            {"type": "text", "text": response.replace("\n", "- ")},
                        ]
                    }
                )
                return "Upcoming procedures information sent"

            # Format full procedures response with both recent and upcoming
            response = self._format_full_procedures_response(recent_encounters)
            
            # Send via template
            template_sender.send_template(
                to_number=self.from_number,
                template_name="care_procedures",
                params={
                    "body": [
                        {"type": "text", "text": response.replace("\n", "- ")},
                    ]
                }
            )
            return "Procedures information sent successfully"
            
        except Exception as e:
            return self._handle_error(e, "retrieving procedures")
            
    def _get_upcoming_encounters(self):
        """Get upcoming encounters for the patient."""
        return Encounter.objects.filter(
            patient=self.patient,
        )
        
    def _format_encounter_details(self, encounter) -> str:
        """
        Format encounter details into a readable format.
        
        Args:
            encounter: Encounter object
            
        Returns:
            Formatted string with encounter details
        """
        date = encounter.created_date.strftime("%d %b %Y")
        doctor = encounter.created_by.get_full_name() if encounter.created_by else "Unknown"
        facility = encounter.facility.name if encounter.facility else "Unknown Facility"
        
        result = f" • {date}: {encounter.encounter_class or 'Procedure'}\n"
        result += f"   - At: {facility}\n"
        result += f"   - By: Dr. {doctor}\n"
        
        if encounter.status:
            result += f"   - Reason: {encounter.status}\n"
            
        return result
            
    def _format_upcoming_procedures(self, encounters) -> str:
        """
        Format upcoming procedures into readable text.
        
        Args:
            encounters: QuerySet of upcoming Encounter objects
            
        Returns:
            Formatted string with upcoming procedures
        """
        response = ""
        
        for encounter in encounters:
            response += self._format_encounter_details(encounter)
            response += "\n"
            
        return response
            
    def _format_full_procedures_response(self, recent_encounters) -> str:
        """
        Format full procedures response with both recent and upcoming procedures.
        
        Args:
            recent_encounters: QuerySet of recent Encounter objects
            
        Returns:
            Formatted string with all procedures
        """
        response = "📋 *Your Procedures:*\n\n"
        response += "*Recent Procedures:*\n"
        
        # Add recent procedures
        for encounter in recent_encounters:
            response += self._format_encounter_details(encounter)
            
            # Add discharge date if available
            if encounter.created_date:
                discharge = encounter.created_date.strftime("%d %b %Y")
                response += f"   - Discharged: {discharge}\n"
            
            response += "\n"
        
        # Check for upcoming procedures
        upcoming_encounters = self._get_upcoming_encounters()
        
        if upcoming_encounters:
            response += "*Upcoming Procedures:*\n"
            
            for encounter in upcoming_encounters:
                response += self._format_encounter_details(encounter)
                response += "\n"
                
        return response