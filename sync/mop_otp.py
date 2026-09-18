import frappe
import random
import requests
import json
import hashlib


# ============================================================
# SETTINGS
# ============================================================

OTP_EXPIRY = 300  # 5 minutes

# MOP_OTP_MOBILE = "7698737440"
MOP_OTP_MOBILE = "8423594555"


MESSAGE_RIDER_URL = (
    "https://wbcapi.messagerider.com/MessageRider/SendMsg"
)

# IMPORTANT:
# It is better to move these credentials to Site Config,
# System Settings, or a custom Settings doctype.
MESSAGE_RIDER_AUTHTOKEN = "0000146"
MESSAGE_RIDER_PASSWORD = "Prism@2025"


# ============================================================
# MOP ITEMS FROM SALES INVOICE DOCUMENT
# ============================================================

def get_mop_items(doc):
    """
    Get all Sales Invoice items where:

        Rate < Item Master MOP

    IMPORTANT:
    MOP is fetched directly from Item Master.
    We do NOT trust row.mop for server-side validation.
    """

    items = []

    for row in doc.get("items") or []:

        if not row.item_code:
            continue

        rate = frappe.utils.flt(row.rate)

        # Always fetch MOP from Item Master
        mop = frappe.utils.flt(
            frappe.db.get_value(
                "Item",
                row.item_code,
                "mop"
            )
        )

        # Rate >= MOP = normal transaction
        # Rate < MOP = OTP required
        if mop > 0 and rate < mop:

            items.append({
                "idx": row.idx,
                "item_code": row.item_code,
                "rate": rate,
                "mop": mop
            })

    return items


# ============================================================
# GET MOP ITEMS FROM CLIENT REQUEST
# ============================================================

def get_mop_items_from_request(items):
    """
    Build MOP violation list from client-provided item/rate data.

    IMPORTANT:
    Client MOP value is ignored.

    Only:
        item_code
        rate
        idx

    are accepted from browser.

    MOP is fetched directly from Item Master.
    """

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            frappe.throw("Invalid MOP item data.")

    if not isinstance(items, list):
        frappe.throw("Invalid MOP item data.")

    mop_items = []

    for row in items:

        item_code = row.get("item_code")

        if not item_code:
            continue

        rate = frappe.utils.flt(row.get("rate"))

        # Fetch MOP from Item Master
        mop = frappe.utils.flt(
            frappe.db.get_value(
                "Item",
                item_code,
                "mop"
            )
        )

        if mop > 0 and rate < mop:

            mop_items.append({
                "idx": row.get("idx"),
                "item_code": item_code,
                "rate": rate,
                "mop": mop
            })

    return mop_items


# ============================================================
# FINGERPRINT
# ============================================================

def get_mop_fingerprint(mop_items):
    """
    Generate a unique fingerprint for the exact MOP violation.

    Fingerprint includes:

        Item
        Row index
        Rate
        MOP

    Therefore, an OTP approved for:

        Item A = Rate 80 / MOP 100

    cannot be reused after changing the rate to:

        Item A = Rate 70 / MOP 100
    """

    normalized = []

    for row in mop_items:

        normalized.append({
            "idx": int(row.get("idx") or 0),
            "item_code": str(row.get("item_code") or ""),
            "rate": round(frappe.utils.flt(row.get("rate")), 6),
            "mop": round(frappe.utils.flt(row.get("mop")), 6),
        })

    normalized.sort(
        key=lambda x: (
            x["idx"],
            x["item_code"]
        )
    )

    raw_data = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        raw_data.encode("utf-8")
    ).hexdigest()


# ============================================================
# CACHE KEYS
# ============================================================

def get_otp_cache_key(token):
    """
    Temporary OTP cache.
    """

    return f"mop_otp_{token}"


def get_approval_cache_key(user, fingerprint):
    """
    OTP approval cache.

    Approval is tied to:

        User
        Exact invoice MOP fingerprint
    """

    user = str(user or "").replace(" ", "_")

    return (
        f"mop_approval_"
        f"{user}_"
        f"{fingerprint}"
    )


# ============================================================
# SEND OTP
# ============================================================

@frappe.whitelist()
def send_mop_otp(token, items):
    """
    Generate and send MOP OTP.

    Works for NEW Sales Invoices because we do not fetch
    Sales Invoice from database.

    items contains only item_code/rate/idx from browser.
    MOP is fetched from Item Master.
    """

    if not token:
        frappe.throw("OTP token is required.")

    if not items:
        frappe.throw("MOP item data is required.")

    # Build authoritative MOP violation list
    mop_items = get_mop_items_from_request(items)

    # If all rates are >= MOP, OTP is not required
    if not mop_items:

        return {
            "success": False,
            "required": False,
            "message": (
                "OTP is not required because all item "
                "rates are greater than or equal to MOP."
            )
        }

    # Generate random 6-digit OTP
    otp = str(
        random.randint(100000, 999999)
    )

    cache_key = get_otp_cache_key(token)

    # Store OTP for 5 minutes
    frappe.cache().set_value(
        cache_key,
        otp,
        expires_in_sec=OTP_EXPIRY
    )

    # Send SMS
    response = send_mop_sms(otp)

    # SMS failed -> remove OTP
    if not response.get("success"):

        frappe.cache().delete_value(
            cache_key
        )

        return {
            "success": False,
            "required": True,
            "message": response.get(
                "error",
                "Unable to send OTP."
            )
        }

    return {
        "success": True,
        "required": True,
        "message": (
            "OTP sent successfully. "
            "Valid for 5 minutes."
        ),
        "expires_in": OTP_EXPIRY
    }


# ============================================================
# VERIFY OTP
# ============================================================

@frappe.whitelist()
def verify_mop_otp(token, otp, items):
    """
    Verify OTP.

    On successful verification:

        1. OTP is deleted immediately
        2. Exact MOP fingerprint is approved
        3. Approval remains valid for 5 minutes
    """

    if not token:

        return {
            "verified": False,
            "message": "OTP token is required."
        }

    if not otp:

        return {
            "verified": False,
            "message": "Please enter OTP."
        }

    if not items:

        return {
            "verified": False,
            "message": "MOP item data is required."
        }

    # Get authoritative MOP values from Item Master
    mop_items = get_mop_items_from_request(items)

    # If MOP violation no longer exists,
    # no OTP is required.
    if not mop_items:

        return {
            "verified": True,
            "message": (
                "OTP is not required because "
                "all item rates are greater than or equal to MOP."
            )
        }

    cache_key = get_otp_cache_key(token)

    # Get OTP
    cached_otp = frappe.cache().get_value(
        cache_key
    )

    if not cached_otp:

        return {
            "verified": False,
            "message": (
                "OTP expired or not found. "
                "Please request a new OTP."
            )
        }

    # Compare OTP
    if str(cached_otp) != str(otp).strip():

        return {
            "verified": False,
            "message": "Invalid OTP."
        }

    # ========================================================
    # OTP IS CORRECT
    # ========================================================

    # Single-use OTP
    frappe.cache().delete_value(
        cache_key
    )

    # Create exact MOP fingerprint
    fingerprint = get_mop_fingerprint(
        mop_items
    )

    # Create approval cache
    approval_key = get_approval_cache_key(
        frappe.session.user,
        fingerprint
    )

    # Approval valid for 5 minutes
    frappe.cache().set_value(
        approval_key,
        "1",
        expires_in_sec=OTP_EXPIRY
    )

    return {
        "verified": True,
        "message": "MOP OTP verified successfully."
    }


# ============================================================
# CHECK APPROVAL
# ============================================================

def is_mop_approval_valid(mop_items):
    """
    Check whether current user has a valid OTP approval
    for the exact current MOP violation.

    This function does NOT consume the approval.

    This is important because a Sales Invoice can go through
    multiple validations during save/submit.
    """

    if not mop_items:
        return True

    fingerprint = get_mop_fingerprint(
        mop_items
    )

    approval_key = get_approval_cache_key(
        frappe.session.user,
        fingerprint
    )

    return bool(
        frappe.cache().get_value(
            approval_key
        )
    )


# ============================================================
# PUBLIC CHECK API
# ============================================================

@frappe.whitelist()
def check_mop_approval(items):
    """
    Client-side check before saving.

    Returns whether current MOP combination already
    has a valid OTP approval.
    """

    if not items:

        return {
            "approved": True
        }

    mop_items = get_mop_items_from_request(
        items
    )

    # No violation
    if not mop_items:

        return {
            "approved": True,
            "required": False
        }

    approved = is_mop_approval_valid(
        mop_items
    )

    return {
        "approved": approved,
        "required": True
    }


# ============================================================
# SMS
# ============================================================

def send_mop_sms(otp):
    """
    Send MOP OTP using MessageRider.
    """

    message = (
        f"Your MOP verification OTP is {otp}. "
        f"This OTP is valid for 5 minutes."
    )

    params = {
        "authtoken": MESSAGE_RIDER_AUTHTOKEN,
        "password": MESSAGE_RIDER_PASSWORD,
        "message": message,
        "receiverMobileNo": MOP_OTP_MOBILE
    }

    try:

        response = requests.get(
            MESSAGE_RIDER_URL,
            params=params,
            timeout=10
        )

        if response.status_code == 200:

            return {
                "success": True,
                "response": response.text
            }

        return {
            "success": False,
            "error": (
                f"SMS API Error: "
                f"{response.status_code} - "
                f"{response.text}"
            )
        }

    except Exception as e:

        frappe.log_error(
            title="MOP OTP SMS Error",
            message=frappe.get_traceback()
        )

        return {
            "success": False,
            "error": (
                f"SMS API Request Failed: {str(e)}"
            )
        }