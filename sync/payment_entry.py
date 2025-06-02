import frappe
import base64
import requests
from frappe.utils.pdf import get_pdf
from frappe.utils import formatdate
from frappe import _

## New Code 02/06/2025

@frappe.whitelist()
def send_whatsapp_on_payment_submit(doc, method=None):
    if isinstance(doc, str):
        doc = frappe.get_doc("Payment Entry", doc)

    if not doc.party_mobile:
        frappe.throw(_("Contact number is missing. Please update the party's mobile number."))

    # Get WhatsApp credentials
    # frappe.msgprint(f"doc.branch: {doc.branch}")
    authtoken, password = get_messagerider_credentials(doc.branch)

    # Skip sending if credentials are not returned (i.e., payment_entry is not enabled or not configured)
    if not authtoken or not password:
        frappe.msgprint(_("WhatsApp sending is skipped as it's not enabled or not configured for this branch."))
        return

    # Generate PDF and attach to Payment Entry
    html = frappe.get_print("Payment Entry", doc.name)
    pdf_content = get_pdf(html)

    file_name = f"{frappe.generate_hash('', 5)}.pdf"
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": file_name,
        "attached_to_doctype": "Payment Entry",
        "attached_to_name": doc.name,
        "is_private": 0,
        "content": pdf_content
    })
    file_doc.save(ignore_permissions=True)
    frappe.db.commit()

    # Format WhatsApp message
    amount = f"Rs. {(doc.paid_amount or 0):,.2f}"
    payment_date = formatdate(doc.posting_date) if doc.posting_date else "Not Mentioned"

    # Entry type based message
    if doc.payment_type == "Pay":
        message = (
            f"Dear *{doc.party_name}*, we have paid a payment of *{amount}* on *{payment_date}* "
            f"against Payment Entry *{doc.name}*. Thank you!"
        )
    else:
        message = (
            f"Dear *{doc.party_name}*, we have received a payment of *{amount}* on *{payment_date}* "
            f"against Payment Entry *{doc.name}*. Thank you!"
        )
    # Prepare payload
    payload = {
        "authtoken": authtoken,
        "Password": password,
        "Message": message,
        "receiverMobileNo": doc.party_mobile
    }

    files = {
        "Uploadfile": (file_name, pdf_content, "application/pdf")
    }

    # Send the WhatsApp message
    response = requests.post(
        "https://wbcapi.messagerider.com/MessageRider/SendMsg",
        data=payload,
        files=files
    )

    try:
        resp_data = response.json()
    except Exception:
        resp_data = {}

    if response.status_code == 200 and resp_data.get("Status") == 1:
        frappe.msgprint(_("✅ WhatsApp message sent successfully to {0}").format(doc.party_mobile))
        doc.add_comment("Comment", text=f"WhatsApp message sent to {doc.party_mobile}.")
    else:
        error_msg = resp_data.get("ErrorMessage") or resp_data.get("Message") or "Unknown error"
        frappe.msgprint(_("❌ Failed to send WhatsApp message. Reason: {0}").format(error_msg))

        # Optional logging for debug
        frappe.log_error(
            title="WhatsApp Send Failure - Payment Entry",
            message=f"Status Code: {response.status_code}\nResponse: {response.text}\nPayload: {payload}"
        )


def get_messagerider_credentials(branch_name):
    config = frappe.get_all("Configuration", limit=1)
    frappe.msgprint(f"config:{config}")
    if not config:
        frappe.throw("No Configuration document found.")

    config_doc = frappe.get_doc("Configuration", config[0].name)
    frappe.msgprint(f"config_doc:{config_doc}")
    # Check if payment entry WhatsApp is enabled
    if config_doc.payment_entry != 1:
        return None, None

    for row in config_doc.configuration_details:
        if row.branch == branch_name:
            return row.authtoken, row.password

    return None, None  # Credentials not found, skip sending

# Add commentMore actions
# def get_messagerider_credentials(branch_name):
#     config = frappe.get_doc("Configuration")
#     frappe.msgprint(f"config:{config}")
#     for row in config.configuration_details:
#         config = frappe.get_all("Configuration", limit=1)
#         frappe.msgprint(f"config:{config}")
#         if not config:
#             frappe.throw("No Configuration document found.")

#     config_doc = frappe.get_doc("Configuration", config[0].name)

#     # If payment_entry is not enabled, return None to indicate WhatsApp sending should be skipped
#     if config_doc.payment_entry != 1:
#         return None, None

#     for row in config_doc.configuration_details:
#         if row.branch == branch_name:
#             return row.authtoken, row.password
#     frappe.throw(f"No MessageRider credentials found for branch: {branch_name}")

#     return None, None  # Credentials not found, skip sending
