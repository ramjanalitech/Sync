frappe.ui.form.on('Payment Entry', {
    refresh(frm) {
        frm.add_custom_button(__('Send via WhatsApp'), function () {
            frappe.call({
                method: 'sync.payment_entry.send_whatsapp_on_payment_submit',  // You need to create this method
                args: {
                    doc: frm.doc.name
                },
                callback(r) {
                    if (r.message) {
                        frappe.msgprint(r.message.message || "WhatsApp response received.");
                    }
                }
            });
        });
    }
});
