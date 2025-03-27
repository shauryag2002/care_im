"""
Backward compatibility module for message templates.

This module provides backward compatibility for code that imports
message template functions from the old location.

For new code, import from care_im.templates.message_templates instead.
"""

import warnings
from care_im.templates.message_templates import MessageTemplates

def get_warning():
    warnings.warn(
        "Importing template functions from care_im.utils.templates is deprecated. "
        "Please import MessageTemplates from care_im.templates.message_templates instead.",
        DeprecationWarning,
        stacklevel=2
    )

# Backward compatibility wrapper functions that map to the new MessageTemplates methods

def get_patient_record(patient_data):
    get_warning()
    return MessageTemplates.patient_record(patient_data)
    
def get_medications_list(medications):
    get_warning()
    return MessageTemplates.medications_list(medications)
    
def get_procedures_list(procedures):
    get_warning()
    return MessageTemplates.procedures_list(procedures)
    
def get_staff_schedule(schedule):
    get_warning()
    return MessageTemplates.staff_schedule(schedule)
    
def get_asset_status(assets):
    get_warning()
    return MessageTemplates.asset_status(assets)
    
def get_inventory_data(inventory):
    get_warning()
    return MessageTemplates.inventory_data(inventory)
    
def get_help_message(is_patient=True):
    get_warning()
    return MessageTemplates.help_message(is_patient)
    
def get_error_message():
    get_warning()
    return MessageTemplates.error_message()
    
def get_token_booking_info(booked_on, status, reason, slot_date=None, slot_time=None):
    get_warning()
    return MessageTemplates.token_booking_info(booked_on, status, reason, slot_date, slot_time)
    
def get_unregistered_user_message(support_email="support@care.ohc.network", helpline="1800-123-456"):
    get_warning()
    return MessageTemplates.unregistered_user_message(support_email, helpline)
