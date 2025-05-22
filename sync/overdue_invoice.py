import frappe
from frappe.utils import nowdate, formatdate
import requests
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def send_overdue_invoice_reminders():
    # Get all submitted, unpaid, overdue invoices
    overdue_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "due_date": ["<", nowdate()]
        },
        fields=["name", "customer", "contact_mobile"]
    )

    for inv in overdue_invoices:
        try:
            doc = frappe.get_doc("Sales Invoice", inv.name)

            if not doc.contact_mobile:
                frappe.logger().info(f"Skipped {doc.name}: Missing contact number.")
                continue

            result = send_invoice_whatsapp(doc.name, overdue=True)

            if result.get("status") == "Sent":
                frappe.logger().info(f"Overdue WhatsApp sent for {doc.name}")
            else:
                frappe.logger().error(f"Failed to send WhatsApp for {doc.name}: {result.get('message')}")

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Error sending overdue WhatsApp for {inv.name}")

# ✅ Move this function outside
def get_messagerider_credentials(branch_name):
    config = frappe.get_doc("Configuration")
    frappe.msgprint(f"config :{config}")
    for row in config.configuration_details:
        if row.branch == branch_name:
            return row.authtoken, row.password
    frappe.throw(f"No MessageRider credentials found for branch: {branch_name}")

# ✅ Move this function outside
def log_whatsapp_status(doc, status, response_data, file_url=None, message_type="Invoice"):
    try:
        frappe.get_doc({
            "doctype": "Whatsapp Log",
            "doctype_name": "Sales Invoice",
            "customer": doc.customer,
            "document_name": doc.name,
            "url": file_url or "",
            "status": status,
            "response": frappe.as_json(response_data),
            "message_type": message_type  # Optional: add this field in your doctype
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Failed to log WhatsApp message for {doc.name}")

def send_invoice_whatsapp(docname, overdue=False):
    doc = frappe.get_doc("Sales Invoice", docname)

    # Generate PDF
    print_format = frappe.db.get_value(
        "Property Setter",
        {"doc_type": "Sales Invoice", "property": "default_print_format"},
        "value"
    ) or "Standard"

    html = frappe.get_print("Sales Invoice", doc.name, print_format=print_format)
    pdf_content = get_pdf(html)

    file_name = f"{frappe.generate_hash('', 5)}.pdf"
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": file_name,
        "attached_to_doctype": "Sales Invoice",
        "attached_to_name": doc.name,
        "is_private": 0,
        "content": pdf_content
    })
    file_doc.save(ignore_permissions=True)
    frappe.db.commit()

    # Compose message
    customer_name = doc.customer_name or doc.customer
    amount = f"Rs. {(doc.rounded_total or 0):,.2f}"
    due_date = formatdate(doc.due_date) if doc.due_date else "Not Mentioned"

    if overdue:
        message = (
            f"Dear {customer_name}, your Sales Invoice *{doc.name}* of *{amount}* is overdue since *{due_date}*. "
            "Please make the payment at the earliest. Thank you!"
        )
    else:
        message = (
            f"Dear {customer_name}, your Sales Invoice *{doc.name}* amount is *{amount}* "
            f"and the due date is *{due_date}*. Thank you!"
        )

    # Get credentials
    authtoken, password = get_messagerider_credentials(doc.branch)

    payload = {
        "authtoken": authtoken,
        "Password": password,
        "Message": message,
        "receiverMobileNo": doc.contact_mobile
    }

    files = {
        "Uploadfile": (file_name, pdf_content, "application/pdf")
    }

    response = requests.post(
        "https://wbcapi.messagerider.com/MessageRider/SendMsg?=null",
        data=payload,
        files=files
    )

    try:
        resp_data = response.json()
    except Exception:
        resp_data = {}

    file_url = file_doc.file_url

    # Log result
    if response.status_code == 200 and resp_data.get("Status") == 1:
        log_whatsapp_status(doc, "Sent", resp_data, file_url, message_type="Overdue" if overdue else "Invoice")
        return {
            "status": "Sent",
            "message": f"WhatsApp sent to {doc.contact_mobile}.",
            "api_response": resp_data
        }
    else:
        log_whatsapp_status(doc, "Failed", resp_data, file_url, message_type="Overdue" if overdue else "Invoice")
        error_msg = resp_data.get("ErrorMessage") or resp_data.get("Message") or "Unknown error"
        return {
            "status": "Failed",
            "message": f"WhatsApp failed: {error_msg}",
            "api_response": resp_data
        }
