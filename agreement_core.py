import os
import sys
import json
import sqlite3
import datetime
import re
import subprocess
import tempfile
import time
import webbrowser
import urllib.parse
import calendar
import ctypes
from ctypes import wintypes


APP_NAME = "Agreement Studio"
APP_VERSION = "2.4"
BASE_DIR = os.path.join(os.path.expanduser("~"), "AgreementStudioData")
DB_PATH = os.path.join(BASE_DIR, "agreements.db")
os.makedirs(BASE_DIR, exist_ok=True)


def enable_windows_high_dpi():
    """Enable native Windows DPI awareness before Tk creates the main window.

    This prevents Windows bitmap-scaling the whole application at 125%, 150% or
    higher display scaling, which is the common cause of soft/blurry Tk text.
    """
    if sys.platform != "win32":
        return
    try:
        # Windows 10+: per-monitor v2 awareness.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        # Windows 8.1 fallback.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        # Older Windows fallback.
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def resource_path(filename):
    """Return a bundled resource path both in source mode and PyInstaller one-file mode."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


AGREEMENT_TYPES = [
    "Comprehensive Rental Agreement",
    "Lease Agreement",
    "Leave & License Agreement",
    "Corporate Stay / Serviced Accommodation Agreement",
    "Commercial Hosting / OTA Agreement",
    "Commercial Lease Agreement",
]

SUBLETTING_POLICIES = [
    "Prohibited without prior written approval",
    "Allowed only for a specifically approved replacement / sub-occupant",
    "Corporate nominee / employee substitution only with prior approval and fresh KYC",
    "OTA / short-term hosting expressly permitted without per-booking approval",
]

RELOCATION_POLICIES = [
    "No relocation without Tenant/Guest's prior written consent",
    "Emergency relocation only; otherwise prior written consent required",
    "Management may relocate for maintenance, safety or operational continuity to an equivalent or higher category",
]

PET_POLICIES = [
    "Not permitted unless specifically approved in writing",
    "Permitted only as stated in Annexure A / booking confirmation",
    "Permitted subject to hygiene rules and additional charges",
]

SMOKING_POLICIES = [
    "Smoking/vaping prohibited inside the premises and all non-designated areas",
    "Smoking permitted only in specifically designated areas",
]

FOREIGN_STATUS_OPTIONS = [
    "Indian citizen / no foreign-national reporting",
    "Foreign national",
    "OCI Cardholder",
    "Mixed / group booking including foreign nationals or OCI Cardholders",
]

OPERATING_MODELS = [
    "Private residential tenancy",
    "Paying Guest / PG accommodation",
    "Corporate stay / serviced apartment",
    "Hotel / guest house / lodging house",
    "Home Stay",
    "OTA / short-term serviced accommodation",
    "Commercial premises",
]

LANGUAGE_PRECEDENCE_OPTIONS = [
    "English version prevails in case of inconsistency",
    "Hindi version prevails in case of inconsistency",
    "Both versions to be read together; signed special terms prevail",
]

PRESET_NAMES = [
    "Strong Residential - 11 Months",
    "Student Accommodation",
    "Corporate / Serviced Stay",
    "OTA Commercial Hosting Rights",
    "Leave & License",
    "Commercial Premises",
    "Foreign Corporate Guest - Gurugram",
]

FIELDS = [
    ("agreement_template", "Agreement Format / Preset", "combo", PRESET_NAMES),
    ("agreement_type", "Agreement Type", "combo", AGREEMENT_TYPES),
    ("agreement_reference", "Agreement / Booking Reference", "entry", None),
    ("agreement_date", "Agreement Date", "entry", None),
    ("place_of_execution", "Place of Execution", "entry", None),
    ("start_date", "Commencement / Check-in Date", "entry", None),
    ("end_date", "End / Check-out Date", "entry", None),
    ("term_months", "Term (months)", "entry", None),
    ("paper_size", "Paper Size", "combo", ["A4", "Legal", "Letter"]),
    ("page_orientation", "Page Orientation", "combo", ["Portrait", "Landscape"]),
    ("margin_top_mm", "Top Margin (mm)", "entry", None),
    ("margin_bottom_mm", "Bottom Margin (mm)", "entry", None),
    ("margin_left_mm", "Left Margin (mm)", "entry", None),
    ("margin_right_mm", "Right Margin (mm)", "entry", None),
    ("show_page_numbers", "Show Page Numbers", "combo", ["Yes", "No"]),
    ("print_page_range", "Pages to Print (All or e.g. 1-3,5)", "entry", None),
    ("print_copies", "Number of Print Copies", "entry", None),
    ("stamp_number", "Stamp / E-Stamp Number", "entry", None),
    ("stamp_value", "Stamp / E-Stamp Value (INR)", "entry", None),
    ("notary_name", "Notary Name", "entry", None),
    ("notary_reg_no", "Notary Registration No.", "entry", None),
    ("jurisdiction", "Jurisdiction / Courts", "entry", None),

    ("landlord_name", "Landlord / Lessor / Licensor Name", "entry", None),
    ("landlord_father", "Father / Spouse Name", "entry", None),
    ("landlord_entity", "Entity / Management Name (if any)", "entry", None),
    ("landlord_address", "Address", "text", None),
    ("landlord_id_type", "ID Type", "combo", ["Aadhaar", "PAN", "Passport", "Driving Licence", "Other"]),
    ("landlord_id_no", "ID Number", "entry", None),
    ("landlord_pan", "PAN (if separately applicable)", "entry", None),
    ("landlord_mobile", "Mobile", "entry", None),
    ("landlord_email", "Email", "entry", None),
    ("authorized_signatory", "Authorised Signatory / Designation", "entry", None),

    ("tenant_name", "Tenant / Lessee / Licensee / Guest Name", "entry", None),
    ("tenant_father", "Father / Spouse Name", "entry", None),
    ("tenant_dob", "Date of Birth", "entry", None),
    ("tenant_address", "Permanent Address", "text", None),
    ("tenant_id_type", "Government ID Type", "combo", ["Aadhaar", "PAN", "Passport", "Driving Licence", "Other"]),
    ("tenant_id_no", "Government ID Number", "entry", None),
    ("tenant_mobile", "Mobile", "entry", None),
    ("tenant_whatsapp", "WhatsApp Number (include country code for non-India)", "entry", None),
    ("tenant_email", "Email", "entry", None),
    ("emergency_contact1", "Emergency Contact 1", "entry", None),
    ("emergency_contact2", "Emergency Contact 2", "entry", None),

    ("corporate_name", "Corporate Client / Booking Entity", "entry", None),
    ("corporate_address", "Registered / Billing Address", "text", None),
    ("corporate_gstin", "GSTIN", "entry", None),
    ("corporate_pan", "PAN", "entry", None),
    ("corporate_representative", "Authorised Representative", "entry", None),
    ("corporate_designation", "Designation", "entry", None),
    ("corporate_mobile", "Mobile", "entry", None),
    ("corporate_email", "Email", "entry", None),

    ("property_name", "Property / Building Name", "entry", None),
    ("premises", "Full Premises / Property Address", "text", None),
    ("property_id", "Municipal / Property / UID Reference", "entry", None),
    ("floor_area", "Floor / Area / Identifying Description", "entry", None),
    ("property_boundaries", "Boundaries / Additional Property Identification", "text", None),
    ("room_unit_no", "Room / Unit / Flat No.", "entry", None),
    ("room_type", "Room Type / Occupancy Category", "entry", None),
    ("occupancy_limit", "Approved Occupancy Limit", "entry", None),
    ("purpose", "Permitted Use", "text", None),
    ("monthly_rent", "Monthly Rent / Licence Fee (INR)", "entry", None),
    ("security_deposit", "Security Deposit (INR)", "entry", None),
    ("due_day", "Rent Due Day", "entry", None),
    ("lockin_months", "Lock-in / Minimum Commitment (months)", "entry", None),
    ("notice_days", "Notice Period (days)", "entry", None),
    ("increment_percent", "Rent Escalation (%)", "entry", None),
    ("increment_after_months", "Escalation After (months)", "entry", None),
    ("taxes", "Taxes / Statutory Levies", "entry", None),
    ("maintenance", "Maintenance / Common Charges", "entry", None),
    ("electricity_rate", "Grid / Mains Electricity", "entry", None),
    ("genset_rate", "Generator / DG Electricity", "entry", None),
    ("utility_due_days", "Utility Invoice Due Within (days)", "entry", None),
    ("grace_days", "Rent / Invoice Grace Period (days)", "entry", None),
    ("late_fee", "Late Fee / Overdue Charge", "entry", None),
    ("payment_mode", "Payment Mode / Bank Details", "text", None),

    ("subletting_policy", "Assignment / Sharing / Subletting Policy", "combo", SUBLETTING_POLICIES),
    ("relocation_policy", "Room / Unit Relocation Policy", "combo", RELOCATION_POLICIES),
    ("access_notice_hours", "Normal Management Entry Notice (hours)", "entry", None),
    ("controlled_entry_time", "Controlled / Last Entry Time (if any)", "entry", None),
    ("deposit_refund_days", "Security Deposit Refund (business days)", "entry", None),
    ("deposit_interest_rate", "Interest on Delayed Undisputed Deposit (% p.a.)", "entry", None),
    ("inventory_report_hours", "Report Existing Damage Within (hours)", "entry", None),
    ("early_exit_rule", "Early Exit / Notice Shortfall Rule", "text", None),
    ("included_services", "Included Services / Facilities", "text", None),
    ("excluded_services", "Excluded / Chargeable Services", "text", None),
    ("pets_policy", "Pets Policy", "combo", PET_POLICIES),
    ("smoking_policy", "Smoking / Vaping Policy", "combo", SMOKING_POLICIES),
    ("special_terms", "Special Negotiated Terms (highest priority)", "text", None),

    ("operating_model", "Property Operating Model", "combo", OPERATING_MODELS),
    ("foreign_status", "Client / Occupant Nationality Status", "combo", FOREIGN_STATUS_OPTIONS),
    ("foreign_nationality", "Nationality (as per passport / OCI)", "entry", None),
    ("passport_no", "Passport Number", "entry", None),
    ("passport_issue_date", "Passport Issue Date", "entry", None),
    ("passport_expiry", "Passport Expiry Date", "entry", None),
    ("visa_oci_no", "Visa / OCI Number", "entry", None),
    ("visa_type", "Visa Type / OCI Status", "entry", None),
    ("visa_issue_date", "Visa Issue Date", "entry", None),
    ("visa_expiry", "Visa / OCI Validity / Expiry", "entry", None),
    ("purpose_of_visit", "Purpose of Visit in India", "entry", None),
    ("frro_registration_no", "FRRO/FRO Registration / Permit No. (if applicable)", "entry", None),
    ("frro_validity", "FRRO/FRO Registration / Permit Validity", "entry", None),
    ("arrival_from", "Arrived From", "entry", None),
    ("arrival_date_time", "Arrival / Check-in Date & Time", "entry", None),
    ("previous_place_of_stay", "Previous Place of Stay in India", "entry", None),
    ("next_destination", "Next Destination / Address After Departure", "entry", None),
    ("departure_date_time", "Departure / Check-out Date & Time", "entry", None),
    ("foreign_sponsor", "Employer / Sponsor / Institution in India", "entry", None),
    ("foreign_contact_abroad", "Emergency Contact Outside India", "entry", None),
    ("form3_arrival_ack", "Form III (earlier Form C) Arrival Acknowledgement / Ref.", "entry", None),
    ("form3_departure_ack", "Form III Departure Acknowledgement / Ref.", "entry", None),
    ("tenant_verification_ref", "Haryana Police Tenant/PG Verification Ref. / Status", "entry", None),
    ("hotel_validation_ref", "Haryana Police Hotel/Customer Validation Ref. (if applicable)", "entry", None),
    ("trade_license_no", "Trade Licence No. / Validity (if applicable)", "entry", None),
    ("lodging_license_no", "Lodging House Licence No. / Validity (if applicable)", "entry", None),
    ("fire_noc_no", "Fire NOC / Fire Safety Approval No. / Validity", "entry", None),
    ("occupancy_certificate_no", "Occupation Certificate / Building Approval Ref.", "entry", None),
    ("guest_house_permission_no", "Guest House / CLU / Zoning Permission Ref. (if applicable)", "entry", None),
    ("tourism_registration_no", "Haryana Tourism Home Stay Registration No. (if applicable)", "entry", None),
    ("statutory_licence_notes", "Other Licences / Permissions / Regulatory Notes", "text", None),
    ("language_precedence", "English-Hindi Version Precedence", "combo", LANGUAGE_PRECEDENCE_OPTIONS),

    ("witness1", "Witness 1 Name & Address", "text", None),
    ("witness2", "Witness 2 Name & Address", "text", None),
]

DEFAULTS = {
    "agreement_template": "Strong Residential - 11 Months",
    "agreement_type": "Comprehensive Rental Agreement",
    "agreement_date": datetime.date.today().strftime("%d-%m-%Y"),
    "paper_size": "Legal",
    "page_orientation": "Portrait",
    "margin_top_mm": "16",
    "margin_bottom_mm": "16",
    "margin_left_mm": "20",
    "margin_right_mm": "18",
    "show_page_numbers": "Yes",
    "print_page_range": "All",
    "print_copies": "1",
    "landlord_id_type": "Aadhaar",
    "tenant_id_type": "Aadhaar",
    "term_months": "11",
    "due_day": "5",
    "lockin_months": "6",
    "notice_days": "30",
    "increment_percent": "10",
    "increment_after_months": "11",
    "taxes": "Applicable statutory taxes / levies, if any, unless expressly included",
    "maintenance": "As stated in Annexure A / commercial particulars",
    "electricity_rate": "As per actual meter / sub-meter reading at the agreed rate",
    "genset_rate": "As per actual generator / DG meter reading at the agreed rate, if applicable",
    "utility_due_days": "3",
    "grace_days": "7",
    "late_fee": "INR 100 per day after the applicable grace period, subject to applicable law and proportionality",
    "subletting_policy": "Prohibited without prior written approval",
    "relocation_policy": "Emergency relocation only; otherwise prior written consent required",
    "access_notice_hours": "24",
    "deposit_refund_days": "15",
    "deposit_interest_rate": "0",
    "inventory_report_hours": "24",
    "early_exit_rule": "Notice shortfall and charges for the unexpired committed / lock-in period may be recovered to the extent expressly agreed and legally recoverable.",
    "pets_policy": "Not permitted unless specifically approved in writing",
    "smoking_policy": "Smoking/vaping prohibited inside the premises and all non-designated areas",
    "purpose": "Lawful residential use only",
    "operating_model": "Private residential tenancy",
    "foreign_status": "Indian citizen / no foreign-national reporting",
    "language_precedence": "English version prevails in case of inconsistency",
}

PRESETS = {
    "Strong Residential - 11 Months": {
        "agreement_template": "Strong Residential - 11 Months",
        "agreement_type": "Comprehensive Rental Agreement",
        "term_months": "11", "lockin_months": "6", "notice_days": "30",
        "increment_percent": "10", "increment_after_months": "11",
        "purpose": "Lawful residential use only",
        "subletting_policy": "Prohibited without prior written approval",
        "relocation_policy": "Emergency relocation only; otherwise prior written consent required",
        "access_notice_hours": "24", "deposit_refund_days": "15", "deposit_interest_rate": "0",
        "operating_model": "Private residential tenancy",
    },
    "Student Accommodation": {
        "agreement_template": "Student Accommodation",
        "agreement_type": "Comprehensive Rental Agreement",
        "term_months": "11", "lockin_months": "2", "notice_days": "30", "due_day": "5",
        "purpose": "Student residential accommodation only",
        "subletting_policy": "Prohibited without prior written approval",
        "relocation_policy": "Management may relocate for maintenance, safety or operational continuity to an equivalent or higher category",
        "controlled_entry_time": "As notified in property rules",
        "operating_model": "Paying Guest / PG accommodation",
    },
    "Corporate / Serviced Stay": {
        "agreement_template": "Corporate / Serviced Stay",
        "agreement_type": "Corporate Stay / Serviced Accommodation Agreement",
        "term_months": "11", "lockin_months": "3", "notice_days": "30",
        "purpose": "Lawful serviced accommodation / corporate residential stay",
        "subletting_policy": "Corporate nominee / employee substitution only with prior approval and fresh KYC",
        "relocation_policy": "Management may relocate for maintenance, safety or operational continuity to an equivalent or higher category",
        "access_notice_hours": "24",
        "operating_model": "Corporate stay / serviced apartment",
    },
    "OTA Commercial Hosting Rights": {
        "agreement_template": "OTA Commercial Hosting Rights",
        "agreement_type": "Commercial Hosting / OTA Agreement",
        "term_months": "11", "lockin_months": "6", "notice_days": "30",
        "purpose": "Lawful serviced accommodation and short-term OTA hosting",
        "subletting_policy": "OTA / short-term hosting expressly permitted without per-booking approval",
        "relocation_policy": "No relocation without Tenant/Guest's prior written consent",
        "access_notice_hours": "24", "deposit_refund_days": "7", "deposit_interest_rate": "18",
        "operating_model": "OTA / short-term serviced accommodation",
    },
    "Leave & License": {
        "agreement_template": "Leave & License",
        "agreement_type": "Leave & License Agreement",
        "term_months": "11", "lockin_months": "3", "notice_days": "30",
        "purpose": "Lawful residential / licensed occupation",
        "subletting_policy": "Prohibited without prior written approval",
        "operating_model": "Private residential tenancy",
    },
    "Commercial Premises": {
        "agreement_template": "Commercial Premises",
        "agreement_type": "Commercial Lease Agreement",
        "term_months": "36", "lockin_months": "12", "notice_days": "90",
        "increment_percent": "10", "increment_after_months": "12",
        "purpose": "Lawful commercial use subject to licences, approvals, building and fire-safety requirements",
        "subletting_policy": "Prohibited without prior written approval",
        "operating_model": "Commercial premises",
    },
    "Foreign Corporate Guest - Gurugram": {
        "agreement_template": "Foreign Corporate Guest - Gurugram",
        "agreement_type": "Corporate Stay / Serviced Accommodation Agreement",
        "term_months": "11", "lockin_months": "3", "notice_days": "30",
        "purpose": "Lawful serviced accommodation / corporate residential stay",
        "operating_model": "Corporate stay / serviced apartment",
        "foreign_status": "Foreign national",
        "subletting_policy": "Corporate nominee / employee substitution only with prior approval and fresh KYC",
        "relocation_policy": "Emergency relocation only; otherwise prior written consent required",
        "access_notice_hours": "24",
    },
}

FORMAT_PROFILES = {
    "Strong Residential - 11 Months": {
        "title_en": "RESIDENTIAL RENT AGREEMENT",
        "subtitle_en": "DETAILED 11-MONTH RESIDENTIAL TENANCY TERMS, FINANCIAL COVENANTS, HOUSE RULES AND EXECUTION",
        "title_hi": "विस्तृत आवासीय किराया अनुबंध",
        "subtitle_hi": "11 माह की आवासीय किरायेदारी, वित्तीय दायित्व, गृह नियम, वैधानिक शर्तें एवं निष्पादन",
        "nature_en": "The Premises are let for bona fide residential occupation for the fixed contractual term. No ownership interest is transferred. The Tenant receives peaceful residential use subject to timely payment, the agreed lock-in/notice terms, the restrictions on assignment/subletting and applicable law.",
        "nature_hi": "परिसर को निश्चित संविदात्मक अवधि के लिए वास्तविक आवासीय उपयोग हेतु दिया जाता है। स्वामित्व का कोई हस्तांतरण नहीं होता। समय पर भुगतान, लॉक-इन/सूचना, उपकिरायेदारी प्रतिबंध तथा लागू कानून के अधीन किरायेदार को शांतिपूर्ण आवासीय उपयोग का अधिकार रहेगा।",
        "special_en": [
            "This format is intended for a fixed-term private residential letting and excludes hotel/guest-house style commercial rebooking unless a separate written amendment expressly authorises it.",
            "The Tenant shall use the Premises primarily as a residence and shall not convert it into a public-facing commercial establishment or short-stay accommodation business without written permission and legally required approvals.",
        ],
        "special_hi": [
            "यह प्रारूप निश्चित अवधि की निजी आवासीय किरायेदारी के लिए है; अलग लिखित संशोधन के बिना होटल/गेस्ट-हाउस जैसी वाणिज्यिक पुनर्बुकिंग अधिकृत नहीं होगी।",
            "किरायेदार परिसर का मुख्य उपयोग निवास के रूप में करेगा और आवश्यक लिखित अनुमति तथा वैधानिक स्वीकृतियों के बिना इसे सार्वजनिक वाणिज्यिक प्रतिष्ठान अथवा अल्पकालिक आवास व्यवसाय में परिवर्तित नहीं करेगा।",
        ],
    },
    "Student Accommodation": {
        "title_en": "STUDENT ACCOMMODATION / PG RESIDENCE AGREEMENT",
        "subtitle_en": "STUDENT RESIDENCE, SAFETY, ATTENDANCE, FACILITIES, PAYMENT, HOUSE RULES AND GUARDIAN-RESPONSIBILITY TERMS",
        "title_hi": "छात्र आवास / पीजी निवास अनुबंध",
        "subtitle_hi": "छात्र निवास, सुरक्षा, उपस्थिति, सुविधाएँ, भुगतान, गृह नियम एवं अभिभावक-संबंधी शर्तें",
        "nature_en": "The Accommodation is provided for student residence / PG use during the confirmed academic or contractual period. The arrangement is personal to the registered student, subject to identity/KYC, property rules, safety controls, approved occupancy and the expressly agreed financial commitment.",
        "nature_hi": "आवास पंजीकृत छात्र को निश्चित शैक्षणिक/संविदात्मक अवधि के लिए छात्र निवास/पीजी उपयोग हेतु प्रदान किया जाता है। व्यवस्था व्यक्तिगत है और पहचान/KYC, संपत्ति नियम, सुरक्षा नियंत्रण, स्वीकृत अधिभोग तथा वित्तीय प्रतिबद्धता के अधीन रहेगी।",
        "special_en": [
            "The registered student shall comply with notified entry/exit, attendance, visitor, anti-ragging, nuisance, safety and common-area rules that are reasonable, non-discriminatory and communicated through official channels.",
            "Where a parent/guardian is recorded as an emergency or sponsoring contact, the Management may communicate material safety incidents, prolonged unexplained absence, payment default or serious rule breaches to that contact to the extent permitted by law and the accommodation arrangement.",
            "Meals, transport, housekeeping, laundry, Wi-Fi, recreation and other student-residence facilities are included only to the extent stated in Annexure A or the accepted booking package and may operate at notified timings.",
        ],
        "special_hi": [
            "पंजीकृत छात्र को उचित एवं आधिकारिक रूप से सूचित प्रवेश/निकास, उपस्थिति, आगंतुक, एंटी-रैगिंग, उपद्रव-निषेध, सुरक्षा तथा कॉमन-एरिया नियमों का पालन करना होगा।",
            "जहाँ माता-पिता/अभिभावक को आपातकालीन या प्रायोजक संपर्क के रूप में दर्ज किया गया हो, वहाँ कानून और आवास व्यवस्था की सीमा में गंभीर सुरक्षा घटना, लंबे समय की अस्पष्ट अनुपस्थिति, भुगतान डिफॉल्ट या गंभीर नियम उल्लंघन की सूचना दी जा सकती है।",
            "भोजन, परिवहन, हाउसकीपिंग, लॉन्ड्री, वाई-फाई, मनोरंजन व अन्य छात्र सुविधाएँ केवल परिशिष्ट-क/स्वीकृत पैकेज में लिखी सीमा तक शामिल होंगी और अधिसूचित समय पर संचालित हो सकती हैं।",
        ],
    },
    "Corporate / Serviced Stay": {
        "title_en": "CORPORATE STAY & SERVICED ACCOMMODATION AGREEMENT",
        "subtitle_en": "CORPORATE BOOKING, AUTHORISED OCCUPANT, SERVICED-STAY, BILLING, KYC, FACILITY AND RISK-ALLOCATION TERMS",
        "title_hi": "कॉरपोरेट स्टे एवं सर्विस्ड आवास अनुबंध",
        "subtitle_hi": "कॉरपोरेट बुकिंग, अधिकृत निवासी, बिलिंग, KYC, सुविधाएँ, सेवा-शर्तें एवं जोखिम आवंटन",
        "nature_en": "The Accommodation is provided as a fixed-term serviced/corporate stay for the registered Guest or authorised corporate occupant. The booking does not transfer ownership and does not create any greater proprietary right than mandatory law may provide; corporate sponsorship and guest liability are allocated by this Agreement.",
        "nature_hi": "आवास पंजीकृत अतिथि/अधिकृत कॉरपोरेट निवासी को निश्चित अवधि के सर्विस्ड/कॉरपोरेट स्टे के रूप में दिया जाता है। स्वामित्व हस्तांतरित नहीं होता; कॉरपोरेट प्रायोजन और अतिथि की देयताएँ इस अनुबंध के अनुसार निर्धारित होंगी।",
        "special_en": [
            "The Corporate Client is liable only for charges it has expressly booked, sponsored or guaranteed; personal incidentals and unauthorised extensions remain payable by the Guest unless separately accepted in writing.",
            "Substitution or rotation of an authorised corporate occupant requires prior approval, fresh KYC/registration and settlement of any revised tariff or statutory formality.",
            "Included housekeeping, Wi-Fi, laundry, meals, transport or other services are hospitality/service inclusions and do not by themselves expand the legal nature or duration of the occupancy.",
        ],
        "special_hi": [
            "कॉरपोरेट ग्राहक केवल उन्हीं शुल्कों के लिए उत्तरदायी होगा जिन्हें उसने स्पष्ट रूप से बुक, प्रायोजित या गारंटी किया हो; व्यक्तिगत खर्च व अनधिकृत विस्तार अलग लिखित स्वीकृति के बिना अतिथि द्वारा देय होंगे।",
            "अधिकृत कॉरपोरेट निवासी का परिवर्तन/रोटेशन पूर्व स्वीकृति, नया KYC/पंजीकरण तथा संशोधित शुल्क/वैधानिक औपचारिकताओं के बाद ही प्रभावी होगा।",
            "हाउसकीपिंग, वाई-फाई, लॉन्ड्री, भोजन, परिवहन आदि की शामिल सेवाएँ सेवा-सुविधाएँ हैं और केवल इनके कारण अधिभोग की कानूनी प्रकृति या अवधि नहीं बढ़ेगी।",
        ],
    },
    "OTA Commercial Hosting Rights": {
        "title_en": "RENT AGREEMENT WITH COMMERCIAL HOSTING / OTA RIGHTS",
        "subtitle_en": "FIXED-TERM OCCUPATION WITH EXPRESS SHORT-STAY REBOOKING, OTA HOSTING, KYC, NON-INTERFERENCE AND COMMERCIAL RESPONSIBILITY TERMS",
        "title_hi": "वाणिज्यिक होस्टिंग / OTA अधिकार सहित किराया अनुबंध",
        "subtitle_hi": "निश्चित अवधि के कब्जे के साथ स्पष्ट अल्पकालिक पुनर्बुकिंग, OTA होस्टिंग, KYC, गैर-हस्तक्षेप एवं वाणिज्यिक दायित्व",
        "nature_en": "The Premises are granted for the fixed contractual term together with the specific commercial hosting rights expressly recorded in this Agreement. The authorised OTA/short-stay activity is contractual permission only and remains subject to applicable KYC, immigration, fire, occupancy, municipal, zoning and licensing requirements.",
        "nature_hi": "परिसर निश्चित संविदात्मक अवधि के साथ इस अनुबंध में स्पष्ट वाणिज्यिक होस्टिंग अधिकारों हेतु दिया जाता है। OTA/अल्पकालिक होस्टिंग की अनुमति केवल संविदात्मक अनुमति है और KYC, आव्रजन, अग्नि, अधिभोग, नगरपालिका, जोनिंग व लाइसेंस संबंधी कानूनों के अधीन रहेगी।",
        "special_en": [
            "Subject to applicable law and required property permissions, the Management gives continuing contractual consent to list, market and rebook the identified unit for registered short-term/serviced guests through OTAs without obtaining a new case-by-case consent for every booking.",
            "Lawful OTA hosting carried out within this express authority shall not by itself be treated by the Management as unauthorised subletting or a termination ground; the primary Tenant/Operator nevertheless remains responsible for rent, utilities, KYC, guest conduct and attributable damage.",
            "No OTA permission in this Agreement overrides a mandatory licence, zoning/CLU restriction, fire requirement, society/building rule that cannot lawfully be waived, immigration reporting duty or police direction.",
        ],
        "special_hi": [
            "लागू कानून व संपत्ति अनुमतियों के अधीन, प्रबंधन चिन्हित इकाई को पंजीकृत अल्पकालिक/सर्विस्ड अतिथियों हेतु OTA पर सूचीबद्ध, विपणित व पुनर्बुक करने की निरंतर संविदात्मक सहमति देता है; प्रत्येक बुकिंग पर नई अनुमति आवश्यक नहीं होगी।",
            "इस स्पष्ट अधिकार के भीतर वैध OTA होस्टिंग को केवल इसी कारण अनधिकृत उपकिरायेदारी/निरस्तीकरण आधार नहीं माना जाएगा; फिर भी मूल किरायेदार/ऑपरेटर किराया, उपयोगिताएँ, KYC, अतिथि आचरण और जिम्मेदार क्षति के लिए उत्तरदायी रहेगा।",
            "यह OTA अनुमति किसी अनिवार्य लाइसेंस, जोनिंग/CLU प्रतिबंध, अग्नि आवश्यकता, अविच्छेद्य सोसायटी/भवन नियम, आव्रजन रिपोर्टिंग या पुलिस निर्देश को निष्प्रभावी नहीं करती।",
        ],
    },
    "Leave & License": {
        "title_en": "LEAVE AND LICENSE AGREEMENT",
        "subtitle_en": "PERSONAL, FIXED-TERM LICENSE TO OCCUPY WITH LICENCE FEE, SECURITY, ACCESS, TERMINATION AND HANDOVER TERMS",
        "title_hi": "लीव एंड लाइसेंस / अनुज्ञप्ति अनुबंध",
        "subtitle_hi": "व्यक्तिगत निश्चित-अवधि अधिभोग अनुमति, अनुज्ञप्ति शुल्क, सुरक्षा, प्रवेश, समाप्ति एवं हस्तांतरण शर्तें",
        "nature_en": "The Licensor grants the Licensee a personal, fixed-term permission to occupy and use the Premises for the permitted purpose, subject to applicable law. No ownership is transferred, no assignment is permitted except as expressly approved, and continued occupation after expiry requires a fresh written arrangement.",
        "nature_hi": "लाइसेंसर लाइसेंसी को अनुमत उद्देश्य हेतु परिसर के उपयोग/अधिभोग की व्यक्तिगत, निश्चित-अवधि अनुमति देता है। स्वामित्व हस्तांतरित नहीं होता, स्पष्ट स्वीकृति के बिना हस्तांतरण अनुमत नहीं है और अवधि के बाद अधिभोग हेतु नया लिखित समझौता आवश्यक होगा।",
        "special_en": [
            "The licence is personal to the named Licensee and shall not be assigned, transferred or converted into a third-party occupancy arrangement without the Licensor's prior written approval and applicable legal formalities.",
            "Licence fee, security deposit, utilities, access rights and handover obligations shall be governed by the written commercial particulars and not by any inconsistent oral understanding.",
        ],
        "special_hi": [
            "अनुज्ञप्ति नामित लाइसेंसी के लिए व्यक्तिगत है और लाइसेंसर की पूर्व लिखित स्वीकृति तथा लागू कानूनी औपचारिकताओं के बिना किसी तीसरे पक्ष को हस्तांतरित/परिवर्तित नहीं की जाएगी।",
            "अनुज्ञप्ति शुल्क, सुरक्षा जमा, उपयोगिताएँ, प्रवेश अधिकार व हस्तांतरण दायित्व लिखित वाणिज्यिक विवरण से नियंत्रित होंगे, किसी असंगत मौखिक समझ से नहीं।",
        ],
    },
    "Commercial Premises": {
        "title_en": "COMMERCIAL LEASE AGREEMENT",
        "subtitle_en": "BUSINESS PREMISES, RENT, SECURITY, TAX, LICENSING, FIT-OUT, COMPLIANCE, DEFAULT AND POSSESSION TERMS",
        "title_hi": "वाणिज्यिक परिसर लीज अनुबंध",
        "subtitle_hi": "व्यावसायिक परिसर, किराया, सुरक्षा, कर, लाइसेंस, फिट-आउट, अनुपालन, डिफॉल्ट एवं कब्जा शर्तें",
        "nature_en": "The Premises are leased for the specifically stated lawful commercial purpose and for no incompatible use. The Lessee is responsible for business-specific registrations, licences and approvals allocated to it; structural/title approvals allocated to the Lessor remain with the Lessor, subject to the written terms and applicable law.",
        "nature_hi": "परिसर केवल स्पष्ट रूप से लिखे वैध वाणिज्यिक उद्देश्य हेतु लीज पर दिया जाता है। व्यवसाय-विशिष्ट पंजीकरण/लाइसेंस जहाँ लीज़ी को सौंपे गए हैं उनकी जिम्मेदारी लीज़ी की होगी; संरचनात्मक/स्वामित्व संबंधी स्वीकृतियाँ लिखित शर्तों व कानून के अधीन लीज़र की जिम्मेदारी रहेंगी।",
        "special_en": [
            "The Lessee shall not undertake structural alterations, signage, hazardous storage, change of use, customer-facing activity or regulated business beyond the approved purpose without the permissions required from the Lessor and competent authorities.",
            "GST, TDS, municipal levies, common-area/maintenance charges and utility liabilities shall be borne and documented strictly according to the written commercial allocation and applicable tax law.",
            "Any fit-out, restoration, signage removal, keys/access return and vacant-possession obligations at exit shall be completed as recorded in the handover/inventory schedule, excluding ordinary wear and tear unless otherwise lawfully agreed.",
        ],
        "special_hi": [
            "लीज़ी लीज़र एवं सक्षम प्राधिकारियों की आवश्यक अनुमति के बिना संरचनात्मक परिवर्तन, साइनेज, खतरनाक भंडारण, उपयोग परिवर्तन या अनुमत उद्देश्य से बाहर विनियमित/ग्राहक-सामना व्यवसाय नहीं करेगा।",
            "GST, TDS, नगरपालिका शुल्क, कॉमन-एरिया/मेंटेनेंस तथा उपयोगिता देयताएँ लिखित वाणिज्यिक आवंटन और लागू कर कानून के अनुसार ही वहन/दस्तावेजीकृत की जाएंगी।",
            "निकास पर फिट-आउट, पुनर्स्थापन, साइनेज हटाना, चाबी/एक्सेस वापसी और खाली कब्जा हैंडओवर/इन्वेंटरी शेड्यूल के अनुसार पूरा किया जाएगा, सामान्य घिसावट को छोड़कर जहाँ कानूनन अन्यथा सहमति न हो।",
        ],
    },
    "Foreign Corporate Guest - Gurugram": {
        "title_en": "FOREIGN NATIONAL CORPORATE STAY & SERVICED ACCOMMODATION AGREEMENT",
        "subtitle_en": "GURUGRAM CORPORATE STAY WITH PASSPORT/VISA/OCI, FORM III, FRRO/FRO, POLICE, SAFETY, BILLING AND RECORD-CUSTODY TERMS",
        "title_hi": "विदेशी नागरिक कॉरपोरेट स्टे एवं सर्विस्ड आवास अनुबंध",
        "subtitle_hi": "गुरुग्राम कॉरपोरेट स्टे: पासपोर्ट/वीज़ा/OCI, Form III, FRRO/FRO, पुलिस, सुरक्षा, बिलिंग एवं रिकॉर्ड शर्तें",
        "nature_en": "The Accommodation is provided to a registered foreign-national/OCI corporate guest for the confirmed serviced-stay period. Occupation is conditional upon valid travel/immigration documentation and any reporting, registration, police, licensing or safety requirement actually applicable to the property and guest category.",
        "nature_hi": "आवास पंजीकृत विदेशी नागरिक/OCI कॉरपोरेट अतिथि को निश्चित सर्विस्ड-स्टे अवधि हेतु दिया जाता है। अधिभोग वैध यात्रा/आव्रजन दस्तावेज तथा अतिथि/संपत्ति पर वास्तव में लागू रिपोर्टिंग, पंजीकरण, पुलिस, लाइसेंस व सुरक्षा आवश्यकताओं के पालन पर निर्भर रहेगा।",
        "special_en": [
            "The Guest shall present a valid passport and the applicable visa/OCI/travel document and shall promptly provide information reasonably required for statutory guest registration and immigration reporting.",
            "Where Form III arrival/departure reporting or other electronic foreigner reporting is legally applicable to the accommodation keeper, the Management shall submit/retain the required particulars within the prescribed time and may preserve the acknowledgement/reference with the booking record.",
            "The Guest and Corporate Client shall cooperate with FRRO/FRO, police or competent-authority requirements applicable to the visa category, length of stay and property. This Agreement does not by itself extend a visa, residential permit or immigration status.",
            "Passport/visa/OCI data shall be used and retained only for legitimate accommodation, safety, billing and legal-compliance purposes and disclosed where legally required or validly authorised.",
        ],
        "special_hi": [
            "अतिथि वैध पासपोर्ट तथा लागू वीज़ा/OCI/यात्रा दस्तावेज प्रस्तुत करेगा और वैधानिक अतिथि पंजीकरण/आव्रजन रिपोर्टिंग हेतु उचित रूप से आवश्यक जानकारी देगा।",
            "जहाँ Form III आगमन/प्रस्थान रिपोर्टिंग या अन्य विदेशी-नागरिक इलेक्ट्रॉनिक रिपोर्टिंग आवास प्रदाता पर कानूनी रूप से लागू हो, वहाँ आवश्यक विवरण निर्धारित समय में जमा/सुरक्षित किए जाएंगे और प्राप्ति/संदर्भ रिकॉर्ड में रखा जा सकेगा।",
            "अतिथि और कॉरपोरेट ग्राहक वीज़ा श्रेणी, प्रवास अवधि और संपत्ति पर लागू FRRO/FRO, पुलिस या सक्षम प्राधिकारी की आवश्यकताओं में सहयोग करेंगे। यह अनुबंध स्वयं किसी वीज़ा/रेजिडेंशियल परमिट/आव्रजन स्थिति को नहीं बढ़ाता।",
            "पासपोर्ट/वीज़ा/OCI डेटा केवल वैध आवास, सुरक्षा, बिलिंग और कानूनी अनुपालन हेतु उपयोग/संग्रहित होगा तथा कानूनन आवश्यक/वैध रूप से अधिकृत स्थिति में ही साझा होगा।",
        ],
    },
}


def infer_template_name(d):
    explicit = clean(d.get("agreement_template"))
    if explicit in FORMAT_PROFILES:
        return explicit
    typ = clean(d.get("agreement_type"))
    operating = clean(d.get("operating_model"))
    foreign = clean(d.get("foreign_status"))
    if foreign in ("Foreign national", "OCI Cardholder", "Mixed / group booking including foreign nationals or OCI Cardholders") and typ == "Corporate Stay / Serviced Accommodation Agreement":
        return "Foreign Corporate Guest - Gurugram"
    if typ == "Commercial Hosting / OTA Agreement" or "OTA" in operating:
        return "OTA Commercial Hosting Rights"
    if typ == "Corporate Stay / Serviced Accommodation Agreement":
        return "Corporate / Serviced Stay"
    if typ == "Leave & License Agreement":
        return "Leave & License"
    if typ == "Commercial Lease Agreement":
        return "Commercial Premises"
    if "PG" in operating or "Student" in clean(d.get("purpose")):
        return "Student Accommodation"
    return "Strong Residential - 11 Months"


CLAUSE_LIBRARY = {
    "No waiver by delay": "Failure or delay by either Party in enforcing any provision once shall not operate as a continuing waiver of that provision or any other right.",
    "No oral modification": "No oral statement shall modify this Agreement. Any variation of commercial terms must be recorded in writing and accepted by the Parties, except a mandatory change required by law.",
    "Damage evidence": "Any material damage deduction should, where reasonably practicable, be supported by photographs, inspection notes, bills, invoices or other verifiable particulars.",
    "No self-help removal": "Any recovery of possession, removal of an occupant or enforcement of termination shall be carried out only through lawful procedures; neither Party authorizes unlawful lockout, detention of belongings or physical coercion.",
    "Official communication record": "Official app messages, acknowledged email, SMS, WhatsApp, receipts, invoices, access logs and other electronic records may be retained and relied upon as evidence to the extent permitted by law.",
    "Utilities meter fault": "If a utility meter is faulty, inaccessible or unreliable, interim billing may be based on a fair average of comparable consumption, appliance load or other reasonable evidence until the meter is restored.",
}

LEGAL_RESEARCH_NOTES = r"""GURUGRAM / HARYANA LEGAL & REGULATORY REFERENCE
Primary-source orientation verified 23 August 2026

IMPORTANT
This offline reference is a drafting aid, not a legal opinion or a guarantee of enforceability. Exact stamp duty, registration, municipal permission, fire approval, police directions, immigration reporting and court procedure depend on the actual property, operating model, term and facts. Re-check current law before execution and obtain case-specific advice for high-value, contested or unusual transactions.

1. CONTRACT FORMATION
- Indian Contract Act, 1872, section 10: contracts require free consent of competent parties, lawful consideration and lawful object, and must not be otherwise void.
- Clauses cannot validate an unlawful use or waive non-waivable statutory rights.

2. STAMPING / REGISTRATION OF LEASES IN HARYANA
- Registration Act, 1908, section 17(1)(d): a lease from year to year, for a term exceeding one year, or reserving yearly rent is compulsorily registrable. Section 18 permits optional registration of leases not exceeding one year, subject to the document and applicable law.
- Section 23 generally requires presentation of a registrable document within four months of execution, subject to statutory exceptions.
- Section 49 restricts the effect/evidentiary use of a document that was required to be registered but was not registered, subject to its proviso and other law.
- Haryana Revenue & Disaster Management Department provides official registration guidance, the Registration Act text and deed templates. Exact stamp duty/fee should be checked for the actual instrument and current Haryana schedule.
- The property description should be sufficient to identify the immovable property.

3. FOREIGN NATIONAL / OCI ACCOMMODATION - CURRENT 2025 REGIME
- The Immigration and Foreigners Act, 2025 came into force on 1 September 2025. Section 8 places reporting duties on a keeper of accommodation, with a qualification for residential premises of a non-commercial nature; a civil authority may direct reporting for specified residential premises/areas.
- Immigration and Foreigners Rules, 2025, rule 17 applies to every foreigner including an OCI Cardholder seeking covered accommodation. It expressly includes hostel, paying guest house, rented accommodation, home stay and similar premises.
- Rule 17 requires prescribed arrival/departure particulars, electronic preservation for at least one year, availability for inspection by authorised authorities, electronic Form III (earlier Form C) transmission within 24 hours after arrival, and departure particulars within 24 hours after departure.
- The foreign guest must provide truthful passport/visa/OCI and other prescribed particulars. The agreement cannot extend or regularise a visa, OCI condition, registration or residential permit.

4. HARYANA POLICE / GURUGRAM SERVICES
- Haryana Police currently provides Tenant/PG Verification Request service and also lists Validation of Owners of Hotel and Customers Registered, Registration of Foreigners (Arrival and Departure), and Extension of Residential Permit of Foreigners through its citizen-service framework.
- Any additional Commissioner of Police / District Magistrate / civil-authority direction applicable to a specific area or period must be followed even if it is not reproduced in this template.

5. LODGING / GUEST HOUSE / COMMERCIAL OPERATIONS
- Haryana Urban Local Bodies' notified service framework includes issue and renewal of a licence for lodging houses. Trade-licence requirements may also apply depending on the establishment/use.
- Guest-house operation in a residential sector can be permission/zoning sensitive. ULB Haryana has issued Gurugram public notices under policies for permission to set up guest houses in specified residential sectors. The agreement therefore records CLU/zoning/guest-house permission references where applicable instead of assuming every residential property can lawfully operate as a guest house.

6. FIRE / BUILDING / OCCUPATION COMPLIANCE
- The Haryana Fire and Emergency Services Act, 2022 governs prevention of fire and fire-safety measures in buildings. Fire NOC / approval requirements depend on the building's use, height, area and applicable classification.
- Occupation certificate/building approval and sanctioned-use restrictions should be checked for the specific property. A private contract cannot override land-use, building or fire restrictions.

7. HARYANA HOME STAY - IF THIS OPERATING MODEL IS SELECTED
- Haryana Home Stay Scheme, 2024 requires eligible Home Stay owners to register with the Tourism Department, maintain guest records and comply with scheme conditions. The published scheme also refers to informing the concerned SHO for foreign tourists and to the then-used Form C process. Under the current 2025 central regime, use the presently prescribed Form III / designated portal process where applicable.

8. ELECTRONIC EXECUTION AND COURT-READINESS
- Information Technology Act, 2000, section 10A: a contract is not unenforceable solely because electronic means were used in its formation.
- Bharatiya Sakshya Adhiniyam, 2023, sections 61-63 govern electronic/digital records and their proof/admissibility. Preserve signed versions, acknowledgements, payment records, notices, meter readings, inventory photographs and original electronic files/metadata; where required in litigation, comply with the statutory electronic-record certificate requirements.

OFFICIAL REFERENCE WEBSITES
- Ministry of Home Affairs - Foreigners Division: https://www.mha.gov.in/
- India Code: https://www.indiacode.nic.in/
- Haryana Police: https://haryanapolice.gov.in/
- Haryana Revenue & Disaster Management: https://revenueharyana.gov.in/
- Urban Local Bodies Haryana: https://ulbharyana.gov.in/
- Haryana Tourism: https://haryanatourism.gov.in/
"""


def clean(value):
    return (value or "").strip()


def money_words(num_text):
    try:
        n = int(float(re.sub(r"[^0-9.]", "", str(num_text))))
    except Exception:
        return ""
    if n == 0:
        return "Zero"
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def under1000(x):
        parts = []
        if x >= 100:
            parts += [ones[x // 100], "Hundred"]
            x %= 100
        if x >= 20:
            parts.append(tens[x // 10])
            x %= 10
        if x > 0:
            parts.append(ones[x])
        return " ".join(parts)

    parts = []
    for value, name in [(10000000, "Crore"), (100000, "Lakh"), (1000, "Thousand")]:
        if n >= value:
            q, n = divmod(n, value)
            parts += [under1000(q), name]
    if n:
        parts.append(under1000(n))
    return " ".join(parts)


def amount_text(value):
    v = clean(value) or "________"
    words = money_words(v)
    return f"INR {v}" + (f" (Rupees {words} only)" if words else "")


def role_names(agreement_type):
    if agreement_type == "Leave & License Agreement":
        return "LICENSOR", "LICENSEE", "Licensor", "Licensee"
    if agreement_type == "Corporate Stay / Serviced Accommodation Agreement":
        return "MANAGEMENT / LICENSOR", "GUEST / LICENSEE", "Management", "Guest"
    if agreement_type == "Commercial Hosting / OTA Agreement":
        return "MANAGEMENT / LESSOR / LICENSOR", "GUEST / TENANT / OPERATOR", "Management", "Guest/Tenant"
    if agreement_type in ("Lease Agreement", "Commercial Lease Agreement"):
        return "LESSOR", "LESSEE", "Lessor", "Lessee"
    return "LANDLORD / LESSOR", "TENANT / LESSEE", "Landlord", "Tenant"


def party_description(d, prefix, fallback):
    name = clean(d.get(prefix + "_name")) or "________________"
    father = clean(d.get(prefix + "_father"))
    address = clean(d.get(prefix + "_address"))
    id_type = clean(d.get(prefix + "_id_type"))
    id_no = clean(d.get(prefix + "_id_no"))
    bits = [name]
    if father:
        bits.append(f"S/o / D/o / W/o {father}")
    if address:
        bits.append(f"address: {address}")
    if id_no:
        bits.append(f"{id_type or 'Government ID'} No. {id_no}")
    return ", ".join(bits) if bits else fallback


def split_special_terms(text):
    raw = clean(text)
    if not raw:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n|\n(?=\s*[-*]\s+)", raw) if p.strip()]


def is_ota_enabled(d):
    return "OTA / short-term hosting expressly permitted" in clean(d.get("subletting_policy")) or d.get("agreement_type") == "Commercial Hosting / OTA Agreement"


def build_agreement_text(d, extra_clauses=None):
    extra_clauses = extra_clauses or []
    typ = clean(d.get("agreement_type")) or "Comprehensive Rental Agreement"
    template_name = infer_template_name(d)
    format_profile = FORMAT_PROFILES.get(template_name, FORMAT_PROFILES["Strong Residential - 11 Months"])
    p1_cap, p2_cap, p1, p2 = role_names(typ)
    corp = clean(d.get("corporate_name"))
    ota = is_ota_enabled(d)
    term = clean(d.get("term_months")) or "________"
    start = clean(d.get("start_date")) or "________"
    end = clean(d.get("end_date")) or "________"
    lockin = clean(d.get("lockin_months")) or "0"
    notice = clean(d.get("notice_days")) or "30"
    rent = amount_text(d.get("monthly_rent"))
    deposit = amount_text(d.get("security_deposit"))
    due_day = clean(d.get("due_day")) or "________"
    inc = clean(d.get("increment_percent"))
    inc_after = clean(d.get("increment_after_months"))
    grace = clean(d.get("grace_days")) or "0"
    refund_days = clean(d.get("deposit_refund_days")) or "15"
    deposit_interest = clean(d.get("deposit_interest_rate")) or "0"
    access_hours = clean(d.get("access_notice_hours")) or "24"
    inv_hours = clean(d.get("inventory_report_hours")) or "24"
    util_days = clean(d.get("utility_due_days")) or "3"
    jur = clean(d.get("jurisdiction")) or clean(d.get("place_of_execution")) or "the competent courts having territorial jurisdiction"
    premises = clean(d.get("premises")) or "________________________________________"
    property_name = clean(d.get("property_name")) or "the Property"
    room = clean(d.get("room_unit_no")) or "________"
    room_type = clean(d.get("room_type")) or "As stated in Annexure A"
    occupancy = clean(d.get("occupancy_limit")) or "As permitted by law / building rules"
    purpose = clean(d.get("purpose")) or "lawful use"
    agreement_ref = clean(d.get("agreement_reference")) or "________"
    party1 = party_description(d, "landlord", "________________")
    entity = clean(d.get("landlord_entity"))
    if entity:
        party1 = f"{entity}, through {clean(d.get('authorized_signatory')) or 'its authorised signatory'}, operating / represented by {party1}"
    party2 = party_description(d, "tenant", "________________")

    lines = []
    lines.append(format_profile["title_en"])
    lines.append(format_profile["subtitle_en"])
    lines.append("")
    lines.append(f"Agreement / Booking Reference: {agreement_ref}")
    lines.append(f"Agreement Date: {clean(d.get('agreement_date')) or '________'} | Place: {clean(d.get('place_of_execution')) or '________'} | Term: {term} months | Lock-in: {lockin} months")
    lines.append("")
    lines.append("STAMP / E-STAMP AND NOTARY PARTICULARS")
    lines.append(f"Stamp / E-Stamp No.: {clean(d.get('stamp_number')) or '________________'} | Value / Duty: {('INR ' + clean(d.get('stamp_value'))) if clean(d.get('stamp_value')) else '________________'}")
    lines.append(f"Notary Name: {clean(d.get('notary_name')) or '________________'} | Registration No.: {clean(d.get('notary_reg_no')) or '________________'}")
    lines.append("")
    lines.append(f"This Agreement is executed on {clean(d.get('agreement_date')) or '________'} at {clean(d.get('place_of_execution')) or '________'}.")
    lines.append("")
    lines.append("BETWEEN")
    lines.append(f"{p1_cap}: {party1}. Mobile: {clean(d.get('landlord_mobile')) or '________'}; Email: {clean(d.get('landlord_email')) or '________'}; PAN: {clean(d.get('landlord_pan')) or '________'}. Hereinafter referred to as the \"{p1}\", which expression shall include its/his/her authorised representatives, legal heirs, successors and permitted assigns where the context permits.")
    lines.append("")
    lines.append("AND")
    lines.append(f"{p2_cap}: {party2}. DOB: {clean(d.get('tenant_dob')) or '________'}; Mobile: {clean(d.get('tenant_mobile')) or '________'}; WhatsApp: {clean(d.get('tenant_whatsapp')) or clean(d.get('tenant_mobile')) or '________'}; Email: {clean(d.get('tenant_email')) or '________'}. Hereinafter referred to as the \"{p2}\".")
    if corp:
        lines.append("")
        lines.append("AND / OR CORPORATE CLIENT / BOOKING ENTITY")
        lines.append(f"{corp}, address: {clean(d.get('corporate_address')) or '________'}, GSTIN: {clean(d.get('corporate_gstin')) or '________'}, PAN: {clean(d.get('corporate_pan')) or '________'}, through {clean(d.get('corporate_representative')) or '________'} ({clean(d.get('corporate_designation')) or 'authorised representative'}), Mobile: {clean(d.get('corporate_mobile')) or '________'}, Email: {clean(d.get('corporate_email')) or '________'}. The Corporate Client provisions apply only to the extent it accepts, sponsors or guarantees this Agreement.")
    lines.append("")
    lines.append("COMMERCIAL PARTICULARS")
    lines.append(f"Property: {property_name} | Premises: {premises} | Room / Unit: {room} | Category: {room_type}")
    lines.append(f"Start: {start} | End: {end} | Term: {term} months | Lock-in: {lockin} months | Notice: {notice} days")
    lines.append(f"Rent / Licence Fee: {rent} per month | Security Deposit: {deposit} | Rent Due Day: {due_day}")
    if inc:
        lines.append(f"Escalation: {inc}% after {inc_after or 'the stated'} months if the arrangement is renewed / extended or continues beyond that period, unless otherwise agreed in writing.")
    lines.append(f"Electricity: {clean(d.get('electricity_rate')) or 'As agreed / applicable'} | Generator / DG: {clean(d.get('genset_rate')) or 'As agreed / applicable'}")
    lines.append(f"Permitted Use: {purpose}")
    lines.append("")
    lines.append("SELECTED AGREEMENT FORMAT")
    lines.append(f"Template / Preset: {template_name}. The agreement structure, defined relationship and format-specific covenants below are generated for this selected preset.")
    lines.append("")
    lines.append("SPECIAL NEGOTIATED TERMS - THESE TERMS PREVAIL OVER GENERAL HOUSE RULES")
    negotiated = list(format_profile.get("special_en", [])) + [
        f"The lock-in / minimum commitment is {lockin} months and the notice period is {notice} days. Notice does not by itself shorten an unexpired lock-in unless the Parties agree in writing or applicable law provides otherwise.",
        f"Assignment / sharing / subletting policy: {clean(d.get('subletting_policy')) or 'Prohibited without prior written approval'}.",
        f"Room / unit relocation policy: {clean(d.get('relocation_policy')) or 'As stated in this Agreement'}.",
        f"Except for a genuine emergency, urgent safety/welfare concern, serious suspected unlawful activity, or lawful authority order, normal Management entry shall follow the agreed notice period of {access_hours} hours and shall state the approximate time and purpose.",
        f"The undisputed balance of the security deposit shall ordinarily be processed/refunded within {refund_days} business days after handover, return of issued items, inspection and final settlement, subject to permitted deductions.",
    ]
    if deposit_interest not in ("", "0", "0.0"):
        negotiated.append(f"Any undisputed security deposit amount remaining unpaid after the stated refund period shall carry simple interest at {deposit_interest}% per annum from the next business day until payment, except for a documented bona fide dispute, court order or banking impossibility beyond reasonable control.")
    negotiated.append("Confirmed commercial terms shall not be changed unilaterally during the fixed term except by a written amendment accepted by the affected Parties or where a mandatory change in law directly applies.")
    for item in split_special_terms(d.get("special_terms")):
        negotiated.append(item.lstrip("-* "))
    for idx, item in enumerate(negotiated, 1):
        lines.append(f"S{idx}. {item}")

    def section(number, title, clauses):
        lines.append("")
        lines.append(f"{number}. {title}")
        for j, clause in enumerate(clauses, 1):
            if clause:
                lines.append(f"{number}.{j} {clause}")

    if typ in ("Leave & License Agreement", "Corporate Stay / Serviced Accommodation Agreement"):
        nature = "The Premises are provided as a limited, personal and fixed-term licence / accommodation right for the confirmed period. The Parties do not intend to create ownership or any greater proprietary right than is required by applicable law."
    elif typ == "Commercial Hosting / OTA Agreement":
        nature = "The Premises are granted for the fixed contractual term together with the specific commercial hosting rights expressly recorded in this Agreement. No ownership interest is transferred."
    else:
        nature = "The Premises are granted for the fixed contractual rental / lease term stated in this Agreement. No ownership interest is transferred and occupation after expiry requires a written renewal or extension, subject to applicable law."

    nature = format_profile.get("nature_en") or nature

    section(1, "DEFINITIONS, PURPOSE AND ACCEPTANCE", [
        f"\"Accommodation / Premises\" means the room, flat, studio, apartment, bed space or other premises described in this Agreement, together with only those facilities expressly included in Annexure A or a signed booking confirmation.",
        "\"Booking Confirmation\" includes an accepted quotation, reservation confirmation, corporate rate letter, purchase order accepted in writing, invoice, app record or other written record identifying dates, tariff, occupancy and inclusions.",
        f"\"Property\" means {property_name} at {premises}, including Room / Unit {room} where specifically allotted.",
        f"The purpose of occupation is limited to: {purpose}.",
        "The Parties confirm that they have read and voluntarily accepted the Agreement, Annexures, payment terms, safety directions, visitor rules and notified house rules.",
        "Check-in / handover and continued occupation are conditional upon valid identification, payment or approved credit, lawful conduct and compliance with applicable requirements.",
    ])

    section(2, "ACCOMMODATION / PREMISES AND COMMERCIAL DETAILS", [
        f"Property / building: {property_name}.",
        f"Full address / Premises: {premises}.",
        f"Room / Unit No.: {room}; category / occupancy type: {room_type}; approved occupancy: {occupancy}.",
        f"Commencement / handover date: {start}; end / check-out date: {end}; confirmed term: {term} months.",
        f"Minimum committed / lock-in period: {lockin} months.",
        f"Rent / accommodation / licence fee: {rent} per month; security deposit: {deposit}.",
    ])

    section(3, "NATURE OF OCCUPANCY AND CONTRACTUAL RIGHTS", [
        nature,
        f"The {p1} retains the ownership, safety, compliance and maintenance rights lawfully preserved by this Agreement; the {p2} is entitled to peaceful use in accordance with this Agreement during the fixed term.",
        f"The {p2} shall hand back peaceful vacant possession / occupation of the Premises on expiry or lawful termination, subject to final settlement and security-deposit accounting.",
        "No clause excludes a non-waivable statutory or consumer right available under applicable law.",
    ])

    section(4, "TERM, EXTENSION, LOCK-IN AND HOLDOVER", [
        f"The fixed term begins on {start} and ends on {end}, unless extended or lawfully terminated in writing.",
        "Any extension or renewal becomes effective only after written confirmation and settlement / approval of the applicable commercial terms. Mere continued occupation does not by itself renew the Agreement except where law provides otherwise.",
        f"The minimum commitment / lock-in is {lockin} months. The {p2} shall give at least {notice} days' prior written notice before vacating. Such notice does not automatically shorten the lock-in.",
        clean(d.get("early_exit_rule")) or "Early departure during a committed period may attract the agreed notice-shortfall or early-departure charge to the extent legally recoverable.",
        "Unauthorised holdover may attract the then-applicable daily / periodic occupation charge, documented additional loss and lawful recovery proceedings.",
    ])

    payment_clauses = [
        f"Monthly rent / fee of {rent} shall be paid on or before day {due_day} of each month, in advance where so agreed.",
        f"Taxes / levies: {clean(d.get('taxes')) or 'Applicable statutory taxes and levies, if any'}.",
        f"Maintenance / common charges: {clean(d.get('maintenance')) or 'As stated in Annexure A'}.",
        "The Tenant/Guest and/or Corporate Client shall pay all chargeable incidentals and services actually requested or consumed, including utilities, additional occupancy, food, laundry, transport, parking, repairs and replacement where applicable.",
        "Payment shall be made only through an approved mode against an official receipt, invoice or system record. Payment to an unauthorised person does not discharge the payment obligation unless acknowledged by the receiving Party.",
        "Any invoice discrepancy should be raised promptly; undisputed amounts remain payable on time.",
        "Amounts received may be appropriated against the oldest undisputed outstanding dues unless otherwise agreed in writing or required by law.",
        f"A grace period of {grace} days applies only where stated. Thereafter the late fee / overdue charge shall be: {clean(d.get('late_fee')) or 'as stated in Annexure A'}, subject to applicable law and proportionality.",
    ]
    if inc:
        payment_clauses.append(f"If the arrangement is renewed / extended or continues beyond {inc_after or 'the stated'} months, the rent / fee shall increase by {inc}% unless the Parties agree otherwise in writing.")
    section(5, "RENT / ACCOMMODATION CHARGES, TAXES AND PAYMENT", payment_clauses)

    section(6, "CORPORATE BILLING, CREDIT AND TAX DEDUCTION", [
        "This section applies only where a Corporate Client is a Party, sponsor or guarantor of the booking.",
        "The Corporate Client shall pay charges it has booked, sponsored, guaranteed or authorised, together with applicable taxes and approved incidentals allocated to its account.",
        "Internal purchase-order or approval processes do not postpone a valid invoice unless the Management expressly accepted such condition in writing.",
        "Personal expenses, unauthorised extensions, prohibited conduct, damage and incidentals not accepted by the Corporate Client remain payable by the Guest/Tenant. Where a written guarantee applies, liability shall be joint and several to the stated extent.",
        "TDS or other tax deduction shall be made only where legally required; the deducting Party shall deposit it on time and provide the correct certificate / reconciliation particulars.",
    ])

    deposit_clauses = [
        f"The security deposit is {deposit}. Unless expressly agreed in writing, it is not routine advance rent and shall not be automatically adjusted against the final month's rent.",
        "Permitted deductions may include unpaid rent / fees, taxes, electricity, utilities, missing inventory, replacement of keys/access devices, excessive cleaning, documented damage beyond ordinary wear and tear, and other amounts properly due under this Agreement.",
        "Ordinary wear and tear shall not be charged as damage. Deductions should be reasonably itemised and, where reasonably available, supported by photographs, inspection notes, bills, invoices or similar evidence.",
        f"The undisputed balance shall ordinarily be refunded / initiated for refund within {refund_days} business days after handover, return of issued items, final inspection and settlement. External banking or card-network release time is outside the payer's direct control.",
    ]
    if deposit_interest not in ("", "0", "0.0"):
        deposit_clauses.append(f"An undisputed balance delayed beyond the stated refund period shall carry simple interest at {deposit_interest}% per annum from the following business day, except for a bona fide documented dispute, court order or banking impossibility beyond reasonable control.")
    deposit_clauses.append("Any early-exit, notice-shortfall or lock-in deduction must remain within the amount expressly agreed and legally recoverable.")
    section(7, "SECURITY DEPOSIT, PRE-AUTHORISATION AND FINAL SETTLEMENT", deposit_clauses)

    section(8, "CANCELLATION, NO-SHOW, EARLY DEPARTURE AND REFUNDS", [
        "Any accepted cancellation, amendment, no-show and refund policy recorded in Annexure A / Booking Confirmation forms part of this Agreement.",
        "A tariff or payment shall be treated as non-refundable only where that condition was clearly disclosed and is enforceable under applicable law.",
        "Early departure during a valid minimum commitment may attract the agreed notice-shortfall / early-departure charge, after crediting any refund required by the accepted terms or applicable law.",
        "No reduction is ordinarily due merely because included facilities are voluntarily not used or the occupant is temporarily absent, unless otherwise agreed.",
        f"If the {p1} cannot provide the confirmed Premises and no reasonably comparable alternative is accepted, the remedy may include refund or credit of affected unused prepaid charges, subject to applicable law.",
    ])

    section(9, "UTILITIES, ELECTRICITY AND APPLIANCES", [
        f"Grid / mains electricity: {clean(d.get('electricity_rate')) or 'As agreed / applicable'}.",
        f"Generator / DG electricity: {clean(d.get('genset_rate')) or 'As agreed / applicable'}.",
        f"Separately billed utility invoices shall be paid within {util_days} days of generation or within the expressly applicable corporate invoice due date.",
        "If a meter is faulty, inaccessible, damaged or unreliable, interim billing may be based on a fair average of comparable consumption, appliance load or other reasonable evidence until the meter is restored.",
        "Tampering with meters, wiring, seals, air-conditioning controls, fire equipment, plumbing, network devices or other utility systems is prohibited and may result in recovery of loss, safety action and lawful termination.",
        "High-load appliances, heaters, hot plates, induction units, personal routers, signal boosters or cooking equipment may be used only if supplied or approved where the Property requires such approval.",
    ])

    relocation = clean(d.get("relocation_policy"))
    if relocation.startswith("No relocation"):
        relocation_clauses = [
            f"Room / Unit {room} is specifically confirmed for the fixed term, subject to lawful termination.",
            f"The {p1} shall not relocate, shift or substitute the confirmed Room / Unit without the {p2}'s prior written consent, except where a competent authority requires otherwise.",
            "If the occupant voluntarily accepts a temporary alternative for emergency repairs, the substitute should be equivalent or higher in category at no additional room charge unless otherwise agreed.",
        ]
    elif relocation.startswith("Emergency relocation"):
        relocation_clauses = [
            f"Room / Unit {room} is the confirmed allocation. Relocation is permitted only for a genuine emergency, urgent safety/structural requirement, lawful authority direction, or with prior written consent.",
            "Any emergency substitute should, where reasonably possible, be equivalent or higher in category. If a lower category is accepted, an appropriate tariff adjustment shall be made.",
        ]
    else:
        relocation_clauses = [
            f"A particular Room / Unit is guaranteed when expressly confirmed. Otherwise the {p1} may allot an equivalent unit within the booked category.",
            f"The {p1} may relocate the occupant for maintenance, safety, renovation, emergency, operational continuity or other reasonable property requirements.",
            "Relocation should, where reasonably possible, be to an equivalent or higher category without additional room charge. If a lower category is accepted, the tariff difference shall be adjusted.",
        ]
    relocation_clauses += [
        f"The approved occupancy limit is {occupancy}. The occupant shall not change rooms / units or exceed lawful occupancy without written approval.",
        "Any change of the primary Tenant/Guest or corporate nominee requires the applicable written approval, fresh KYC / registration and revised commercial terms, if any.",
    ]
    section(10, "ROOM / UNIT ALLOCATION, OCCUPANCY AND RELOCATION", relocation_clauses)

    sub_policy = clean(d.get("subletting_policy"))
    if ota:
        sub_clauses = [
            f"EXPRESS AUTHORISATION: During the fixed term the {p2} may advertise, list, market, commercially rebook, share, license or sublet the confirmed Premises for lawful short-term / serviced stays through recognised online travel agencies and booking platforms, without obtaining separate consent for each individual booking.",
            "This continuing consent is subject to applicable law, KYC / guest-registration requirements, occupancy and fire-safety limits, and binding building/society rules that cannot lawfully be waived.",
            f"Lawful OTA hosting carried out within this Agreement shall not, by itself, be treated by the {p1} as unauthorised subletting, misuse or a ground for termination.",
            "A short-term guest receives only the temporary right of occupation for the booked period and acquires no ownership, continuing tenancy or independent right against the owner / Management beyond that booking.",
            f"The {p2} remains responsible for rent, utilities, documented physical damage beyond ordinary wear and tear, and material misconduct caused by persons admitted under the {p2}'s bookings.",
            "No separate NOC or fee is required for each OTA booking unless a new mandatory legal requirement applies or the Parties later agree otherwise in writing.",
        ]
    elif sub_policy.startswith("Corporate nominee"):
        sub_clauses = [
            "Corporate nomination of an employee / contractor disclosed in the booking is permitted only after Management approval, fresh KYC and updated registration.",
            "No rotation, replacement or additional occupant is valid merely because of internal corporate approval.",
            "Unless expressly released in writing, the original Guest and any guaranteeing Corporate Client remain responsible for payment, conduct, damage and overstay arising from the approved nominee arrangement.",
        ]
    elif sub_policy.startswith("Allowed only"):
        sub_clauses = [
            "Assignment, sharing, replacement occupation or subletting is allowed only for a specifically named person and period approved in writing, subject to lawful use, KYC, revised tariff and additional documents / charges where applicable.",
            "Approval is specific and does not create a general right to sublet. It may be withdrawn for material breach, safety concerns, misrepresentation, non-payment or violation of law.",
            "The original Tenant/Guest remains responsible unless expressly released in writing.",
        ]
    else:
        sub_clauses = [
            f"The {p2} shall not assign, transfer, resell, share, license, part with possession of, commercially rebook or sublet the Premises without the {p1}'s prior written approval.",
            "Any approved arrangement shall be specific to the named person and approved period, subject to KYC, lawful use, revised tariff and required documents / charges.",
            "Unless expressly released in writing, the original Tenant/Guest and any guarantor remain responsible for payment, conduct, damage, overstay and other obligations arising from the approved arrangement.",
        ]
    section(11, "ASSIGNMENT, SHARING, SUBLETTING AND COMMERCIAL HOSTING", sub_clauses)

    section(12, "CHECK-IN, KYC AND STATUTORY REGISTRATION", [
        "Handover / check-in is conditional upon valid original government-issued identification, required registration, payment and execution formalities.",
        "Aadhaar information shall be collected or used only through a lawful and permitted process; another valid government identity document may be accepted where legally appropriate.",
        "A foreign national shall provide valid passport, visa, arrival and other information required for applicable hotel / immigration / foreigner registration, and authorises lawful submission to competent authorities.",
        "False, altered, expired, incomplete or misleading documents may result in refusal / cancellation and reporting to competent authorities where appropriate.",
        "A minor may stay only with an authorised adult or with lawful written consent and safeguards accepted by the Property.",
        "Material changes in identity, contact, visa, employer, sponsorship or emergency-contact details relevant to the stay shall be notified promptly.",
    ])

    section(13, "CHECK-OUT, NOTICE, KEYS AND EXIT FORMALITIES", [
        f"The contractual end / check-out date is {end}, unless extended or terminated earlier in writing.",
        f"At least {notice} days' prior written notice shall be given where this Agreement requires notice. Notice does not reduce the stated {lockin}-month lock-in unless otherwise agreed or legally required.",
        "Notice is valid when sent through an officially accepted channel such as acknowledged email, official app, registered post, written application, SMS / WhatsApp where accepted, or another channel recorded by the Parties.",
        "On handover, the occupant shall remove personal belongings, return keys, access cards, remotes and issued items, permit final inspection and settle outstanding dues.",
        "Items left behind may be stored, delivered or disposed of after reasonable notice in accordance with the Property's lost-and-found procedure and applicable law. Perishable, hazardous or unlawful items may be dealt with immediately where permitted.",
        "Completion of check-out does not extinguish liability for charges or damage discovered during a reasonable post-departure inspection.",
    ])

    section(14, "ACCESS CONTROL, PROPERTY ENTRY AND MANAGEMENT ACCESS", [
        "Keys, access cards, passwords and digital credentials are the responsibility of the registered occupant and shall not be copied or shared with unauthorised persons, except as expressly permitted for registered OTA guests where Clause 11 authorises such hosting.",
        f"Controlled / last entry time, if applicable: {clean(d.get('controlled_entry_time')) or 'As notified in applicable property rules'}.",
        "The Management may maintain visitor / vehicle / access records and verify identity at entry for legitimate safety and compliance purposes.",
        f"Except in the circumstances stated below, non-emergency entry for housekeeping, inspection, inventory, repairs, pest control, compliance or showing near departure should follow at least {access_hours} hours' prior notice / agreed notice and occur at a reasonable time with minimum interference.",
        "Prior notice is not required for a genuine emergency, fire, flooding, gas/electrical danger, urgent medical or welfare concern, imminent threat to persons/property, serious suspected unlawful activity, or a lawful police/court/authority direction. The occupant should be informed as soon as reasonably practicable after emergency entry.",
        "No additional locking device may be installed or used in a way that prevents lawful emergency access.",
    ])

    visitors_clause = "Registered short-term / serviced guests hosted under Clause 11 are permitted occupants for their respective bookings, subject to KYC, occupancy and safety requirements." if ota else "Visitors are permitted only in approved areas / hours and subject to registration, identification, security screening and applicable property rules."
    section(15, "VISITORS, ADDITIONAL OCCUPANTS AND OVERNIGHT GUESTS", [
        visitors_clause,
        "No unapproved person may remain overnight or use the Premises as an occupant where prior approval, KYC or additional-person charges are required.",
        "The registered Tenant/Guest is responsible for the conduct of visitors and persons admitted by them and for documented charges or damage caused by such persons, without limiting the individual person's own liability.",
        "The Management may refuse or remove a visitor for safety, overcrowding, nuisance, invalid identification, unlawful conduct, guest objection or material breach of policy.",
        "Unregistered commercial meetings, parties, public gatherings, filming, photography shoots or events materially different from ordinary permitted use require prior written approval and lawful permits where applicable.",
    ])

    section(16, "HOUSEKEEPING, MAINTENANCE AND ROOM CARE", [
        "Housekeeping, linen change and cleaning shall be provided only to the extent included in the agreed service plan and schedule.",
        "A Do Not Disturb request may delay routine service but does not prevent emergency access, essential maintenance or a reasonable welfare check after prolonged non-contact.",
        "The occupant shall promptly report leaks, electrical faults, pest activity, breakage, unsafe conditions or malfunctioning equipment and take reasonable steps to prevent further damage.",
        "The Premises shall be kept reasonably clean and hygienic and shall not be used in a way likely to cause infestation, foul odour, blockage, fire risk or avoidable damage.",
        "Furniture, appliances, fixtures and decor shall not be removed, materially shifted, painted, drilled, pasted upon or altered without required approval.",
        "Windows, doors and water outlets shall be secured when leaving. Balconies, ledges and fire exits shall not be used for unsafe storage or activity.",
    ])

    section(17, "FACILITIES, INTERNET, MEALS, LAUNDRY, PARKING AND THIRD-PARTY SERVICES", [
        f"Included services / facilities: {clean(d.get('included_services')) or 'Only those expressly stated in Annexure A / Booking Confirmation'}.",
        f"Excluded / chargeable services: {clean(d.get('excluded_services')) or 'As stated in Annexure A and this Agreement'}.",
        "Facility timings, capacity and access rules may be reasonably changed for maintenance, safety or operations, subject to any fixed commercial commitment expressly recorded in this Agreement.",
        "Wi-Fi, where provided, is on a reasonable-use and availability basis. Uninterrupted speed and compatibility with every device or corporate network are not guaranteed.",
        "The network shall not be used for unlawful access, infringement, harassment, malware, mass distribution, crypto-mining, interference or activity threatening security or service quality.",
        "Meal plans / food packages, if included, are available during notified timings and according to the booked plan. Allergies and dietary requirements should be disclosed in advance.",
        "Independent third-party services such as laundry, transport, delivery, medical, tours or food delivery may be subject to separate terms; responsibility for an independent provider remains subject to applicable law.",
        "Parking, gym, recreation and wellness facilities, where available, are subject to registration, capacity and displayed safety rules.",
    ])

    section(18, "CONDUCT, QUIET ENJOYMENT AND PERMITTED USE", [
        "The occupant and visitors shall behave lawfully and respectfully and shall not cause nuisance, harassment, intimidation, threat, violence, obstruction, excessive noise or disturbance to neighbours, other occupants or staff.",
        "Complaints should be made through the official management / property channel. Abusive, discriminatory, threatening or violent conduct is prohibited.",
        "Quiet hours and local noise restrictions shall be observed.",
        f"The Premises shall be used only for {purpose}. Any materially different storefront, warehouse, clinic, salon, call-centre, public venue, registered office or customer-facing business use requires prior written approval and lawful permissions.",
        "Parties, events, political meetings, promotional activities, commercial photography, filming or media production require prior written approval where not part of the expressly permitted use.",
        f"Pets: {clean(d.get('pets_policy')) or 'As stated in Annexure A'}.",
    ])

    section(19, "PROHIBITED AND UNLAWFUL ACTIVITIES", [
        f"Smoking / vaping: {clean(d.get('smoking_policy')) or 'As stated in Property rules'}. Reasonable cleaning, alarm-response and damage charges may be recovered where smoking evidence is established.",
        "Alcohol may be possessed or consumed only where lawful, by persons of lawful age and in compliance with applicable property policy. Disorderly conduct or unlawful supply is prohibited.",
        "Possession, use, manufacture, sale or distribution of unlawful drugs, contraband, explosives, hazardous chemicals, weapons or prohibited substances is prohibited.",
        "Gambling, trafficking, sexual exploitation, prostitution, violence, theft, fraud, cybercrime and other unlawful activity are prohibited.",
        "Fire exits, detectors, sprinklers, extinguishers, CCTV, access systems and safety notices shall not be obstructed, disabled or tampered with.",
        "Candles, open flames, fireworks, flammable fuel or other fire hazards are prohibited except where specifically supplied / approved for a controlled lawful purpose.",
        "Depending on seriousness, prohibited items / conduct may result in removal of the item where lawful, denial of access, termination and/or reporting to competent authorities.",
    ])

    section(20, "PROPERTY, INVENTORY, DAMAGE AND EXCESSIVE CLEANING", [
        "The occupant shall take reasonable care of the Premises, furniture, appliances, linen, electronics, fixtures, common areas and supplied inventory.",
        f"Existing damage or inventory discrepancy should be reported within {inv_hours} hours of handover / check-in or as soon as reasonably discovered. Unreported obvious damage may be considered at final inspection together with all available evidence.",
        "The responsible Tenant/Guest and/or Corporate Client shall pay the reasonable documented cost of repair, specialist cleaning, restoration or replacement for loss or damage caused by them, approved sub-occupants, visitors or invitees, excluding ordinary wear and tear.",
        "Lost keys, access cards, remotes, linen, utensils, appliances and other supplied items may be charged at the notified or reasonable replacement cost.",
        "Where responsibility in a jointly occupied unit is established against more than one occupant, the responsible occupants may be charged jointly in a reasonable proportion; an unrelated person shall not be charged merely because damage occurred in a common area.",
        "Documented damage and recovery charges may be deducted from the security deposit or invoiced separately.",
    ])

    section(21, "PERSONAL BELONGINGS, SAFEKEEPING AND LOST PROPERTY", [
        "The occupant is responsible for cash, jewellery, documents, electronics, vehicles and personal belongings and should use available lockers / safes and suitable insurance where appropriate.",
        "Doors, windows, cupboards and luggage should be secured when unattended; access credentials shall not be disclosed.",
        "Loss, theft or suspicious activity should be reported promptly so that reasonable assistance, record preservation and police reporting, where appropriate, can be undertaken.",
        "The Management / owner is not liable for loss, theft or damage except to the extent caused by proven negligence, wilful misconduct, breach of a specific safekeeping obligation or as otherwise required by law.",
    ])

    section(22, "SAFETY, HEALTH, MEDICAL ASSISTANCE AND EMERGENCIES", [
        "The occupant shall follow fire, evacuation, access, balcony, electrical, food-safety, gym / pool and other applicable safety instructions.",
        "Information reasonably necessary for emergency assistance, accessibility support or allergy management should be disclosed truthfully and handled in accordance with applicable privacy requirements.",
        f"Emergency contacts recorded are: {clean(d.get('emergency_contact1')) or '________'} and {clean(d.get('emergency_contact2')) or '________'}.",
        "The Management is not a medical provider. In an apparent emergency it may contact an emergency contact, ambulance, doctor, hospital, police, fire service or Corporate Client and may facilitate transport where reasonably possible.",
        "Medical consultation, medicine, ambulance, hospital and related costs are borne according to the applicable arrangement, except where liability is imposed by law due to another Party's proven fault.",
        "Nothing excludes responsibility for injury or emergency loss to the extent caused by negligence, wilful misconduct or breach of a non-waivable duty.",
    ])

    section(23, "PRIVACY, CCTV, DATA USE AND CORPORATE REPORTING", [
        "Identity, contact, booking, payment, access, visitor, CCTV, service and incident information may be processed for accommodation, safety, legal compliance, billing, support and legitimate property operations.",
        "CCTV may operate in entrances, corridors, reception, parking and other common areas for safety and security, but shall not be installed inside private rooms or bathrooms.",
        "Information may be disclosed to payment processors, service providers, professional advisers, insurers, a sponsoring Corporate Client and competent government / law-enforcement authorities where necessary, authorised or legally required.",
        "Where a Corporate Client sponsors the stay, booking status, attendance / check-in status, invoices, approved usage, safety incidents and material rule breaches may be shared to the extent reasonably necessary and legally permitted.",
        "Marketing communication shall require any consent mandated by law. Essential booking, payment, service and safety messages are not marketing.",
        "Records may be retained for operational, tax, security, dispute and legal-compliance periods and then deleted / anonymised where required.",
    ])

    section(24, "SERVICE REQUESTS, COMPLAINTS AND RECTIFICATION", [
        "A service defect, safety concern or billing issue should be reported promptly through the official property / management channel so that there is a reasonable opportunity to investigate and rectify it.",
        "The occupant shall reasonably cooperate with necessary inspection and repair. Any relocation offered to resolve a complaint remains subject to the relocation policy expressly selected in this Agreement.",
        "Failure to report a readily remediable issue during the stay may be considered when assessing a later claim, without removing non-waivable legal rights.",
        "A complaint does not suspend undisputed payment obligations. The Parties shall work in good faith to resolve disputed amounts.",
    ])

    termination_base = [
        "Material grounds for refusal of check-in, suspension of services or termination may include material non-payment, invalid KYC, fraud, unlawful activity, serious nuisance, violence, harassment, prohibited items, unsafe conduct, unauthorised occupancy, unauthorised subletting, material property damage or repeated material breach after warning.",
        "Immediate termination / safety action may occur where reasonably necessary to protect persons, property, legal compliance or peaceful operation. For a remediable non-serious breach, a reasonable opportunity to cure should ordinarily be given where appropriate.",
        "Upon lawful termination the occupant shall leave peacefully within the required time, return issued items and settle dues. Recovery of possession shall use lawful procedures; unlawful lockout, detention of belongings or physical coercion is not authorised by this Agreement.",
        "Where termination results from the Tenant/Guest/Corporate Client's material breach, refund, if any, shall be determined by the accepted terms, actual recoverable loss and applicable law.",
        f"Where the {p1} terminates without occupant breach and cannot provide a reasonably comparable alternative, affected unused prepaid accommodation charges shall be refunded or credited to the extent required by the accepted terms and applicable law.",
    ]
    if ota:
        termination_base.append("Lawful OTA hosting / commercial rebooking expressly permitted by Clause 11 shall not, by itself, constitute unauthorised subletting or a ground for termination.")
    section(25, "TERMINATION, REFUSAL OF SERVICE AND LAWFUL REMOVAL", termination_base)

    section(26, "FORCE MAJEURE AND ACCOMMODATION UNAVAILABILITY", [
        "A Party is not liable for delay or failure caused by an event beyond reasonable control, including natural disaster, fire, flood, epidemic, government restriction, civil disturbance, utility failure, labour disruption, structural emergency or mandatory closure, to the extent performance is prevented.",
        "The affected Party shall notify the other as soon as reasonably possible and take reasonable steps to reduce disruption.",
        f"If the confirmed Premises become unavailable, the {p1} may offer a comparable alternative, revised dates, credit or refund of affected unused charges, having regard to the selected relocation policy, accepted terms and applicable law.",
        "Force majeure does not excuse payment for accommodation / services already supplied.",
    ])

    section(27, "INDEMNITY AND LIMITATION OF LIABILITY", [
        f"The {p2} and any responsible Corporate Client shall indemnify the {p1} against third-party claims, penalties, property loss and reasonable costs arising directly from their fraud, unlawful act, wilful misconduct, material breach or acts of visitors / approved sub-occupants, except to the extent caused by the {p1} or its own breach.",
        f"To the maximum extent permitted by law, the {p1} is not liable for indirect, special or consequential commercial loss, loss of profit, business interruption or loss of data arising from the stay or temporary service interruption.",
        f"Subject to non-waivable rights, the {p1}'s aggregate contractual liability for an affected booking / period shall not exceed the accommodation charges paid or payable for that affected period, except where a higher liability cannot lawfully be excluded.",
        "No exclusion or limitation applies to fraud, wilful misconduct, death or personal injury caused by negligence, breach of a non-waivable statutory duty, or liability that cannot lawfully be excluded or limited.",
    ])

    section(28, "INSURANCE AND RISK RESPONSIBILITY", [
        "The Tenant/Guest and Corporate Client are advised to maintain appropriate personal accident, medical, property, travel, cyber or business insurance for their own risks where relevant.",
        "Property insurance maintained by the owner / Management does not insure the occupant's personal belongings, health, travel changes or business risks unless expressly stated.",
    ])

    section(29, "NOTICES AND OFFICIAL COMMUNICATION", [
        "Notices may be sent by hand, registered post, official app, acknowledged email, SMS or WhatsApp to the contact details recorded in this Agreement or later updated in writing.",
        "The Parties shall keep their mobile, email, billing and emergency-contact particulars current.",
        "Routine electronic notice is treated as received when delivered to the registered account / device unless a failure message is received, subject to any mandatory legal method applicable to termination, demand or legal notices.",
        "Operational house rules and safety directions may be displayed at the Property or communicated through official digital channels, but shall not unilaterally alter fixed commercial terms.",
    ])

    section(30, "ELECTRONIC ACCEPTANCE, RECORDS AND COUNTERPARTS", [
        "This Agreement may be executed by physical signature, legally valid electronic signature, OTP / app confirmation, digital acceptance or exchange of signed counterparts where permitted.",
        "The Parties consent to creation and retention of booking, payment, access and communication records and acknowledge that such records may be used as evidence subject to applicable law.",
        "A person signing for a company / Corporate Client represents that he or she is authorised to bind it, and proof of authority may be requested.",
        "No Party should sign a materially incomplete agreement. Software-generated fields, commercial particulars and annexures should be reviewed before acceptance.",
    ])

    section(31, "GENERAL TERMS, ENTIRE AGREEMENT AND ORDER OF PRECEDENCE", [
        "This Agreement, its Annexures, accepted Booking Confirmation and any signed amendment constitute the entire agreement on the subject and replace prior oral discussions to the extent permitted by law.",
        "In case of inconsistency, the following order applies: (a) the latest specifically signed amendment; (b) Special Negotiated Terms; (c) Annexure A / accepted Booking Confirmation; (d) the main clauses of this Agreement; and (e) operational house rules, unless applicable law requires otherwise.",
        "Fixed commercial terms shall not be changed unilaterally after confirmation except for a mandatory change in law / tax, a guest-requested service, or a variation expressly permitted by this Agreement. Reasonable safety and operational rules may be updated with notice so long as they do not defeat fixed negotiated rights.",
        "Any waiver or amendment must be in writing by an authorised person. Failure to enforce a provision once is not a continuing waiver.",
        "If any provision is invalid or unenforceable, it shall be limited or severed to the minimum extent necessary and the remaining provisions shall continue.",
        f"The {p1} may transfer this Agreement to a successor owner / operator upon notice provided the confirmed occupant rights are preserved. The {p2} may transfer only as allowed under Clause 11.",
    ])

    section(32, "GOVERNING LAW AND DISPUTE RESOLUTION", [
        "This Agreement shall be governed by the laws applicable in India.",
        "The Parties shall first attempt in good faith to resolve a dispute through the property manager / authorised representatives within fifteen (15) days of written notice, unless urgent legal relief is reasonably required.",
        f"Subject to any non-waivable consumer, statutory or territorial jurisdiction, the competent courts / authorities at {jur} shall have jurisdiction over disputes arising from this Agreement.",
        "Nothing restricts a consumer or other entitled person from approaching a competent consumer commission or statutory authority where that right cannot lawfully be excluded.",
    ])

    section(33, "DECLARATION BY TENANT / GUEST AND CORPORATE CLIENT", [
        "The signatories confirm that the information and documents supplied are true, current and complete to the best of their knowledge and that no material fact relevant to lawful occupation has deliberately been concealed.",
        f"They confirm that they have read the property details, rent / tariff, taxes, payment schedule, cancellation / early-exit terms, security deposit terms, {lockin}-month lock-in, {notice}-day notice requirement, utility terms, relocation policy, access policy, subletting / hosting policy, visitor rules, safety instructions, statutory compliance provisions and house rules.",
        "They agree to pay charges properly due and to be responsible for the conduct and damage attributable to the Tenant/Guest, registered occupants, approved sub-occupants and visitors according to this Agreement, subject always to proof, causation and applicable law.",
        "They understand that serious or repeated material breach may result in lawful termination, recovery of documented loss and reporting to competent authorities where required, but no clause authorises unlawful dispossession, coercion, detention of belongings or any remedy prohibited by law.",
        "They consent to lawful KYC, guest registration, safety monitoring and data processing described in this Agreement, including statutory reporting in relation to foreign nationals or OCI Cardholders where applicable.",
        "They acknowledge receipt or availability of a complete copy of this Agreement and its Annexures and confirm that they have had a reasonable opportunity to read, seek clarification and obtain independent advice before execution.",
    ])

    operating_model = clean(d.get("operating_model")) or "Private residential tenancy"
    foreign_status = clean(d.get("foreign_status")) or "Indian citizen / no foreign-national reporting"
    foreign_applies = foreign_status != "Indian citizen / no foreign-national reporting"
    language_precedence = clean(d.get("language_precedence")) or "English version prevails in case of inconsistency"

    section(34, "STATUTORY EXECUTION, STAMP DUTY AND REGISTRATION", [
        "The Parties intend this document to record a lawful contract entered into with free consent by persons competent to contract, for lawful consideration and a lawful object. Nothing in this Agreement is intended to contract out of a mandatory statute or to validate an arrangement that is otherwise prohibited by law.",
        "The instrument shall bear the stamp duty legally applicable in Haryana to the nature, term, consideration and form of the transaction. Responsibility for purchasing/e-stamping and bearing the duty/cost shall be recorded by the Parties consistently with the applicable stamp law and current Haryana registration process; any statutory liability that cannot lawfully be shifted by contract shall remain unaffected.",
        "Where the transaction is a lease from year to year, for a term exceeding one year, or otherwise falls within a class for which registration is compulsory under section 17 of the Registration Act, 1908 or section 107 of the Transfer of Property Act, 1882, the Parties shall cooperate in timely presentation and registration before the competent Sub-Registrar/Joint Sub-Registrar. A lease not exceeding one year may be optionally registrable under section 18 of the Registration Act, subject to the instrument and current Haryana law.",
        "The Parties shall provide a description of the Premises sufficient to identify it, including the full postal address, unit/room/flat number and, where available, municipal/property identifier, floor/area and boundaries or other identifying particulars. If registration is undertaken, any map, plan or supporting property description required by the registering authority shall be provided.",
        "No material blank, unauthenticated alteration or inconsistent interlineation should remain at execution. Any correction made before signing should be initialled/attested by the executing Parties where appropriate. Each Party shall retain a complete signed copy together with stamp/e-stamp details and registration particulars, if any.",
        "Notarisation or witness signatures may strengthen identification and proof of execution where used, but shall not be treated as a substitute for mandatory stamp duty or registration. Failure to register a document that is compulsorily registrable may affect the manner and extent to which it can be relied upon in evidence, subject to the Registration Act and other applicable law.",
    ])

    section(35, "FOREIGN NATIONAL / OCI ACCOMMODATION, FORM III AND IMMIGRATION COMPLIANCE", [
        f"Client / Occupant status selected for this Agreement: {foreign_status}. Where a foreign national or OCI Cardholder is accommodated, the Parties acknowledge that the Immigration and Foreigners Act, 2025 and the Immigration and Foreigners Rules, 2025 may impose direct statutory duties that operate independently of this contract.",
        "For accommodation covered by rule 17 of the Immigration and Foreigners Rules, 2025, the keeper of accommodation shall obtain the prescribed particulars from every foreigner, including an OCI Cardholder, at arrival and departure, maintain the prescribed particulars electronically for at least one year, and keep them available for inspection by the competent authorities in accordance with law.",
        "Where rule 17 applies, the keeper of accommodation shall transmit the duly completed Form III (earlier Form C) electronically to the Registration Officer through the designated online portal/mobile application as soon as possible and not later than twenty-four (24) hours after arrival. Departure particulars shall likewise be transmitted as soon as possible and not later than twenty-four (24) hours after departure.",
        "For the purpose of the 2025 Rules, accommodation expressly includes categories such as hostel, paying guest house, rented accommodation, home stay and other premises of like nature. The statutory Act contains a qualification for residential premises of a non-commercial nature, but a competent civil authority may direct reporting in specified areas; accordingly, the Parties shall comply with any lawful local direction applicable in Gurugram from time to time.",
        "The foreign Guest/Occupant shall provide true and legible passport, visa/OCI, nationality, contact, arrival, previous-stay, next-destination and other particulars reasonably required for statutory reporting, and shall promptly notify any extension, curtailment, cancellation, change of address, change of visa status or registration/residential-permit condition relevant to the stay.",
        "The foreign Guest/Occupant warrants only that the documents supplied are authentic to the best of his/her knowledge and that the stay and activities at the Premises will remain within the conditions of the visa, OCI status, registration certificate, residential permit and applicable law. Management may refuse check-in or require lawful departure where a material immigration document is invalid, expired, apparently forged or incompatible with the proposed stay, subject to applicable law and reasonable verification.",
        "Management may inspect and retain lawful copies/records of travel and identity documents for KYC and statutory reporting, but this Agreement does not authorise permanent confiscation or retention of an original passport or travel document except where expressly permitted by law or required by a competent authority.",
        f"Form III arrival acknowledgement/reference recorded by the Parties: {clean(d.get('form3_arrival_ack')) or 'Not yet recorded / Not applicable'}. Departure acknowledgement/reference: {clean(d.get('form3_departure_ack')) or 'Not yet recorded / Not applicable'}.",
    ])

    section(36, "HARYANA POLICE / GURUGRAM VERIFICATION AND COOPERATION", [
        "Haryana Police provides citizen services for Tenant/PG Verification and related verification requests through its notified citizen-service channels. Where tenant/PG verification is required by a lawful direction, requested by the owner/Management as a reasonable security measure, or selected by the Parties, the Tenant/Guest shall provide the necessary truthful particulars and reasonable cooperation.",
        "Haryana Police also lists services concerning validation of hotel owners/customers and registration of foreigners (arrival and departure). These administrative processes are separate from the contractual relationship and shall be complied with to the extent applicable to the selected operating model and occupant status.",
        f"Tenant/PG verification reference/status: {clean(d.get('tenant_verification_ref')) or 'Not recorded / Not applicable'}. Hotel/customer validation reference, if applicable: {clean(d.get('hotel_validation_ref')) or 'Not recorded / Not applicable'}.",
        "Neither Party shall make a knowingly false statement to the police, FRRO/FRO, registration authority or any other competent authority. A material falsehood or forged identity/immigration document constitutes a serious contractual breach in addition to any consequences under law.",
        "Cooperation with verification shall be proportionate and limited to information legitimately required for the accommodation, safety, compliance or lawful reporting purpose; private information unrelated to those purposes should not be demanded merely because this Agreement has been signed.",
    ])

    section(37, "PROPERTY OPERATING PERMISSIONS, LODGING HOUSE / TRADE LICENCE AND ZONING", [
        f"The selected operating model is: {operating_model}. The Parties acknowledge that a private residential tenancy, PG, serviced apartment, hotel/guest house, lodging house, home stay and OTA/short-term accommodation can attract different municipal, planning, licensing, society/building and tax requirements. This Agreement by itself is not a municipal, tourism, fire, planning, zoning or trade licence.",
        "As between the Parties, approvals legally imposed on the property owner/operator/keeper of accommodation shall be the responsibility of the person on whom the law places that duty. Personal KYC, immigration, visa and conduct obligations of an occupant remain the occupant's responsibility. No allocation in this contract prevents a competent authority from proceeding against the person legally responsible under the relevant statute.",
        "Urban Local Bodies Haryana lists services for issue/renewal of trade licences and licences for lodging houses. If the use of the Premises falls within a category requiring such licence, the responsible owner/operator shall obtain and maintain the applicable licence for the period during which that regulated activity is carried on.",
        "Where a guest house/boarding house or similar commercial accommodation is operated in a residential or controlled area, the use shall remain subject to applicable development-plan/zoning policy, change-of-land-use or specific guest-house permission, building-use permission, sanctioned plan, occupation certificate and any binding society/RWA or title restrictions that cannot lawfully be waived by this Agreement.",
        f"Recorded permissions/references: Trade Licence - {clean(d.get('trade_license_no')) or 'Not recorded'}; Lodging House Licence - {clean(d.get('lodging_license_no')) or 'Not recorded'}; Guest House/CLU/Zoning Permission - {clean(d.get('guest_house_permission_no')) or 'Not recorded'}; Occupation Certificate/Building Approval - {clean(d.get('occupancy_certificate_no')) or 'Not recorded'}.",
        "A contractual permission to sublet or host through an OTA does not override a statutory prohibition, building/society restriction, planning condition or licence requirement. If a required approval is refused, suspended or withdrawn, the Parties shall promptly discuss a lawful adjustment, alternative arrangement or termination in accordance with this Agreement and applicable law.",
    ])

    section(38, "FIRE, BUILDING SAFETY, OCCUPATION AND EMERGENCY COMPLIANCE", [
        "The Premises and common areas shall be used consistently with applicable fire and building-safety requirements, including the Haryana Fire and Emergency Services Act, 2022 and rules/orders made thereunder to the extent applicable to the building classification, height, area and use.",
        "Where a Fire NOC, approval of a fire-fighting scheme, occupation certificate or other fire/building approval is legally required for the relevant property/use, the responsible owner/operator shall maintain the approval and shall not knowingly permit occupation in a manner prohibited by a competent authority.",
        f"Fire NOC / fire-safety approval reference: {clean(d.get('fire_noc_no')) or 'Not recorded / applicability to be confirmed for property classification'}.",
        "The Tenant/Guest, Corporate Client, visitors and approved sub-occupants shall not block fire exits, staircases, refuge areas or access routes; disable detectors, alarms, sprinklers or extinguishers; overload electrical circuits; store hazardous substances; or otherwise interfere with statutory fire-safety systems.",
        "Management may enter without the ordinary notice period in a genuine fire, flooding, gas/electrical hazard, medical emergency, imminent threat to life/property or pursuant to a lawful direction of police, fire services, court or other competent authority. The reason for emergency entry should be documented as soon as reasonably practicable.",
    ])

    if operating_model == "Home Stay":
        section(39, "HARYANA HOME STAY-SPECIFIC COMPLIANCE", [
            "Where the premises are operated as a Home Stay, the owner/operator shall comply with the Haryana Home Stay Scheme, 2024 and any subsequent valid amendment or replacement applicable to the unit, including registration and display requirements where the scheme applies.",
            "The owner/operator shall maintain the guest register and records required under the scheme, maintain reasonable standards of cleanliness, sanitation and hygiene, issue appropriate bills/receipts, and furnish periodic tourist information to the Tourism Department to the extent required by the scheme.",
            "For foreign tourists, the owner/operator shall also comply with the applicable foreigner-reporting process, including Form III / the earlier Form C process and any lawful intimation required to the police/Registration Officer. These obligations are in addition to, and not a substitute for, the Immigration and Foreigners Rules, 2025.",
            f"Haryana Tourism Home Stay registration reference: {clean(d.get('tourism_registration_no')) or 'Not recorded'}.",
        ])
    else:
        section(39, "HOME STAY / TOURISM REGISTRATION WHERE APPLICABLE", [
            "This clause is relevant only if the actual operating model is a Home Stay or another tourism-registration category. If not applicable, it does not create an obligation to obtain a Home Stay registration merely because it appears in this comprehensive template.",
            "If the operating model changes during the term to a Home Stay or other regulated tourism accommodation, the responsible owner/operator shall first obtain any registration, permission or approval then required and comply with guest-register, billing, tourist-information and foreign-guest reporting duties applicable to that model.",
            f"Tourism registration reference, if any: {clean(d.get('tourism_registration_no')) or 'Not applicable / not recorded'}.",
        ])

    section(40, "ELECTRONIC CONTRACTING, DIGITAL RECORDS AND EVIDENTIARY PRESERVATION", [
        "Electronic communications and electronically formed contracts are not to be treated as unenforceable solely because electronic means were used, subject to the Information Technology Act, 2000 and to any separate statutory requirement for stamping, attestation or registration of the instrument.",
        "The Parties authorise retention of authentic copies of the signed agreement, amendments, invoices, receipts, bank/UPI records, acknowledged emails, SMS/WhatsApp messages, app logs, access logs, meter readings, photographs and inspection records that are legitimately generated in the course of the relationship.",
        "Where an electronic or digital record is later relied upon in legal proceedings, the Party relying on it should preserve the original source, metadata and chain of custody to the extent reasonably possible and comply with the requirements then applicable under the Bharatiya Sakshya Adhiniyam, 2023, including section 63 and any prescribed certificate requirement for computer/electronic output where applicable.",
        "Screenshots alone should not be deliberately substituted for available original records when the original electronic message, file, device record, server log, invoice or banking record can reasonably be preserved. Nothing in this clause alters the statutory rules governing admissibility, proof, privilege or discovery.",
        "Electronic execution does not cure deficient stamp duty, lack of mandatory registration, lack of authority of a signatory or any other defect that the law requires to be satisfied independently of electronic acceptance.",
    ])

    section(41, "AUTHORITY, TITLE, REPRESENTATIONS AND NON-TRANSFER OF OWNERSHIP", [
        f"The {p1} represents that he/she/it is the owner, lawful lessor/licensor, authorised operator, management entity or otherwise has sufficient authority to grant the contractual occupation/use expressly stated in this Agreement. If signing through an agent or entity, the relevant authority should be capable of verification on reasonable request.",
        f"The {p2} acknowledges that this Agreement does not transfer ownership, title or any permanent proprietary interest in the Premises. Rights of occupation are limited to the nature, term and purpose expressly created by the selected agreement type and applicable law.",
        "A Corporate Client signatory represents that he/she is authorised to bind the Corporate Client to the obligations accepted by that entity. Corporate nomination of an occupant does not by itself transfer title or create a tenancy in favour of the employee/nominee beyond the rights expressly recorded.",
        "If a material defect in authority, title or legal right to provide the Premises is discovered and substantially prevents lawful occupation, the affected Party may seek appropriate contractual and statutory remedies, including termination/refund for the affected unused period where legally justified.",
    ])

    section(42, "ENGLISH AND HINDI VERSIONS; INTERPRETATION", [
        f"The Parties may execute or retain an English version and a Hindi version generated from the same commercial inputs. Selected precedence rule: {language_precedence}.",
        "The Hindi version is intended to communicate the same commercial bargain and legal obligations in Hindi. If a translation term is capable of more than one meaning, the document shall be interpreted in a manner that best gives effect to the specifically completed commercial particulars, signed special negotiated terms and applicable law, subject to the selected precedence rule.",
        "Amounts, dates, property identifiers, passport/visa particulars, agreement reference numbers and other factual fields should be verified against the original records because transliteration or translation must not alter those factual particulars.",
        "A Party who does not understand the language of a version should request explanation or independent translation before signing. No Party should be asked to sign a version that it materially does not understand without a reasonable opportunity for explanation.",
    ])

    section(43, "CHANGE IN LAW, SAVINGS AND COURT-READINESS", [
        "If any statute, rule, notification, order or binding direction changes after execution, the mandatory law shall prevail to the extent of inconsistency. The Parties shall, where reasonably necessary, record a written amendment that preserves the original commercial intent as closely as lawfully possible.",
        "No provision shall be interpreted as a waiver of a non-waivable consumer, tenancy, immigration, fire-safety, municipal, registration, evidence or other statutory protection. An invalid provision shall be severed or read down only to the minimum extent necessary so that the remainder can continue where legally possible.",
        "For evidentiary clarity, the Parties should maintain a complete execution set containing the signed agreement, annexures, identity/KYC references, stamp/e-stamp proof, registration endorsement if any, payment proof, possession/handover record, meter readings, inventory/condition photographs and significant notices. This is a record-preservation covenant and not a representation that every listed item is legally mandatory in every transaction.",
        "The Parties agree that claims for rent, deposit, damage, possession, injunction, specific performance, consumer relief or other remedies shall remain subject to the substantive and procedural law actually applicable at the time of the dispute. This Agreement does not predetermine a court's jurisdiction, admissibility ruling, measure of damages or grant of relief beyond what the law permits.",
    ])

    lines.append("")
    lines.append("HEALTH AND EMERGENCY INFORMATION DECLARATION")
    lines.append("The Tenant/Guest confirms that information reasonably necessary for emergency assistance, accessibility support, allergy management or safe accommodation has been disclosed truthfully. In an apparent emergency the Management may contact the recorded emergency contacts, Corporate Client, ambulance, doctor, hospital, police, fire service or another competent emergency service as reasonably appropriate. This does not make the Management a medical provider or exclude liability imposed by law.")

    lines.append("")
    lines.append("ANNEXURE A - ACCOMMODATION, PAYMENT AND FACILITY DETAILS")
    annex_a = [
        ("Tenant / Guest", clean(d.get("tenant_name")) or "________"),
        ("Corporate Client", corp or "Not Applicable"),
        ("Agreement Reference", agreement_ref),
        ("Property", property_name),
        ("Premises / Address", premises),
        ("Municipal / Property / UID Reference", clean(d.get("property_id")) or "Not recorded"),
        ("Floor / Area / Identification", clean(d.get("floor_area")) or "Not recorded"),
        ("Boundaries / Additional Identification", clean(d.get("property_boundaries")) or "Not recorded"),
        ("Operating Model", clean(d.get("operating_model")) or "Not specified"),
        ("Room / Unit No.", room),
        ("Room Type / Occupancy", room_type),
        ("Commencement Date", start),
        ("End Date", end),
        ("Confirmed Term", f"{term} months"),
        ("Lock-in / Minimum Commitment", f"{lockin} months"),
        ("Rent / Accommodation Charge", rent + " per month"),
        ("Security Deposit", deposit),
        ("Notice Period", f"{notice} days"),
        ("Grid / Mains Electricity", clean(d.get("electricity_rate")) or "As applicable"),
        ("Generator / DG Electricity", clean(d.get("genset_rate")) or "As applicable"),
        ("Included Services", clean(d.get("included_services")) or "As separately stated / Not specified"),
        ("Excluded / Chargeable Services", clean(d.get("excluded_services")) or "As stated in the Agreement"),
        ("Taxes", clean(d.get("taxes")) or "As applicable"),
        ("Controlled / Last Entry", clean(d.get("controlled_entry_time")) or "Not specified"),
        ("Subletting / Hosting", sub_policy or "As stated in Clause 11"),
        ("Relocation", relocation or "As stated in Clause 10"),
    ]
    for label, value in annex_a:
        lines.append(f"{label}: {value}")

    lines.append("")
    lines.append("ANNEXURE B - TENANT / GUEST UNDERTAKING AND QUICK HOUSE RULES")
    undertakings = [
        f"I shall use the Premises only for {purpose} and other use expressly approved in writing.",
        ("I may conduct lawful OTA / short-term hosting under Clause 11 and shall comply with KYC, occupancy, fire-safety and guest-registration duties." if ota else "I shall not assign, share, resell or sublet the Premises except as expressly permitted under Clause 11."),
        "I shall complete KYC, register occupants / visitors as required, and shall not give access credentials to an unauthorised person.",
        "I shall pay authorised charges, observe check-in / check-out, lock-in and notice terms, and return all issued items.",
        "I shall not engage in unlawful activity, create nuisance, possess prohibited items, damage property, or tamper with safety and utility systems.",
        "I shall follow visitor, quiet-hour, fire-safety, facility, internet, parking, housekeeping and emergency rules applicable to the Property.",
        "I shall promptly report material service defects, damage, safety concerns, theft or suspicious activity.",
        "I understand that serious material breach may result in lawful termination, recovery of documented loss and reporting to competent authorities where required.",
    ]
    for i, u in enumerate(undertakings, 1):
        lines.append(f"B{i}. {u}")
    lines.append(f"Tenant / Guest Signature: ______________________________  Date: __________________")

    lines.append("")
    lines.append("ANNEXURE C - CORPORATE CLIENT UNDERTAKING (IF APPLICABLE)")
    if corp:
        corp_undertakings = [
            "It shall pay sponsored or guaranteed charges according to the accepted corporate billing terms.",
            "It shall ensure that its authorised occupant receives and complies with this Agreement and Property rules.",
            "It shall promptly notify the Management if the occupant's authorisation, employment, assignment or sponsorship ends.",
            "It shall not replace, rotate or add occupants without the required prior approval and completed KYC.",
            "It shall cooperate in emergencies, investigations, payment reconciliation and orderly relocation / departure where reasonably required.",
            "It remains liable for its own obligations and any guarantee expressly given notwithstanding employee transfer, resignation or internal approval delay.",
        ]
        lines.append(f"Corporate Client: {corp}")
        for i, u in enumerate(corp_undertakings, 1):
            lines.append(f"C{i}. {u}")
    else:
        lines.append("Not Applicable unless a Corporate Client is added by a written amendment / accepted booking document signed or otherwise validly accepted by the concerned parties.")

    if extra_clauses:
        lines.append("")
        lines.append("ANNEXURE D - ADDITIONAL / CUSTOM CLAUSES")
        for i, clause in enumerate([c for c in extra_clauses if clean(c)], 1):
            lines.append(f"D{i}. {clean(clause)}")

    lines.append("")
    lines.append("ANNEXURE E - FOREIGN NATIONAL / OCI AND REGULATORY PARTICULARS")
    foreign_annex = [
        ("Client / Occupant Status", clean(d.get("foreign_status")) or "Indian citizen / not applicable"),
        ("Nationality", clean(d.get("foreign_nationality")) or "Not applicable / not recorded"),
        ("Passport Number", clean(d.get("passport_no")) or "Not applicable / not recorded"),
        ("Passport Issue / Expiry", f"{clean(d.get('passport_issue_date')) or 'Not recorded'} / {clean(d.get('passport_expiry')) or 'Not recorded'}"),
        ("Visa / OCI Number", clean(d.get("visa_oci_no")) or "Not applicable / not recorded"),
        ("Visa Type / OCI Status", clean(d.get("visa_type")) or "Not applicable / not recorded"),
        ("Visa Issue / Validity", f"{clean(d.get('visa_issue_date')) or 'Not recorded'} / {clean(d.get('visa_expiry')) or 'Not recorded'}"),
        ("Purpose of Visit", clean(d.get("purpose_of_visit")) or "Not recorded"),
        ("FRRO/FRO Registration / Permit", f"{clean(d.get('frro_registration_no')) or 'Not applicable / not recorded'}; validity: {clean(d.get('frro_validity')) or 'Not recorded'}"),
        ("Arrived From", clean(d.get("arrival_from")) or "Not recorded"),
        ("Arrival / Check-in", clean(d.get("arrival_date_time")) or "Not recorded"),
        ("Previous Place of Stay", clean(d.get("previous_place_of_stay")) or "Not recorded"),
        ("Next Destination", clean(d.get("next_destination")) or "Not recorded"),
        ("Departure / Check-out", clean(d.get("departure_date_time")) or "Not recorded"),
        ("Employer / Sponsor / Institution", clean(d.get("foreign_sponsor")) or "Not recorded"),
        ("Emergency Contact Outside India", clean(d.get("foreign_contact_abroad")) or "Not recorded"),
        ("Form III Arrival Ack / Ref", clean(d.get("form3_arrival_ack")) or "Not recorded / not applicable"),
        ("Form III Departure Ack / Ref", clean(d.get("form3_departure_ack")) or "Not recorded / not applicable"),
        ("Haryana Police Tenant/PG Verification", clean(d.get("tenant_verification_ref")) or "Not recorded / not applicable"),
        ("Trade / Lodging Licence", f"{clean(d.get('trade_license_no')) or 'Not recorded'} / {clean(d.get('lodging_license_no')) or 'Not recorded'}"),
        ("Fire / Occupation Approval", f"{clean(d.get('fire_noc_no')) or 'Not recorded'} / {clean(d.get('occupancy_certificate_no')) or 'Not recorded'}"),
        ("Guest House / CLU / Zoning Permission", clean(d.get("guest_house_permission_no")) or "Not recorded / not applicable"),
        ("Haryana Tourism Home Stay Registration", clean(d.get("tourism_registration_no")) or "Not recorded / not applicable"),
    ]
    for label, value in foreign_annex:
        lines.append(f"{label}: {value}")
    if clean(d.get("statutory_licence_notes")):
        lines.append(f"Other Regulatory Notes: {clean(d.get('statutory_licence_notes'))}")

    lines.append("")
    lines.append("EXECUTION AND SIGNATURES")
    lines.append("In witness whereof, the Parties sign / validly accept this Agreement after reviewing and completing all applicable blanks and particulars.")
    lines.append("")
    lines.append(f"{p1_cap}")
    lines.append(f"Name / Entity: {clean(d.get('landlord_entity')) or clean(d.get('landlord_name')) or '________________'}")
    lines.append(f"Authorised Signatory: {clean(d.get('authorized_signatory')) or '________________'}")
    lines.append("Signature / Seal: ______________________________    Date: __________________")
    lines.append("")
    lines.append(f"{p2_cap}")
    lines.append(f"Name: {clean(d.get('tenant_name')) or '________________'}")
    lines.append(f"Government ID: {clean(d.get('tenant_id_type')) or 'ID'} No. {clean(d.get('tenant_id_no')) or '________________'}")
    lines.append("Signature / Electronic Acceptance: ______________________________    Date: __________________")
    if corp:
        lines.append("")
        lines.append("CORPORATE CLIENT / BOOKING ENTITY")
        lines.append(f"Entity: {corp} | Authorised Representative: {clean(d.get('corporate_representative')) or '________________'}")
        lines.append("Signature / Seal / Electronic Acceptance: ______________________________    Date: __________________")
    lines.append("")
    lines.append("WITNESS 1")
    lines.append(clean(d.get("witness1")) or "Name / Address / Signature: ________________________________________________")
    lines.append("")
    lines.append("WITNESS 2")
    lines.append(clean(d.get("witness2")) or "Name / Address / Signature: ________________________________________________")
    lines.append("")
    lines.append("NOTARY ATTESTATION")
    lines.append(f"Attested before me on __________________ at {clean(d.get('place_of_execution')) or '________________'}")
    lines.append(f"Notary Name: {clean(d.get('notary_name')) or '________________'} | Registration No.: {clean(d.get('notary_reg_no')) or '________________'}")
    lines.append("Signature & Official Seal: ________________________________________________")
    return "\n".join(lines)

def _hi_agreement_type(value):
    return {
        "Comprehensive Rental Agreement": "विस्तृत किरायानामा",
        "Lease Agreement": "पट्टा अनुबंध",
        "Leave & License Agreement": "अनुज्ञप्ति एवं निवास अनुबंध",
        "Corporate Stay / Serviced Accommodation Agreement": "कॉरपोरेट निवास एवं सेवायुक्त आवास अनुबंध",
        "Commercial Hosting / OTA Agreement": "वाणिज्यिक अल्पकालिक आवास एवं ऑनलाइन बुकिंग अनुबंध",
        "Commercial Lease Agreement": "वाणिज्यिक पट्टा अनुबंध",
    }.get(clean(value), "विस्तृत किरायानामा")


def _hi_sub_policy(value):
    return {
        "Prohibited without prior written approval": "पूर्व लिखित स्वीकृति के बिना हस्तांतरण, साझेदारी अथवा उपकिरायेदारी निषिद्ध होगी",
        "Allowed only for a specifically approved replacement / sub-occupant": "केवल लिखित रूप से अनुमोदित प्रतिस्थापन अथवा सह-अधिभोगी के लिए अनुमति होगी",
        "Corporate nominee / employee substitution only with prior approval and fresh KYC": "कॉरपोरेट नामित व्यक्ति/कर्मचारी का परिवर्तन केवल पूर्व स्वीकृति एवं नवीन केवाईसी के बाद होगा",
        "OTA / short-term hosting expressly permitted without per-booking approval": "ऑनलाइन ट्रैवल एजेंसी/अल्पकालिक आवास हेतु प्रत्येक बुकिंग पर अलग स्वीकृति के बिना स्पष्ट अनुमति होगी",
    }.get(clean(value), clean(value) or "पूर्व लिखित स्वीकृति के बिना उपकिरायेदारी निषिद्ध होगी")


def _hi_relocation_policy(value):
    return {
        "No relocation without Tenant/Guest's prior written consent": "किरायेदार/अतिथि की पूर्व लिखित सहमति के बिना कक्ष/इकाई परिवर्तन नहीं होगा",
        "Emergency relocation only; otherwise prior written consent required": "केवल वास्तविक आपातकाल में वैकल्पिक व्यवस्था की जा सकेगी; अन्यथा पूर्व लिखित सहमति आवश्यक होगी",
        "Management may relocate for maintenance, safety or operational continuity to an equivalent or higher category": "रखरखाव, सुरक्षा या संचालन निरंतरता हेतु समान अथवा उच्च श्रेणी की इकाई में उचित स्थानांतरण किया जा सकेगा",
    }.get(clean(value), clean(value) or "इस अनुबंध के अनुसार")


def _hi_foreign_status(value):
    return {
        "Indian citizen / no foreign-national reporting": "भारतीय नागरिक / विदेशी नागरिक रिपोर्टिंग लागू नहीं",
        "Foreign national": "विदेशी नागरिक",
        "OCI Cardholder": "ओसीआई कार्डधारक",
        "Mixed / group booking including foreign nationals or OCI Cardholders": "मिश्रित/समूह बुकिंग जिसमें विदेशी नागरिक अथवा ओसीआई कार्डधारक शामिल हैं",
    }.get(clean(value), clean(value) or "भारतीय नागरिक / लागू नहीं")


def _hi_operating_model(value):
    return {
        "Private residential tenancy": "निजी आवासीय किरायेदारी",
        "Paying Guest / PG accommodation": "पेइंग गेस्ट / पीजी आवास",
        "Corporate stay / serviced apartment": "कॉरपोरेट निवास / सेवायुक्त अपार्टमेंट",
        "Hotel / guest house / lodging house": "होटल / गेस्ट हाउस / लॉजिंग हाउस",
        "Home Stay": "होम स्टे",
        "OTA / short-term serviced accommodation": "ऑनलाइन बुकिंग / अल्पकालिक सेवायुक्त आवास",
        "Commercial premises": "वाणिज्यिक परिसर",
    }.get(clean(value), clean(value) or "निजी आवासीय किरायेदारी")


def _hi_language_precedence(value):
    return {
        "English version prevails in case of inconsistency": "किसी असंगति की स्थिति में अंग्रेज़ी संस्करण प्रभावी होगा",
        "Hindi version prevails in case of inconsistency": "किसी असंगति की स्थिति में हिंदी संस्करण प्रभावी होगा",
        "Both versions to be read together; signed special terms prevail": "दोनों संस्करण साथ पढ़े जाएंगे; हस्ताक्षरित विशेष शर्तें सर्वोपरि होंगी",
    }.get(clean(value), "किसी असंगति की स्थिति में अंग्रेज़ी संस्करण प्रभावी होगा")


def _hi_purpose(value):
    return {
        "Lawful residential use only": "केवल वैध आवासीय उपयोग",
        "Student residential accommodation only": "केवल छात्र आवासीय उपयोग",
        "Lawful serviced accommodation / corporate residential stay": "वैध सेवायुक्त आवास / कॉरपोरेट आवासीय निवास",
        "Lawful serviced accommodation and short-term OTA hosting": "वैध सेवायुक्त आवास एवं अल्पकालिक ऑनलाइन बुकिंग आवास",
        "Lawful residential / licensed occupation": "वैध आवासीय / अनुज्ञप्ति आधारित अधिभोग",
        "Lawful commercial use subject to licences, approvals, building and fire-safety requirements": "आवश्यक लाइसेंस, अनुमतियों, भवन एवं अग्नि-सुरक्षा मानकों के अधीन वैध वाणिज्यिक उपयोग",
    }.get(clean(value), clean(value) or "वैध उपयोग")


def _hi_amount(value):
    v = clean(value) or "________"
    return f"रु. {v}/-"


def build_agreement_text_hindi(d, extra_clauses=None):
    extra_clauses = extra_clauses or []
    typ = clean(d.get("agreement_type")) or "Comprehensive Rental Agreement"
    template_name = infer_template_name(d)
    format_profile = FORMAT_PROFILES.get(template_name, FORMAT_PROFILES["Strong Residential - 11 Months"])
    hi_typ = _hi_agreement_type(typ)
    term = clean(d.get("term_months")) or "________"
    start = clean(d.get("start_date")) or "________"
    end = clean(d.get("end_date")) or "________"
    lockin = clean(d.get("lockin_months")) or "0"
    notice = clean(d.get("notice_days")) or "30"
    rent = _hi_amount(d.get("monthly_rent"))
    deposit = _hi_amount(d.get("security_deposit"))
    due_day = clean(d.get("due_day")) or "________"
    inc = clean(d.get("increment_percent"))
    inc_after = clean(d.get("increment_after_months"))
    access_hours = clean(d.get("access_notice_hours")) or "24"
    refund_days = clean(d.get("deposit_refund_days")) or "15"
    util_days = clean(d.get("utility_due_days")) or "3"
    premises = clean(d.get("premises")) or "________________________________________"
    property_name = clean(d.get("property_name")) or "संपत्ति"
    room = clean(d.get("room_unit_no")) or "________"
    room_type = clean(d.get("room_type")) or "परिशिष्ट-क के अनुसार"
    purpose = _hi_purpose(d.get("purpose"))
    corp = clean(d.get("corporate_name"))
    operating_model = _hi_operating_model(d.get("operating_model"))
    foreign_status = _hi_foreign_status(d.get("foreign_status"))
    sub_policy = _hi_sub_policy(d.get("subletting_policy"))
    relocation = _hi_relocation_policy(d.get("relocation_policy"))
    lang_rule = _hi_language_precedence(d.get("language_precedence"))
    jur = clean(d.get("jurisdiction")) or clean(d.get("place_of_execution")) or "गुरुग्राम, हरियाणा के सक्षम न्यायालय/प्राधिकरण"
    ota = is_ota_enabled(d)

    landlord_name = clean(d.get("landlord_entity")) or clean(d.get("landlord_name")) or "________________"
    tenant_name = clean(d.get("tenant_name")) or "________________"
    landlord_desc = party_description(d, "landlord", "________________")
    tenant_desc = party_description(d, "tenant", "________________")

    lines = []
    lines.append(format_profile["title_hi"])
    lines.append(format_profile["subtitle_hi"])
    lines.append("")
    lines.append(f"अनुबंध/बुकिंग संदर्भ: {clean(d.get('agreement_reference')) or '________'}")
    lines.append(f"अनुबंध दिनांक: {clean(d.get('agreement_date')) or '________'} | निष्पादन स्थान: {clean(d.get('place_of_execution')) or '________'} | अवधि: {term} माह | लॉक-इन: {lockin} माह")
    lines.append("")
    lines.append("स्टाम्प / ई-स्टाम्प एवं नोटरी विवरण")
    lines.append(f"स्टाम्प / ई-स्टाम्प संख्या: {clean(d.get('stamp_number')) or '________________'} | मूल्य / शुल्क: {('रु. ' + clean(d.get('stamp_value'))) if clean(d.get('stamp_value')) else '________________'}")
    lines.append(f"नोटरी का नाम: {clean(d.get('notary_name')) or '________________'} | पंजीकरण संख्या: {clean(d.get('notary_reg_no')) or '________________'}")
    lines.append("")
    lines.append(f"यह अनुबंध दिनांक {clean(d.get('agreement_date')) or '________'} को {clean(d.get('place_of_execution')) or '________'} में निष्पादित किया गया।")
    lines.append("")
    lines.append("प्रथम पक्ष / मकान-मालिक / प्रबंधन")
    lines.append(f"{landlord_desc}; संस्था/प्रबंधन: {clean(d.get('landlord_entity')) or 'लागू नहीं'}; मोबाइल: {clean(d.get('landlord_mobile')) or '________'}; ई-मेल: {clean(d.get('landlord_email')) or '________'}; पैन: {clean(d.get('landlord_pan')) or '________'}; अधिकृत हस्ताक्षरकर्ता: {clean(d.get('authorized_signatory')) or '________'}। आगे इसे संदर्भानुसार 'प्रथम पक्ष/प्रबंधन' कहा जाएगा।")
    lines.append("")
    lines.append("द्वितीय पक्ष / किरायेदार / अतिथि")
    lines.append(f"{tenant_desc}; जन्मतिथि: {clean(d.get('tenant_dob')) or '________'}; मोबाइल: {clean(d.get('tenant_mobile')) or '________'}; व्हाट्सऐप: {clean(d.get('tenant_whatsapp')) or clean(d.get('tenant_mobile')) or '________'}; ई-मेल: {clean(d.get('tenant_email')) or '________'}। आगे इसे संदर्भानुसार 'द्वितीय पक्ष/किरायेदार/अतिथि' कहा जाएगा।")
    if corp:
        lines.append("")
        lines.append("कॉरपोरेट ग्राहक / बुकिंग संस्था (यदि लागू हो)")
        lines.append(f"{corp}, पंजीकृत/बिलिंग पता: {clean(d.get('corporate_address')) or '________'}, जीएसटीआईएन: {clean(d.get('corporate_gstin')) or '________'}, पैन: {clean(d.get('corporate_pan')) or '________'}, प्रतिनिधि: {clean(d.get('corporate_representative')) or '________'} ({clean(d.get('corporate_designation')) or 'अधिकृत प्रतिनिधि'}), मोबाइल: {clean(d.get('corporate_mobile')) or '________'}, ई-मेल: {clean(d.get('corporate_email')) or '________'}।")
    lines.append("")
    lines.append("मुख्य वाणिज्यिक विवरण")
    lines.append(f"संपत्ति: {property_name} | पूरा पता: {premises} | कक्ष/इकाई: {room} | श्रेणी: {room_type} | संचालन मॉडल: {operating_model}")
    lines.append(f"प्रारम्भ: {start} | समाप्ति: {end} | अवधि: {term} माह | लॉक-इन: {lockin} माह | खाली करने की पूर्व सूचना: {notice} दिन")
    lines.append(f"मासिक किराया/अनुज्ञप्ति शुल्क: {rent} | सुरक्षा जमा: {deposit} | भुगतान की नियत तिथि/दिन: {due_day}")
    if inc:
        lines.append(f"किराया वृद्धि: नवीनीकरण/विस्तार अथवा निर्धारित अवधि के बाद निरंतर अधिभोग की स्थिति में {inc_after or 'निर्धारित'} माह के बाद {inc}% वृद्धि, जब तक पक्ष लिखित रूप से अन्यथा सहमत न हों।")
    lines.append(f"ग्रिड/मुख्य विद्युत: {clean(d.get('electricity_rate')) or 'सहमति/वास्तविक मीटर के अनुसार'} | जनरेटर/डीजी: {clean(d.get('genset_rate')) or 'सहमति/वास्तविक मीटर के अनुसार'}")
    lines.append(f"अनुमत उपयोग: {purpose}")
    lines.append("")
    lines.append("चयनित अनुबंध प्रारूप")
    lines.append(f"टेम्पलेट / प्रीसेट: {template_name}। नीचे की संरचना और प्रारूप-विशिष्ट शर्तें इसी चयन के अनुसार उत्पन्न की गई हैं।")
    lines.append("")
    lines.append("विशेष सहमत शर्तें - सामान्य गृह नियमों पर वरीयता")
    special = list(format_profile.get("special_hi", [])) + [
        f"लॉक-इन अवधि {lockin} माह तथा खाली करने की पूर्व सूचना {notice} दिन होगी। केवल सूचना देना शेष लॉक-इन को स्वतः समाप्त नहीं करेगा, जब तक लिखित सहमति अथवा लागू कानून अन्यथा न कहे।",
        f"हस्तांतरण/साझेदारी/उपकिरायेदारी नीति: {sub_policy}।",
        f"कक्ष/इकाई परिवर्तन नीति: {relocation}।",
        f"वास्तविक आपातकाल, तात्कालिक सुरक्षा/कल्याण आवश्यकता, गंभीर संदिग्ध अवैध गतिविधि अथवा सक्षम प्राधिकारी के विधिसम्मत आदेश को छोड़कर सामान्य प्रवेश से कम से कम {access_hours} घंटे पहले सूचना दी जाएगी और उद्देश्य तथा अनुमानित समय बताया जाएगा।",
        f"हस्तांतरण, चाबी/एक्सेस डिवाइस वापसी, अंतिम निरीक्षण एवं देयताओं के समायोजन के बाद सुरक्षा जमा की निर्विवाद शेष राशि सामान्यतः {refund_days} कार्यदिवस के भीतर लौटाई/प्रक्रियाबद्ध की जाएगी।",
        "स्थिर वाणिज्यिक शर्तें एकतरफा परिवर्तित नहीं की जाएंगी, सिवाय अनिवार्य विधिक/कर परिवर्तन, पक्षों द्वारा लिखित संशोधन या इस अनुबंध में स्पष्ट रूप से अनुमत स्थिति के।",
    ]
    if clean(d.get("deposit_interest_rate")) not in ("", "0", "0.0"):
        special.append(f"निर्धारित वापसी अवधि के बाद भी निर्विवाद सुरक्षा जमा बकाया रहने पर, प्रलेखित वास्तविक विवाद/न्यायालय आदेश/बैंकिंग बाधा को छोड़कर, {clean(d.get('deposit_interest_rate'))}% वार्षिक साधारण ब्याज लागू होगा।")
    for item in split_special_terms(d.get("special_terms")):
        special.append(item.lstrip("-* "))
    for i, item in enumerate(special, 1):
        lines.append(f"वि.{i} {item}")

    def sec(n, title, clauses):
        lines.append("")
        lines.append(f"{n}. {title}")
        for j, clause in enumerate(clauses, 1):
            if clause:
                lines.append(f"{n}.{j} {clause}")

    sec(1, "परिभाषाएँ, उद्देश्य और स्वीकृति", [
        f"'परिसर/आवास' से आशय {property_name}, पता {premises}, कक्ष/इकाई {room} तथा केवल उन सुविधाओं से है जो इस अनुबंध, परिशिष्ट-क या स्वीकृत बुकिंग पुष्टि में स्पष्ट रूप से सम्मिलित हैं।",
        "'बुकिंग पुष्टि' में स्वीकृत कोटेशन, आरक्षण पुष्टि, कॉरपोरेट दर-पत्र, लिखित रूप से स्वीकृत खरीद आदेश, चालान, ऐप/सिस्टम रिकॉर्ड अथवा अन्य लिखित रिकॉर्ड सम्मिलित होगा जिससे तिथियाँ, शुल्क, अधिभोग और सुविधाएँ ज्ञात हों।",
        "पक्ष यह स्वीकार करते हैं कि अनुबंध को पढ़ने, समझने और प्रश्न पूछने का उचित अवसर मिला है तथा कोई भी पक्ष ऐसी मौखिक बात पर निर्भर नहीं करेगा जिसे अंतिम लिखित अनुबंध में शामिल नहीं किया गया है।",
        "चेक-इन, कब्जा और निरंतर अधिभोग वैध पहचान, देय भुगतान, वैध उपयोग, सुरक्षा नियमों तथा लागू वैधानिक आवश्यकताओं के पालन पर निर्भर रहेगा।",
    ])
    sec(2, "परिसर, पहचान और वाणिज्यिक विवरण", [
        f"संपत्ति का नाम {property_name}; पूरा पता {premises}; कक्ष/इकाई {room}; श्रेणी {room_type}; संपत्ति/नगरपालिका संदर्भ {clean(d.get('property_id')) or 'दर्ज नहीं'}; तल/क्षेत्र विवरण {clean(d.get('floor_area')) or 'दर्ज नहीं'}।",
        f"प्रारम्भ दिनांक {start} तथा समाप्ति दिनांक {end} है। निर्धारित अवधि {term} माह है। निरंतर अधिभोग केवल लिखित नवीनीकरण/विस्तार के आधार पर होगा।",
        f"अनुमत अधिभोग सीमा: {clean(d.get('occupancy_limit')) or 'कानून/भवन नियमों के अनुसार'}। सीमा से अधिक व्यक्तियों को ठहराना अथवा अनधिकृत व्यक्ति को स्थायी कब्जा देना निषिद्ध है।",
        f"परिसर का अनुमत उद्देश्य {purpose} है। उपयोग का वास्तविक स्वरूप चयनित संचालन मॉडल '{operating_model}' और लागू अनुमति/लाइसेंस के अनुरूप रहना आवश्यक है।",
    ])
    sec(3, "अधिभोग का स्वरूप, स्वामित्व और शांतिपूर्ण उपयोग", [
        "यह अनुबंध स्वामित्व का हस्तांतरण नहीं करता। द्वितीय पक्ष को केवल अनुबंध के प्रकार, अवधि, उद्देश्य और लागू कानून से उत्पन्न सीमित अधिकार प्राप्त होंगे।",
        "प्रथम पक्ष उचित किराया/शुल्क भुगतान और अनुबंध पालन की स्थिति में द्वितीय पक्ष के वैध एवं शांतिपूर्ण उपयोग में अनावश्यक हस्तक्षेप नहीं करेगा, सिवाय सुरक्षा, रखरखाव, आपातकाल, वैधानिक निरीक्षण या विधिसम्मत प्रवर्तन के।",
        "समाप्ति/वैध निरस्तीकरण के बाद कब्जा जारी रखने का कोई स्वतः अधिकार नहीं होगा। किसी भी होल्डओवर की शर्तें लिखित सहमति अथवा लागू कानून से निर्धारित होंगी।",
        "किसी गैर-त्याज्य वैधानिक अधिकार को इस अनुबंध की भाषा से समाप्त या कम नहीं माना जाएगा।",
    ])
    sec(4, "अवधि, लॉक-इन, विस्तार और होल्डओवर", [
        f"अनुबंध {start} से प्रारम्भ होकर {end} तक रहेगा, जब तक वैध रूप से पहले समाप्त या लिखित रूप में विस्तारित न किया जाए।",
        f"न्यूनतम प्रतिबद्ध/लॉक-इन अवधि {lockin} माह है। लॉक-इन के दौरान समयपूर्व निकास पर केवल वही वास्तविक/सहमति-आधारित राशि वसूल की जा सकेगी जो अनुबंध और कानून के अनुसार विधिसम्मत हो।",
        f"खाली करने के लिए कम से कम {notice} दिन की लिखित पूर्व सूचना देनी होगी। सूचना अवधि का पालन लॉक-इन के शेष दायित्व को स्वतः समाप्त नहीं करता।",
        "अवधि बढ़ाने का अनुरोध समाप्ति से पूर्व किया जाना चाहिए और वह केवल लिखित स्वीकृति, संशोधित शुल्क/कर तथा आवश्यक भुगतान/क्रेडिट स्वीकृति के बाद प्रभावी होगा।",
        "अनधिकृत होल्डओवर पर लागू दैनिक/अनुपातिक शुल्क, दस्तावेजित हानि और विधिसम्मत वसूली की जा सकेगी; आत्म-सहायता द्वारा अवैध बेदखली अनुमत नहीं है।",
    ])
    sec(5, "किराया/आवास शुल्क, कर और भुगतान", [
        f"मासिक किराया/आवास शुल्क {rent} होगा और प्रत्येक माह के {due_day} दिन तक अथवा स्वीकृत बिलिंग व्यवस्था के अनुसार देय होगा।",
        f"अनुग्रह अवधि, यदि लागू हो: {clean(d.get('grace_days')) or '0'} दिन। विलम्ब शुल्क: {clean(d.get('late_fee')) or 'अनुबंध/कानून के अनुसार'}। कोई भी विलम्ब शुल्क अत्यधिक दंडात्मक नहीं होगा और लागू कानून के अधीन रहेगा।",
        f"कर/वैधानिक शुल्क: {clean(d.get('taxes')) or 'लागू कानून के अनुसार'}। सुविधा/रखरखाव शुल्क: {clean(d.get('maintenance')) or 'परिशिष्ट-क के अनुसार'}।",
        "भुगतान अधिकृत माध्यम से और रसीद/चालान/सिस्टम रिकॉर्ड के विरुद्ध किया जाएगा। किसी अनधिकृत व्यक्ति को भुगतान तब तक दायित्व समाप्त नहीं करेगा जब तक प्रथम पक्ष उसे स्वीकार न कर ले।",
        "चालान में विवाद होने पर विवादित मद शीघ्र लिखित रूप से बताई जाएगी; निर्विवाद राशि नियत समय पर देय रहेगी।",
    ])
    sec(6, "कॉरपोरेट बिलिंग, प्रायोजन और कर कटौती", [
        "जहाँ कॉरपोरेट ग्राहक बुकिंग प्रायोजित/गारंटी करता है, वह केवल उन शुल्कों के लिए उत्तरदायी होगा जिन्हें उसने लिखित रूप से स्वीकार, प्रायोजित या गारंटी किया है।",
        "कॉरपोरेट ग्राहक की आंतरिक खरीद आदेश या अनुमोदन प्रक्रिया किसी विधिसम्मत एवं पहले से स्वीकृत चालान की देयता को स्वतः स्थगित नहीं करेगी।",
        "व्यक्तिगत खर्च, अनधिकृत विस्तार, व्यक्तिगत क्षति, निषिद्ध आचरण या कॉरपोरेट द्वारा अस्वीकृत अतिरिक्त सेवाएँ संबंधित अतिथि/किरायेदार द्वारा देय होंगी, जब तक लिखित गारंटी अन्यथा न कहे।",
        "स्रोत पर कर कटौती केवल विधिक आवश्यकता होने पर की जाएगी और संबंधित प्रमाणपत्र/समायोजन विवरण समय पर उपलब्ध कराया जाएगा।",
    ])
    sec(7, "सुरक्षा जमा, कटौती और अंतिम समायोजन", [
        f"सुरक्षा जमा {deposit} होगा। यह नियमित मासिक किराये का अग्रिम भुगतान नहीं माना जाएगा जब तक पक्ष लिखित रूप से समायोजन स्वीकार न करें।",
        "कटौती केवल वास्तविक और विधिसम्मत देयताओं, बकाया किराया/बिजली, गायब वस्तु, चाबी/कार्ड प्रतिस्थापन, असामान्य सफाई अथवा सामान्य घिसावट से परे प्रमाणित क्षति के लिए की जाएगी।",
        "जहाँ व्यावहारिक हो, क्षति कटौती फोटो, निरीक्षण नोट, बिल, चालान, प्रतिस्थापन कोटेशन अथवा अन्य सत्यापन योग्य विवरण से समर्थित होगी और सामान्य घिसावट को क्षति नहीं माना जाएगा।",
        f"चाबी/एक्सेस डिवाइस वापसी, अंतिम निरीक्षण तथा निर्विवाद देयताओं के समायोजन के बाद शेष सुरक्षा जमा सामान्यतः {refund_days} कार्यदिवस में लौटाया/प्रक्रियाबद्ध किया जाएगा।",
        "सुरक्षा जमा का अनुचित रोकना या अनुबंध से परे स्वचालित जब्ती मान्य नहीं होगी; किसी वास्तविक विवाद को लिखित कारण और उपलब्ध दस्तावेजों के साथ बताया जाएगा।",
    ])
    sec(8, "रद्दीकरण, समयपूर्व प्रस्थान और धनवापसी", [
        "बुकिंग/अनुबंध के समय स्वीकृत रद्दीकरण, नो-शो और समयपूर्व निकास नीति इस अनुबंध का भाग होगी, परन्तु वह लागू कानून के अधीन रहेगी।",
        "लॉक-इन के दौरान समयपूर्व निकास पर नोटिस-शॉर्टफॉल, वास्तविक नुकसान या अनुबंधित प्रतिबद्धता की विधिसम्मत राशि ली जा सकती है, परन्तु अनुचित या कानून-विरुद्ध दंड नहीं लगाया जाएगा।",
        "केवल सुविधा का उपयोग न करना, यात्रा पर रहना या अस्थायी अनुपस्थिति सामान्यतः किराया कम करने का आधार नहीं होगा, जब तक लिखित रूप से अन्यथा न हो।",
        "यदि प्रथम पक्ष बिना द्वितीय पक्ष की गलती के पुष्टि किया गया परिसर उपलब्ध न करा सके और उचित वैकल्पिक व्यवस्था भी उपलब्ध न हो, तो प्रभावित अप्रयुक्त अवधि की राशि कानून/स्वीकृत शर्तों के अनुसार लौटाई या समायोजित की जाएगी।",
    ])
    sec(9, "विद्युत, उपयोगिताएँ, मीटर और उपकरण", [
        f"ग्रिड/मुख्य विद्युत: {clean(d.get('electricity_rate')) or 'वास्तविक मीटर एवं सहमत दर के अनुसार'}। जनरेटर/डीजी: {clean(d.get('genset_rate')) or 'वास्तविक मीटर एवं सहमत दर के अनुसार'}।",
        f"अलग उपयोगिता चालान सामान्यतः {util_days} दिन के भीतर अथवा लिखित रूप से सहमत अवधि में देय होगा।",
        "मीटर खराब/अप्राप्य/अविश्वसनीय होने पर, मीटर ठीक होने तक पूर्व तुलनीय खपत, उपकरण भार या अन्य युक्तिसंगत साक्ष्य के आधार पर निष्पक्ष अंतरिम बिलिंग की जा सकेगी।",
        "मीटर, सील, वायरिंग, अग्नि उपकरण, प्लम्बिंग, नेटवर्क या भवन सेवाओं से छेड़छाड़ निषिद्ध है और वास्तविक हानि/सुरक्षा कार्रवाई/वैध समाप्ति का कारण बन सकती है।",
        "उच्च-लोड उपकरण, हीटर, इंडक्शन, अतिरिक्त राउटर/बूस्टर या खाना पकाने के उपकरण केवल स्वीकृति/सुरक्षा नियम के अनुसार उपयोग किए जाएंगे।",
    ])
    sec(10, "कक्ष/इकाई आवंटन, अधिभोग और स्थानांतरण", [
        f"कक्ष/इकाई {room} का आवंटन किया गया है। स्थानांतरण नीति: {relocation}।",
        "किसी भी स्थानांतरण में सुरक्षा, रखरखाव, उपलब्धता और लिखित/स्पष्ट सहमति की आवश्यकता चयनित नीति के अनुसार लागू होगी। जहाँ उचित हो, वैकल्पिक इकाई समान या उच्च श्रेणी की होगी और बिना सहमति अतिरिक्त कमरे का शुल्क नहीं लगेगा।",
        "अधिभोग सीमा का उल्लंघन, अनधिकृत कक्ष परिवर्तन या किसी अन्य व्यक्ति को स्थायी कब्जा देना गंभीर उल्लंघन माना जा सकता है।",
        "वास्तविक आपातकाल में अस्थायी व्यवस्था आवश्यक हो सकती है, परन्तु आपातकाल समाप्त होने पर स्थिति और आगे की व्यवस्था लिखित रूप से स्पष्ट की जाएगी।",
    ])
    sec(11, "हस्तांतरण, साझेदारी, उपकिरायेदारी और ऑनलाइन आवास", [
        f"चयनित नीति: {sub_policy}।",
        "जहाँ उपकिरायेदारी/साझेदारी निषिद्ध है, द्वितीय पक्ष किसी तीसरे व्यक्ति को भुगतान अथवा अन्यथा परिसर का कब्जा, लाइसेंस, पुनर्बुकिंग या नियंत्रण नहीं देगा बिना आवश्यक लिखित स्वीकृति के।",
        "जहाँ ऑनलाइन/अल्पकालिक आवास स्पष्ट रूप से अनुमत है, प्रत्येक अतिथि की वैध पहचान, विदेशी नागरिक रिपोर्टिंग, अधिभोग सीमा, अग्नि-सुरक्षा, भवन/सोसायटी नियम और अन्य गैर-त्याज्य कानूनी आवश्यकताएँ फिर भी लागू रहेंगी।",
        "अनुमोदित सह-अधिभोगी/अल्पकालिक अतिथि को मूल किरायेदार से अधिक स्थायी अधिकार प्राप्त नहीं होगा और मूल पक्ष अपनी भुगतान/क्षति/आचरण जिम्मेदारियों से तब तक मुक्त नहीं होगा जब तक लिखित रूप से स्पष्ट विमोचन न दिया जाए।",
        "किसी अनुबंधित ऑनलाइन बुकिंग की अनुमति नगरपालिका, योजना, पर्यटन, अग्नि, सोसायटी या अन्य वैधानिक अनुमति की कमी को स्वतः ठीक नहीं करती।",
    ])
    sec(12, "चेक-इन, केवाईसी और पहचान", [
        "चेक-इन वैध पहचान और आवश्यक भुगतान/हस्ताक्षर औपचारिकताओं के अधीन होगा। पहचान दस्तावेज केवल वैध उद्देश्य और लागू कानून के अनुसार लिए/संग्रहीत किए जाएंगे।",
        "आधार विवरण का उपयोग केवल वैधानिक रूप से अनुमत प्रक्रिया में किया जाएगा; जहाँ कानून अनुमति देता हो वहाँ अन्य वैध सरकारी पहचान स्वीकार की जा सकती है।",
        "विदेशी नागरिक/ओसीआई के लिए पासपोर्ट, वीज़ा/ओसीआई, संपर्क, यात्रा और अन्य वैधानिक विवरण धारा 35 के अनुसार आवश्यक होंगे।",
        "झूठे, परिवर्तित, समाप्त अथवा भ्रामक दस्तावेज चेक-इन अस्वीकृति, वैध समाप्ति और सक्षम प्राधिकारी को रिपोर्ट करने का आधार हो सकते हैं।",
    ])
    sec(13, "चेक-आउट, नोटिस, चाबी और निकास औपचारिकताएँ", [
        f"खाली करने से कम से कम {notice} दिन पूर्व लिखित नोटिस दिया जाएगा, जब तक विशेष लिखित शर्त अन्यथा न हो।",
        "चेक-आउट पर निजी सामान हटाना, चाबी/कार्ड/रिमोट लौटाना, अंतिम निरीक्षण की अनुमति देना और निर्विवाद देयताओं का भुगतान करना होगा।",
        "छूटी हुई वस्तुएँ लागू लॉस्ट-एंड-फाउंड नीति और कानून के अनुसार रखी/भेजी/निस्तारित की जा सकती हैं; उचित भंडारण/कूरियर लागत ली जा सकती है।",
        "चेक-आउट पूरा होना ऐसी छिपी/बाद में उचित निरीक्षण में मिली क्षति की जिम्मेदारी समाप्त नहीं करता जो वास्तव में द्वितीय पक्ष से संबंधित सिद्ध हो।",
    ])
    sec(14, "प्रवेश नियंत्रण और प्रबंधन का प्रवेश", [
        "चाबी, कार्ड, पासवर्ड और डिजिटल एक्सेस का सुरक्षित उपयोग करना द्वितीय पक्ष की जिम्मेदारी है।",
        f"सामान्य गैर-आपातकालीन प्रवेश से कम से कम {access_hours} घंटे पूर्व सूचना देना, उद्देश्य और अनुमानित समय बताना और युक्तिसंगत समय पर न्यूनतम हस्तक्षेप के साथ प्रवेश करना अपेक्षित होगा।",
        "वास्तविक अग्नि, बाढ़, गैस/विद्युत खतरा, गंभीर चिकित्सा/कल्याण चिंता, तात्कालिक संपत्ति हानि अथवा सक्षम प्राधिकारी के विधिसम्मत आदेश में पूर्व सूचना के बिना प्रवेश किया जा सकता है।",
        "द्वितीय पक्ष ऐसा अतिरिक्त ताला नहीं लगाएगा जिससे विधिसम्मत आपातकालीन प्रवेश असंभव हो जाए।",
    ])
    sec(15, "अतिथि, अतिरिक्त अधिभोगी और आगंतुक", [
        "आगंतुकों का प्रवेश सुरक्षा, पहचान, समय और अधिभोग नियमों के अधीन होगा।",
        "अनुमोदित/पंजीकृत अतिरिक्त अधिभोगी या ऑनलाइन अतिथि, जहाँ धारा 11 के अनुसार अनुमति है, अपने प्रवास के दौरान सभी लागू सुरक्षा, केवाईसी और गृह नियमों का पालन करेंगे।",
        "द्वितीय पक्ष अपने द्वारा बुलाए/अनुमत व्यक्ति के आचरण और उससे सिद्ध हुई क्षति के लिए इस अनुबंध की सीमा तक जिम्मेदार रहेगा।",
        "भीड़, उत्पात, अवैध गतिविधि, झूठी पहचान, सुरक्षा खतरे या स्पष्ट नियम उल्लंघन की स्थिति में आगंतुक प्रवेश रोका/समाप्त किया जा सकता है।",
    ])
    sec(16, "सफाई, रखरखाव और परिसर की देखभाल", [
        "सफाई/लिनेन/हाउसकीपिंग केवल स्वीकृत सेवा योजना के अनुसार उपलब्ध होगी। 'डू नॉट डिस्टर्ब' सामान्य सेवा को टाल सकता है पर वास्तविक आपातकाल या आवश्यक मरम्मत को नहीं।",
        "लीकेज, विद्युत दोष, कीट, टूट-फूट, असुरक्षित स्थिति या उपकरण खराबी शीघ्र रिपोर्ट की जाएगी और आगे नुकसान रोकने के लिए युक्तिसंगत कदम उठाए जाएंगे।",
        "फर्नीचर, उपकरण, फिटिंग, दीवार, पेंट, सजावट या स्थायी संरचना बिना स्वीकृति नहीं हटाई/बदली/ड्रिल/पेस्ट की जाएगी।",
        "बालकनी, अग्नि निकास, सीढ़ी और सेवा क्षेत्र में असुरक्षित भंडारण निषिद्ध होगा।",
    ])
    sec(17, "सुविधाएँ, इंटरनेट, भोजन, लॉन्ड्री, पार्किंग और तृतीय-पक्ष सेवाएँ", [
        f"सम्मिलित सुविधाएँ: {clean(d.get('included_services')) or 'स्वीकृत बुकिंग/परिशिष्ट के अनुसार'}। अतिरिक्त/प्रभारित सेवाएँ: {clean(d.get('excluded_services')) or 'इस अनुबंध/परिशिष्ट के अनुसार'}।",
        "वाई-फाई उपलब्धता और उचित उपयोग के आधार पर है; प्रत्येक उपकरण/कॉरपोरेट नेटवर्क के लिए निरंतर गति की गारंटी नहीं है। अवैध नेटवर्क उपयोग, मैलवेयर, क्रिप्टो-माइनिंग या सेवा बाधित करना निषिद्ध है।",
        "भोजन योजना/रूम सर्विस/लॉन्ड्री/परिवहन केवल शामिल योजना और समय के अनुसार होंगे। स्वतंत्र सेवा प्रदाता के कार्य के लिए प्रबंधन केवल कानून द्वारा लगाए गए दायित्व की सीमा तक जिम्मेदार होगा।",
        "पार्किंग उपलब्धता, पंजीकरण और संपत्ति नियमों के अधीन है। वाहन/अंदर की वस्तुएँ मालिक के जोखिम पर रहेंगी, सिवाय सिद्ध लापरवाही या कानून द्वारा अन्यथा निर्धारित स्थिति के।",
    ])
    sec(18, "आचरण, शांतिपूर्ण उपयोग और अनुमत गतिविधि", [
        "द्वितीय पक्ष, आगंतुक और अधिभोगी पड़ोसियों, अन्य अतिथियों और कर्मचारियों के प्रति वैध एवं सम्मानजनक व्यवहार करेंगे और उत्पात, धमकी, हिंसा, उत्पीड़न, अवरोध या अत्यधिक शोर नहीं करेंगे।",
        "सेवा/कर्मचारी शिकायतें आधिकारिक चैनल से की जाएंगी। शिकायत करने का अधिकार सुरक्षित है, पर हिंसक/धमकीपूर्ण व्यवहार स्वीकार्य नहीं होगा।",
        f"परिसर का उपयोग केवल {purpose} तथा स्पष्ट रूप से स्वीकृत सहायक गतिविधि के लिए होगा।",
        "बिना लिखित स्वीकृति और आवश्यक वैधानिक अनुमति के सार्वजनिक कार्यक्रम, व्यावसायिक शूट, फिल्मांकन, पार्टी, प्रचार कार्यक्रम, क्लिनिक, सैलून, कॉल सेंटर, गोदाम या ग्राहक-सामना व्यवसाय नहीं चलाया जाएगा।",
    ])
    sec(19, "निषिद्ध और अवैध गतिविधियाँ", [
        f"धूम्रपान/वेपिंग नीति: {clean(d.get('smoking_policy')) or 'कमरे और गैर-निर्धारित क्षेत्रों में निषिद्ध'}।",
        "अवैध मादक पदार्थ, हथियार, विस्फोटक, खतरनाक रसायन, तस्करी, जुआ, यौन शोषण, हिंसा, चोरी, धोखाधड़ी, साइबर अपराध या अन्य अवैध गतिविधि पूर्णतः निषिद्ध है।",
        "अग्नि निकास, डिटेक्टर, स्प्रिंकलर, अग्निशामक, सीसीटीवी, एक्सेस सिस्टम या सुरक्षा सूचना से छेड़छाड़ नहीं की जाएगी।",
        "गंभीरता के अनुसार निषिद्ध वस्तु हटाई जा सकती है, प्रवेश रोका जा सकता है, वैध समाप्ति की जा सकती है और सक्षम प्राधिकारी को सूचना दी जा सकती है।",
    ])
    sec(20, "इन्वेंटरी, क्षति और विशेष सफाई", [
        f"मौजूदा क्षति/इन्वेंटरी अंतर सामान्यतः {clean(d.get('inventory_report_hours')) or '24'} घंटे के भीतर अथवा पता चलने पर शीघ्र रिपोर्ट करना चाहिए।",
        "सामान्य घिसावट के अतिरिक्त द्वितीय पक्ष, उसके अनुमोदित अधिभोगी/आगंतुक द्वारा वास्तव में की गई क्षति की युक्तिसंगत एवं दस्तावेजित मरम्मत/प्रतिस्थापन लागत वसूल की जा सकती है।",
        "खोई चाबी, कार्ड, रिमोट, लिनेन, उपकरण और अन्य जारी वस्तु का उचित प्रतिस्थापन मूल्य लिया जा सकता है।",
        "साझा इकाई में जिम्मेदारी प्रमाणित होने पर संबंधित व्यक्तियों पर युक्तिसंगत अनुपात में राशि लगाई जा सकती है; केवल सामूहिक क्षेत्र में घटना होने से असंबंधित व्यक्ति को स्वतः जिम्मेदार नहीं माना जाएगा।",
    ])
    sec(21, "निजी सामान, सुरक्षा और लॉस्ट-एंड-फाउंड", [
        "नकदी, आभूषण, दस्तावेज, इलेक्ट्रॉनिक्स और निजी वस्तुओं की सामान्य सुरक्षा द्वितीय पक्ष की जिम्मेदारी है; उपलब्ध लॉकर/सेफ का उपयोग और उपयुक्त बीमा करना उचित है।",
        "चोरी/संदिग्ध घटना शीघ्र रिपोर्ट की जाएगी ताकि रिकॉर्ड, सीसीटीवी और पुलिस सहायता उचित रूप से संरक्षित/मांगी जा सके।",
        "प्रबंधन केवल सिद्ध लापरवाही, जानबूझकर कदाचार, विशिष्ट सुरक्षित-रखने के दायित्व या कानून द्वारा निर्धारित सीमा तक नुकसान के लिए जिम्मेदार होगा।",
    ])
    sec(22, "स्वास्थ्य, सुरक्षा, चिकित्सा और आपातकाल", [
        "अग्नि, निकासी, बालकनी, विद्युत, खाद्य सुरक्षा, जिम/पूल और अन्य प्रदर्शित सुरक्षा निर्देशों का पालन किया जाएगा।",
        f"आपात संपर्क: {clean(d.get('emergency_contact1')) or '________'}; {clean(d.get('emergency_contact2')) or '________'}; विदेशी संपर्क: {clean(d.get('foreign_contact_abroad')) or 'लागू नहीं/दर्ज नहीं'}।",
        "प्रबंधन चिकित्सा सेवा प्रदाता नहीं है; वास्तविक आपातकाल में एम्बुलेंस, डॉक्टर, अस्पताल, पुलिस, अग्निशमन, कॉरपोरेट ग्राहक या आपात संपर्क से संपर्क किया जा सकता है।",
        "चिकित्सा/एम्बुलेंस/अस्पताल लागत संबंधित व्यवस्था के अनुसार होगी, सिवाय जहाँ किसी पक्ष की सिद्ध लापरवाही के कारण कानून अन्य दायित्व लगाए।",
    ])
    sec(23, "गोपनीयता, सीसीटीवी और डेटा उपयोग", [
        "पहचान, संपर्क, बुकिंग, भुगतान, प्रवेश, आगंतुक, सीसीटीवी, सेवा और घटना संबंधी डेटा केवल वैध आवास, सुरक्षा, बिलिंग, सहायता और वैधानिक अनुपालन उद्देश्य के लिए संसाधित किया जा सकता है।",
        "सीसीटीवी सामान्य क्षेत्र, प्रवेश, गलियारा, रिसेप्शन और पार्किंग में हो सकता है; निजी कमरे या बाथरूम के अंदर नहीं।",
        "कानूनी आवश्यकता/वैध अनुबंध उद्देश्य होने पर जानकारी भुगतान सेवा प्रदाता, पेशेवर सलाहकार, बीमाकर्ता, कॉरपोरेट प्रायोजक, पुलिस, एफआरआरओ/एफआरओ या अन्य सक्षम प्राधिकारी को दी जा सकती है।",
        "रिकॉर्ड केवल आवश्यक संचालन, कर, सुरक्षा, विवाद और वैधानिक अवधि तक रखा जाएगा और जहाँ आवश्यक हो सुरक्षित रूप से नष्ट/अनाम किया जाएगा।",
    ])
    sec(24, "सेवा शिकायत, जांच और सुधार", [
        "सेवा दोष, सुरक्षा चिंता या बिलिंग विवाद शीघ्र आधिकारिक माध्यम से रिपोर्ट किया जाएगा ताकि जांच और सुधार का उचित अवसर मिले।",
        "आवश्यक निरीक्षण/मरम्मत में सहयोग किया जाएगा, पर गैर-आपातकालीन प्रवेश धारा 14 और चयनित स्थानांतरण नीति के अधीन रहेगा।",
        "आसानी से सुधारी जा सकने वाली समस्या को समय पर न बताने का तथ्य बाद के दावे में विचार किया जा सकता है, पर इससे गैर-त्याज्य अधिकार समाप्त नहीं होंगे।",
        "शिकायत निर्विवाद भुगतान स्वतः स्थगित नहीं करती; विवादित राशि पर पक्ष सद्भावना से समाधान का प्रयास करेंगे।",
    ])
    sec(25, "समाप्ति, सेवा अस्वीकृति और विधिसम्मत कब्जा-वापसी", [
        "गंभीर गैर-भुगतान, झूठा केवाईसी, धोखाधड़ी, अवैध गतिविधि, हिंसा/उत्पीड़न, गंभीर सुरक्षा उल्लंघन, निषिद्ध वस्तु, अनधिकृत अधिभोग/उपकिरायेदारी, महत्वपूर्ण संपत्ति क्षति या चेतावनी के बाद बार-बार गंभीर उल्लंघन वैध समाप्ति का आधार हो सकता है।",
        "तात्कालिक जीवन/संपत्ति/वैधानिक सुरक्षा खतरे में तुरंत सुरक्षा कार्रवाई की जा सकती है; सुधार योग्य गैर-गंभीर उल्लंघन पर सामान्यतः युक्तिसंगत सुधार अवसर दिया जाएगा।",
        "समाप्ति के बाद कब्जा विधिसम्मत प्रक्रिया से वापस लिया जाएगा। यह अनुबंध अवैध लॉकआउट, बल प्रयोग, निजी सामान रोकने या शारीरिक दबाव को अनुमति नहीं देता।",
        "उल्लंघन के कारण समाप्ति पर धनवापसी वास्तविक स्वीकृत शर्तों, सिद्ध नुकसान और कानून के अनुसार होगी। बिना अतिथि की गलती के प्रथम पक्ष द्वारा समाप्ति पर प्रभावित अप्रयुक्त पूर्वभुगतान का उचित समायोजन/वापसी किया जाएगा।",
        "जहाँ ऑनलाइन आवास धारा 11 में स्पष्ट रूप से अनुमत है, केवल वैध ऑनलाइन होस्टिंग स्वयं समाप्ति का आधार नहीं होगी।" if ota else "अनधिकृत उपकिरायेदारी/व्यावसायिक पुनर्बुकिंग धारा 11 के अधीन रहेगी।",
    ])
    sec(26, "अप्रत्याशित घटना और परिसर अनुपलब्धता", [
        "प्राकृतिक आपदा, आग, बाढ़, महामारी, सरकारी प्रतिबंध, नागरिक अशांति, उपयोगिता विफलता, संरचनात्मक आपातकाल या अन्य युक्तिसंगत नियंत्रण से बाहर घटना से असंभव प्रदर्शन के लिए पक्ष उस सीमा तक जिम्मेदार नहीं होगा।",
        "प्रभावित पक्ष यथाशीघ्र सूचना देगा और व्यवधान कम करने के युक्तिसंगत प्रयास करेगा।",
        "परिसर अनुपलब्ध होने पर लागू स्थानांतरण नीति के अनुसार तुलनीय विकल्प, संशोधित तिथि, क्रेडिट या प्रभावित अप्रयुक्त राशि की वापसी पर विचार किया जाएगा।",
        "पहले से दी गई सेवाओं/आवास का देय भुगतान केवल अप्रत्याशित घटना के कारण समाप्त नहीं होगा।",
    ])
    sec(27, "प्रतिपूर्ति और दायित्व की सीमा", [
        "द्वितीय पक्ष/जिम्मेदार कॉरपोरेट ग्राहक अपने धोखाधड़ी, अवैध कृत्य, जानबूझकर कदाचार, गंभीर अनुबंध उल्लंघन या अपने आमंत्रित व्यक्ति के कृत्य से सीधे उत्पन्न तृतीय-पक्ष दावों/दंड/हानि के लिए प्रथम पक्ष को उचित सीमा तक प्रतिपूर्ति करेगा, पर प्रथम पक्ष की अपनी गलती की सीमा तक नहीं।",
        "कानून द्वारा अनुमत अधिकतम सीमा तक अप्रत्यक्ष/विशेष/परिणामी व्यावसायिक हानि के लिए दायित्व सीमित हो सकता है, पर धोखाधड़ी, जानबूझकर कदाचार, लापरवाही से मृत्यु/व्यक्तिगत चोट या गैर-त्याज्य वैधानिक दायित्व को अनुचित रूप से बाहर नहीं किया जाएगा।",
        "उपभोक्ता, किरायेदारी या अन्य गैर-त्याज्य वैधानिक उपचार सुरक्षित रहेंगे।",
    ])
    sec(28, "बीमा और जोखिम", [
        "परिस्थिति के अनुसार व्यक्तिगत दुर्घटना, चिकित्सा, यात्रा, संपत्ति, साइबर और व्यावसायिक बीमा रखना पक्षों के लिए उचित हो सकता है।",
        "संपत्ति मालिक का बीमा स्वतः किरायेदार/अतिथि के निजी सामान, स्वास्थ्य, यात्रा परिवर्तन या व्यवसाय जोखिम को कवर नहीं करता।",
    ])
    sec(29, "नोटिस और आधिकारिक संचार", [
        "नोटिस हाथ से, पंजीकृत डाक, आधिकारिक ऐप, ई-मेल, एसएमएस या व्हाट्सऐप द्वारा दर्ज संपर्क पर भेजा जा सकता है, पर किसी कानूनी नोटिस के लिए अनिवार्य वैधानिक विधि लागू रहेगी।",
        "पक्ष मोबाइल, ई-मेल, बिलिंग और आपात संपर्क अद्यतन रखेंगे।",
        "स्थिर वाणिज्यिक शर्तें केवल सामान्य हाउस-रूल सूचना द्वारा नहीं बदली जा सकतीं; सुरक्षा/संचालन नियम युक्तिसंगत सूचना से अद्यतन हो सकते हैं।",
    ])
    sec(30, "इलेक्ट्रॉनिक स्वीकृति और प्रतियाँ", [
        "जहाँ कानून अनुमति देता है वहाँ भौतिक हस्ताक्षर, वैध इलेक्ट्रॉनिक हस्ताक्षर, ओटीपी/ऐप पुष्टि, डिजिटल स्वीकृति अथवा हस्ताक्षरित प्रतियों के आदान-प्रदान से अनुबंध निष्पादित किया जा सकता है।",
        "कंपनी/कॉरपोरेट ग्राहक की ओर से हस्ताक्षर करने वाला व्यक्ति अपने अधिकार की पुष्टि करता है और उचित अनुरोध पर प्राधिकरण प्रमाण उपलब्ध कराया जा सकता है।",
        "कोई पक्ष महत्वपूर्ण रिक्त स्थान वाला दस्तावेज हस्ताक्षर न करे; सभी उत्पन्न फील्ड और परिशिष्ट निष्पादन से पहले सत्यापित किए जाएँ।",
    ])
    sec(31, "पूर्ण अनुबंध, संशोधन और वरीयता", [
        "यह अनुबंध, परिशिष्ट, स्वीकृत बुकिंग पुष्टि और बाद का हस्ताक्षरित संशोधन विषय पर पूर्ण समझौता होगा।",
        "असंगति में क्रम सामान्यतः: नवीनतम हस्ताक्षरित संशोधन; विशेष सहमत शर्तें; परिशिष्ट-क/बुकिंग पुष्टि; मुख्य धाराएँ; संचालन हाउस-रूल, जब तक कानून अन्यथा न कहे।",
        "मौखिक परिवर्तन स्थिर वाणिज्यिक शर्त नहीं बदलेगा। छूट/संशोधन लिखित एवं अधिकृत होना चाहिए। एक बार अधिकार न लागू करना स्थायी छूट नहीं है।",
        "किसी धारा के अमान्य होने पर उसे न्यूनतम आवश्यक सीमा तक अलग/पढ़ा जाएगा और शेष अनुबंध जारी रहेगा जहाँ कानून अनुमति देता है।",
    ])
    sec(32, "लागू कानून और विवाद समाधान", [
        "यह अनुबंध भारत के लागू कानून तथा हरियाणा में लागू राज्य कानूनों के अधीन होगा।",
        "तत्काल न्यायिक राहत की आवश्यकता न हो तो पक्ष लिखित विवाद सूचना के बाद सामान्यतः 15 दिन के भीतर प्रबंधन/अधिकृत प्रतिनिधि स्तर पर सद्भावना से समाधान का प्रयास करेंगे।",
        f"गैर-त्याज्य उपभोक्ता/वैधानिक/क्षेत्रीय अधिकारिता के अधीन सक्षम न्यायालय/प्राधिकरण {jur} होंगे।",
        "जहाँ कानून अनुमति देता है वहाँ उपभोक्ता आयोग, किराया नियंत्रक, पंजीकरण/राजस्व/पुलिस/एफआरआरओ अथवा अन्य सक्षम प्राधिकारी के अधिकार सुरक्षित रहेंगे।",
    ])
    sec(33, "घोषणा और स्वैच्छिक स्वीकृति", [
        "हस्ताक्षरकर्ता उपलब्ध जानकारी के अनुसार दिए गए विवरण और दस्तावेजों को सही एवं वर्तमान बताते हैं।",
        "उन्होंने किराया, जमा, लॉक-इन, नोटिस, उपयोगिता, स्थानांतरण, प्रवेश, उपकिरायेदारी, अतिथि, सुरक्षा, विदेशी नागरिक और वैधानिक अनुपालन धाराओं को पढ़ा/समझा है।",
        "गंभीर उल्लंघन पर वैध समाप्ति, दस्तावेजित वसूली और आवश्यक प्राधिकरण रिपोर्टिंग हो सकती है, पर कोई अवैध उपचार अधिकृत नहीं है।",
        "पक्षों को हस्ताक्षर से पहले स्वतंत्र विधिक/कर/पंजीकरण सलाह लेने का अवसर है।",
    ])
    sec(34, "स्टाम्प शुल्क, पंजीकरण और दस्तावेज निष्पादन", [
        "पक्षों का उद्देश्य भारतीय संविदा अधिनियम, 1872 के अनुसार स्वतंत्र सहमति, सक्षम पक्ष, वैध प्रतिफल और वैध उद्देश्य वाला अनुबंध बनाना है।",
        "हरियाणा में इस दस्तावेज के स्वरूप, अवधि और प्रतिफल पर लागू स्टाम्प शुल्क समय पर अदा किया जाएगा। पक्षों के बीच सामान्यतः किराया/पट्टा दस्तावेज का स्टाम्प शुल्क किरायेदार/पट्टेदार द्वारा वहन किया जाएगा, जब तक लिखित रूप से अन्य वैध व्यवस्था न हो; पर वैधानिक दायित्व सक्षम प्राधिकारी के अनुसार रहेगा।",
        "वर्ष-दर-वर्ष पट्टा, एक वर्ष से अधिक अवधि का पट्टा या पंजीकरण अधिनियम, 1908 की धारा 17/संपत्ति अंतरण अधिनियम, 1882 की धारा 107 के अंतर्गत अनिवार्य पंजीकरण वाली स्थिति में पक्ष सक्षम उप-पंजीयक/संयुक्त उप-पंजीयक के समक्ष समय पर पंजीकरण में सहयोग करेंगे। एक वर्ष से अधिक न होने वाले पट्टे का पंजीकरण धारा 18 के अधीन वैकल्पिक हो सकता है, वर्तमान कानून के अधीन।",
        "संपत्ति का विवरण पहचान योग्य होना चाहिए; पता, इकाई संख्या, संपत्ति/नगरपालिका आईडी, तल/क्षेत्र और उपलब्ध सीमा/मानचित्र विवरण सही दर्ज किए जाएँ।",
        "नोटरीकरण अनिवार्य पंजीकरण या स्टाम्प शुल्क का विकल्प नहीं है। अनिवार्य रूप से पंजीकरण योग्य दस्तावेज का पंजीकरण न होने से उसके साक्ष्यात्मक उपयोग पर पंजीकरण अधिनियम की धारा 49 के परिणाम लागू हो सकते हैं।",
    ])
    sec(35, "विदेशी नागरिक/ओसीआई, फॉर्म-III और आव्रजन अनुपालन", [
        f"इस अनुबंध में चयनित स्थिति: {foreign_status}। 1 सितम्बर 2025 से प्रभावी Immigration and Foreigners Act, 2025 तथा Immigration and Foreigners Rules, 2025 के लागू प्रावधान स्वतंत्र वैधानिक दायित्व उत्पन्न कर सकते हैं।",
        "नियम 17 के अंतर्गत लागू 'keeper of accommodation' प्रत्येक विदेशी नागरिक, ओसीआई कार्डधारक सहित, से आगमन एवं प्रस्थान के आवश्यक विवरण प्राप्त करेगा, उन्हें कम से कम एक वर्ष इलेक्ट्रॉनिक रूप से रखेगा और सक्षम अधिकारी के निरीक्षण हेतु उपलब्ध रखेगा।",
        "जहाँ नियम 17 लागू है, विधिवत भरा Form III (पूर्व Form C) विदेशी नागरिक के आगमन के यथाशीघ्र और अधिकतम 24 घंटे के भीतर नामित ऑनलाइन पोर्टल/मोबाइल ऐप से Registration Officer को भेजा जाएगा; प्रस्थान विवरण भी प्रस्थान के अधिकतम 24 घंटे के भीतर भेजे जाएंगे।",
        "2025 नियमों में accommodation की परिभाषा में हॉस्टल, पेइंग गेस्ट, किराये का आवास, होम स्टे और समान परिसर शामिल हैं। गैर-वाणिज्यिक निजी आवास पर अधिनियम में विशेष अपवाद है, पर सक्षम civil authority निर्दिष्ट क्षेत्र में रिपोर्टिंग का निर्देश दे सकती है; गुरुग्राम में लागू किसी वैध निर्देश का पालन किया जाएगा।",
        "विदेशी अतिथि पासपोर्ट, वीज़ा/ओसीआई, राष्ट्रीयता, संपर्क, आगमन, पिछला ठहराव, अगला गंतव्य, वीज़ा उद्देश्य और FRRO/FRO पंजीकरण/परमिट के सही विवरण देगा और स्थिति बदलने पर शीघ्र सूचित करेगा।",
        "प्रबंधन वैध केवाईसी/रिपोर्टिंग हेतु दस्तावेज देख/प्रतिलिपि रख सकता है, पर मूल पासपोर्ट को स्थायी रूप से रोकने का अधिकार इस अनुबंध से नहीं मिलता जब तक कानून/सक्षम प्राधिकारी स्पष्ट रूप से ऐसा न कहे।",
        f"Form III आगमन संदर्भ: {clean(d.get('form3_arrival_ack')) or 'दर्ज नहीं/लागू नहीं'}; प्रस्थान संदर्भ: {clean(d.get('form3_departure_ack')) or 'दर्ज नहीं/लागू नहीं'}।",
    ])
    sec(36, "हरियाणा पुलिस / गुरुग्राम सत्यापन", [
        "हरियाणा पुलिस की नागरिक सेवाओं में Tenant/PG Verification उपलब्ध है। जहाँ सक्षम निर्देश, संपत्ति सुरक्षा नीति अथवा पक्षों की लिखित शर्त के अनुसार सत्यापन अपेक्षित हो, किरायेदार/अतिथि सही विवरण देकर सहयोग करेगा।",
        "हरियाणा पुलिस होटल मालिक/ग्राहक validation तथा विदेशियों के आगमन/प्रस्थान पंजीकरण जैसी सेवाएँ भी सूचीबद्ध करती है; चयनित संचालन मॉडल के अनुसार लागू प्रक्रिया का पालन जिम्मेदार पक्ष करेगा।",
        f"Tenant/PG सत्यापन संदर्भ: {clean(d.get('tenant_verification_ref')) or 'दर्ज नहीं/लागू नहीं'}; होटल/ग्राहक validation संदर्भ: {clean(d.get('hotel_validation_ref')) or 'दर्ज नहीं/लागू नहीं'}।",
        "पुलिस, FRRO/FRO या अन्य सक्षम अधिकारी को जानबूझकर झूठी सूचना देना अथवा जाली दस्तावेज देना गंभीर अनुबंध उल्लंघन होगा और स्वतंत्र वैधानिक परिणाम हो सकते हैं।",
    ])
    sec(37, "संचालन अनुमति, ट्रेड/लॉजिंग लाइसेंस और भूमि उपयोग", [
        f"वास्तविक संचालन मॉडल '{operating_model}' है। निजी किरायेदारी, पीजी, सेवायुक्त अपार्टमेंट, होटल/गेस्ट हाउस, लॉजिंग हाउस, होम स्टे और ऑनलाइन अल्पकालिक आवास पर अलग-अलग नगरपालिका/योजना/लाइसेंस नियम लागू हो सकते हैं।",
        "Urban Local Bodies Haryana ट्रेड लाइसेंस तथा लॉजिंग हाउस लाइसेंस के निर्गमन/नवीनीकरण की सेवाएँ प्रदान करता है। जिस संचालन पर ऐसा लाइसेंस लागू हो, जिम्मेदार मालिक/ऑपरेटर उसे प्राप्त और वैध रखेगा।",
        "गुरुग्राम के नियंत्रित/आवासीय क्षेत्र में गेस्ट/बोर्डिंग हाउस उपयोग लागू development plan, zoning policy, CLU/विशेष अनुमति, स्वीकृत भवन योजना, occupation certificate और बाध्यकारी सोसायटी/टाइटल प्रतिबंधों के अधीन रहेगा।",
        f"ट्रेड लाइसेंस: {clean(d.get('trade_license_no')) or 'दर्ज नहीं'}; लॉजिंग लाइसेंस: {clean(d.get('lodging_license_no')) or 'दर्ज नहीं'}; गेस्ट हाउस/CLU/Zoning अनुमति: {clean(d.get('guest_house_permission_no')) or 'दर्ज नहीं'}; Occupation Certificate: {clean(d.get('occupancy_certificate_no')) or 'दर्ज नहीं'}।",
        "केवल निजी अनुबंध द्वारा दी गई ऑनलाइन होस्टिंग अनुमति किसी वैधानिक/नगरपालिका/सोसायटी निषेध को समाप्त नहीं करेगी।",
    ])
    sec(38, "अग्नि, भवन और आपात सुरक्षा अनुपालन", [
        "परिसर का उपयोग लागू Haryana Fire and Emergency Services Act, 2022, भवन सुरक्षा नियम, सक्षम प्राधिकारी के आदेश और अग्नि-सुरक्षा अनुमोदन के अनुरूप किया जाएगा।",
        "जहाँ भवन वर्गीकरण, ऊँचाई, क्षेत्र अथवा उपयोग के कारण Fire NOC/Fire Fighting Scheme/Occupation Certificate आवश्यक हो, जिम्मेदार मालिक/ऑपरेटर उसे वैध रखेगा।",
        f"Fire NOC / अग्नि सुरक्षा संदर्भ: {clean(d.get('fire_noc_no')) or 'दर्ज नहीं/लागूता संपत्ति के अनुसार पुष्टि की जाए'}।",
        "अग्नि निकास, सीढ़ी, refuge area, अग्निशमन यंत्र, detector, alarm, sprinkler अथवा विद्युत सुरक्षा व्यवस्था बाधित करना गंभीर उल्लंघन होगा।",
    ])
    sec(39, "होम स्टे / पर्यटन पंजीकरण (जहाँ लागू हो)", [
        "यदि परिसर Home Stay के रूप में संचालित है, मालिक/ऑपरेटर Haryana Home Stay Scheme, 2024 और वैध संशोधनों के अनुसार पंजीकरण, प्रदर्शन, अतिथि रजिस्टर, स्वच्छता, बिलिंग और आवधिक पर्यटक सूचना संबंधी लागू शर्तों का पालन करेगा।",
        "विदेशी पर्यटक के लिए संबंधित पुलिस/Registration Officer को आवश्यक सूचना और Form III प्रक्रिया का पालन किया जाएगा; पर्यटन योजना की प्रक्रिया आव्रजन नियमों का विकल्प नहीं है।",
        f"हरियाणा पर्यटन Home Stay पंजीकरण संदर्भ: {clean(d.get('tourism_registration_no')) or 'दर्ज नहीं/लागू नहीं'}।",
        "यदि वास्तविक मॉडल Home Stay नहीं है तो इस धारा की उपस्थिति मात्र से Home Stay पंजीकरण का काल्पनिक दायित्व नहीं बनेगा; वास्तविक कानून और उपयोग निर्णायक होगा।",
    ])
    sec(40, "इलेक्ट्रॉनिक अनुबंध और न्यायालय हेतु डिजिटल साक्ष्य संरक्षण", [
        "Information Technology Act, 2000 के अनुसार केवल इलेक्ट्रॉनिक माध्यम से प्रस्ताव/स्वीकृति होने के कारण अनुबंध को अस्वीकार्य नहीं माना जाना चाहिए, पर स्टाम्प/पंजीकरण/प्राधिकरण जैसी स्वतंत्र आवश्यकताएँ फिर भी लागू रहेंगी।",
        "हस्ताक्षरित अनुबंध, संशोधन, चालान, बैंक/UPI प्रमाण, ई-मेल, संदेश, ऐप लॉग, एक्सेस लॉग, मीटर रीडिंग, फोटो और निरीक्षण रिकॉर्ड की प्रामाणिक प्रतियाँ सुरक्षित रखी जा सकती हैं।",
        "Bharatiya Sakshya Adhiniyam, 2023 की धारा 61-63 सहित लागू साक्ष्य नियमों के अनुसार इलेक्ट्रॉनिक रिकॉर्ड प्रस्तुत करते समय मूल स्रोत, मेटाडेटा, chain of custody और आवश्यक प्रमाणपत्र/तकनीकी विवरण यथासंभव सुरक्षित रखे जाएँ।",
        "जहाँ मूल इलेक्ट्रॉनिक रिकॉर्ड उपलब्ध हो, केवल स्क्रीनशॉट पर अनावश्यक निर्भरता से बचना उचित होगा। यह धारा न्यायालय की स्वतंत्र admissibility/proof determination को बाध्य नहीं करती।",
    ])
    sec(41, "अधिकार, स्वामित्व/प्राधिकरण और गैर-हस्तांतरण", [
        "प्रथम पक्ष यह दर्शाता है कि वह मालिक, वैध पट्टादाता/अनुज्ञापक, अधिकृत ऑपरेटर/प्रबंधन अथवा ऐसा व्यक्ति/संस्था है जिसके पास इस अनुबंध के अनुरूप अधिभोग देने का पर्याप्त अधिकार है।",
        "द्वितीय पक्ष को स्वामित्व या स्थायी मालिकाना अधिकार नहीं मिलता। कॉरपोरेट नामांकन भी स्वयं में कर्मचारी/नामित व्यक्ति को स्थायी किरायेदारी नहीं देता।",
        "कंपनी की ओर से हस्ताक्षर करने वाला व्यक्ति अपने प्राधिकरण की पुष्टि करता है। उचित अनुरोध पर बोर्ड/अधिकृत पत्र/प्रबंधन अधिकार का प्रमाण मांगा जा सकता है।",
        "यदि प्रथम पक्ष के अधिकार में गंभीर दोष के कारण वैध अधिभोग असंभव हो जाए, प्रभावित पक्ष लागू कानून और अनुबंध के अनुसार उचित उपचार मांग सकता है।",
    ])
    sec(42, "अंग्रेज़ी और हिंदी संस्करण", [
        f"इस अनुबंध का अंग्रेज़ी और हिंदी संस्करण समान वाणिज्यिक डेटा से बनाया जा सकता है। चयनित वरीयता नियम: {lang_rule}।",
        "राशि, तारीख, संपत्ति पहचान, पासपोर्ट/वीज़ा संख्या, रसीद/संदर्भ संख्या जैसे तथ्य मूल दस्तावेजों से सत्यापित किए जाएँ; अनुवाद से तथ्य नहीं बदलेंगे।",
        "यदि किसी अनुवादित शब्द के अनेक अर्थ हों तो हस्ताक्षरित विशेष शर्तें, पूर्ण वाणिज्यिक विवरण, पक्षों की स्पष्ट मंशा और लागू कानून के अनुरूप अर्थ ग्रहण किया जाएगा।",
        "जो पक्ष किसी संस्करण की भाषा नहीं समझता उसे हस्ताक्षर से पहले स्पष्टीकरण/स्वतंत्र अनुवाद का युक्तिसंगत अवसर दिया जाना चाहिए।",
    ])
    sec(43, "कानून में परिवर्तन, बचाव और न्यायालय-तैयार रिकॉर्ड", [
        "निष्पादन के बाद कानून/नियम/अधिसूचना/बाध्यकारी आदेश बदलने पर अनिवार्य नया कानून असंगत सीमा तक प्रभावी होगा और आवश्यक होने पर पक्ष लिखित संशोधन करेंगे।",
        "कोई धारा गैर-त्याज्य उपभोक्ता, किराया, आव्रजन, अग्नि, नगरपालिका, पंजीकरण, साक्ष्य या अन्य वैधानिक अधिकार को समाप्त नहीं करेगी।",
        "साक्ष्य स्पष्टता हेतु हस्ताक्षरित अनुबंध, परिशिष्ट, स्टाम्प/ई-स्टाम्प, पंजीकरण एंडोर्समेंट (यदि हो), केवाईसी संदर्भ, भुगतान रिकॉर्ड, कब्जा/हैंडओवर रिकॉर्ड, मीटर रीडिंग, इन्वेंटरी फोटो और महत्वपूर्ण नोटिस सुरक्षित रखना उचित है। यह सूची प्रत्येक मामले में सभी वस्तुओं को अनिवार्य घोषित नहीं करती।",
        "अंतिम अधिकारिता, साक्ष्य स्वीकार्यता, क्षतिपूर्ति, कब्जा, निषेधाज्ञा, उपभोक्ता राहत या अन्य उपचार उस समय लागू कानून और सक्षम न्यायालय/प्राधिकरण द्वारा निर्धारित होंगे।",
    ])

    lines.append("")
    lines.append("स्वास्थ्य एवं आपातकालीन घोषणा")
    lines.append("द्वितीय पक्ष पुष्टि करता है कि सुरक्षित आवास या आपात सहायता के लिए आवश्यक जानकारी सत्य रूप से दी गई है। वास्तविक आपातकाल में प्रबंधन दर्ज आपात संपर्क, कॉरपोरेट ग्राहक, एम्बुलेंस, डॉक्टर, अस्पताल, पुलिस, अग्निशमन अथवा अन्य सक्षम सेवा से संपर्क कर सकता है।")

    lines.append("")
    lines.append("परिशिष्ट-क - आवास, भुगतान और सुविधा विवरण")
    annex = [
        ("किरायेदार/अतिथि", tenant_name),
        ("कॉरपोरेट ग्राहक", corp or "लागू नहीं"),
        ("संपत्ति", property_name),
        ("पता", premises),
        ("संपत्ति/नगरपालिका संदर्भ", clean(d.get("property_id")) or "दर्ज नहीं"),
        ("तल/क्षेत्र", clean(d.get("floor_area")) or "दर्ज नहीं"),
        ("सीमाएँ/अतिरिक्त पहचान", clean(d.get("property_boundaries")) or "दर्ज नहीं"),
        ("कक्ष/इकाई", room),
        ("श्रेणी", room_type),
        ("संचालन मॉडल", operating_model),
        ("प्रारम्भ", start),
        ("समाप्ति", end),
        ("अवधि", f"{term} माह"),
        ("लॉक-इन", f"{lockin} माह"),
        ("मासिक किराया", rent),
        ("सुरक्षा जमा", deposit),
        ("नोटिस", f"{notice} दिन"),
        ("विद्युत", clean(d.get("electricity_rate")) or "लागू दर"),
        ("जनरेटर/डीजी", clean(d.get("genset_rate")) or "लागू दर"),
        ("समाविष्ट सुविधाएँ", clean(d.get("included_services")) or "स्वीकृत बुकिंग के अनुसार"),
        ("अतिरिक्त सेवाएँ", clean(d.get("excluded_services")) or "अनुबंध के अनुसार"),
    ]
    for label, value in annex:
        lines.append(f"{label}: {value}")

    lines.append("")
    lines.append("परिशिष्ट-ख - किरायेदार/अतिथि उपक्रम एवं संक्षिप्त गृह नियम")
    undertakings = [
        f"मैं परिसर का उपयोग केवल {purpose} के लिए करूंगा/करूंगी।",
        "मैं धारा 11 के विपरीत अनधिकृत हस्तांतरण/उपकिरायेदारी/साझेदारी नहीं करूंगा/करूंगी।",
        "मैं सही केवाईसी और जहाँ लागू हो विदेशी नागरिक/ओसीआई विवरण उपलब्ध कराऊंगा/कराऊंगी।",
        "मैं किराया, उपयोगिता एवं अन्य अधिकृत शुल्क समय पर चुकाऊंगा/चुकाऊंगी और लॉक-इन/नोटिस शर्तों का पालन करूंगा/करूंगी।",
        "मैं अवैध गतिविधि, निषिद्ध वस्तु, उत्पात, संपत्ति क्षति या सुरक्षा/मीटर से छेड़छाड़ नहीं करूंगा/करूंगी।",
        "मैं आगंतुक, अग्नि सुरक्षा, इंटरनेट, पार्किंग, हाउसकीपिंग और आपात नियमों का पालन करूंगा/करूंगी।",
        "मैं सेवा दोष, क्षति, सुरक्षा चिंता, चोरी या संदिग्ध घटना शीघ्र रिपोर्ट करूंगा/करूंगी।",
        "मैं समझता/समझती हूं कि गंभीर उल्लंघन पर विधिसम्मत समाप्ति, दस्तावेजित वसूली और सक्षम प्राधिकारी को सूचना हो सकती है।",
    ]
    for i, u in enumerate(undertakings, 1):
        lines.append(f"ख.{i} {u}")
    lines.append("किरायेदार/अतिथि हस्ताक्षर: ______________________________   दिनांक: __________________")

    lines.append("")
    lines.append("परिशिष्ट-ग - कॉरपोरेट ग्राहक उपक्रम (यदि लागू हो)")
    if corp:
        for i, u in enumerate([
            "स्वीकृत प्रायोजित/गारंटीकृत शुल्कों का भुगतान करेगा।",
            "नामित अधिभोगी को अनुबंध एवं संपत्ति नियम उपलब्ध कराएगा।",
            "अधिभोगी की नौकरी/नामांकन/प्रायोजन समाप्त होने पर शीघ्र सूचित करेगा।",
            "पूर्व स्वीकृति एवं आवश्यक केवाईसी के बिना अधिभोगी नहीं बदलेगा।",
            "आपातकाल, जांच, भुगतान मिलान और वैध निकास में उचित सहयोग करेगा।",
        ], 1):
            lines.append(f"ग.{i} {u}")
    else:
        lines.append("लागू नहीं, जब तक कॉरपोरेट ग्राहक बाद में वैध लिखित संशोधन/बुकिंग दस्तावेज द्वारा पक्ष न बने।")

    if extra_clauses:
        lines.append("")
        lines.append("परिशिष्ट-घ - अतिरिक्त / विशेष धाराएँ")
        for i, clause in enumerate([c for c in extra_clauses if clean(c)], 1):
            lines.append(f"घ.{i} {clean(clause)}")

    lines.append("")
    lines.append("परिशिष्ट-ङ - विदेशी नागरिक / ओसीआई एवं नियामक विवरण")
    fitems = [
        ("स्थिति", foreign_status),
        ("राष्ट्रीयता", clean(d.get("foreign_nationality")) or "लागू नहीं/दर्ज नहीं"),
        ("पासपोर्ट संख्या", clean(d.get("passport_no")) or "लागू नहीं/दर्ज नहीं"),
        ("पासपोर्ट जारी/समाप्ति", f"{clean(d.get('passport_issue_date')) or 'दर्ज नहीं'} / {clean(d.get('passport_expiry')) or 'दर्ज नहीं'}"),
        ("वीज़ा/ओसीआई संख्या", clean(d.get("visa_oci_no")) or "लागू नहीं/दर्ज नहीं"),
        ("वीज़ा प्रकार/स्थिति", clean(d.get("visa_type")) or "लागू नहीं/दर्ज नहीं"),
        ("वीज़ा वैधता", clean(d.get("visa_expiry")) or "दर्ज नहीं"),
        ("भारत यात्रा उद्देश्य", clean(d.get("purpose_of_visit")) or "दर्ज नहीं"),
        ("FRRO/FRO पंजीकरण/परमिट", f"{clean(d.get('frro_registration_no')) or 'दर्ज नहीं'}; वैधता {clean(d.get('frro_validity')) or 'दर्ज नहीं'}"),
        ("आगमन", clean(d.get("arrival_date_time")) or "दर्ज नहीं"),
        ("कहाँ से आया", clean(d.get("arrival_from")) or "दर्ज नहीं"),
        ("पिछला ठहराव", clean(d.get("previous_place_of_stay")) or "दर्ज नहीं"),
        ("अगला गंतव्य", clean(d.get("next_destination")) or "दर्ज नहीं"),
        ("प्रस्थान", clean(d.get("departure_date_time")) or "दर्ज नहीं"),
        ("नियोक्ता/प्रायोजक", clean(d.get("foreign_sponsor")) or "दर्ज नहीं"),
        ("विदेशी आपात संपर्क", clean(d.get("foreign_contact_abroad")) or "दर्ज नहीं"),
        ("Form III आगमन संदर्भ", clean(d.get("form3_arrival_ack")) or "दर्ज नहीं/लागू नहीं"),
        ("Form III प्रस्थान संदर्भ", clean(d.get("form3_departure_ack")) or "दर्ज नहीं/लागू नहीं"),
        ("हरियाणा पुलिस Tenant/PG सत्यापन", clean(d.get("tenant_verification_ref")) or "दर्ज नहीं/लागू नहीं"),
        ("ट्रेड/लॉजिंग लाइसेंस", f"{clean(d.get('trade_license_no')) or 'दर्ज नहीं'} / {clean(d.get('lodging_license_no')) or 'दर्ज नहीं'}"),
        ("Fire NOC / Occupation Certificate", f"{clean(d.get('fire_noc_no')) or 'दर्ज नहीं'} / {clean(d.get('occupancy_certificate_no')) or 'दर्ज नहीं'}"),
        ("Guest House / CLU / Zoning अनुमति", clean(d.get("guest_house_permission_no")) or "दर्ज नहीं/लागू नहीं"),
        ("Home Stay पंजीकरण", clean(d.get("tourism_registration_no")) or "दर्ज नहीं/लागू नहीं"),
    ]
    for label, value in fitems:
        lines.append(f"{label}: {value}")
    if clean(d.get("statutory_licence_notes")):
        lines.append(f"अन्य नियामक टिप्पणियाँ: {clean(d.get('statutory_licence_notes'))}")

    lines.append("")
    lines.append("निष्पादन एवं हस्ताक्षर")
    lines.append("पक्ष सभी लागू रिक्त विवरण पूर्ण एवं सत्यापित करने के बाद इस अनुबंध पर हस्ताक्षर/वैध इलेक्ट्रॉनिक स्वीकृति करते हैं।")
    lines.append("")
    lines.append("प्रथम पक्ष / मकान-मालिक / प्रबंधन")
    lines.append(f"नाम/संस्था: {landlord_name}")
    lines.append(f"अधिकृत हस्ताक्षरकर्ता: {clean(d.get('authorized_signatory')) or '________________'}")
    lines.append("हस्ताक्षर/मुहर: ______________________________   दिनांक: __________________")
    lines.append("")
    lines.append("द्वितीय पक्ष / किरायेदार / अतिथि")
    lines.append(f"नाम: {tenant_name}")
    lines.append(f"सरकारी पहचान: {clean(d.get('tenant_id_type')) or 'आईडी'} संख्या {clean(d.get('tenant_id_no')) or '________________'}")
    lines.append("हस्ताक्षर/इलेक्ट्रॉनिक स्वीकृति: ______________________________   दिनांक: __________________")
    if corp:
        lines.append("")
        lines.append("कॉरपोरेट ग्राहक / बुकिंग संस्था")
        lines.append(f"संस्था: {corp} | प्रतिनिधि: {clean(d.get('corporate_representative')) or '________________'}")
        lines.append("हस्ताक्षर/मुहर: ______________________________   दिनांक: __________________")
    lines.append("")
    lines.append("साक्षी 1")
    lines.append(clean(d.get("witness1")) or "नाम / पता / हस्ताक्षर: ________________________________________________")
    lines.append("")
    lines.append("साक्षी 2")
    lines.append(clean(d.get("witness2")) or "नाम / पता / हस्ताक्षर: ________________________________________________")
    lines.append("")
    lines.append("नोटरी सत्यापन")
    lines.append(f"मेरे समक्ष दिनांक __________________ को {clean(d.get('place_of_execution')) or '________________'} में सत्यापित।")
    lines.append(f"नोटरी नाम: {clean(d.get('notary_name')) or '________________'} | पंजीकरण संख्या: {clean(d.get('notary_reg_no')) or '________________'}")
    lines.append("हस्ताक्षर एवं आधिकारिक मुहर: ________________________________________________")
    return "\n".join(lines)


