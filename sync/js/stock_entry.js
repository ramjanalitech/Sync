//  Code Refactor
frappe.ui.form.on("Stock Entry", {
    on_submit: function(frm) {
        // Handle Material Transfer
        if (frm.doc.stock_entry_type === "Material Transfer") {
            if (frm.doc.sync == 1){
                handleMaterialTransfer(frm);
            }            
        }
        // Handle Material Receipt
        if (frm.doc.stock_entry_type === "Material Receipt") {
            handleMaterialReceipt(frm);
        }
    }
});

// Function to handle Material Transfer
function handleMaterialTransfer(frm) {
    // Log the stock entry data
    console.log("Stock Entry Data:", frm.doc);

    // Validate items
    if (!frm.doc.items || frm.doc.items.length === 0) {
        frappe.msgprint("No items found in the Stock Entry. Please add items and try again.");
        return;
    }

    // Call a server-side method to handle the API request
    frappe.call({
        method: "sync.sync_stock_entry.create_stock_entry_in_second_site",
        args: {
            "stock_entry_data": frm.doc
        },
        async: false,  // Make the call synchronous
        callback: function(r) {
            if (r.exc) {
                console.error("Error:", r.exc);
                frappe.msgprint("Failed to create stock entry in the second site.");
            } else {
                frappe.msgprint("Stock entry created successfully in the second site.");
            }
        }
    });
}

// Function to handle Material Receipt
function handleMaterialReceipt(frm) {
    // Log the customer for debugging
    console.log("Customer:", frm.doc.sales_customer);
    frm.set_df_property("sales_customer", "reqd", 1);
    // Validate items
    if (!frm.doc.items || frm.doc.items.length === 0) {
        frappe.msgprint("No items found in the Stock Entry. Please add items and try again.");
        return;
    }

    // Validate customer
    if (!frm.doc.sales_customer) {
        frappe.msgprint("Customer is not set in the Stock Entry. Please provide a customer.");
        return;
    }

    // Call a server-side method to create a Sales Invoice
    frappe.call({
        method: "sync.sync_stock_entry.create_sales_invoice_from_stock_entry",
        args: {
            "stock_entry": frm.doc,  // Pass the Stock Entry document
            "sales_customer": frm.doc.sales_customer  // Pass the customer explicitly
        },
        async: false,  // Make the call synchronous
        callback: function(r) {
            if (r.exc) {
                console.error("Error:", r.exc);
                frappe.msgprint("Failed to create Sales Invoice.");
            } else {
                frappe.msgprint("Sales Invoice created successfully.");
            }
        }
    });
}

frappe.ui.form.on("Stock Entry Detail", {
    item_code: update_tax_basic_rate,
    basic_rate: update_tax_basic_rate,
    gst_rate: update_tax_basic_rate
});

function update_tax_basic_rate(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let basic_rate = flt(row.basic_rate);
    let gst_rate = flt(row.gst_rate);

    row.tax_basic_rate = basic_rate + (basic_rate * gst_rate / 100);
    frm.refresh_field("items");
}

frappe.ui.form.on("Stock Entry Detail", {
    item_code: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) return;

        frappe.call({
            method: "sync.sync_stock_entry.get_item_tax_template",
            args: { item_code: row.item_code },
            callback: function (r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, "item_tax_template", r.message);
                }
            }
        });
    }
});