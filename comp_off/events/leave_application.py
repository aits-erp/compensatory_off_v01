import frappe
from frappe import _
from frappe.utils import getdate


def validate_comp_off_source(doc, method=None):
	if not frappe.db.get_value("Leave Type", doc.leave_type, "is_compensatory"):
		return

	source_names = [
		row.compensatory_leave_request
		for row in (doc.get("custom_comp_off_source_request") or [])
		if row.compensatory_leave_request
	]

	if not source_names:
		frappe.throw(
			_("Select the approved Compensatory Leave Request(s) that earned this leave."),
			title=_("Compensatory Leave Request Required"),
		)

	if len(source_names) != len(set(source_names)):
		frappe.throw(_("The same Compensatory Leave Request cannot be selected more than once."))

	if doc.total_leave_days and len(source_names) != doc.total_leave_days:
		frappe.throw(
			_("Select exactly {0} Worked Holiday(s) to match the {0} day(s) of leave applied for.").format(
				doc.total_leave_days
			),
			title=_("Worked Holiday Count Mismatch"),
		)

	used_by = {
		row.compensatory_leave_request: row.parent
		for row in frappe.db.sql(
			"""
			select cosr.compensatory_leave_request, cosr.parent
			from `tabComp Off Source Request` cosr
			inner join `tabLeave Application` la on la.name = cosr.parent
			where cosr.parenttype = 'Leave Application'
			  and la.docstatus = 1
			  and la.name != %(name)s
			""",
			{"name": doc.name or ""},
			as_dict=True,
		)
	}

	for source_name in source_names:
		source = frappe.db.get_value(
			"Compensatory Leave Request",
			source_name,
			["employee", "leave_type", "work_from_date", "work_end_date", "docstatus"],
			as_dict=True,
		)

		if not source:
			frappe.throw(_("The selected Compensatory Leave Request {0} does not exist.").format(source_name))
		if source.docstatus != 1:
			frappe.throw(_("Compensatory Leave Request {0} must be submitted.").format(source_name))
		if source.employee != doc.employee:
			frappe.throw(_("Compensatory Leave Request {0} belongs to another employee.").format(source_name))
		if source.leave_type != doc.leave_type:
			frappe.throw(_("The leave type of {0} does not match this Leave Application.").format(source_name))
		if getdate(source.work_from_date) != getdate(source.work_end_date):
			frappe.throw(_("Compensatory Leave Request {0} must cover a single worked date.").format(source_name))
		if getdate(doc.from_date) <= getdate(source.work_end_date):
			frappe.throw(
				_("Compensatory Off can be used only after the worked holiday date linked to {0}.").format(source_name)
			)
		if source_name in used_by:
			frappe.throw(
				_("Compensatory Leave Request {0} is already linked to Leave Application {1}.").format(
					source_name, frappe.bold(used_by[source_name])
				)
			)

# """Safeguards for standard HRMS Compensatory Off leave applications."""

# import frappe
# from frappe import _
# from frappe.utils import getdate


# def validate_comp_off_source(doc, method=None):
# 	"""Validate the worked-holiday request linked to a Comp Off application.

# 	HRMS remains responsible for normal leave validation, approval, allocation,
# 	and ledger entries.  This app only makes the standard Compensatory Leave
# 	Request traceable from the standard Leave Application and prevents its reuse.
# 	"""
# 	# Use the standard Leave Type flag rather than duplicating configuration in
# 	# HR Settings. Non-compensatory leave applications retain native HRMS flow.
# 	if not frappe.db.get_value("Leave Type", doc.leave_type, "is_compensatory"):
# 		return

# 	if not doc.custom_comp_off_source_request:
# 		frappe.throw(
# 			_("Select the approved Compensatory Leave Request that earned this leave."),
# 			title=_("Compensatory Leave Request Required"),
# 		)

# 	source = frappe.db.get_value(
# 		"Compensatory Leave Request",
# 		doc.custom_comp_off_source_request,
# 		[
# 			"employee",
# 			"leave_type",
# 			"work_from_date",
# 			"work_end_date",
# 			"docstatus",
# 		],
# 		as_dict=True,
# 	)

# 	if not source:
# 		frappe.throw(_("The selected Compensatory Leave Request does not exist."))

# 	if source.docstatus != 1:
# 		frappe.throw(_("The selected Compensatory Leave Request must be submitted."))

# 	if source.employee != doc.employee:
# 		frappe.throw(_("The selected Compensatory Leave Request belongs to another employee."))

# 	if source.leave_type != doc.leave_type:
# 		frappe.throw(_("The source request leave type must match this Leave Application."))

# 	# One source field represents one earned day.  Multiple worked holidays must
# 	# be recorded as separate standard Compensatory Leave Requests so each leave
# 	# application retains an unambiguous audit trail.
# 	if getdate(source.work_from_date) != getdate(source.work_end_date):
# 		frappe.throw(
# 			_("Select a Compensatory Leave Request for one worked holiday date only."),
# 			title=_("Multiple Worked Dates Not Supported"),
# 		)

# 	# HRMS credits Comp Off from the day after the holiday work ends.
# 	if getdate(doc.from_date) <= getdate(source.work_end_date):
# 		frappe.throw(
# 			_("Compensatory Off can be used only after the worked holiday date."),
# 			title=_("Invalid Compensatory Off Date"),
# 		)

# 	# A source request represents a specific earned credit.  It may be linked to
# 	# one submitted application only; drafts are intentionally reusable until one
# 	# of them is approved and submitted.
# 	already_used = frappe.db.exists(
# 		"Leave Application",
# 		{
# 			"custom_comp_off_source_request": doc.custom_comp_off_source_request,
# 			"docstatus": 1,
# 			"name": ["!=", doc.name],
# 		},
# 	)

# 	if already_used:
# 		frappe.throw(
# 			_("This worked-holiday credit is already linked to Leave Application {0}.").format(
# 				frappe.bold(already_used)
# 			),
# 			title=_("Compensatory Credit Already Used"),
# 		)
