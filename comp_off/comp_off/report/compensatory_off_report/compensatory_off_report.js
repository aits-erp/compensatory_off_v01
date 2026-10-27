// Copyright (c) 2026, aits and contributors
// For license information, please see license.txt

frappe.query_reports["Compensatory Off Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			// Data filter for now; the .py leaves it empty until a Division field is mapped
			fieldname: "division",
			label: __("Division"),
			fieldtype: "Data",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) {
			return value;
		}

		// Compensatory Leave Request rows (they carry the employee ID) in bold
		if (data.employee && value) {
			value = `<b>${value}</b>`;
		}

		// Colour the Status column
		if (column.fieldname === "status" && data.status) {
			const colors = {
				"Available": "green",
				"Partially Utilised": "orange",
				"Fully Utilised": "blue",
				"Expired": "red",
			};
			const color = colors[data.status];
			if (color) {
				value = `<span style="color: var(--${color}-600, ${color});">${value}</span>`;
			}
		}

		return value;
	},
};