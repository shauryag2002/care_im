"""WhatsApp message templates for different types of responses."""

from typing import Dict, List, Optional


class MessageTemplates:
    """Formats different types of messages for WhatsApp communication."""
    
    @staticmethod
    def patient_record(patient_data: Dict[str, str]) -> str:
        """
        Format patient record data.
        
        Args:
            patient_data: Dictionary containing patient information
            
        Returns:
            Formatted patient record message
        """
        return (
            f"🏥 *Patient Record*\n\n"
            f"Patient ID: {patient_data.get('id', 'N/A')}\n"
            f"Name: {patient_data.get('name', 'N/A')}\n"
            f"Age: {patient_data.get('age', 'N/A')}\n"
            f"Last Visit: {patient_data.get('last_visit', 'N/A')}\n"
        )

    @staticmethod
    def medications_list(medications: List[Dict[str, str]]) -> str:
        """
        Format current medications list.
        
        Args:
            medications: List of medication dictionaries
            
        Returns:
            Formatted medications list message
        """
        if not medications:
            return "You have no active medications."

        med_list = "\n".join([
            f"• {med.get('name')} - {med.get('dosage')} {med.get('frequency')}"
            for med in medications
        ])
        return f"💊 *Current Medications*\n\n{med_list}"

    @staticmethod
    def procedures_list(procedures: List[Dict[str, str]]) -> str:
        """
        Format procedures list.
        
        Args:
            procedures: List of procedure dictionaries
            
        Returns:
            Formatted procedures list message
        """
        if not procedures:
            return "No procedures found."

        proc_list = "\n".join([
            f"• {proc.get('name')} - {proc.get('date')}"
            for proc in procedures
        ])
        return f"🔬 *Procedures*\n\n{proc_list}"

    @staticmethod
    def staff_schedule(schedule: List[Dict[str, str]]) -> str:
        """
        Format staff schedule.
        
        Args:
            schedule: List of shift dictionaries
            
        Returns:
            Formatted staff schedule message
        """
        if not schedule:
            return "No upcoming shifts scheduled."

        schedule_list = "\n".join([
            f"• {shift.get('date')} - {shift.get('time')}: {shift.get('location')}"
            for shift in schedule
        ])
        return f"📅 *Your Schedule*\n\n{schedule_list}"

    @staticmethod
    def asset_status(assets: List[Dict[str, str]]) -> str:
        """
        Format asset status information.
        
        Args:
            assets: List of asset dictionaries
            
        Returns:
            Formatted asset status message
        """
        if not assets:
            return "No assets found."

        asset_list = "\n".join([
            f"• {asset.get('name')}: {asset.get('status')}"
            for asset in assets
        ])
        return f"🔧 *Asset Status*\n\n{asset_list}"

    @staticmethod
    def inventory_data(inventory: List[Dict[str, str]]) -> str:
        """
        Format inventory information.
        
        Args:
            inventory: List of inventory item dictionaries
            
        Returns:
            Formatted inventory status message
        """
        if not inventory:
            return "No inventory data available."

        inventory_list = "\n".join([
            f"• {item.get('name')}: {item.get('quantity')} {item.get('unit')} available"
            for item in inventory
        ])
        return f"📦 *Inventory Status*\n\n{inventory_list}"

    @staticmethod
    def help_message(is_patient: bool = True) -> str:
        """
        Format help message based on user type.
        
        Args:
            is_patient: True if the user is a patient, False if staff
            
        Returns:
            Formatted help message
        """
        if is_patient:
            return (
                "🏥 *Available Commands*\n\n"
                "1. *records* - View your patient records\n"
                "2. *medications* - View current medications\n"
                "3. *procedures* - View your procedures\n"
                "4. *token* - Get a token\n"
                "5. *help* - Show this message\n\n"
                "Send any of these commands to get the information you need."
            )
        else:
            return (
                "🏥 *Available Commands*\n\n"
                "1. *schedule* - View your work schedule\n"
                "2. *resource* - Check resources status\n"
                "3. *help* - Show this message\n\n"
                "Send any of these commands to get the information you need."
            )

    @staticmethod
    def error_message() -> str:
        """
        Format error message.
        
        Returns:
            Formatted error message
        """
        return (
            "❌ Sorry, I couldn't process your request.\n\n"
            "Please try again later or contact support if the issue persists."
        )

    @staticmethod
    def token_booking_info(booked_on: str, status: str, reason: str, 
                           slot_date: Optional[str] = None, 
                           slot_time: Optional[str] = None) -> str:
        """
        Format token booking information.
        
        Args:
            booked_on: Date the token was booked
            status: Token status
            reason: Reason for the visit
            slot_date: Date of the appointment slot (optional)
            slot_time: Time of the appointment slot (optional)
            
        Returns:
            Formatted token booking information
        """
        base_info = (
            f"🎟️ *Token Booking*\n\n"
            f"Booked on: {booked_on}\n"
            f"Status: {status}\n"
            f"Reason: {reason}"
        )
        if slot_date and slot_time:
            base_info += f"\nSlot: {slot_date} at {slot_time}"
        return base_info
        
    @staticmethod
    def unregistered_user_message(support_email: str = "support@care.ohc.network", 
                                 helpline: str = "1800-123-456") -> str:
        """
        Format message for unregistered users.
        
        Args:
            support_email: Support email address
            helpline: Support phone number
            
        Returns:
            Formatted message for unregistered users
        """
        languages = {
            'en': 'English',
            'ml': 'Malayalam',
            'hi': 'Hindi',
            'ta': 'Tamil'
        }

        lang_support = "\n".join([f"   • {name}" for code, name in languages.items()])

        return (
            "🏥 *You are not registered in our system*\n\n"
            "*How to Register:*\n\n"
            "1️⃣ *Visit a Hospital*\n"
            "   • Find your nearest CARE-registered hospital\n"
            "   • Registration is available during OPD hours\n\n"
            "2️⃣ *Required Documents*\n"
            "   • Valid ID (Aadhaar/PAN/Passport)\n"
            "   • Address proof\n"
            "   • Recent photograph\n"
            "   • Previous medical records (if any)\n\n"
            "3️⃣ *At Registration Desk*\n"
            "   • Fill patient registration form\n"
            "   • Provide this WhatsApp number\n"
            "   • Get your Patient ID\n\n"
            "4️⃣ *Need Help?*\n"
            f"   • Call: {helpline} (24x7 Toll-free)\n"
            f"   • Email: {support_email}\n"
            "   • Available in:\n"
            f"{lang_support}\n\n"
            "*After Registration You Can:*\n"
            "✓ View medical records\n"
            "✓ Check appointments\n"
            "✓ Get medication reminders\n"
            "✓ Receive important updates\n\n"
            "Type 'help' anytime to see available commands."
        )