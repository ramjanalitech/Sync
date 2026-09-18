import frappe
import random
import requests

@frappe.whitelist()
def get_last_rates(customer, item_code):
    selling_rate = frappe.db.sql("""
        SELECT sii.rate FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON sii.parent = si.name
        WHERE sii.item_code = %s AND si.customer = %s
        AND si.docstatus = 1
        ORDER BY si.posting_date DESC, si.modified DESC
        LIMIT 1
    """, (item_code, customer), as_dict=1)

    purchase_rate = frappe.db.sql("""
        SELECT pii.rate FROM `tabPurchase Invoice Item` pii
        JOIN `tabPurchase Invoice` pi ON pii.parent = pi.name
        WHERE pii.item_code = %s AND pi.docstatus = 1
        ORDER BY pi.posting_date DESC, pi.modified DESC
        LIMIT 1
    """, (item_code,), as_dict=1)

    return {
        "selling_rate": selling_rate[0].rate if selling_rate else None,
        "purchase_rate": purchase_rate[0].rate if purchase_rate else None
    }

## New Code 

@frappe.whitelist()
def send_overdue_otp(customer):
    phone = "8423594555"  # Must include country code if required by API

    # phone = "7977185868"
    if not phone:
        return {"success": False, "error": "No phone number found"}

    otp = str(random.randint(100000, 999999))
    # frappe.msgprint(f"Generated OTP: {otp}")

    customer_name = frappe.db.get_value("Customer", customer, "customer_name")
    # Store OTP in cache for 5 minutes
    frappe.cache().set_value(f"overdue_otp_{customer}", otp, expires_in_sec=300)

    # Send OTP
    # return send_whatsapp_message(phone, otp)
    return send_whatsapp_message(phone, otp, customer_name)


@frappe.whitelist()
def verify_overdue_otp(customer, otp):
    cached_otp = frappe.cache().get_value(f"overdue_otp_{customer}")
    if cached_otp and cached_otp == otp:
        frappe.cache().delete_value(f"overdue_otp_{customer}")
        return {"verified": True}
    return {"verified": False}


@frappe.whitelist()
# def send_whatsapp_message(receiver_mobile_no, otp):
def send_whatsapp_message(receiver_mobile_no, otp, customer_name=None):
    # url = "https://wbcapi.messagerider.com/MessageRider/SendMsg"
    url = "https://wbcapi.messagerider.com/MessageRider/SendMsg"
    
    # message = f" <b>{customer_name}<b>, Your verification OTP is {otp}" if customer_name else f"Your verification OTP is {otp}"
    
    message = f"Customer Name : {customer_name}, Your verification OTP is {otp}" if customer_name else f"Your verification OTP is {otp}"
    params = {
        "authtoken": "0000146",
        "password": "Prism@2025",
        # "message": f"Your verification OTP is {otp}",
        "message": message,
        "receiverMobileNo": receiver_mobile_no
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "response": response.text
            }
        else:
            frappe.throw(f"Error from API: {response.status_code} - {response.text}")
    except Exception as e:
        frappe.throw(f"API Request Failed: {str(e)}")

# MOP Code

from sync.mop_otp import (
    get_mop_items,
    is_mop_approval_valid,
)


def validate_mop(doc, method=None):
    """
    Server-side MOP validation.

    Rules:
    - Rate >= MOP -> normal save/submit
    - Rate < MOP -> valid OTP approval required

    MOP is always fetched from Item Master on the server.
    No Sales Invoice field is used for OTP/token storage.
    """

    mop_items = get_mop_items(doc)

    # No MOP violation
    if not mop_items:
        return

    # Check whether OTP approval exists for the exact
    # current item/rate/MOP combination.
    if is_mop_approval_valid(mop_items):
        return

    frappe.throw(
        "MOP approval is required because one or more item "
        "rates are below the Minimum Offer Price (MOP). "
        "Please verify the OTP."
    )

# # import frappe

# from sync.mop_otp import (
#     get_mop_items,
#     consume_mop_verification
# )


# def validate_mop(doc, method=None):
#     """
#     Server-side MOP validation for Sales Invoice.

#     If Rate < MOP, valid OTP verification is required.
#     """

#     mop_items = get_mop_items(doc)

#     # No MOP violation
#     if not mop_items:
#         return

#     token = doc.get("custom_mop_otp_token")

#     if not token:
#         frappe.throw(
#             "MOP approval is required because one or more item rates "
#             "are below the Minimum Offer Price."
#         )

#     # Verify OTP approval
#     verified = consume_mop_verification(
#         doc.name,
#         token
#     )

#     if not verified:

#         frappe.throw(
#             "MOP OTP verification is required before saving/submitting "
#             "this Sales Invoice."
#         )