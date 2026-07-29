app_name = "comp_off"
app_title = "Comp Off"
app_publisher = "aits"
app_description = "compansatory off customization"
app_email = "nikhil@aitsind.com"
app_license = "mit"

# Leave Application stays a standard HRMS document.  These hooks only add a
# source-reference and validation around the existing Compensatory Leave flow.
doctype_js = {
	"Leave Application": "public/js/leave_application.js",
}

doc_events = {
	"Leave Application": {
		"validate": "comp_off.events.leave_application.validate_comp_off_source",
	}
}

# Custom Fields are standard Frappe metadata, not custom business DocTypes.
# Keep them in fixtures so every environment receives the same fields on migrate.
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			[
				"name",
				"in",
				[
					"HR Settings-custom_comp_off_leave_type",
					"Leave Application-custom_comp_off_source_request",
					"Leave Application-custom_comp_off_worked_on",
					"Leave Application-custom_related_leave_application",
				],
			]
		],
	}
]

# Apps
# ------------------

required_apps = ["hrms"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "comp_off",
# 		"logo": "/assets/comp_off/logo.png",
# 		"title": "Comp Off",
# 		"route": "/comp_off",
# 		"has_permission": "comp_off.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/comp_off/css/comp_off.css"
# app_include_js = "/assets/comp_off/js/comp_off.js"

# include js, css files in header of web template
# web_include_css = "/assets/comp_off/css/comp_off.css"
# web_include_js = "/assets/comp_off/js/comp_off.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "comp_off/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "comp_off/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "comp_off.utils.jinja_methods",
# 	"filters": "comp_off.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "comp_off.install.before_install"
# after_install = "comp_off.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "comp_off.uninstall.before_uninstall"
# after_uninstall = "comp_off.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "comp_off.utils.before_app_install"
# after_app_install = "comp_off.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "comp_off.utils.before_app_uninstall"
# after_app_uninstall = "comp_off.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "comp_off.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"comp_off.tasks.all"
# 	],
# 	"daily": [
# 		"comp_off.tasks.daily"
# 	],
# 	"hourly": [
# 		"comp_off.tasks.hourly"
# 	],
# 	"weekly": [
# 		"comp_off.tasks.weekly"
# 	],
# 	"monthly": [
# 		"comp_off.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "comp_off.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "comp_off.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "comp_off.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["comp_off.utils.before_request"]
# after_request = ["comp_off.utils.after_request"]

# Job Events
# ----------
# before_job = ["comp_off.utils.before_job"]
# after_job = ["comp_off.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"comp_off.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
