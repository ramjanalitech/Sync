import frappe
import requests
import json

@frappe.whitelist()
def create_stock_entry_in_second_site(stock_entry_data):
    # Convert the string to a dictionary
    stock_entry_data = frappe.parse_json(stock_entry_data)

    # # API details for xyz.fortunes.space (target instance)
    # XYZ_URL = "https://xyz.fortunes.space/api/resource/Stock Entry"
    # XYZ_API_KEY = "0a73d7be214fc77"
    # XYZ_API_SECRET = "c0299c4c760368e"

    # Fetch API details from Sync Setting doctype
    sync_settings = frappe.get_doc("Sync Setting", "Sync Setting")  # Assuming there's only one document
    XYZ_URL = sync_settings.api_url + "/api/resource/Stock Entry"
    XYZ_API_KEY = sync_settings.api_key
    XYZ_API_SECRET = sync_settings.api_secret
    
    # Prepare the payload for the second site
    payload = {
        "stock_entry_type": "Material Receipt",  # Use the same stock entry type
        "from_warehouse": stock_entry_data.get("from_warehouse"),
        "to_warehouse": stock_entry_data.get("to_warehouse"),
        "items": []
    }

    # Add items to the payload
    for item in stock_entry_data.get("items", []):
        # Prepare the item payload
        item_payload = {
            "item_code": item.get("item_code"),
            "qty": item.get("qty"),
            "uom": item.get("uom"),
            "basic_rate": item.get("basic_rate"),
            "valuation_rate": item.get("valuation_rate"),  # Add valuation_rate
            "warehouse": item.get("warehouse"),
            "target_warehouse": item.get("target_warehouse"),  # Add target_warehouse
            "serial_no": item.get("serial_no")
        }

        # Handle serial numbers (if applicable)
        if item.get("has_serial_no"):  # Check if the item has serial numbers
            serial_nos = item.get("serial_no")  # Get the serial numbers
            if serial_nos:
                # Ensure serial numbers are provided and valid
                if isinstance(serial_nos, str):
                    serial_nos = serial_nos.split("\n")  # Split serial numbers if they are in a string
                item_payload["serial_no"] = "\n".join(serial_nos)  # Add serial numbers to the payload
            else:
                frappe.throw(f"Serial numbers are required for item {item.get('item_code')}")

        payload["items"].append(item_payload)

    # Send the API request to create the stock entry in the second site
    headers = {
        "Authorization": f"token {XYZ_API_KEY}:{XYZ_API_SECRET}",
        "Content-Type": "application/json"
    }
    response = requests.post(XYZ_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return "Stock entry created successfully in the second site."
    else:
        frappe.throw(f"Failed to create stock entry in the second site: {response.status_code} - {response.text}")