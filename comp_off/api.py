"""Server-side query for selecting Comp Off source requests."""

import frappe
from frappe.utils import formatdate, getdate


@frappe.whitelist()
def get_available_comp_off_requests(doctype, txt, searchfield, start, page_len, filters):
	filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
	employee = filters.get("employee")
	leave_type = filters.get("leave_type")

	if not employee or not leave_type:
		return []

	if not frappe.db.get_value("Leave Type", leave_type, "is_compensatory"):
		return []

	used_request_names = {
		row.compensatory_leave_request
		for row in frappe.db.sql(
			"""
			select cosr.compensatory_leave_request
			from `tabComp Off Source Request` cosr
			inner join `tabLeave Application` la on la.name = cosr.parent
			where cosr.parenttype = 'Leave Application' and la.docstatus = 1
			""",
			as_dict=True,
		)
	}

	requests = frappe.get_list(
		"Compensatory Leave Request",
		filters={"employee": employee, "leave_type": leave_type, "docstatus": 1},
		fields=["name", "work_from_date", "work_end_date"],
		order_by="work_from_date asc, creation asc",
	)

	results = []
	for request in requests:
		if request.name in used_request_names:
			continue
		if getdate(request.work_from_date) != getdate(request.work_end_date):
			continue
		if txt and txt.lower() not in request.name.lower():
			continue
		results.append([request.name, formatdate(getdate(request.work_from_date))])

	return results[start : start + page_len]

# """Client-side data providers for Comp Off forms."""

# import frappe
# from frappe.utils import formatdate, getdate


# @frappe.whitelist()
# def get_available_comp_off_requests(employee, leave_type):
# 	"""Return unused, submitted Compensatory Leave Requests for one employee.

# 	Attendance is evidence of holiday work. A submitted Compensatory Leave Request
# 	is the standard HRMS transaction that turns that evidence into a leave credit.
# 	Only those credited, unused dates are valid options on a Leave Application.
# 	"""
# 	if not employee or not leave_type:
# 		return []

# 	# Use the standard Leave Type setting. No HR Settings custom field is needed.
# 	if not frappe.db.get_value("Leave Type", leave_type, "is_compensatory"):
# 		return []

# 	requests = frappe.get_list(
# 		"Compensatory Leave Request",
# 		filters={"employee": employee, "leave_type": leave_type, "docstatus": 1},
# 		fields=["name", "work_from_date", "work_end_date", "reason"],
# 		order_by="work_from_date asc, creation asc",
# 	)

# 	used_request_names = set(
# 		frappe.get_all(
# 			"Leave Application",
# 			filters={
# 				"leave_type": leave_type,
# 				"docstatus": 1,
# 				"custom_comp_off_source_request": ["is", "set"],
# 			},
# 			pluck="custom_comp_off_source_request",
# 		)
# 	)

# 	available_requests = []
# 	for request in requests:
# 		# Each Leave Application consumes one source credit. Multi-date requests are
# 		# intentionally excluded because the app keeps a one-worked-date-to-one-leave
# 		# audit trail.
# 		if request.name in used_request_names or getdate(request.work_from_date) != getdate(
# 			request.work_end_date
# 		):
# 			continue

# 		work_date = getdate(request.work_from_date)
# 		available_requests.append(
# 			{
# 				"name": request.name,
# 				"work_date": str(work_date),
# 				"label": f"{formatdate(work_date)} — {request.name}",
# 			}
# 		)

# 	return available_requests
