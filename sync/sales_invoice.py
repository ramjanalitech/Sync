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
    phone = "7698737440"  # Must include country code if required by API

    # phone = "7977185868"
    if not phone:
        return {"success": False, "error": "No phone number found"}

    otp = str(random.randint(100000, 999999))
    # frappe.msgprint(f"Generated OTP: {otp}")

    # Store OTP in cache for 5 minutes
    frappe.cache().set_value(f"overdue_otp_{customer}", otp, expires_in_sec=300)

    # Send OTP
    return send_whatsapp_message(phone, otp)


@frappe.whitelist()
def verify_overdue_otp(customer, otp):
    cached_otp = frappe.cache().get_value(f"overdue_otp_{customer}")
    if cached_otp and cached_otp == otp:
        frappe.cache().delete_value(f"overdue_otp_{customer}")
        return {"verified": True}
    return {"verified": False}


@frappe.whitelist()
def send_whatsapp_message(receiver_mobile_no, otp):
    # url = "https://wbcapi.messagerider.com/MessageRider/SendMsg"
    url = "https://wbcapi.messagerider.com/MessageRider/SendMsg"
    
    params = {
        "authtoken": "0000146",
        "password": "Prism@2025",
        "message": f"Your verification OTP is {otp}",
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
