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

	custom_comp_off_available_work_date(frm) {
		const selectedRequest = frm._compOffRequestsByOption?.get(
			frm.doc.custom_comp_off_available_work_date
		);

		if (selectedRequest) {
			frm.set_value("custom_comp_off_source_request", selectedRequest.name);
		} else if (!frm.doc.custom_comp_off_available_work_date) {
			frm.set_value("custom_comp_off_source_request", null);
		}
	},

	custom_comp_off_source_request(frm) {
		configure_available_work_dates(frm);
	},
});

function configure_comp_off_fields(frm) {
	if (!frm.doc.leave_type) {
		set_comp_off_field_state(frm, false);
		return;
	}

	frappe.db.get_value("Leave Type", frm.doc.leave_type, "is_compensatory").then((response) => {
		const isCompOff = Number(response.message?.is_compensatory || 0) === 1;
		set_comp_off_field_state(frm, isCompOff);
	});
}

function set_comp_off_field_state(frm, isCompOff) {
	frm.toggle_display("custom_comp_off_available_work_date", isCompOff);
	frm.set_df_property("custom_comp_off_source_request", "reqd", isCompOff);

	if (!isCompOff) {
		frm.set_value("custom_comp_off_available_work_date", null);
		frm.set_value("custom_comp_off_source_request", null);
	}

	configure_comp_off_query(frm);
	configure_available_work_dates(frm, isCompOff);
}

function configure_comp_off_query(frm) {
	frm.set_query("custom_comp_off_source_request", () => ({
		filters: {
			employee: frm.doc.employee,
			docstatus: 1,
		},
	}));
}

function configure_available_work_dates(frm, isCompOff = true) {
	if (!isCompOff || !frm.doc.employee || !frm.doc.leave_type) {
		frm.set_df_property("custom_comp_off_available_work_date", "options", "");
		return;
	}

	frappe.call({
		method: "comp_off.api.get_available_comp_off_requests",
		args: {
			employee: frm.doc.employee,
			leave_type: frm.doc.leave_type,
		},
		callback(response) {
			const requests = response.message || [];
			frm._compOffRequestsByOption = new Map(
				requests.map((request) => [request.label, request])
			);
			frm.set_df_property(
				"custom_comp_off_available_work_date",
				"options",
				["", ...requests.map((request) => request.label)].join("\n")
			);

			const selectedRequest = requests.find(
				(request) => request.name === frm.doc.custom_comp_off_source_request
			);
			if (selectedRequest && frm.doc.custom_comp_off_available_work_date !== selectedRequest.label) {
				frm.set_value("custom_comp_off_available_work_date", selectedRequest.label);
			}
		},
	});
}
