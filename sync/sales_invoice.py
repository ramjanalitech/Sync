import frappe

# @frappe.whitelist()
# def get_last_rates(customer, item_code):
#     selling_rate = frappe.db.sql("""
#         SELECT rate FROM `tabSales Invoice Item`
#         WHERE item_code = %s AND parenttype = 'Sales Invoice'
#         AND docstatus = 1 AND parent IN (
#             SELECT name FROM `tabSales Invoice`
#             WHERE customer = %s AND docstatus = 1
#         )
#         ORDER BY posting_date DESC, modified DESC
#         LIMIT 1
#     """, (item_code, customer), as_dict=1)

#     purchase_rate = frappe.db.sql("""
#         SELECT rate FROM `tabPurchase Invoice Item`
#         WHERE item_code = %s AND parenttype = 'Purchase Invoice'
#         AND docstatus = 1
#         ORDER BY posting_date DESC, modified DESC
#         LIMIT 1
#     """, (item_code,), as_dict=1)

#     return {
#         "selling_rate": selling_rate[0].rate if selling_rate else None,
#         "purchase_rate": purchase_rate[0].rate if purchase_rate else None
#     }

@frappe.whitelist()
def get_last_rates(customer, item_code):
    selling_rate = frappe.db.sql("""
        SELECT sii.rate FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON sii.parent = si.name
        WHERE sii.item_code = %s AND si.customer = %s
        AND si.docstatus = 1
        ORDER BY si.posting_date DESC, si.modified DESC
        LIMIT 1
    """, (item_code, customer), as_dict=1)

    purchase_rate = frappe.db.sql("""
        SELECT pii.rate FROM `tabPurchase Invoice Item` pii
        JOIN `tabPurchase Invoice` pi ON pii.parent = pi.name
        WHERE pii.item_code = %s AND pi.docstatus = 1
        ORDER BY pi.posting_date DESC, pi.modified DESC
        LIMIT 1
    """, (item_code,), as_dict=1)

    return {
        "selling_rate": selling_rate[0].rate if selling_rate else None,
        "purchase_rate": purchase_rate[0].rate if purchase_rate else None
    }
