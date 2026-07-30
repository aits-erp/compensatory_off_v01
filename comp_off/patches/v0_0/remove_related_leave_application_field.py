"""Remove the superseded Related Leave Application custom field."""

import frappe


def execute():
	field_name = "Leave Application-custom_related_leave_application"
	if frappe.db.exists("Custom Field", field_name):
		frappe.delete_doc("Custom Field", field_name, force=True, ignore_permissions=True)
