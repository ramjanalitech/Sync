frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        frm.add_custom_button(__('Whatsapp SMS'), function() {
            frappe.call({
                method: 'sync.whatsapp.whatsapp_get_doc',
                args: {
                    doc: frm.doc,
                },
                callback: function (r) {
                    console.log("Response:", r.message);
                    if (r.message === "Success") {
                        frappe.msgprint("Invoice sent successfully.");
                    } else {
                        frappe.msgprint("Failed to send invoice.");
                    }
                }
            });
        });
    }
});