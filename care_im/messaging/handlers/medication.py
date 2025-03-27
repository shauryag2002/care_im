"""Handler for medication related requests."""

import logging
from typing import Dict, Any, List

from care.emr.models.medication_request import MedicationRequest
from care.emr.resources.medication.request.spec import MedicationRequestStatus

from care_im.messaging.handlers.base import BaseHandler
from care_im.messaging.template_sender import WhatsAppSender

logger = logging.getLogger(__name__)


class MedicationHandler(BaseHandler):
    """Handler for medication related functionality."""
    
    def get_medications(self, template_sender: WhatsAppSender) -> str:
        """
        Get and format active medications for the patient.
        
        Args:
            template_sender: WhatsApp template sender instance
            
        Returns:
            Status message indicating whether the medications were sent
        """
        try:
            logger.info(f"Getting medications for patient: {self.patient}")
            if not self.patient:
                return "No patient records found. Please visit a facility to register."

            # Get active medication requests
            active_medications = MedicationRequest.objects.filter(
                patient=self.patient, 
                status=MedicationRequestStatus.active.value
            ).select_related('encounter', 'created_by', 'requester')

            if not active_medications:
                single_line_message = "📋 You don't have any active medications at this time. Please consult your doctor if you need any prescriptions."
                template_sender.send_template(
                    to_number=self.from_number, 
                    template_name="care_medications", 
                    params={
                        "body": [
                            {"type": "text", "text": single_line_message}
                        ]
                    }
                )
                return single_line_message

            # Process medications into a format suitable for WhatsApp template
            response_parts = self._format_medication_info(active_medications)
            
            # Join all parts with a separator for WhatsApp template
            single_line_response = " | ".join(response_parts)

            logger.info(f"Sending medications response: {single_line_response[:100]}...")
            template_sender.send_template(
                self.from_number, 
                "care_medications", 
                params={
                    "body": [
                        {"type": "text", "text": single_line_response}
                    ]
                }
            )
            return "Medication information sent successfully"
            
        except Exception as e:
            return self._handle_error(e, "retrieving medications")
            
    def _format_medication_info(self, medications: List[MedicationRequest]) -> List[str]:
        """
        Format medication information into a list of formatted string parts.
        
        Args:
            medications: List of medication request objects
            
        Returns:
            List of formatted strings for each part of the medication information
        """
        response_parts = []

        for med in medications:
            # Medication name and category
            med_name = med.medication.get('display', 'Unknown Medication')
            response_parts.append(f"*{med_name}*")
            if med.category: 
                response_parts.append(f"Category: {med.category}")

            # Priority and status
            if med.priority: 
                response_parts.append(f"Priority: {med.priority}")
            if med.status_reason: 
                response_parts.append(f"Status: {med.status} ({med.status_reason})")

            # Dosage information
            if med.dosage_instruction:
                response_parts.append("📝 *Dosage Instructions:*")
                for instruction in med.dosage_instruction:
                    # Add timing/frequency
                    self._add_timing_info(instruction, response_parts)
                    
                    # Add dosage quantity
                    self._add_dosage_qty_info(instruction, response_parts)
                    
                    # Add duration if specified
                    self._add_duration_info(instruction, response_parts)
                    
                    # Add route and method
                    self._add_route_method_info(instruction, response_parts)
                    
                    # Add additional instructions
                    self._add_additional_instructions(instruction, response_parts)
                    
                    # Add as needed flag
                    if instruction.get('as_needed_boolean'): 
                        response_parts.append("• Take as needed")

            # Method of administration
            if med.method: 
                response_parts.append(f"Method: {med.method.get('text', 'Not specified')}")

            # Prescription details
            response_parts.append("📋 *Prescription Details:*")
            if med.authored_on: 
                response_parts.append(f"• Prescribed on: {med.authored_on.strftime('%d %B, %Y')}")
            if med.requester: 
                response_parts.append(f"• Requesting Doctor: Dr. {med.requester.get_full_name()}")
            if med.created_by: 
                response_parts.append(f"• Prescribed by: Dr. {med.created_by.get_full_name()}")

            # Notes if any
            if med.note: 
                response_parts.append(f"📌 *Notes:* {med.note}")

        return response_parts
        
    def _add_timing_info(self, instruction: Dict, response_parts: List[str]) -> None:
        """Add timing information to response parts."""
        timing = instruction.get('timing', {})
        timing_code = timing.get('code', {})
        if timing_code.get('display'): 
            response_parts.append(f"• Frequency: {timing_code['display']}")
            
    def _add_dosage_qty_info(self, instruction: Dict, response_parts: List[str]) -> None:
        """Add dosage quantity information to response parts."""
        dose_rate = instruction.get('dose_and_rate', {})
        if dose_rate:
            dose_qty = dose_rate.get('dose_quantity', {})
            if dose_qty:
                value = dose_qty.get('value')
                unit = dose_qty.get('unit', {}).get('display')
                if value and unit: 
                    response_parts.append(f"• Dose: {value} {unit}")
                    
    def _add_duration_info(self, instruction: Dict, response_parts: List[str]) -> None:
        """Add duration information to response parts."""
        timing = instruction.get('timing', {})
        if timing.get('repeat', {}).get('bounds_duration'):
            duration = timing['repeat']['bounds_duration']
            value = duration.get('value')
            unit = duration.get('unit')
            if value and unit: 
                response_parts.append(f"• Duration: {value} {unit}")
                
    def _add_route_method_info(self, instruction: Dict, response_parts: List[str]) -> None:
        """Add route and method information to response parts."""
        if instruction.get('route', {}).get('display'): 
            response_parts.append(f"• Route: {instruction['route']['display']}")
        if instruction.get('method', {}).get('display'): 
            response_parts.append(f"• Method: {instruction['method']['display']}")
            
    def _add_additional_instructions(self, instruction: Dict, response_parts: List[str]) -> None:
        """Add additional instructions to response parts."""
        if instruction.get('additional_instruction'):
            for instr in instruction['additional_instruction']:
                if instr.get('display'): 
                    response_parts.append(f"• Note: {instr['display']}")