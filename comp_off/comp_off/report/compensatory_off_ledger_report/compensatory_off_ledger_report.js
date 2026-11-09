/* global frappe */

frappe.query_reports["Compensatory Off Ledger Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_end(),
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "employee",
			label: __("Employee UID"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Data",
		},
		{
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
	],
	formatter(value, row, column, data, default_formatter) {
		const formatted_value = default_formatter(value, row, column, data);
		if (column.fieldname !== "credit" || !data) {
			return formatted_value;
		}

		const credit = Number(data.credit);
		if (!Number.isFinite(credit) || credit === 0) {
			return formatted_value;
		}

		const color = credit > 0 ? "#198754" : "#dc3545";
		return `<span style="color: ${color}; font-weight: 600;">${formatted_value}</span>`;
	},
};
