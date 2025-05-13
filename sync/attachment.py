# # your_app/api.py

# import frappe
# import requests
# import time
# import base64
# from frappe.utils import get_url, get_site_path
# from frappe.utils.file_manager import save_file

# # On submit → generate PDF and attach
# # def generate_and_attach_pdf(doc, method):
# #     try:
# #         # Get the PDF link
# #         pdf_link = get_sales_invoice_pdf_link(doc.name)

# #         # Download and save the PDF
# #         pdfurl_generate(pdf_link, "Sales Invoice", doc.name)

# #         frappe.msgprint("PDF generated and attached successfully.")

# #     except Exception:
# #         frappe.log_error(frappe.get_traceback(), "Error generating and saving Sales Invoice PDF")
# #         frappe.throw("Failed to generate and save PDF.")

# # Create public shareable PDF link
# def get_sales_invoice_pdf_link(docname):
#     try:
#         doc = frappe.get_doc("Sales Invoice", docname)
#         key = doc.get_document_share_key(expires_on=None, no_expiry=True)

#         print_format = (
#             frappe.db.get_value("Property Setter", {
#                 "doc_type": "Sales Invoice",
#                 "property": "default_print_format"
#             }, "value") or "Standard"
#         )

#         return (
#             f"{get_url()}/api/method/frappe.utils.print_format.download_pdf"
#             f"?doctype=Sales%20Invoice&name={docname}&format={print_format}&key={key}"
#         )

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Error generating PDF link")
#         frappe.throw("Failed to generate PDF link.")

# # Download PDF from link and save to Sales Invoice
# def pdfurl_generate(pdf_link, doctype, docname):
#     try:
#         max_retries = 5
#         min_pdf_size = 5000  # Minimum 5KB valid PDF

#         for attempt in range(max_retries):
#             response = requests.get(pdf_link)

#             if (
#                 response.status_code == 200
#                 and response.headers.get("Content-Type") == "application/pdf"
#                 and len(response.content) > min_pdf_size
#             ):
#                 break

#             time.sleep(2)  # wait before retrying

#         # Final check
#         if not response or len(response.content) <= min_pdf_size:
#             frappe.throw("PDF could not be generated properly. Try again later.")

#         # Save file
#         file_name = f"{frappe.generate_hash('', 5)}.pdf"
#         file_path = f"/public/files/{file_name}"

#         with open(get_site_path() + file_path, "wb") as f:
#             f.write(response.content)

#         saved_file = save_file(
#             fname=file_name,
#             content=base64.b64encode(response.content),
#             dt=doctype,
#             dn=docname,
#             decode=True,
#             is_private=0,
#         )

#         return get_url() + saved_file.file_url

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Error downloading PDF")
#         frappe.throw("Failed to download and save PDF.")

# def generate_and_attach_pdf(doc, method):
#     # Enqueue the PDF generation AFTER transaction commits
#     frappe.enqueue(
#         method="sync.attachment.generate_and_attach_pdf_background",
#         queue="default",
#         timeout=300,
#         is_async=True,
#         docname=doc.name
#     )

# def generate_and_attach_pdf_background(docname):
#     try:
#         # Now safe to fetch document
#         frappe.db.commit()  # Ensure all writes are saved
#         frappe.sleep(5)  # Wait 5 seconds to allow background processes

#         pdf_link = get_sales_invoice_pdf_link(docname)
#         pdfurl_generate(pdf_link, "Sales Invoice", docname)

#         frappe.logger().info(f"PDF generated and saved for {docname}")

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), f"Error generating PDF for {docname}")

import frappe
from frappe.utils import get_files_path
from frappe.utils.pdf import get_pdf
from frappe import _

def generate_pdf_on_submit(doc, method=None):
    try:
        # Get PDF content directly
        pdf_content = get_pdf(
            frappe.get_print(
                "Sales Invoice",
                doc.name,
                print_format=doc.get("print_format") or "Standard",
                as_pdf=True
            )
        )

        if not pdf_content:
            frappe.throw(_("Failed to generate PDF for Sales Invoice {0}").format(doc.name))

        # Save file
        file_name = f"{frappe.generate_hash('', 5)}.pdf"
        file_path = get_files_path(file_name)

        with open(file_path, "wb") as f:
            f.write(pdf_content)

        # Attach file to Sales Invoice
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

        frappe.logger().info(f"Successfully generated and attached PDF for {doc.name}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error generating PDF on submit")
        frappe.throw(_("Error generating PDF. Please try again."))
