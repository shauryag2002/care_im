from django.db.models import Q
from care.facility.models import Facility
from care.users.models import User
from care.emr.models import Patient
from care.emr.models.medication_request import MedicationRequest
from care.emr.resources.medication.request.spec import MedicationRequestStatus
from .templates import MessageTemplates
from care_im.utils.whatsapp_client import WhatsAppClient
from care.facility.models import FacilityUser
import logging

logger = logging.getLogger(__name__)

class WhatsAppMessageHandler:
    def __init__(self, from_number: str):
        self.from_number = from_number
        self.user = None
        self.patient = None
        self._identify_user()
        self.templates = MessageTemplates()
        self.whatsapp_client = WhatsAppClient()

    def _identify_user(self):
        """Identify if the sender is a patient or staff member"""
        try:
            logger.info(f"Identifying user with phone number: {self.from_number}")

            # Normalize phone number
            normalized_number = self.from_number.strip().replace(" ", "")
            if not normalized_number.startswith('+'):
                if (normalized_number.startswith('91') and len(normalized_number) >= 12):
                    normalized_number = f"+{normalized_number}"
                elif len(normalized_number) == 10:
                    normalized_number = f"+91{normalized_number}"
                else:
                    normalized_number = f"+{normalized_number}"

            logger.info(f"Looking up user/patient with normalized number: {normalized_number}")

            # First try to find a patient record
            try:
                self.patient = Patient.objects.filter(
                    phone_number=normalized_number
                ).order_by('-modified_date').first()
                logger.info(f"Found patient: {self.patient}")
                if self.patient:
                    return
            except Patient.DoesNotExist:
                # If no patient found, try emergency contact
                self.patient = Patient.objects.filter(
                    emergency_phone_number=normalized_number
                ).first()
                if self.patient:
                    logger.info(f"Found patient via emergency contact: {self.patient}")
                    return

            # Then try to find a staff user
            try:
                self.user = User.objects.filter(phone_number=normalized_number).first()
                logger.info(f"Found staff user: {self.user}")
            except User.DoesNotExist:
                try:
                    self.user = User.objects.get(alt_phone_number=normalized_number)
                    logger.info(f"Found staff user via alternate number: {self.user}")
                except User.DoesNotExist:
                    if self.patient:
                        # If we found a patient but no staff user, create a basic user for the patient
                        self.user = User.objects.filter(
                            phone_number=normalized_number
                        ).first()
                        if not self.user:
                            logger.info(f"Creating new user for patient: {self.patient}")
                            self.user = User.objects.create(
                                phone_number=normalized_number,
                                username=f"patient_{self.patient.external_id}",
                                first_name=self.patient.name,
                                is_active=True,
                                verified=True
                            )

            logger.info(f"Identified user: {self.user}, patient: {self.patient}")
        except Exception as e:
            logger.error(f"Error in user identification: {str(e)}")
            self.user = None
            self.patient = None

    def process_message(self, message_text: str) -> str:
        """Process incoming message and return appropriate response"""
        message_text = message_text.lower().strip()

        if not (self.user or self.patient):
            return self._handle_unregistered_user()

        if message_text == 'help':
            return self.templates.help_message(
                # Show patient menu if we found a patient record
                is_patient=bool(self.patient or (self.user and not self.user.is_staff))
            )

        # Handle patient requests if we found a patient record or non-staff user
        if self.patient or (self.user and not self.user.is_staff):
            return self._handle_patient_request(message_text)
        else:
            return self._handle_staff_request(message_text)

    def _handle_unregistered_user(self) -> str:
        support_email = "support@care.ohc.network"
        helpline = "1800-123-456"  # You can update this with your actual helpline number

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

    def _handle_patient_request(self, message_text: str) -> str:
        """Handle requests from patients"""
        if 'records' in message_text:
            return self._get_patient_records()
        elif 'medications' in message_text:
            return self._get_current_medications()
        elif 'procedures' in message_text:
            return self._get_procedures()
        elif 'token' in message_text:
            return self._get_token_booking()
        else:
            return self.templates.help_message(is_patient=True)


    def _retrieve_token_booking_info(self, patient: Patient) -> dict:
        """Retrieve token booking information for the patient"""
        try:
            from care.emr.models import TokenBooking

            # Get the latest token booking for the patient
            token_booking = TokenBooking.objects.filter(
                patient=self.patient
            ).order_by('-created_date').first()

            if not token_booking:
                return None
            # logger.info(f"token_booking: {token_booking.}")
            # return token_booking
            return {
                'slot_id': token_booking.token_slot.id,
                'slot_date': token_booking.token_slot.start_datetime.strftime('%d %B, %Y'),
                'slot_time': token_booking.token_slot.end_datetime.strftime('%I:%M %p'),
                # 'facility': token_booking.token_slot.facility.name,
                'booked_on': token_booking.booked_on.strftime('%d %B, %Y %I:%M %p'),
                'status': token_booking.status,
                'reason': token_booking.reason_for_visit or 'Not specified'
            }
        except Exception as e:
            logger.error(f"Error retrieving token booking info: {str(e)}")
            return None
    def _get_token_booking(self) -> str:
        """Get token booking details for the patient"""
        try:
            if not self.patient:
                return "No patient record found. Please register to get your token booking details."


            token_booking_info = self._retrieve_token_booking_info(self.patient)

            if not token_booking_info:
                return "No token booking details available at this time."

            return self.templates.token_booking_info(token_booking_info.get('booked_on'), token_booking_info.get('status'), token_booking_info.get('reason'), token_booking_info.get('slot_date'), token_booking_info.get('slot_time'))
        except Exception as e:
            logger.error(f"Error retrieving token booking details: {str(e)}")
            return "Sorry, I couldn't retrieve your token booking details. Please try again later."

    def _handle_staff_request(self, message_text: str) -> str:
        """Handle requests from hospital staff"""
        if 'schedule' in message_text:
            return self._get_staff_schedule()
        elif message_text.startswith('/s '):
            try:
                facility_number = message_text.split()[1]
                return self._get_staff_schedule(facility_id=facility_number)
            except IndexError:
                return "Invalid command. Use '/s <facility_number>'"
        elif message_text.startswith('/a '):
            try:
                facility_number = message_text.split()[1]
                return self._get_asset_status(facility_id=facility_number)
            except IndexError:
                return "Invalid command. Use '/a <facility_number>'"
        elif message_text.startswith('/r '):
            try:
                facility_number = message_text.split()[1]
                return self._get_resource_status(facility_id=facility_number)
            except IndexError:
                return "Invalid command. Use '/r <facility_number>'"
        elif 'asset' in message_text:
            return self._get_asset_status()
        elif 'resource' in message_text:
            return self._get_resource_status()
        # elif 'inventory' in message_text:
        #     return self._get_inventory_data()
        else:
            return self.templates.help_message(is_patient=False)

    def _get_patient_records(self) -> str:
        """Get patient records"""
        try:
            if not self.patient:
                return "No patient records found. Please visit a facility to register."

            # Format the last visit date nicely
            last_visit_date = self.patient.modified_date
            formatted_date = last_visit_date.strftime("%d %B, %Y") if last_visit_date else 'Not Available'

            return self.templates.patient_record({
                'id': self.patient.id,
                'name': self.patient.name,
                'age': self.patient.get_age(),
                'gender': self.patient.gender,
                'blood_group': self.patient.blood_group or 'Not Available',
                'last_visit': formatted_date
            })
        except Exception as e:
            logger.error(f"Error getting patient records: {str(e)}")
            return "Sorry, I couldn't retrieve your records. Please try again later."

    def _get_current_medications(self) -> str:
        """Get active medications for the patient"""
        try:
            logger.info(f"self.patient: {self.patient}")
            if not self.patient:
                return "No patient records found. Please visit a facility to register."

            # Get active medication requests
            active_medications = MedicationRequest.objects.filter(
                patient=self.patient,
                status=MedicationRequestStatus.active.value
            ).select_related('encounter', 'created_by', 'requester')

            if not active_medications:
                return "📋 You don't have any active medications at this time.\n\nPlease consult your doctor if you need any prescriptions."

            response = "💊 *Your Current Medications*\n\n"

            for med in active_medications:
                # Medication name and category
                med_name = med.medication.get('display', 'Unknown Medication')
                response += f"*{med_name}*\n"
                if med.category:
                    response += f"Category: {med.category}\n"

                # Priority and status
                if med.priority:
                    response += f"Priority: {med.priority}\n"
                if med.status_reason:
                    response += f"Status: {med.status} ({med.status_reason})\n"

                # Dosage information
                if med.dosage_instruction:
                    response += "📝 *Dosage Instructions:*\n"
                    for instruction in med.dosage_instruction:
                        # Timing/Frequency
                        timing = instruction.get('timing', {})
                        timing_code = timing.get('code', {})
                        if timing_code.get('display'):
                            response += f"• Frequency: {timing_code['display']}\n"

                        # Dose quantity
                        dose_rate = instruction.get('dose_and_rate', {})
                        if dose_rate:
                            dose_qty = dose_rate.get('dose_quantity', {})
                            if dose_qty:
                                value = dose_qty.get('value')
                                unit = dose_qty.get('unit', {}).get('display')
                                if value and unit:
                                    response += f"• Dose: {value} {unit}\n"

                        # Duration if specified
                        if timing.get('repeat', {}).get('bounds_duration'):
                            duration = timing['repeat']['bounds_duration']
                            value = duration.get('value')
                            unit = duration.get('unit')
                            if value and unit:
                                response += f"• Duration: {value} {unit}\n"

                        # Route and method
                        if instruction.get('route', {}).get('display'):
                            response += f"• Route: {instruction['route']['display']}\n"
                        if instruction.get('method', {}).get('display'):
                            response += f"• Method: {instruction['method']['display']}\n"

                        # Additional instructions
                        if instruction.get('additional_instruction'):
                            for instr in instruction['additional_instruction']:
                                if instr.get('display'):
                                    response += f"• Note: {instr['display']}\n"

                        # As needed flag
                        if instruction.get('as_needed_boolean'):
                            response += "• Take as needed\n"

                # Method of administration
                if med.method:
                    response += f"Method: {med.method.get('text', 'Not specified')}\n"

                # Prescription details
                response += "\n📋 *Prescription Details:*\n"
                if med.authored_on:
                    response += f"• Prescribed on: {med.authored_on.strftime('%d %B, %Y')}\n"
                if med.requester:
                    response += f"• Requesting Doctor: Dr. {med.requester.get_full_name()}\n"
                if med.created_by:
                    response += f"• Prescribed by: Dr. {med.created_by.get_full_name()}\n"

                # Notes if any
                if med.note:
                    response += f"\n📌 *Notes:* {med.note}\n"

                response += "\n" + "-"*30 + "\n\n"

            response += ("ℹ️ *Reminder:*\n"
                        "• Take medicines as prescribed\n"
                        "• Don't skip doses\n"
                        "• Complete full course\n"
                        "• Contact doctor for any side effects\n\n"
                        "Type 'help' to see other available commands.")

            return response

        except Exception as e:
            logger.error(f"Error getting medications: {str(e)}")
            return "Sorry, I couldn't retrieve your medications. Please try again later or contact support."

    def _get_procedures(self,is_template=False) -> str:
        """Get recent and upcoming procedures for the patient"""
        try:
            if not self.patient:
                return "🚫 Error: Could not find your patient records. Please contact support."

            from care.emr.models import Encounter
            from django.utils import timezone
            from datetime import timedelta

            # Get recent procedures from encounters - last 30 days
            recent_encounters = Encounter.objects.filter(
                patient=self.patient,
                # encounter_class="procedure",
                # admission_date__gte=timezone.now() - timedelta(days=30)
            )
            # .select_related(
            #     'created_by',
            #     'facility'
            # ).order_by('-admission_date')
            logger.info(f"recent_encounters: {recent_encounters}")
            if not recent_encounters:
                upcoming_encounters = Encounter.objects.filter(
                    patient=self.patient,
                    # encounter_class="procedure",
                    # admission_date__gt=timezone.now()
                )
                # .select_related(
                #     'created_by',
                #     'facility'
                # ).order_by('admission_date')

                if not upcoming_encounters:
                    return "No recent or upcoming procedures found."

                response = ""
                if not is_template:
                    response += "📋 *Your Procedures:*\n\n"

                response += "*Upcoming Procedures:*\n"

                for encounter in upcoming_encounters:
                    date = encounter.created_date.strftime("%d %b %Y")
                    doctor = encounter.created_by.get_full_name() if encounter.created_by else "Unknown"
                    facility = encounter.facility.name if encounter.facility else "Unknown Facility"

                    response += f" • {date}: {encounter.encounter_class or 'Procedure'}\n"
                    response += f"   - At: {facility}\n"
                    response += f"   - By: Dr. {doctor}\n"
                    if encounter.status:
                        response += f"   - Reason: {encounter.status}\n"
                    response += "\n"

                return response

            response = "📋 *Your Procedures:*\n\n"
            response += "*Recent Procedures:*\n"

            for encounter in recent_encounters:
                date = encounter.created_date.strftime("%d %b %Y")
                doctor = encounter.created_by.get_full_name() if encounter.created_by else "Unknown"
                facility = encounter.facility.name if encounter.facility else "Unknown Facility"

                response += f" • {date}: {encounter.encounter_class or 'Procedure'}\n"
                response += f"   - At: {facility}\n"
                response += f"   - By: Dr. {doctor}\n"
                if encounter.status:
                    response += f"   - Reason: {encounter.status}\n"
                if encounter.created_date:
                    discharge = encounter.created_date.strftime("%d %b %Y")
                    response += f"   - Discharged: {discharge}\n"
                response += "\n"

            # Check if there are any upcoming procedures
            upcoming_encounters = Encounter.objects.filter(
                patient=self.patient,
                # encounter_class="procedure",
                # admission_date__gt=timezone.now()
            )
            # .select_related(
            #     'created_by',
            #     'facility'
            # ).order_by('admission_date')

            if upcoming_encounters:
                response += "*Upcoming Procedures:*\n"
                for encounter in upcoming_encounters:
                    date = encounter.created_date.strftime("%d %b %Y")
                    doctor = encounter.created_by.get_full_name() if encounter.created_by else "Unknown"
                    facility = encounter.facility.name if encounter.facility else "Unknown Facility"

                    response += f" • {date}: {encounter.encounter_class or 'Procedure'}\n"
                    response += f"   - At: {facility}\n"
                    response += f"   - By: Dr. {doctor}\n"
                    if encounter.status:
                        response += f"   - Reason: {encounter.status}\n"
                    response += "\n"

            return response
        except Exception as e:
            logger.error(f"Error getting procedures: {str(e)}")
            return f"Sorry, I couldn't retrieve your procedures. Please try again later."

    def _get_staff_schedule(self, facility_id=None) -> str:
        """Get staff schedule information with availability"""
        try:
            if not self.user:
                return "Error: You don't have permission to view staff schedules."

            # Get facilities this user is associated with
            user_facilities = Facility.objects.filter(
                facilityuser__user=self.user,
            ).distinct()

            # If no facilities found
            if not user_facilities.exists():
                return "You are not associated with any facilities."

            # If no facility_id specified, show list of user's facilities
            if not facility_id:
                response = "🏥 *Your Facilities*\n\n"
                for i, facility in enumerate(user_facilities, 1):
                    response += f"{i}. {facility.name}\n"

                response += "\n📝 *To view schedule for a specific facility:*\n"
                response += "Type `/s <facility_number>`\n"
                response += "Example: `/s 2` for second facility"
                return response

            # Get requested facility
            try:
                facility = user_facilities[int(facility_id)-1]
            except (IndexError, ValueError):
                return "Invalid facility number. Please try again."

            # Get all active facility users for this facility
            staff = FacilityUser.objects.filter(
                facility=facility,
            ).select_related('user')

            from care.emr.models.scheduling.schedule import SchedulableUserResource, Schedule, Availability
            from care.emr.models import AvailabilityException
            from care.emr.resources.scheduling.schedule.spec import SlotTypeOptions
            from django.utils import timezone
            from datetime import datetime, timedelta

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
                days = {i: [] for i in range(7)}  # Initialize all days with empty lists
                for avail in availabilities:
                    for slot in avail.availability:
                        try:
                            day = int(slot['day_of_week'])
                            # Ensure time strings are properly formatted
                            start_time = slot.get('start_time', '')
                            end_time = slot.get('end_time', '')

                            # Clean and validate time formats
                            def clean_time(time_str):
                                if not time_str:
                                    return None
                                # Remove any seconds if present
                                if len(time_str.split(':')) > 2:
                                    time_str = ':'.join(time_str.split(':')[:2])
                                # Add minutes if missing
                                if ':' not in time_str:
                                    time_str = f"{time_str}:00"
                                return time_str

                            start_time = clean_time(start_time)
                            end_time = clean_time(end_time)

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
                for day_num in range(7):
                    response += f"   {day_names[day_num]}:\n"
                    if days[day_num]:  # If there are slots for this day
                        for slot in sorted(days[day_num], key=lambda x: x['start']):
                            try:
                                # Parse time in 24h format and convert to 12h format
                                start = datetime.strptime(slot['start'], '%H:%M')
                                end = datetime.strptime(slot['end'], '%H:%M')
                                response += f"      {start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}\n"
                            except ValueError as e:
                                logger.error(f"Error parsing time slot {slot}: {e}")
                                continue
                    else:
                        response += "      No scheduled hours\n"
                    response += "\n"

                # Add exceptions if any
                if exceptions:
                    response += "   *Exceptions:*\n"
                    for exc in exceptions:
                        date = exc.valid_from.strftime('%d %b')
                        start = exc.start_time.strftime('%I:%M %p')
                        end = exc.end_time.strftime('%I:%M %p')
                        response += f"      {date}: {start} - {end}\n"

                response += "\n"

            response += "\n📝 *To view another facility:*\n"
            response += "Type 'schedule' to see your facilities"

            return response

        except Exception as e:
            logger.error(f"Error getting staff schedule: {str(e)}")
            return f"Sorry, I couldn't retrieve the staff schedule. Error: {str(e)}"

    def _get_asset_status(self, facility_id=None) -> str:
        """Get status of medical assets and equipment"""
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
                response = "🏥 *Your Facilities*\n\n"
                for i, facility in enumerate(user_facilities, 1):
                    response += f"{i}. {facility.name}\n"

                response += "\n📝 *To view assets for a specific facility:*\n"
                response += "Type `/a <facility_number>`\n"
                response += "Example: `/a 2` for second facility"
                return response

            # Get requested facility
            try:
                facility = user_facilities[int(facility_id)-1]
            except (IndexError, ValueError):
                return "Invalid facility number. Please try again."

            # Get facility assets
            from care.facility.models.asset import Asset, AvailabilityStatus

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

            # Format response by status
            if status_groups[AvailabilityStatus.OPERATIONAL]:
                response += "✅ *Operational Assets:*\n"
                for asset in status_groups[AvailabilityStatus.OPERATIONAL]:
                    response += f" • {asset['name']} ({asset['class']})\n"
                    response += f"   - Location: {asset['location']}\n"
                response += "\n"

            if status_groups[AvailabilityStatus.DOWN]:
                response += "❌ *Down Assets:*\n"
                for asset in status_groups[AvailabilityStatus.DOWN]:
                    response += f" • {asset['name']} ({asset['class']})\n"
                    response += f"   - Location: {asset['location']}\n"
                    response += f"   - Last Seen: {asset['last_update']}\n"
                response += "\n"

            if status_groups[AvailabilityStatus.UNDER_MAINTENANCE]:
                response += "🔧 *Under Maintenance:*\n"
                for asset in status_groups[AvailabilityStatus.UNDER_MAINTENANCE]:
                    response += f" • {asset['name']} ({asset['class']})\n"
                    response += f"   - Location: {asset['location']}\n"
                response += "\n"

            # Add bed capacity if available
            if hasattr(facility, 'total_bed_capacity') and hasattr(facility, 'current_bed_capacity'):
                response += "*Bed Availability:*\n"
                response += f" • Total Beds: {facility.total_bed_capacity or 0}\n"
                response += f" • Available Beds: {facility.current_bed_capacity or 0}\n"

            response += "\n📝 *To view another facility:*\n"
            response += "Type 'asset' to see your facilities"

            return response
        except Exception as e:
            logger.info(f"Error getting asset status: {str(e)}")
            return f"Sorry, I couldn't retrieve the asset status. Error: {str(e)}"

    def _get_resource_status(self, facility_id=None) -> str:
        """Get status of medical resources and resource requests"""
        try:
            if not self.user:
                return "Error: You don't have permission to view resource status."

            # Get facilities this user is associated with
            user_facilities = Facility.objects.filter(
                facilityuser__user=self.user,
            ).distinct()

            # If no facilities found
            if not user_facilities.exists():
                return "You are not associated with any facilities."

            # If no facility_id specified, show list of user's facilities
            if not facility_id:
                response = "🏥 *Your Facilities*\n\n"
                for i, facility in enumerate(user_facilities, 1):
                    response += f"{i}. {facility.name}\n"

                response += "\n📝 *To view resources for a specific facility:*\n"
                response += "Type `/r <facility_number>`\n"
                response += "Example: `/r 2` for second facility"
                return response

            # Get requested facility
            try:
                facility = user_facilities[int(facility_id)-1]
            except (IndexError, ValueError):
                return "Invalid facility number. Please try again."

            # Get facility resources
            from care.facility.models.resources import ResourceRequest, RESOURCE_STATUS_CHOICES, RESOURCE_CATEGORY_CHOICES

            # Convert choices tuples to dictionaries for easier lookup
            status_dict = dict(RESOURCE_STATUS_CHOICES)
            category_dict = dict(RESOURCE_CATEGORY_CHOICES)

            # Get both incoming and outgoing resource requests - applying filter before slice
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
                debug_info = (
                    f"\n\n*Debug Information:*\n"
                    f"- {facility_info}\n"
                    f"- Total requests found (including deleted): {all_requests_count}\n"
                    f"- Deleted requests: {deleted_requests_count}\n"
                    f"- Incoming requests (visible/total): {incoming_requests_count_visible}/{incoming_requests_count_all}\n"
                    f"- Outgoing requests (visible/total): {outgoing_requests_count_visible}/{outgoing_requests_count_all}\n"
                )
                return f"No active resource requests found for {facility.name}. {debug_info}"

            response = f"📊 *Resource Requests at {facility.name}*\n\n"

            # Process incoming requests
            if incoming_requests:
                response += "*Incoming Requests:*\n\n"

                for request in incoming_requests:
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

            # Process outgoing requests
            if outgoing_requests:
                response += "*Outgoing Requests:*\n\n"

                for request in outgoing_requests:
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

            # Add debug information
            debug_info = (
                f"\n*Debug Information:*\n"
                f"- {facility_info}\n"
                f"- Total requests found (including deleted): {all_requests_count}\n"
                f"- Active requests: {visible_requests_count}\n"
                f"- Deleted requests: {deleted_requests_count}\n"
                f"- Incoming requests (visible/total): {incoming_requests_count_visible}/{incoming_requests_count_all}\n"
                f"- Outgoing requests (visible/total): {outgoing_requests_count_visible}/{outgoing_requests_count_all}\n"
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
        except Exception as e:
            logger.error(f"Error getting resource status: {str(e)}", exc_info=True)
            return f"Sorry, I couldn't retrieve the resource status. Error: {str(e)}"

    def _get_inventory_data(self) -> str:
        """Get inventory information"""
        try:
            if not self.user or not hasattr(self.user, 'currentfacilityuser_set'):
                return "Error: You don't have permission to view inventory data."

            facility_user = self.user.currentfacilityuser_set.first()
            if not facility_user:
                return "Error: You're not associated with any facility."

            facility = facility_user.facility

            response = f"📦 *Inventory Status at {facility.name}*\n\n"

            # Medication inventory
            response += "*Medicine Stock:*\n"
            if hasattr(facility, 'inventory_items'):
                med_items = facility.inventory_items.filter(item_type='MEDICINE')
                for item in med_items:
                    status = "Low" if item.quantity < item.min_quantity else "Adequate"
                    response += f" • {item.name}\n"
                    response += f"   - Stock: {item.quantity} {item.unit}\n"
                    response += f"   - Status: {status}\n"

            # Supply inventory
            response += "\n*Supply Stock:*\n"
            if hasattr(facility, 'inventory_items'):
                supply_items = facility.inventory_items.filter(item_type='SUPPLY')
                for item in supply_items:
                    status = "Low" if item.quantity < item.min_quantity else "Adequate"
                    response += f" • {item.name}\n"
                    response += f"   - Stock: {item.quantity} {item.unit}\n"
                    response += f"   - Status: {status}\n"

            return response
        except Exception as e:
            return f"Sorry, I couldn't retrieve the inventory data. Error: {str(e)}"
    def send_whatsapp_message(self,to_number:str, message: str) -> dict:
        """Send a text message to a WhatsApp number"""
        response = self.process_message(message)
        # Remove + and ensure 91 prefix
        formatted_number = to_number.replace('+', '')
        if not formatted_number.startswith('91'):
            formatted_number = '91' + formatted_number
        logger.info(f"resy: {response} and to_number: {formatted_number}")
        self.whatsapp_client.send_message(formatted_number, response)
