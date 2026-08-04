frappe.ui.form.on("Leave Application", {
	refresh(frm) {
		configure_comp_off_fields(frm);
	},

	employee(frm) {
		frm.clear_table("custom_comp_off_source_request");
		frm.refresh_field("custom_comp_off_source_request");
		configure_comp_off_fields(frm);
	},

	leave_type(frm) {
		frm.clear_table("custom_comp_off_source_request");
		frm.refresh_field("custom_comp_off_source_request");
		configure_comp_off_fields(frm);
	},

	custom_comp_off_source_request(frm) {
		refresh_worked_holiday_summary(frm);
		check_comp_off_fifo_order(frm);
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
	frm.toggle_display("custom_comp_off_source_request", isCompOff);
	frm.toggle_display("custom_comp_off_available_work_date", isCompOff);
	frm.set_df_property("custom_comp_off_source_request", "reqd", isCompOff);

	if (!isCompOff) {
		frm.clear_table("custom_comp_off_source_request");
		frm.set_value("custom_comp_off_available_work_date", "");
		frm.refresh_field("custom_comp_off_source_request");
	}

	configure_comp_off_query(frm);
	refresh_worked_holiday_summary(frm);
}

function configure_comp_off_query(frm) {
	frm.set_query("custom_comp_off_source_request", () => ({
		query: "comp_off.api.get_available_comp_off_requests",
		filters: { employee: frm.doc.employee, leave_type: frm.doc.leave_type },
	}));
}

function refresh_worked_holiday_summary(frm) {
	const names = (frm.doc.custom_comp_off_source_request || [])
		.map((row) => row.compensatory_leave_request)
		.filter(Boolean);

	if (!names.length) {
		frm.set_value("custom_comp_off_available_work_date", "");
		return;
	}

	frappe.db
		.get_list("Compensatory Leave Request", {
			filters: { name: ["in", names] },
			fields: ["name", "work_from_date"],
			order_by: "work_from_date asc",
		})
		.then((rows) => {
			frm.set_value(
				"custom_comp_off_available_work_date",
				rows.map((r) => frappe.datetime.str_to_user(r.work_from_date)).join(", ")
			);
		});
}

function check_comp_off_fifo_order(frm) {
	const selectedNames = (frm.doc.custom_comp_off_source_request || [])
		.map((row) => row.compensatory_leave_request)
		.filter(Boolean);

	if (!selectedNames.length || !frm.doc.employee || !frm.doc.leave_type) {
		return;
	}

	frappe.call({
		method: "comp_off.api.get_available_comp_off_dates",
		args: { employee: frm.doc.employee, leave_type: frm.doc.leave_type },
		callback(response) {
			const available = response.message || []; // already oldest-first
			if (!available.length) return;

			// The "correct" FIFO picks are the oldest N, N = number selected.
			const expected = available.slice(0, selectedNames.length);
			const skippedOlder = expected.filter((r) => !selectedNames.includes(r.name));

			if (skippedOlder.length) {
				const dates = skippedOlder.map((r) => frappe.datetime.str_to_user(r.work_date)).join(", ");
				frappe.show_alert(
					{
						message: __(
							"Older worked-holiday credit(s) dated {0} are still unused. Consider using Compensatory Off oldest-first (FIFO).",
							[dates]
						),
						indicator: "orange",
					},
					8
				);
			}
		},
	});
}
