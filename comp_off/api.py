"""Server-side data helpers for Comp Off leave applications."""

import frappe
from frappe.utils import formatdate, getdate


def _get_unused_comp_off_requests(employee, leave_type):
	"""Unused, submitted, single-day Compensatory Leave Requests for an
	employee, oldest worked date first. Shared by the Link-query used on the
	Table MultiSelect field and the FIFO lookup used by the client script.
	"""
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

	available = []
	for request in requests:
		if request.name in used_request_names:
			continue
		if getdate(request.work_from_date) != getdate(request.work_end_date):
			continue
		available.append(frappe._dict(name=request.name, work_date=getdate(request.work_from_date)))

	return available


@frappe.whitelist()
def get_available_comp_off_requests(doctype, txt, searchfield, start, page_len, filters):
	"""Link-query used by the custom_comp_off_source_request Table MultiSelect field."""
	filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
	available = _get_unused_comp_off_requests(filters.get("employee"), filters.get("leave_type"))

	results = [
		[r.name, formatdate(r.work_date)] for r in available if not txt or txt.lower() in r.name.lower()
	]
	return results[start : start + page_len]


@frappe.whitelist()
def get_available_comp_off_dates(employee, leave_type):
	"""Full list (oldest first) of unused Compensatory Leave Requests — used
	by the client script to detect and warn about non-FIFO selection.
	"""
	available = _get_unused_comp_off_requests(employee, leave_type)
	return [{"name": r.name, "work_date": str(r.work_date)} for r in available]

# """Server-side query for selecting Comp Off source requests."""

# import frappe
# from frappe.utils import formatdate, getdate



# @frappe.whitelist()
# def get_available_comp_off_requests(doctype, txt, searchfield, start, page_len, filters):
# 	filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
# 	employee = filters.get("employee")
# 	leave_type = filters.get("leave_type")

# 	if not employee or not leave_type:
# 		return []

# 	if not frappe.db.get_value("Leave Type", leave_type, "is_compensatory"):
# 		return []

# 	used_request_names = {
# 		row.compensatory_leave_request
# 		for row in frappe.db.sql(
# 			"""
# 			select cosr.compensatory_leave_request
# 			from `tabComp Off Source Request` cosr
# 			inner join `tabLeave Application` la on la.name = cosr.parent
# 			where cosr.parenttype = 'Leave Application' and la.docstatus = 1
# 			""",
# 			as_dict=True,
# 		)
# 	}

# 	requests = frappe.get_list(
# 		"Compensatory Leave Request",
# 		filters={"employee": employee, "leave_type": leave_type, "docstatus": 1},
# 		fields=["name", "work_from_date", "work_end_date"],
# 		order_by="work_from_date asc, creation asc",
# 	)

# 	results = []
# 	for request in requests:
# 		if request.name in used_request_names:
# 			continue
# 		if getdate(request.work_from_date) != getdate(request.work_end_date):
# 			continue
# 		if txt and txt.lower() not in request.name.lower():
# 			continue
# 		results.append([request.name, formatdate(getdate(request.work_from_date))])

# 	return results[start : start + page_len]
