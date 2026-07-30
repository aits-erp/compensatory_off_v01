"""Client-side data providers for Comp Off forms."""

import frappe
from frappe.utils import formatdate, getdate


@frappe.whitelist()
def get_available_comp_off_requests(employee, leave_type):
	"""Return unused, submitted Compensatory Leave Requests for one employee.

	Attendance is evidence of holiday work. A submitted Compensatory Leave Request
	is the standard HRMS transaction that turns that evidence into a leave credit.
	Only those credited, unused dates are valid options on a Leave Application.
	"""
	if not employee or not leave_type:
		return []

	configured_leave_type = frappe.db.get_single_value("HR Settings", "custom_comp_off_leave_type")
	if leave_type != configured_leave_type:
		return []

	requests = frappe.get_list(
		"Compensatory Leave Request",
		filters={"employee": employee, "leave_type": leave_type, "docstatus": 1},
		fields=["name", "work_from_date", "work_end_date", "reason"],
		order_by="work_from_date asc, creation asc",
	)

	used_request_names = set(
		frappe.get_all(
			"Leave Application",
			filters={
				"leave_type": leave_type,
				"docstatus": 1,
				"custom_comp_off_source_request": ["is", "set"],
			},
			pluck="custom_comp_off_source_request",
		)
	)

	available_requests = []
	for request in requests:
		# Each Leave Application consumes one source credit. Multi-date requests are
		# intentionally excluded because the app keeps a one-worked-date-to-one-leave
		# audit trail.
		if request.name in used_request_names or getdate(request.work_from_date) != getdate(
			request.work_end_date
		):
			continue

		work_date = getdate(request.work_from_date)
		available_requests.append(
			{
				"name": request.name,
				"work_date": str(work_date),
				"label": f"{formatdate(work_date)} — {request.name}",
			}
		)

	return available_requests
