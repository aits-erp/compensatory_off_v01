import re
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, formatdate, getdate, today


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 110},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 110},
		{"label": _("Division"), "fieldname": "division", "fieldtype": "Data", "width": 110},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 130},
		{"label": _("Work Date"), "fieldname": "work_date", "fieldtype": "Date", "width": 100},
		{"label": _("Against Date"), "fieldname": "against_date", "fieldtype": "Data", "width": 150},
		{"label": _("Leave Application ID"), "fieldname": "leave_application", "fieldtype": "Link", "options": "Leave Application", "width": 160},
		{"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 100},
		{"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 100},
		{"label": _("Credit"), "fieldname": "credit", "fieldtype": "Float", "width": 80},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Utilised"), "fieldname": "utilised", "fieldtype": "Float", "width": 80},
		{"label": _("Balance Credit"), "fieldname": "balance", "fieldtype": "Float", "width": 100},
		{"label": _("Created By"), "fieldname": "created_by", "fieldtype": "Data", "width": 150},
		{"label": _("Modified By"), "fieldname": "modified_by", "fieldtype": "Data", "width": 150},
	]


# Division mapping: not decided yet.
# Until a source field is chosen, the Division column stays empty and the
# Division filter is accepted but does not filter anything.
# Once the field is known, put its Employee fieldname here, e.g. "custom_division".
DIVISION_FIELD = None


def get_division_field():
	meta = frappe.get_meta("Employee")
	# explicit mapping first, then auto-detect common names if they get added later
	for fieldname in (DIVISION_FIELD, "division", "custom_division"):
		if fieldname and meta.has_field(fieldname):
			return fieldname
	return None


def parse_dates(value):
	"""'17-08-2024, 18-08-2024' -> [date, date]. Accepts dd-mm-yyyy, yyyy-mm-dd, dd/mm/yyyy."""
	out = []
	for part in re.split(r"[,;\n]+", value or ""):
		part = part.strip()
		if not part:
			continue
		for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
			try:
				out.append(datetime.strptime(part, fmt).date())
				break
			except ValueError:
				continue
	return out


def get_source_requests(app_names):
	"""Leave Application -> set of Compensatory Leave Requests from the Table MultiSelect."""
	if not app_names:
		return {}
	meta = frappe.get_meta("Comp Off Source Request")
	link_field = next(
		(f.fieldname for f in meta.fields if f.fieldtype == "Link" and f.options == "Compensatory Leave Request"),
		None,
	)
	if not link_field:
		return {}
	rows = frappe.get_all(
		"Comp Off Source Request",
		filters={"parent": ["in", app_names], "parenttype": "Leave Application"},
		fields=["parent", link_field],
	)
	out = {}
	for row in rows:
		if row.get(link_field):
			out.setdefault(row.parent, set()).add(row.get(link_field))
	return out


def get_data(filters):
	division_field = get_division_field()
	division_select = f"e.`{division_field}`" if division_field else "''"

	conditions = ""
	values = {}
	for key in ("company", "branch", "department"):
		if filters.get(key):
			conditions += f" and e.{key} = %({key})s"
			values[key] = filters[key]
	if division_field and filters.get("division"):
		conditions += f" and e.`{division_field}` = %(division)s"
		values["division"] = filters["division"]
	if filters.get("from_date"):
		conditions += " and clr.work_from_date >= %(from_date)s"
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions += " and clr.work_from_date <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	requests = frappe.db.sql(
		f"""
		select clr.name, clr.employee, clr.employee_name, clr.work_from_date,
			clr.work_end_date, clr.half_day, clr.leave_allocation,
			clr.custom_is_expired, clr.expiry,
			e.company, e.branch, e.department, {division_select} as division
		from `tabCompensatory Leave Request` clr
		inner join `tabEmployee` e on e.name = clr.employee
		where clr.docstatus = 1 {conditions}
		order by clr.employee, clr.work_from_date
		""",
		values,
		as_dict=True,
	)
	if not requests:
		return []

	# credit + date coverage of each request
	for r in requests:
		end = r.work_end_date or r.work_from_date
		r.dates = [add_days(r.work_from_date, i) for i in range(date_diff(end, r.work_from_date) + 1)]
		r.credit = 0.5 if r.half_day else float(len(r.dates))

	employees = list({r.employee for r in requests})
	leave_apps = frappe.get_all(
		"Leave Application",
		filters={
			"employee": ["in", employees],
			"docstatus": ["<", 2],
			"status": ["not in", ["Rejected", "Cancelled"]],
			"custom_comp_off_available_work_date": ["is", "set"],
		},
		fields=[
			"name", "employee", "from_date", "to_date", "total_leave_days", "status",
			"docstatus", "owner", "modified_by", "custom_comp_off_available_work_date",
		],
		order_by="from_date",
	)

	# usage[request name] -> {leave application name: {"app":..., "dates": [...], "days": x}}
	usage = {r.name: {} for r in requests}
	by_emp = {}
	for r in requests:
		by_emp.setdefault(r.employee, []).append(r)

	source_map = get_source_requests([a.name for a in leave_apps])

	for app in leave_apps:
		dates = parse_dates(app.custom_comp_off_available_work_date)
		if not dates:
			continue
		per_date = flt(app.total_leave_days) / len(dates)

		# prefer the requests linked in "Automatically Assigned Compensatory Leave Requests"
		emp_requests = by_emp.get(app.employee, [])
		linked = source_map.get(app.name)
		candidates = [r for r in emp_requests if r.name in linked] if linked else emp_requests
		if not candidates:
			candidates = emp_requests

		for d in dates:
			for r in candidates:
				if getdate(r.dates[0]) <= d <= getdate(r.dates[-1]):
					entry = usage[r.name].setdefault(app.name, {"app": app, "dates": [], "days": 0.0})
					entry["dates"].append(d)
					entry["days"] += per_date
					break

	allocation_end = {}
	alloc_names = [r.leave_allocation for r in requests if r.leave_allocation]
	if alloc_names:
		allocation_end = dict(
			frappe.get_all(
				"Leave Allocation",
				filters={"name": ["in", alloc_names]},
				fields=["name", "to_date"],
				as_list=True,
			)
		)

	user_names = {}

	def full_name(user):
		if user not in user_names:
			user_names[user] = frappe.db.get_value("User", user, "full_name") or user
		return user_names[user]

	data = []
	for r in requests:
		used = sum(e["days"] for e in usage[r.name].values())
		balance = flt(r.credit) - used

		if used == 0:
			status = "Available"
		elif balance > 0:
			status = "Partially Utilised"
		else:
			status = "Fully Utilised"
		end = allocation_end.get(r.leave_allocation)
		expired = (
			r.custom_is_expired
			or (r.expiry and getdate(r.expiry) < getdate(today()))
			or (end and getdate(end) < getdate(today()))
		)
		if balance > 0 and expired:
			status = "Expired"

		data.append(
			{
				"employee": r.employee,
				"employee_name": r.employee_name,
				"company": r.company,
				"branch": r.branch,
				"division": r.division,
				"department": r.department,
				"work_date": r.work_from_date,
				"credit": flt(r.credit),
				"status": status,
				"utilised": used,
				"balance": balance,
			}
		)

		for entry in usage[r.name].values():
			app = entry["app"]
			data.append(
				{
					"against_date": ", ".join(formatdate(d) for d in sorted(entry["dates"])),
					"leave_application": app.name,
					"from_date": app.from_date,
					"to_date": app.to_date,
					"credit": -flt(entry["days"]),
					"status": "Draft" if app.docstatus == 0 else app.status,
					"created_by": full_name(app.owner),
					"modified_by": full_name(app.modified_by),
				}
			)

	return data