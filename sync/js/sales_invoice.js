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
  
// OTP when Customer is overdue 

frappe.ui.form.on('Sales Invoice', {
    validate: function(frm) {
        if (!frm.doc.customer) return;

        // If already bypassed, allow save
        if (frm.doc.by_pass) {
            return;
        }

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Sales Invoice",
                filters: {
                    customer: frm.doc.customer,
                    docstatus: 1,
                    status: "Overdue"
                },
                fields: ["name"]
            },
            async: false,
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    // Overdue found → send OTP
                    frappe.call({
                        method: "sync.sales_invoice.send_overdue_otp",
                        args: { customer: frm.doc.customer },
                        async: false,
                        callback: function(res) {
                            if (res.message && res.message.success) {
                                frappe.prompt(
                                    [
                                        {
                                            label: 'Enter OTP Wich iS sent on 9890472868',
                                            fieldname: 'otp',
                                            fieldtype: 'Data',
                                            reqd: true
                                        }
                                    ],
                                    function(values) {
                                        frappe.call({
                                            method: "sync.sales_invoice.verify_overdue_otp",
                                            args: {
                                                customer: frm.doc.customer,
                                                otp: values.otp
                                            },
                                            async: false,
                                            callback: function(vr) {
                                                if (vr.message && vr.message.verified) {
                                                    frm.set_value("by_pass", 1);
                                                    frappe.msgprint("✅ OTP Verified. Please try saving again.");
                                                    frappe.validated = false; // block current save
                                                } else {
                                                    frappe.msgprint("❌ Invalid OTP. Cannot save.");
                                                    frappe.validated = false;
                                                }
                                            }
                                        });
                                    },
                                    'OTP Verification',
                                    'Verify'
                                );

                                frappe.validated = false; // block first save until OTP handled
                            } else {
                                frappe.msgprint("❌ Failed to send OTP. Cannot save.");
                                frappe.validated = false;
                            }
                        }
                    });
                }
            }
        });
    }
});

// New-1

frappe.ui.form.on("Sales Invoice", {

    // ========================================================
    // REFRESH
    // ========================================================

    refresh(frm) {

        // MOP in Sales Invoice Item is fetched from Item Master.
        // Users should not manually edit it.
        if (
            frm.fields_dict.items &&
            frm.fields_dict.items.grid
        ) {

            frm.fields_dict.items.grid.update_docfield_property(
                "mop",
                "read_only",
                1
            );
        }
    },


    // ========================================================
    // BEFORE SAVE
    // ========================================================

    before_save: async function(frm) {

        // ----------------------------------------------------
        // Get items from Sales Invoice
        // ----------------------------------------------------

        const items = [];

        (frm.doc.items || []).forEach(row => {

            if (!row.item_code) {
                return;
            }

            items.push({
                idx: row.idx,
                item_code: row.item_code,
                rate: flt(row.rate)
            });
        });


        // ----------------------------------------------------
        // Nothing to check
        // ----------------------------------------------------

        if (!items.length) {
            return;
        }


        // ----------------------------------------------------
        // Check whether OTP approval already exists
        // ----------------------------------------------------

        const check_response = await frappe.call({

            method:
                "sync.mop_otp.check_mop_approval",

            args: {
                items: JSON.stringify(items)
            },

            freeze: true,

            freeze_message:
                "Checking MOP approval..."
        });


        const check_result =
            check_response.message || {};


        // ----------------------------------------------------
        // No MOP violation OR already approved
        // ----------------------------------------------------

        if (
            check_result.approved
        ) {
            return;
        }


        // ----------------------------------------------------
        // OTP REQUIRED
        // ----------------------------------------------------

        const verified =
            await show_mop_otp_dialog(
                frm,
                items
            );


        // ----------------------------------------------------
        // OTP failed/cancelled
        // ----------------------------------------------------

        if (!verified) {

            frappe.validated = false;

            frappe.throw(
                "Sales Invoice cannot be saved without MOP OTP verification."
            );

            return;
        }


        // ----------------------------------------------------
        // OTP verified
        //
        // IMPORTANT:
        // We do NOT call frm.save() again here.
        //
        // The current save operation continues after
        // before_save completes.
        // ----------------------------------------------------

        return;
    }

});


// ============================================================
// MOP OTP DIALOG
// ============================================================

async function show_mop_otp_dialog(frm, items) {

    return new Promise(async (resolve) => {

        let resolved = false;

        const resolve_once = function(value) {

            if (resolved) {
                return;
            }

            resolved = true;

            resolve(value);
        };


        // ----------------------------------------------------
        // Build MOP item display
        // ----------------------------------------------------

        const display_items = [];

        (items || []).forEach(row => {

            const invoice_row =
                (frm.doc.items || []).find(
                    r => r.idx === row.idx
                );

            if (!invoice_row) {
                return;
            }

            const mop = flt(invoice_row.mop);
            const rate = flt(invoice_row.rate);

            if (
                mop > 0 &&
                rate < mop
            ) {

                display_items.push({
                    idx: row.idx,
                    item_code: row.item_code,
                    rate: rate,
                    mop: mop
                });
            }
        });


        // ----------------------------------------------------
        // HTML
        // ----------------------------------------------------

        const item_html =
            display_items.map(row => {

                return `
                    <tr>
                        <td>
                            ${frappe.utils.escape_html(
                                row.item_code
                            )}
                        </td>

                        <td style="text-align:right;">
                            ${format_currency(row.rate)}
                        </td>

                        <td style="text-align:right;">
                            ${format_currency(row.mop)}
                        </td>
                    </tr>
                `;

            }).join("");


        // ----------------------------------------------------
        // Dialog
        // ----------------------------------------------------

        const d = new frappe.ui.Dialog({

            title: "MOP Approval Required",

            fields: [

                {
                    fieldname: "info",
                    fieldtype: "HTML",

                    options: `
                        <div class="alert alert-warning">
                            <strong>
                                MOP Approval Required
                            </strong>

                            <br>

                            One or more item rates are below
                            the Minimum Offer Price (MOP).
                        </div>

                        <table class="table table-bordered">

                            <thead>
                                <tr>
                                    <th>Item</th>
                                    <th style="text-align:right;">
                                        Rate
                                    </th>
                                    <th style="text-align:right;">
                                        MOP
                                    </th>
                                </tr>
                            </thead>

                            <tbody>
                                ${item_html}
                            </tbody>

                        </table>

                        <div class="alert alert-info">
                            OTP will be sent to the authorized
                            mobile number.
                        </div>
                    `
                },

                {
                    fieldname: "otp",
                    fieldtype: "Data",
                    label: "Enter OTP",

                    description:
                        "OTP is valid for 5 minutes."
                }

            ],

            primary_action_label:
                "Verify OTP",

            primary_action:
                async function() {

                    const otp =
                        d.get_value("otp");


                    // ------------------------------------------------
                    // Validate OTP input
                    // ------------------------------------------------

                    if (!otp) {

                        frappe.msgprint({
                            title: "OTP Required",
                            message:
                                "Please enter the OTP.",
                            indicator: "orange"
                        });

                        return;
                    }


                    // ------------------------------------------------
                    // Verify OTP
                    // ------------------------------------------------

                    const response =
                        await frappe.call({

                            method:
                                "sync.mop_otp.verify_mop_otp",

                            args: {

                                token:
                                    frm.__mop_otp_token,

                                otp: otp,

                                items:
                                    JSON.stringify(items)
                            },

                            freeze: true,

                            freeze_message:
                                "Verifying OTP..."
                        });


                    const result =
                        response.message || {};


                    // ------------------------------------------------
                    // Success
                    // ------------------------------------------------

                    if (
                        result.verified
                    ) {

                        d.hide();

                        frappe.show_alert({
                            message:
                                "MOP OTP verified successfully.",
                            indicator: "green"
                        });

                        resolve_once(true);

                        return;
                    }


                    // ------------------------------------------------
                    // Failed
                    // ------------------------------------------------

                    frappe.msgprint({

                        title:
                            "OTP Verification Failed",

                        message:
                            result.message ||
                            "Invalid or expired OTP.",

                        indicator:
                            "red"
                    });
                },


            secondary_action_label:
                "Cancel",

            secondary_action:
                function() {

                    d.hide();

                    resolve_once(false);
                }
        });


        // ----------------------------------------------------
        // Show dialog
        // ----------------------------------------------------

        d.show();


        // ----------------------------------------------------
        // Generate temporary browser token
        //
        // This is NOT a Sales Invoice field.
        // It exists only in JavaScript memory.
        // ----------------------------------------------------

        frm.__mop_otp_token =
            frappe.utils.get_random(32);


        // ----------------------------------------------------
        // Send OTP automatically
        // ----------------------------------------------------

        const send_response =
            await frappe.call({

                method:
                    "sync.mop_otp.send_mop_otp",

                args: {

                    token:
                        frm.__mop_otp_token,

                    items:
                        JSON.stringify(items)
                },

                freeze: true,

                freeze_message:
                    "Sending MOP OTP..."
            });


        const send_result =
            send_response.message || {};


        // ----------------------------------------------------
        // SMS sent
        // ----------------------------------------------------

        if (
            send_result.success
        ) {

            frappe.show_alert({

                message:
                    "OTP sent successfully. Valid for 5 minutes.",

                indicator:
                    "green"
            });

            return;
        }


        // ----------------------------------------------------
        // SMS failed
        // ----------------------------------------------------

        d.hide();

        frappe.msgprint({

            title:
                "OTP Sending Failed",

            message:
                send_result.message ||
                "Unable to send OTP.",

            indicator:
                "red"
        });

        resolve_once(false);
    });
}