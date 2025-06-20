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

frappe.ui.form.on('Sales Invoice Item', {
    fetch_last_rate: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!frm.doc.customer || !row.item_code) {
            frappe.msgprint("Please select both Customer and Item.");
            return;
        }

        frappe.call({
            method: "sync.sales_invoice.get_last_rates",
            args: {
                customer: frm.doc.customer,
                item_code: row.item_code
            },
            callback: function (r) {
                if (r.message) {
                    const { selling_rate, purchase_rate } = r.message;

                    let msg = "";
                    if (selling_rate) {
                        msg += "💰 Last Selling Rate: " + selling_rate + "<br>";
                    } else {
                        msg += "No previous selling rate found.<br>";
                    }

                    if (purchase_rate) {
                        msg += "🛒 Last Purchase Rate: " + purchase_rate;
                    } else {
                        msg += "No previous purchase rate found.";
                    }

                    frappe.msgprint(msg);
                } else {
                    frappe.msgprint("No rate data found.");
                }
            }
        });
    }
});

frappe.ui.form.on('Sales Invoice Item', {
    rate: function(frm, cdt, cdn) {
        update_include_gst_rate(frm, cdt, cdn);
    },
    gst_rate: function(frm, cdt, cdn) {
        update_include_gst_rate(frm, cdt, cdn);
        update_base_rate_from_include(frm, cdt, cdn);
    },
    including_gst_rate: function(frm, cdt, cdn) {
        update_base_rate_from_include(frm, cdt, cdn);
    },
    items_add: function(frm, cdt, cdn) {
        update_include_gst_rate(frm, cdt, cdn);
    }
});

function update_include_gst_rate(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.rate && row.gst_rate != null) {
        row.including_gst_rate = row.rate * (1 + row.gst_rate / 100);
        frm.refresh_field('items');
    }
}

function update_base_rate_from_include(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.including_gst_rate && row.gst_rate != null) {
        row.rate = row.including_gst_rate / (1 + row.gst_rate / 100);
        frm.refresh_field('items');
    }
}

frappe.ui.form.on('Sales Invoice', {
    margin_per: function(frm) {
      calculate_margin_total(frm);
    },
  
    grand_total: function(frm) {
      calculate_margin_total(frm);
    }
  });
  
  function calculate_margin_total(frm) {
    if (frm.doc.margin_per && frm.doc.total) {
      frm.set_value(
        'margin_amount',
        (frm.doc.margin_per / 100) * frm.doc.total
      );
    }
  }
  