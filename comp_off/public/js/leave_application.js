frappe.ui.form.on("Leave Application", {
	refresh(frm) {
		configure_comp_off_fields(frm);
	},

	employee(frm) {
		configure_comp_off_fields(frm);
	},

	leave_type(frm) {
		configure_comp_off_fields(frm);
	},
});

function configure_comp_off_fields(frm) {
	if (!frm.doc.leave_type) {
		set_comp_off_field_state(frm, false);
		return;
	}
	frappe.db.get_value("Leave Type", frm.doc.leave_type, "is_compensatory").then((r) => {
		set_comp_off_field_state(frm, Number(r.message?.is_compensatory || 0) === 1);
	});
}

function set_comp_off_field_state(frm, isCompOff) {
	// Source rows are audit data, assigned only by the server on submission.
	frm.toggle_display("custom_comp_off_source_request", false);
	frm.toggle_display("custom_comp_off_available_work_date", isCompOff);
	frm.set_df_property("custom_comp_off_source_request", "read_only", 1);
	frm.set_df_property("custom_comp_off_source_request", "hidden", 1);
}
