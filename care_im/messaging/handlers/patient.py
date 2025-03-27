"""Handler for patient record related requests."""

import logging
from typing import Dict, Any

from care_im.messaging.handlers.base import BaseHandler
from care_im.messaging.template_sender import WhatsAppSender

logger = logging.getLogger(__name__)


class PatientHandler(BaseHandler):
    """Handler for patient record related functionality."""
    
    def get_patient_records(self, template_sender: WhatsAppSender) -> str:
        """
        Get and format patient records.
        
        Args:
            template_sender: WhatsApp template sender instance
            
        Returns:
            Status message indicating whether the records were sent
        """
        try:
            if not self.patient:
                return "No patient records found. Please visit a facility to register."

            # Format the last visit date nicely
            last_visit_date = self.patient.modified_date
            formatted_date = last_visit_date.strftime("%d %B, %Y") if last_visit_date else 'Not Available'

            # Send the patient record template
            template_sender.send_template(
                self.from_number,
                "care_patient_record",
                params={
                    "body": [
                        {"type": "text", "text": self.patient.id},
                        {"type": "text", "text": self.patient.name},
                        {"type": "text", "text": self.patient.get_age()},
                        {"type": "text", "text": formatted_date},
                        {"type": "text", "text": f"Gender: {self.patient.gender}, Blood Group: {self.patient.blood_group or 'Not Available'}"}
                    ]
                }
            )
            
            return "Patient records sent successfully"
        except Exception as e:
            return self._handle_error(e, "retrieving patient records")