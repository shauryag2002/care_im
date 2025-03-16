"""WhatsApp message templates for different types of responses"""

class MessageTemplates:
    @staticmethod
    def patient_record(patient_data: dict) -> str:
        """Format patient record data"""
        return (
            f"🏥 *Patient Record*\n\n"
            f"Patient ID: {patient_data.get('id', 'N/A')}\n"
            f"Name: {patient_data.get('name', 'N/A')}\n"
            f"Age: {patient_data.get('age', 'N/A')}\n"
            f"Last Visit: {patient_data.get('last_visit', 'N/A')}\n"
        )

    @staticmethod
    def medications_list(medications: list) -> str:
        """Format current medications list"""
        if not medications:
            return "You have no active medications."

        med_list = "\n".join([
            f"• {med.get('name')} - {med.get('dosage')} {med.get('frequency')}"
            for med in medications
        ])
        return f"💊 *Current Medications*\n\n{med_list}"

    @staticmethod
    def procedures_list(procedures: list) -> str:
        """Format procedures list"""
        if not procedures:
            return "No procedures found."

        proc_list = "\n".join([
            f"• {proc.get('name')} - {proc.get('date')}"
            for proc in procedures
        ])
        return f"🔬 *Procedures*\n\n{proc_list}"

    @staticmethod
    def staff_schedule(schedule: list) -> str:
        """Format staff schedule"""
        if not schedule:
            return "No upcoming shifts scheduled."

        schedule_list = "\n".join([
            f"• {shift.get('date')} - {shift.get('time')}: {shift.get('location')}"
            for shift in schedule
        ])
        return f"📅 *Your Schedule*\n\n{schedule_list}"

    @staticmethod
    def asset_status(assets: list) -> str:
        """Format asset status information"""
        if not assets:
            return "No assets found."

        asset_list = "\n".join([
            f"• {asset.get('name')}: {asset.get('status')}"
            for asset in assets
        ])
        return f"🔧 *Asset Status*\n\n{asset_list}"

    @staticmethod
    def inventory_data(inventory: list) -> str:
        """Format inventory information"""
        if not inventory:
            return "No inventory data available."

        inventory_list = "\n".join([
            f"• {item.get('name')}: {item.get('quantity')} {item.get('unit')} available"
            for item in inventory
        ])
        return f"📦 *Inventory Status*\n\n{inventory_list}"

    @staticmethod
    def help_message(is_patient: bool = True) -> str:
        """Format help message based on user type"""
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
        """Format error message"""
        return (
            "❌ Sorry, I couldn't process your request.\n\n"
            "Please try again later or contact support if the issue persists."
        )

    @staticmethod
    def token_booking_info(booked_on: str, status: str, reason: str, slot_date: str = None, slot_time: str = None) -> str:
        """Format token booking information"""
        base_info = (
            f"🎟️ *Token Booking*\n\n"
            f"Booked on: {booked_on}\n"
            f"Status: {status}\n"
            f"Reason: {reason}"
        )
        if slot_date and slot_time:
            base_info += f"\nSlot: {slot_date} at {slot_time}"
        return base_info
