"""Fault-tolerant compensatory off ledger report.

The report deliberately relies only on metadata that exists on the site.  It
therefore works with a plain HRMS installation, with this app's automatic
source table, and with optional Real Group HRMS fields, without importing or
depending on the Real Group app.
"""

from collections import defaultdict

import frappe
from frappe.utils import flt


REQUEST_DOCTYPE = "Compensatory Leave Request"
LEAVE_APPLICATION_DOCTYPE = "Leave Application"
SOURCE_DOCTYPE = "Comp Off Source Request"
LEGACY_DETAILS_DOCTYPE = "Compensatory Leave Details"


def execute(filters=None):
	"""Return the client ledger layout without raising for absent custom fields."""
	columns = get_columns()
	try:
		if not _doctype_exists(REQUEST_DOCTYPE):
			return columns, []

		requests = _get_requests(filters or {})
		if not requests:
			return columns, []

		employees = _get_employees({request.employee for request in requests if request.employee})
		usages, leave_applications = _get_usages([request.name for request in requests])
		return columns, _build_rows(requests, employees, usages, leave_applications, filters or {})
	except Exception:
		# Reports must remain usable even if an optional custom field/table was
		# removed or a third-party app is not installed on this site.
		return columns, []


def get_columns():
	"""Column labels intentionally match the detailed client workbook layout."""
	return [
		{"fieldname": "employee", "label": "Employee UID", "fieldtype": "Link", "options": "Employee", "width": 140},
		{"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 180},
		{"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 180},
		{"fieldname": "branch", "label": "Branch", "fieldtype": "Data", "width": 120},
		{"fieldname": "division", "label": "Division", "fieldtype": "Data", "width": 140},
		{"fieldname": "department", "label": "Department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"fieldname": "work_date", "label": "Work Date", "fieldtype": "Date", "width": 105},
		{"fieldname": "against_date", "label": "Against Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "leave_application", "label": "Leave Application ID", "fieldtype": "Link", "options": LEAVE_APPLICATION_DOCTYPE, "width": 185},
		{"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "width": 105},
		{"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "width": 105},
		{"fieldname": "credit", "label": "Credit", "fieldtype": "Float", "width": 80},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 115},
		{"fieldname": "utilised", "label": "Utillised", "fieldtype": "Float", "width": 90},
		{"fieldname": "balance_credit", "label": "Balance Credit", "fieldtype": "Float", "width": 110},
		{"fieldname": "creation", "label": "creation", "fieldtype": "Datetime", "width": 150},
		{"fieldname": "modified", "label": "modified", "fieldtype": "Datetime", "width": 150},
		{"fieldname": "expiry_date", "label": "Expiry date", "fieldtype": "Date", "width": 105},
	]


def _get_requests(filters):
	available = _available_fields(
		REQUEST_DOCTYPE,
		[
			"employee",
			"employee_name",
			"work_from_date",
			"work_end_date",
			"credit",
			"custom_credit",
			"status",
			"expiry",
			"custom_expiry",
			"custom_is_expired",
		],
	)
	if "employee" not in available:
		return []

	query_filters = {"docstatus": 1}
	if filters.get("employee"):
		query_filters["employee"] = filters["employee"]
	if filters.get("from_date") and "work_from_date" in available:
		query_filters["work_from_date"] = [">=", filters["from_date"]]
	if filters.get("to_date") and "work_from_date" in available:
		query_filters.setdefault("work_from_date", ["<=", filters["to_date"]])
		if isinstance(query_filters["work_from_date"], list) and query_filters["work_from_date"][0] == ">=":
			query_filters["work_from_date"] = ["between", [filters["from_date"], filters["to_date"]]]

	return _safe_get_all(
		REQUEST_DOCTYPE,
		filters=query_filters,
		fields=["name", "creation", "modified", "docstatus", *available],
		order_by="work_from_date asc, creation asc" if "work_from_date" in available else "creation asc",
	)


def _get_employees(employee_names):
	if not employee_names or not _doctype_exists("Employee"):
		return {}

	field_candidates = ["employee_name", "company", "department", "branch", "custom_branch", "division", "custom_division"]
	fields = _available_fields("Employee", field_candidates)
	rows = _safe_get_all("Employee", filters={"name": ["in", list(employee_names)]}, fields=["name", *fields])
	return {row.name: row for row in rows}


def _get_usages(request_names):
	"""Read both supported request-to-leave mappings, preferring this app's table."""
	usages = defaultdict(list)

	if _doctype_exists(SOURCE_DOCTYPE) and _has_field(SOURCE_DOCTYPE, "compensatory_leave_request"):
		source_rows = _safe_get_all(
			SOURCE_DOCTYPE,
			filters={
				"parenttype": LEAVE_APPLICATION_DOCTYPE,
				"parentfield": "custom_comp_off_source_request",
				"compensatory_leave_request": ["in", request_names],
			},
			fields=["parent", "compensatory_leave_request"],
		)
		for row in source_rows:
			if row.compensatory_leave_request and row.parent:
				usages[row.compensatory_leave_request].append({"leave_application": row.parent, "amount": None})

	# Older Real Group data can store the same connection in a different child
	# table.  It is only used when our source table has no connection for that
	# particular request, so a site with both formats cannot double-count use.
	if _doctype_exists(LEGACY_DETAILS_DOCTYPE) and _has_field(LEGACY_DETAILS_DOCTYPE, "leave_application"):
		legacy_fields = ["parent", "leave_application"]
		if _has_field(LEGACY_DETAILS_DOCTYPE, "total_leave"):
			legacy_fields.append("total_leave")
		legacy_rows = _safe_get_all(
			LEGACY_DETAILS_DOCTYPE,
			filters={"parenttype": REQUEST_DOCTYPE, "parent": ["in", request_names]},
			fields=legacy_fields,
		)
		for row in legacy_rows:
			if row.parent and row.leave_application and not usages[row.parent]:
				usages[row.parent].append(
					{"leave_application": row.leave_application, "amount": row.get("total_leave")}
				)

	leave_application_names = {
		row["leave_application"]
		for request_usages in usages.values()
		for row in request_usages
		if row.get("leave_application")
	}
	return usages, _get_leave_applications(leave_application_names)


def _get_leave_applications(leave_application_names):
	if not leave_application_names or not _doctype_exists(LEAVE_APPLICATION_DOCTYPE):
		return {}

	fields = _available_fields(LEAVE_APPLICATION_DOCTYPE, ["from_date", "to_date", "total_leave_days"])
	rows = _safe_get_all(
		LEAVE_APPLICATION_DOCTYPE,
		filters={"name": ["in", list(leave_application_names)], "docstatus": 1},
		fields=["name", *fields],
	)
	return {row.name: row for row in rows}


def _build_rows(requests, employees, usages, leave_applications, filters):
	rows = []
	for request in requests:
		employee = employees.get(request.employee)
		if not _matches_employee_filters(employee, filters):
			continue

		credit = _request_credit(request)
		usage_rows = _normalise_usages(usages.get(request.name, []), leave_applications)
		utilised = sum(flt(usage["amount"]) for usage in usage_rows)
		balance = max(0, credit - utilised)
		status = _request_status(request)
		if status == "Expired":
			balance = 0

		rows.append(
			{
				"employee": request.employee,
				"employee_name": _value(employee, "employee_name") or _value(request, "employee_name"),
				"company": _value(employee, "company"),
				"branch": _first_value(employee, "custom_branch", "branch"),
				"division": _first_value(employee, "custom_division", "division"),
				"department": _value(employee, "department"),
				"work_date": _first_value(request, "work_from_date", "work_end_date"),
				"credit": credit,
				"status": status,
				"utilised": utilised or None,
				"balance_credit": balance,
				"creation": _value(request, "creation"),
				"modified": _value(request, "modified"),
				"expiry_date": _first_value(request, "expiry", "custom_expiry"),
				"bold": 1,
			}
		)

		for usage in usage_rows:
			leave_application = leave_applications.get(usage["leave_application"])
			if not leave_application:
				continue
			rows.append(
				{
					"against_date": _first_value(request, "work_from_date", "work_end_date"),
					"leave_application": usage["leave_application"],
					"from_date": _value(leave_application, "from_date"),
					"to_date": _value(leave_application, "to_date"),
					"credit": -flt(usage["amount"]),
					"indent": 1,
				}
			)
	return rows


def _normalise_usages(request_usages, leave_applications):
	"""Derive a per-source share when only the automatic source link exists."""
	by_application = defaultdict(list)
	for usage in request_usages:
		if usage["leave_application"] in leave_applications:
			by_application[usage["leave_application"]].append(usage)

	result = []
	for leave_application_name, application_usages in by_application.items():
		leave_application = leave_applications[leave_application_name]
		for usage in application_usages:
			amount = usage.get("amount")
			if amount in (None, ""):
				amount = flt(_value(leave_application, "total_leave_days")) / len(application_usages)
			result.append({"leave_application": leave_application_name, "amount": flt(amount)})
	return result


def _request_credit(request):
	for fieldname in ("credit", "custom_credit"):
		value = _value(request, fieldname)
		if value not in (None, ""):
			return flt(value)
	# This app assigns one submitted Compensatory Leave Request per eligible
	# worked day.  Use that documented standard-app value when no optional
	# credit field exists.
	return 1.0


def _request_status(request):
	if _value(request, "custom_is_expired"):
		return "Expired"
	return _value(request, "status") or "Submitted"


def _matches_employee_filters(employee, filters):
	# Missing optional fields are intentionally treated as blanks, not errors.
	if not employee:
		return not any(filters.get(key) for key in ("company", "branch", "division", "department"))
	return (
		(not filters.get("company") or _value(employee, "company") == filters["company"])
		and (not filters.get("branch") or _first_value(employee, "custom_branch", "branch") == filters["branch"])
		and (not filters.get("division") or _first_value(employee, "custom_division", "division") == filters["division"])
		and (not filters.get("department") or _value(employee, "department") == filters["department"])
	)


def _doctype_exists(doctype):
	try:
		return bool(frappe.db.exists("DocType", doctype))
	except Exception:
		return False


def _has_field(doctype, fieldname):
	try:
		return frappe.get_meta(doctype).has_field(fieldname)
	except Exception:
		return False


def _available_fields(doctype, candidates):
	return [fieldname for fieldname in candidates if _has_field(doctype, fieldname)]


def _safe_get_all(doctype, **kwargs):
	try:
		return frappe.get_all(doctype, **kwargs)
	except Exception:
		return []


def _value(document, fieldname):
	return document.get(fieldname) if document else None


def _first_value(document, *fieldnames):
	for fieldname in fieldnames:
		value = _value(document, fieldname)
		if value not in (None, ""):
			return value
	return None
