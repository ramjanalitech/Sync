import frappe
import requests
import json
import base64
import time
from frappe.utils import nowdate, get_url, get_site_path
from frappe.utils.file_manager import save_file

# Manual trigger
@frappe.whitelist()
def whatsapp_get_doc(doc, method=None):
    try:
        doc = json.loads(doc)
        invoice = {
            "name": doc["name"],
            "customer": doc["customer"],
            "contact_mobile": doc["contact_mobile"]
        }

        frappe.msgprint(f"contact_mobile : {doc['contact_mobile']}")

        # Send WhatsApp and return the response
        return send_invoice_whatsapp(invoice)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in whatsapp_get_doc")
        return f"Error: {str(e)}"

# # Send Sales Invoice via WhatsApp (MessageRider API)
def send_invoice_whatsapp(invoice):
    try:
        pdf_link = get_sales_invoice_pdf_link(invoice["name"])
        frappe.msgprint(f"pdf_link : {pdf_link}")
        response = requests.get(pdf_link)
        frappe.msgprint(f"response : {response}")
        file_bytes = response.content
        frappe.msgprint(f"file_bytes : {file_bytes}")
        file_name = f"{invoice['name']}.pdf"
        frappe.msgprint(f"file_name : {file_name}")

        payload = {
            "authtoken": "0000091",
            "Password": "Admin@#1",
            "Message": invoice["name"],
            "receiverMobileNo": invoice["contact_mobile"]
        }

        files = {
            "Uploadfile": (file_name, file_bytes, "application/pdf")
        }

        frappe.msgprint(f"payload : {payload}")
        response = requests.post(
            "http://wb3api.messagerider.com/MessageRider/SendMsg",
            data=payload,
            files=files
        )

        try:
            resp_data = response.json()
            frappe.msgprint(f"resp_data : {resp_data}")
        except Exception:
            resp_data = {}

        if response.status_code == 200 and resp_data.get("Status") == 1:
            status = "Sent"
            message = f"WhatsApp sent successfully for {invoice['name']}."
        else:
            status = "Not Sent"
            error_msg = resp_data.get("ErrorMessage") or resp_data.get("Message") or "Unknown error"
            message = f"WhatsApp failed for {invoice['name']}: {error_msg}"

        frappe.msgprint(message)
        return {
            "status": status,
            "message": message,
            "api_response": resp_data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error sending WhatsApp for {invoice['name']}")
        return {
            "status": "Error",
            "message": f"Exception occurred: {str(e)}"
        }

# Get PDF print link for public access
def get_sales_invoice_pdf_link(docname):
    try:
        doc = frappe.get_doc("Sales Invoice", docname)
        key = doc.get_document_share_key(expires_on=None, no_expiry=True)

        print_format = (
            frappe.db.get_value("Property Setter", {
                "doc_type": "Sales Invoice",
                "property": "default_print_format"
            }, "value") or "Standard"
        )
        
        return (
            f"{get_url()}/api/method/frappe.utils.print_format.download_pdf"
            f"?doctype=Sales%20Invoice&name={docname}&format={print_format}&key={key}"
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error generating PDF link")
        frappe.throw("Failed to generate PDF link.")

# # Download the PDF and save it publicly in ERPNext
# def pdfurl_generate(pdf_link, doctype, docname):
#     try:
#         response = requests.get(pdf_link)
#         file_name = f"{frappe.generate_hash('', 5)}.pdf"
#         file_path = f"/public/files/{file_name}"

#         with open(get_site_path() + file_path, "wb") as file:
#             file.write(response.content)

#         saved_file = save_file(
#             fname=file_name,
#             content=base64.b64encode(response.content),
#             dt=doctype,
#             dn=docname,
#             decode=True,
#             is_private=0,
#         )
#         return get_url() + saved_file.file_url

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Error in pdfurl_generate")
#         frappe.throw("Failed to generate PDF URL.")

def pdfurl_generate(pdf_link, doctype, docname):
    try:
        max_retries = 5
        min_pdf_size = 5000  # 5 KB minimum size for a valid PDF

        for attempt in range(max_retries):
            response = requests.get(pdf_link)
            
            if (
                response.status_code == 200
                and response.headers.get("Content-Type") == "application/pdf"
                and len(response.content) > min_pdf_size
            ):
                break

            time.sleep(2)  # wait before retrying

        # Final check before saving
        if not response or len(response.content) <= min_pdf_size:
            frappe.throw("PDF could not be generated correctly. Try again later.")

        file_name = f"{frappe.generate_hash('', 5)}.pdf"
        file_path = f"/public/files/{file_name}"

        with open(get_site_path() + file_path, "wb") as f:
            f.write(response.content)

        saved_file = save_file(
            fname=file_name,
            content=base64.b64encode(response.content),
            dt=doctype,
            dn=docname,
            decode=True,
            is_private=0,
        )

        return get_url() + saved_file.file_url

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error in pdfurl_generate")
        frappe.throw("Failed to generate PDF URL.")

### New Code
        
@frappe.whitelist()
def pdfurl_generate_new(pdf_link, doctype, docname):
    try:
        max_retries = 5
        min_pdf_size = 5000  # 5 KB minimum

        response = None

        for attempt in range(max_retries):
            response = requests.get(pdf_link)
            if (
                response.status_code == 200
                and response.headers.get("Content-Type") == "application/pdf"
                and len(response.content) > min_pdf_size
            ):
                break
            time.sleep(2)  # wait before retrying

        # Final safety check
        if not response or response.status_code != 200 or len(response.content) <= min_pdf_size:
            frappe.throw("PDF could not be generated correctly. Please try again.")

        file_name = f"{frappe.generate_hash('', 5)}.pdf"
        file_path = f"/public/files/{file_name}"

        with open(get_site_path() + file_path, "wb") as f:
            f.write(response.content)

        saved_file = save_file(
            fname=file_name,
            content=base64.b64encode(response.content),
            dt=doctype,
            dn=docname,
            decode=True,
            is_private=0,
        )

        return get_url() + saved_file.file_url

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error in pdfurl_generate_new")
        frappe.throw("Failed to generate PDF URL.")


############# New Version ############
        
# import frappe
# import json
# import base64
# import requests
# from frappe.utils.pdf import get_pdf
# from frappe.utils import get_files_path
# from frappe import _
# from frappe.utils.file_manager import save_file

# @frappe.whitelist()
# def whatsapp_get_doc(doc, method=None):
#     try:
#         doc = json.loads(doc)
#         invoice = {
#             "name": doc["name"],
#             "customer": doc["customer"],
#             "contact_mobile": doc["contact_mobile"]
#         }

#         frappe.msgprint(f"contact_mobile : {doc['contact_mobile']}")

#         return send_invoice_whatsapp(invoice)

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Error in whatsapp_get_doc")
#         return f"Error: {str(e)}"

# def send_invoice_whatsapp(invoice):
#     try:
#         doc = frappe.get_doc("Sales Invoice", invoice["name"])

#         # Generate PDF directly using frappe.print_format
#         pdf_content = get_pdf(
#             frappe.get_print(
#                 "Sales Invoice",
#                 invoice["name"],
#                 print_format=doc.get("print_format") or "Standard",
#                 as_pdf=True
#             )
#         )

#         if not pdf_content or len(pdf_content) < 5000:
#             frappe.throw("PDF could not be generated properly.")

#         file_name = f"{invoice['name']}.pdf"

#         # Save file in File doctype
#         saved_file = save_file(
#             fname=file_name,
#             content=base64.b64encode(pdf_content),
#             dt="Sales Invoice",
#             dn=invoice["name"],
#             decode=True,
#             is_private=0,
#         )

#         frappe.msgprint(f"PDF saved: {saved_file.file_url}")

#         # Send to MessageRider
#         payload = {
#             "authtoken": "0000091",
#             "Password": "Admin@#1",
#             "Message": invoice["name"],
#             "receiverMobileNo": invoice["contact_mobile"]
#         }

#         files = {
#             "Uploadfile": (file_name, pdf_content, "application/pdf")
#         }

#         response = requests.post(
#             "http://wb3api.messagerider.com/MessageRider/SendMsg",
#             data=payload,
#             files=files
#         )

#         try:
#             resp_data = response.json()
#         except Exception:
#             resp_data = {}

#         if response.status_code == 200 and resp_data.get("Status") == 1:
#             message = f"WhatsApp sent successfully for {invoice['name']}."
#         else:
#             error_msg = resp_data.get("ErrorMessage") or resp_data.get("Message") or "Unknown error"
#             message = f"WhatsApp failed for {invoice['name']}: {error_msg}"

#         frappe.msgprint(message)
#         return {
#             "status": "Sent" if "successfully" in message else "Failed",
#             "message": message,
#             "api_response": resp_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), f"Error sending WhatsApp for {invoice['name']}")
#         return {
#             "status": "Error",
#             "message": f"Exception occurred: {str(e)}"
#         }

####### Imdad Code 
        
import frappe
import json
import base64
import requests
from frappe.utils.pdf import get_pdf
from frappe.utils import get_url
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def whatsapp_get_doc(doc, method=None):
    try:
        doc = json.loads(doc)
        invoice = {
            "name": doc["name"],
            "customer": doc["customer"],
            "contact_mobile": doc["contact_mobile"]
        }

        return send_invoice_whatsapp(invoice)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in whatsapp_get_doc")
        return f"Error: {str(e)}"

def send_invoice_whatsapp(invoice):
    try:
        doc = frappe.get_doc("Sales Invoice", invoice["name"])

        # Generate PDF from the Sales Invoice
        pdf_content = get_pdf(
            frappe.get_print(
                "Sales Invoice",
                invoice["name"],
                print_format=doc.get("print_format") or "Standard",
                as_pdf=True
            )
        )

        if not pdf_content or len(pdf_content) < 5000:
            frappe.throw("PDF could not be generated properly.")

        # Save the PDF file to public files
        file_name = f"{invoice['name']}.pdf"
        saved_file = save_file(
            fname=file_name,
            content=base64.b64encode(pdf_content),
            dt="Sales Invoice",
            dn=invoice["name"],
            decode=True,
            is_private=0,
        )

        # Construct the public media URL
        media_url = get_url() + saved_file.file_url

        # Construct the WhatsApp message
        message = f"Dear {invoice['customer']}, please find your Sales Invoice here."

        # Construct the WhatsApp API URL
        api_url = (
            "http://wapi.jrad.in:8089/api/send_message.php"
            "?token=dHo59guygpFd7rvzLzNkwlMz6jZSvkbg"
            "&instanceName=Prism"
            f"&number=91{invoice['contact_mobile']}"
            f"&text={message}"
            "&is_media=1"
            f"&media={media_url}"
        )

        frappe.msgprint(f"api_url :{api_url}")
        response = requests.get(api_url)

        try:
            result = response.json()
        except Exception:
            result = {"status": "error", "message": response.text}

        if response.status_code == 200 and result.get("status") == "success":
            status = "Sent"
            message = f"WhatsApp sent successfully for {invoice['name']}."
        else:
            status = "Failed"
            message = f"WhatsApp failed for {invoice['name']}: {result.get('message')}"

        frappe.msgprint(message)
        return {
            "status": status,
            "message": message,
            "api_response": result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error sending WhatsApp for {invoice['name']}")
        return {
            "status": "Error",
            "message": f"Exception occurred: {str(e)}"
        }

