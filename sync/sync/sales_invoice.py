import frappe

# @frappe.whitelist()
# def get_last_selling_rate(customer, item_code):
#     result = frappe.db.sql("""
#         SELECT sii.rate
#         FROM `tabSales Invoice Item` sii
#         JOIN `tabSales Invoice` si ON sii.parent = si.name
#         WHERE si.customer = %s
#           AND sii.item_code = %s
#           AND si.docstatus = 1
#         ORDER BY si.posting_date DESC, si.creation DESC
#         LIMIT 1
#     """, (customer, item_code), as_dict=True)

#     # frappe.msgprint(f"Result: {result}")

#     return result[0]["rate"] if result else None

@frappe.whitelist()
def get_last_selling_rate(customer, item_code):
    result = frappe.db.sql("""
        SELECT sii.rate
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON sii.parent = si.name
        WHERE si.customer = %s
          AND sii.item_code = %s
          AND si.docstatus = 1
        ORDER BY si.posting_date DESC, si.creation DESC, si.name DESC
        LIMIT 1
    """, (customer, item_code), as_dict=True)

    return result[0]["rate"] if result else None
