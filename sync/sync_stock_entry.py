import frappe
import requests
import json
from frappe.utils import nowdate

@frappe.whitelist()
def create_stock_entry_in_second_site(stock_entry_data):
    """
    Sync Stock Entry to a second site via API.
    """
    stock_entry_data = frappe.parse_json(stock_entry_data)
    sync_settings = get_sync_settings()

    # Prepare payload for the second site
    payload = prepare_stock_entry_payload(stock_entry_data)

    # Send API request to the second site
    response = send_api_request(sync_settings, payload)

    # Process API response
    if response.status_code == 200:
        log_successful_sync(stock_entry_data, response)
        return "Stock entry created successfully in the second site."
    else:
        log_failed_sync(stock_entry_data, response, payload)
        frappe.throw(f"Failed to create stock entry in the second site: {response.status_code} - {response.text}")

@frappe.whitelist()
def create_sales_invoice_from_stock_entry(stock_entry, sales_customer):
    """
    Create a Sales Invoice from a Stock Entry.
    """
    stock_entry = frappe.parse_json(stock_entry)
    validate_customer(sales_customer)

    # Create and save Sales Invoice
    sales_invoice = create_sales_invoice(stock_entry, sales_customer)
    log_sales_invoice_creation(sales_invoice, stock_entry)

    return sales_invoice.name

# Helper Functions

def get_sync_settings():
    """
    Fetch API details from Sync Setting doctype.
    """
    sync_settings = frappe.get_doc("Sync Setting", "Sync Setting")
    if not sync_settings.sync_url or not sync_settings.api_key or not sync_settings.api_secret:
        frappe.throw("API URL, API Key, or API Secret is missing in Sync Setting.")
    return sync_settings

def prepare_stock_entry_payload(stock_entry_data):
    """
    Prepare payload for Stock Entry API request.
    """
    payload = {
        "stock_entry_type": "Material Receipt",
        "from_warehouse": stock_entry_data.get("from_warehouse"),
        "to_warehouse": stock_entry_data.get("to_warehouse"),
        "items": []
    }

    for item in stock_entry_data.get("items", []):
        item_payload = prepare_item_payload(item)
        payload["items"].append(item_payload)

    return payload

def prepare_item_payload(item):
    """
    Prepare payload for an item in the Stock Entry.
    """
    item_payload = {
        "item_code": item.get("item_code"),
        "qty": item.get("qty"),
        "uom": item.get("uom"),
        "basic_rate": item.get("basic_rate"),
        "valuation_rate": item.get("valuation_rate"),
        "warehouse": item.get("warehouse"),
        "target_warehouse": item.get("target_warehouse"),
        "serial_no": item.get("serial_no")
    }

    if item.get("has_serial_no"):
        serial_nos = item.get("serial_no")
        if serial_nos:
            if isinstance(serial_nos, str):
                serial_nos = serial_nos.split("\n")
            item_payload["serial_no"] = "\n".join(serial_nos)
        else:
            frappe.throw(f"Serial numbers are required for item {item.get('item_code')}.")

    return item_payload

def send_api_request(sync_settings, payload):
    """
    Send API request to the second site.
    """
    headers = {
        "Authorization": f"token {sync_settings.api_key}:{sync_settings.api_secret}",
        "Content-Type": "application/json"
    }
    try:
        return requests.post(
            f"{sync_settings.sync_url}/api/resource/Stock Entry",
            headers=headers,
            json=payload,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"API Request Failed: {str(e)}", "Stock Entry Sync Error")
        frappe.throw("Failed to connect to the second site. Please check the API settings and try again.")

def log_successful_sync(stock_entry_data, response):
    """
    Log successful sync in Event Sync Log.
    """
    second_site_docname = response.json().get("data", {}).get("name")
    frappe.msgprint(f"second_site_docname:{second_site_docname}")
    frappe.get_doc({
        "doctype": "Event Sync Log",
        "document_type": "Stock Entry",
        "document_number": stock_entry_data.get("name"),
        "synced_document_number": second_site_docname,
        "status": "Synced",
        "message": "Stock entry successfully created on both sites."
    }).insert(ignore_permissions=True)

def log_failed_sync(stock_entry_data, response, payload):
    """
    Log failed sync in Event Sync Log.
    """
    frappe.log_error(f"API Response: {response.text}\nPayload: {payload}", "Stock Entry Sync Error")
    frappe.get_doc({
        "doctype": "Event Sync Log",
        "document_type": "Stock Entry",
        "document_number": stock_entry_data.get("name"),
        "status": "Failed",
        "message": f"Failed to create stock entry: {response.status_code} - {response.text}"
    }).insert(ignore_permissions=True)

def validate_customer(customer):
    """
    Validate customer existence.
    """
    if not customer:
        frappe.throw("Customer is not provided. Please provide a customer.")
    if not frappe.db.exists("Customer", customer):
        frappe.throw(f"Customer '{customer}' does not exist. Please provide a valid customer.")


def validate_item(item):
    """
    Validate item details.
    """
    if not item.get("valuation_rate") or float(item.get("valuation_rate", 0)) <= 0:
        frappe.throw(f"Invalid valuation rate for item {item.get('item_code')}.")
    if not item.get("qty") or float(item.get("qty", 0)) <= 0:
        frappe.throw(f"Invalid quantity for item {item.get('item_code')}.")
    if not frappe.db.exists("Warehouse", item.get("t_warehouse")):
        frappe.throw(f"Target warehouse {item.get('t_warehouse')} does not exist.")

def log_sales_invoice_creation(sales_invoice, stock_entry):
    """
    Log Sales Invoice creation in Event Sync Log.
    """
    frappe.get_doc({
        "doctype": "Event Sync Log",
        "document_type": "Sales Invoice",
        "document_number": sales_invoice.name,
        "status": "Synced",
        "message": f"Sales Invoice drafted from Stock Entry {stock_entry.get('name')}."
    }).insert(ignore_permissions=True)

def prepare_sales_invoice_item(item):
    """
    Prepare item payload for Sales Invoice.
    """
    frappe.msgprint(f"Item: {item.get('item_code')}, Serial No: {item.get('serial_no')}")  # Debugging log
    item_payload = {
        "item_code": item.get("item_code"),
        "qty": item.get("qty"),
        "rate": item.get("valuation_rate"),
        "warehouse": item.get("t_warehouse")
    }

    # Handle serial numbers for serialized items
    if item.get("has_serial_no"):
        serial_nos = item.get("serial_no")
        if serial_nos:
            if isinstance(serial_nos, str):
                serial_nos = serial_nos.split("\n")
            item_payload["serial_no"] = "\n".join(serial_nos)  # Add serial numbers to the payload
        else:
            frappe.throw(f"Serial numbers are required for item {item.get('item_code')}.")

    return item_payload

def create_sales_invoice(stock_entry, customer):
    """
    Create and save a Sales Invoice.
    """
    sales_invoice = frappe.new_doc("Sales Invoice")
    sync_settings = frappe.get_doc("Sync Setting", "Sync Setting")
    
    # Set basic details
    sales_invoice.customer = customer
    sales_invoice.posting_date = nowdate()
    sales_invoice.due_date = nowdate()
    sales_invoice.company = stock_entry.get("company")
    sales_invoice.set_warehouse = stock_entry.get("to_warehouse")
    sales_invoice.update_stock = 1  # Ensure stock is updated
    
    # Set payment terms template if valid
    if sync_settings.get("payment_terms_template") and frappe.db.exists("Payment Terms Template", sync_settings.payment_terms_template):
        sales_invoice.payment_terms_template = sync_settings.payment_terms_template
    else:
        frappe.msgprint("Payment Terms Template is not set or invalid. Proceeding without it.")
    
    # Add items to the Sales Invoice
    for item in stock_entry.get("items", []):
        validate_item(item)
        item_payload = prepare_sales_invoice_item(item)
        sales_invoice.append("items", item_payload)
        frappe.msgprint(f"Item Added: {item_payload}")  # Debugging log
    
    # Save the Sales Invoice as a draft
    sales_invoice.insert(ignore_permissions=True)
    return sales_invoice