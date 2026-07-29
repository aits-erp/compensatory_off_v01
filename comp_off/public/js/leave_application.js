frappe.ui.form.on("Leave Application", {
	refresh(frm) {
		configure_comp_off_fields(frm);
	},

	employee(frm) {
		configure_comp_off_query(frm);
	},

	leave_type(frm) {
		configure_comp_off_fields(frm);
	},
});

function configure_comp_off_fields(frm) {
	frappe.db.get_single_value("HR Settings", "custom_comp_off_leave_type").then((compOffType) => {
		const isCompOff = Boolean(compOffType) && frm.doc.leave_type === compOffType;

		frm.toggle_display("custom_comp_off_source_request", isCompOff);
		frm.toggle_display("custom_comp_off_worked_on", isCompOff);
		frm.set_df_property("custom_comp_off_source_request", "reqd", isCompOff);

		if (!isCompOff) {
			frm.set_value("custom_comp_off_source_request", null);
			frm.set_value("custom_comp_off_worked_on", null);
		}

		configure_comp_off_query(frm);
	});
}

function configure_comp_off_query(frm) {
	frm.set_query("custom_comp_off_source_request", () => ({
		filters: {
			employee: frm.doc.employee,
			docstatus: 1,
		},
	}));
}
