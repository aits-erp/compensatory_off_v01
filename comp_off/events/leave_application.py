import frappe
from frappe import _
from frappe.utils import flt, formatdate, getdate


def assign_comp_off_sources_fifo(doc, method=None):
	"""Automatically attach the oldest eligible earned credits before submit.

	The standard HRMS leave allocation and ledger remain the source of truth for
	balances. This mapping makes each consumed Comp Off day auditable and stops a
	worked-holiday credit from being reused. Draft Leave Applications deliberately
	do not reserve credits.
	"""
	if not _is_compensatory_leave(doc.leave_type):
		return

	required_credits = _get_required_credit_count(doc)
	sources = _get_oldest_unused_sources(
		doc.employee, doc.leave_type, getdate(doc.from_date), required_credits
	)

	if len(sources) < required_credits:
		frappe.throw(
			_("Insufficient unused Compensatory Off credits. Leave requested: {0} day(s); credits available: {1}.").format(
				required_credits, len(sources)
			),
			title=_("Insufficient Compensatory Off Credits"),
		)

	# Never honour source rows submitted by the browser. The server replaces them
	# with the actual FIFO allocation at the point the leave is submitted.
	doc.set("custom_comp_off_source_request", [])
	for source in sources:
		doc.append("custom_comp_off_source_request", {"compensatory_leave_request": source.name})

	doc.custom_comp_off_available_work_date = ", ".join(
		formatdate(source.work_from_date) for source in sources
	)


def _is_compensatory_leave(leave_type):
	return bool(leave_type and frappe.db.get_value("Leave Type", leave_type, "is_compensatory"))


def _get_required_credit_count(doc):
	leave_days = flt(doc.total_leave_days)
	if leave_days <= 0:
		frappe.throw(_("Total leave days must be greater than zero for Compensatory Off."))

	if leave_days != int(leave_days):
		frappe.throw(
			_("Automatic Compensatory Off currently supports full-day leave only."),
			title=_("Half-Day Compensatory Off Not Supported"),
		)

	return int(leave_days)


def _get_oldest_unused_sources(employee, leave_type, leave_from_date, limit):
	"""Lock and return the oldest eligible Comp Off credits for an employee."""
	return frappe.db.sql(
		"""
			select request.name, request.work_from_date, request.work_end_date
			from `tabCompensatory Leave Request` request
			where request.employee = %(employee)s
			  and request.leave_type = %(leave_type)s
			  and request.docstatus = 1
			  and request.work_from_date = request.work_end_date
			  and request.work_end_date < %(leave_from_date)s
			  and not exists (
				select 1
				from `tabComp Off Source Request` source
				inner join `tabLeave Application` application on application.name = source.parent
				where source.parenttype = 'Leave Application'
				  and source.parentfield = 'custom_comp_off_source_request'
				  and source.compensatory_leave_request = request.name
				  and application.docstatus = 1
			  )
			order by request.work_from_date asc, request.creation asc
			limit %(limit)s
			for update
		""",
		{
			"employee": employee,
			"leave_type": leave_type,
			"leave_from_date": leave_from_date,
			"limit": limit,
		},
		as_dict=True,
	)
