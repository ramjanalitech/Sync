import frappe
from frappe.utils import nowdate

def on_submit(doc, method):
    # Check if the stock entry type is "Material Receipt"
    if doc.stock_entry_type == "Material Receipt":
        # Create a new Sales Invoice
        sales_invoice = frappe.new_doc("Sales Invoice")
        
        # Set basic details for the Sales Invoice
        sales_invoice.customer = "Your Customer Name"  # Replace with the actual customer name
        sales_invoice.posting_date = nowdate()
        sales_invoice.due_date = nowdate()
        sales_invoice.company = doc.company
        
        # Add items to the Sales Invoice from the Stock Entry
        for item in doc.items:
            sales_invoice.append("items", {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.valuation_rate,  # Use valuation rate from the stock entry
                "warehouse": item.t_warehouse  # Use target warehouse from the stock entry
            })
        
        # Save and submit the Sales Invoice
        sales_invoice.insert(ignore_permissions=True)
        sales_invoice.submit()
        
        # Link the Sales Invoice to the Stock Entry (optional)
        frappe.msgprint(f"Sales Invoice {sales_invoice.name} created successfully.")