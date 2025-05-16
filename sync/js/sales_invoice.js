// frappe.ui.form.on('Sales Invoice', {
//     refresh: function(frm) {
//         frm.add_custom_button(__('Whatsapp SMS'), function() {
//             frappe.call({
//                 method: 'sync.whatsapp.generate_pdf_and_send_whatsapp',
//                 args: {
//                     doc: frm.doc,
//                 },
//                 callback: function (r) {
//                     console.log("Response:", r.message);
//                     if (r.message === "Success") {
//                         frappe.msgprint("Invoice sent successfully.");
//                     } else {
//                         frappe.msgprint("Failed to send invoice.");
//                     }
//                 }
//             });
//         });
//     }
// });

// frappe.ui.form.on('Sales Invoice', {
//     refresh: function(frm) {
//         if (frm.doc.docstatus === 1) {
//             frm.add_custom_button(__('Send WhatsApp'), function() {
//                 frappe.call({
//                     method: 'sync.whatsapp.send_invoice_whatsapp_button',
//                     args: {
//                         doc: frm.doc.name
//                     },
//                     freeze: true,
//                     callback: function(r) {
//                         if (r.message) {
//                             frappe.msgprint(r.message.message || "Done");
//                         }
//                     }
//                 });
//             });
//         }
//     }
// });

frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        frm.add_custom_button(__('Send via WhatsApp'), function () {
            frappe.call({
                // method: "your_app_path.whatsapp.send_invoice_whatsapp_button",
                method: 'sync.whatsapp.send_invoice_whatsapp_button',
                args: {
                    docname: frm.doc.name
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


