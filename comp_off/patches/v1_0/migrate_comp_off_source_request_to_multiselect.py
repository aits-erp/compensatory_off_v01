import frappe


def execute():
	"""One-time migration: move the legacy single-value
	`custom_comp_off_source_request` link (from before this field became a
	Table MultiSelect) into the new `Comp Off Source Request` child rows.

	Frappe never drops old columns on a field type change, so the legacy
	value is still readable via SQL even though the ORM now treats this
	fieldname as a child table. Safe to re-run: already-migrated rows are
	skipped.
	"""
	if not frappe.db.has_column("Leave Application", "custom_comp_off_source_request"):
		return

	legacy_rows = frappe.db.sql(
		"""
		select name, custom_comp_off_source_request as source_request
		from `tabLeave Application`
		where custom_comp_off_source_request is not null
		  and custom_comp_off_source_request != ''
		""",
		as_dict=True,
	)

	if not legacy_rows:
		return

	migrated, skipped = 0, 0

	for row in legacy_rows:
		source_name = row.source_request

		if not frappe.db.exists("Compensatory Leave Request", source_name):
			skipped += 1
			continue

		if frappe.db.exists(
			"Comp Off Source Request",
			{
				"parent": row.name,
				"parenttype": "Leave Application",
				"compensatory_leave_request": source_name,
			},
		):
			continue  # already migrated

		next_idx = frappe.db.count(
			"Comp Off Source Request",
			{"parent": row.name, "parenttype": "Leave Application"},
		) + 1

		child = frappe.get_doc(
			{
				"doctype": "Comp Off Source Request",
				"parent": row.name,
				"parenttype": "Leave Application",
				"parentfield": "custom_comp_off_source_request",
				"idx": next_idx,
				"compensatory_leave_request": source_name,
			}
		)
		child.db_insert()
		migrated += 1

	frappe.db.commit()
	frappe.logger("comp_off").info(
		f"comp_off migration: migrated {migrated} link(s), skipped {skipped} (missing source doc)."
	)