"""Safeguards for standard HRMS Compensatory Off leave applications."""

import frappe
from frappe import _
from frappe.utils import getdate


def validate_comp_off_source(doc, method=None):
	"""Validate the worked-holiday request linked to a Comp Off application.

	HRMS remains responsible for normal leave validation, approval, allocation,
	and ledger entries.  This app only makes the standard Compensatory Leave
	Request traceable from the standard Leave Application and prevents its reuse.
	"""
	comp_off_leave_type = frappe.db.get_single_value("HR Settings", "custom_comp_off_leave_type")

	# A site may not have configured the app yet.  Leave all standard behaviour
	# unchanged until HR selects the compensatory leave type in HR Settings.
	if not comp_off_leave_type or doc.leave_type != comp_off_leave_type:
		return

	if not doc.custom_comp_off_source_request:
		frappe.throw(
			_("Select the approved Compensatory Leave Request that earned this leave."),
			title=_("Compensatory Leave Request Required"),
		)

	source = frappe.db.get_value(
		"Compensatory Leave Request",
		doc.custom_comp_off_source_request,
		[
			"employee",
			"leave_type",
			"work_from_date",
			"work_end_date",
			"docstatus",
		],
		as_dict=True,
	)

	if not source:
		frappe.throw(_("The selected Compensatory Leave Request does not exist."))

	if source.docstatus != 1:
		frappe.throw(_("The selected Compensatory Leave Request must be submitted."))

	if source.employee != doc.employee:
		frappe.throw(_("The selected Compensatory Leave Request belongs to another employee."))

	if source.leave_type != doc.leave_type:
		frappe.throw(_("The source request leave type must match this Leave Application."))

	# One source field represents one earned day.  Multiple worked holidays must
	# be recorded as separate standard Compensatory Leave Requests so each leave
	# application retains an unambiguous audit trail.
	if getdate(source.work_from_date) != getdate(source.work_end_date):
		frappe.throw(
			_("Select a Compensatory Leave Request for one worked holiday date only."),
			title=_("Multiple Worked Dates Not Supported"),
		)

	# HRMS credits Comp Off from the day after the holiday work ends.
	if getdate(doc.from_date) <= getdate(source.work_end_date):
		frappe.throw(
			_("Compensatory Off can be used only after the worked holiday date."),
			title=_("Invalid Compensatory Off Date"),
		)

	# A source request represents a specific earned credit.  It may be linked to
	# one submitted application only; drafts are intentionally reusable until one
	# of them is approved and submitted.
	already_used = frappe.db.exists(
		"Leave Application",
		{
			"custom_comp_off_source_request": doc.custom_comp_off_source_request,
			"docstatus": 1,
			"name": ["!=", doc.name],
		},
	)

	if already_used:
		frappe.throw(
			_("This worked-holiday credit is already linked to Leave Application {0}.").format(
				frappe.bold(already_used)
			),
			title=_("Compensatory Credit Already Used"),
		)
