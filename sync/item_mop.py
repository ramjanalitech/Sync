import frappe


ALLOWED_MOP_USERS = [
    "Administrator",
    "prieshgada@gmail.com"
]


def validate_mop(doc, method=None):

    # New Item
    if doc.is_new():
        return

    # Get old document
    old_doc = doc.get_doc_before_save()

    if not old_doc:
        return

    old_mop = frappe.utils.flt(
        old_doc.get("mop")
    )

    new_mop = frappe.utils.flt(
        doc.get("mop")
    )

    # Nothing changed
    if old_mop == new_mop:
        return

    # User is authorized
    if frappe.session.user in ALLOWED_MOP_USERS:
        return

    frappe.throw(
        "You are not authorized to create or modify MOP."
    )