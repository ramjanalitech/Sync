import frappe
import base64
import requests
from frappe.utils.pdf import get_pdf
from frappe.utils import formatdate
from frappe.utils import get_files_path, get_url
from frappe import _

@frappe.whitelist()
def generate_pdf_and_send_whatsapp_on_submit(doc, method=None):
    # Call the shared utility
    send_invoice_whatsapp(doc.name)

@frappe.whitelist()
def send_invoice_whatsapp_button(docname):
    doc = frappe.get_doc("Sales Invoice", docname)

    invoice = {
        "name": doc.name,
        "customer": doc.customer,
        "contact_mobile": doc.contact_mobile
    }

    if not doc.contact_mobile:
        frappe.throw(_("Contact number is missing. Please update the customer's mobile number."))

    # Optional: log or debug
    frappe.msgprint(f"Sending WhatsApp for invoice: {invoice['name']}")
    
    return send_invoice_whatsapp(invoice)

def get_messagerider_credentials(branch_name):
    config = frappe.get_doc("Configuration")
    for row in config.configuration_details:
        if row.branch == branch_name:
            return row.authtoken, row.password
    frappe.throw(f"No MessageRider credentials found for branch: {branch_name}")

def send_invoice_whatsapp(docname):
    doc = frappe.get_doc("Sales Invoice", docname)

    # Generate PDF
    print_format = frappe.db.get_value(
        "Property Setter",
        {"doc_type": "Sales Invoice", "property": "default_print_format"},
        "value"
    ) or "Standard"

    # Generate HTML using that print format
    html = frappe.get_print(
        "Sales Invoice",
        doc.name,
        print_format=print_format
    )

    # Convert HTML to PDF
    pdf_content = get_pdf(html)

    # Save File
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

    # WhatsApp message
    customer_name = doc.customer_name or doc.customer
    amount = f"Rs. {(doc.rounded_total or 0):,.2f}"
    # due_date = doc.due_date or "Not Mentioned"
    due_date = formatdate(doc.due_date) if doc.due_date else "Not Mentioned"

    message = (
        f"Dear {customer_name}, your Sales Invoice *{doc.name}* amount is *{amount}* "
        f"and the due date is *{due_date}*. Thank you!"
    )
    
    # if doc.branch in ["Pimpri", "Pune City"]:
    #     authtoken = frappe.conf.get("messagerider_authtoken_pimpri")
    #     password = frappe.conf.get("messagerider_password_pimpri")
    #     frappe.msgprint(f"authtoken : {authtoken}")
    #     frappe.msgprint(f"password : {password}")
    # elif doc.branch in ["Vapi"]:
    #     authtoken = frappe.conf.get("messagerider_authtoken_vapi")
    #     password = frappe.conf.get("messagerider_password_vapi")
    #     frappe.msgprint(f"authtoken : {authtoken}")
    #     frappe.msgprint(f"password : {password}")
    # else:
    #     authtoken = frappe.conf.get("messagerider_authtoken_ahmedabad")
    #     password = frappe.conf.get("messagerider_password_ahmedabad")
    #     frappe.msgprint(f"authtoken : {authtoken}")
    #     frappe.msgprint(f"password : {password}")

    # Fetch credentials based on branch
    authtoken, password = get_messagerider_credentials(doc.branch)
    frappe.msgprint(f"authtoken: {authtoken}")
    frappe.msgprint(f"password: {password}")

    payload = {
        # "authtoken": "0000091",
        # "Password": "Admin@#1",
        "authtoken": authtoken,
        "Password": password,
        "Message": message,
        "receiverMobileNo": doc.contact_mobile
    }
    frappe.msgprint(f"payload :{payload}")
    files = {
        "Uploadfile": (file_name, pdf_content, "application/pdf")
    }

    response = requests.post(
        # "http://wb3api.messagerider.com/MessageRider/SendMsg",
        "https://wbcapi.messagerider.com/MessageRider/SendMsg?=null",
        data=payload,
        files=files
    )

    try:
        resp_data = response.json()
    except Exception:
        resp_data = {}

    if response.status_code == 200 and resp_data.get("Status") == 1:
        return {
            "status": "Sent",
            "message": f"WhatsApp sent to {doc.contact_mobile}.",
            "api_response": resp_data
        }
    else:
        error_msg = resp_data.get("ErrorMessage") or resp_data.get("Message") or "Unknown error"
        return {
            "status": "Failed",
            "message": f"WhatsApp failed: {error_msg}",
            "api_response": resp_data
        }


@frappe.whitelist()
def send_whatsapp_with_pdf(file_url, file_name, doc):
    try:
        full_url = get_url() + file_url
        response = requests.get(full_url)
        file_bytes = response.content

        # Compose WhatsApp message
        customer_name = doc.customer_name or doc.customer
        amount = f"₹{doc.rounded_total:,.2f}"
        due_date = doc.due_date or "Not Mentioned"

        message = (
            f"Dear {customer_name}, your Sales Invoice *{doc.name}* amount is *{amount}* "
            f"and the due date is *{due_date}*. Thank you!"
        )

        payload = {
            "authtoken": "0000091",
            "Password": "Admin@#1",
            #"Message": f"Invoice {doc.name}",
            "Message": message,
            "receiverMobileNo": doc.contact_mobile  # Ensure this field exists
        }

        files = {
            "Uploadfile": (file_name, file_bytes, "application/pdf")
        }

        resp = requests.post(
            "http://wb3api.messagerider.com/MessageRider/SendMsg",
            data=payload,
            files=files
        )

        try:
            resp_data = resp.json()
        except Exception:
            resp_data = {}

        if resp.status_code == 200 and resp_data.get("Status") == 1:
            frappe.logger().info(f"WhatsApp sent successfully for {doc.name}")
        else:
            err_msg = resp_data.get("ErrorMessage") or resp_data.get("Message") or "Unknown error"
            frappe.logger().error(f"WhatsApp failed for {doc.name}: {err_msg}")

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Error sending WhatsApp for {doc.name}")
