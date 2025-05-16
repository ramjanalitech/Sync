import frappe
from frappe.utils import get_files_path
from frappe.utils.pdf import get_pdf
from frappe import _

def generate_pdf_on_submit(doc, method=None):
    try:
        # Generate HTML and convert to PDF
        html = frappe.get_print(
            "Sales Invoice",
            doc.name,
            print_format=doc.get("print_format") or "Standard"
        )
        pdf_content = get_pdf(html)

        if not pdf_content:
            frappe.throw(_("Failed to generate PDF for Sales Invoice {0}").format(doc.name))

        # Save file
        file_name = f"{doc.name}.pdf"
        file_path = get_files_path(file_name)

        with open(file_path, "wb") as f:
            f.write(pdf_content)

        # Attach to document
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
