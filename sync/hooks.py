app_name = "sync"
app_title = "Sync"
app_publisher = "RamjanAli Lal"
app_description = "Sync Data"
app_email = "ramjanlal.tech@gmail.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sync/css/sync.css"
# app_include_js = "/assets/sync/js/sync.js"

# include js, css files in header of web template
# web_include_css = "/assets/sync/css/sync.css"
# web_include_js = "/assets/sync/js/sync.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sync/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

doctype_js = {
    "Stock Entry": "js/stock_entry.js",
    "Sales Invoice": "js/sales_invoice.js",
    "Payment Entry": "js/payment_entry.js",
    "Process Statement Of Accounts": "js/process_statement_of_accounts.js"
}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "sync/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sync.utils.jinja_methods",
# 	"filters": "sync.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sync.install.before_install"
# after_install = "sync.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sync.uninstall.before_uninstall"
# after_uninstall = "sync.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sync.utils.before_app_install"
# after_app_install = "sync.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sync.utils.before_app_uninstall"
# after_app_uninstall = "sync.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sync.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events = {
    "Sales Invoice": {
        # "on_submit": "sync.attachment.generate_pdf_on_submit"
        "on_submit": "sync.whatsapp.generate_pdf_and_send_whatsapp_on_submit"
    },
    "Payment Entry": {
        "on_submit": "sync.payment_entry.send_whatsapp_on_payment_submit"
    }
}

# scheduler_events = {
#     "daily": [
#         "sync.overdue_invoice.send_overdue_invoice_reminders"
#     ]
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"sync.tasks.all"
# 	],
# 	"daily": [
# 		"sync.tasks.daily"
# 	],
# 	"hourly": [
# 		"sync.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sync.tasks.weekly"
# 	],
# 	"monthly": [
# 		"sync.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "sync.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "sync.sync.sales_invoice.get_last_selling_rate":"sync.sync.sales_invoice.get_last_selling_rate",
    "sync.whatsapp.generate_pdf_and_send_whatsapp":"sync.whatsapp.generate_pdf_and_send_whatsapp",
    "sync.payment_entry.send_whatsapp_on_payment_submit":"sync.payment_entry.send_whatsapp_on_payment_submit",
    "sync.sales_invoice.get_last_rates":"sync.sales_invoice.get_last_rates",
    "sync.overdue_invoice.send_overdue_invoice_reminders":"sync.overdue_invoice.send_overdue_invoice_reminders",
    "sync.sync_stock_entry.get_item_tax_template":"sync.sync_stock_entry.get_item_tax_template",
    "sync.sales_invoice.send_overdue_otp":"sync.sales_invoice.send_overdue_otp",
    "sync.sales_invoice.verify_overdue_otp":"sync.sales_invoice.verify_overdue_otp"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sync.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sync.utils.before_request"]
# after_request = ["sync.utils.after_request"]

# Job Events
# ----------
# before_job = ["sync.utils.before_job"]
# after_job = ["sync.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sync.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

