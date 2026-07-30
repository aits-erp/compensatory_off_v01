# Comp Off

Compensatory-off enhancements for Frappe HRMS using only standard HRMS
documents and Custom Fields. The app does not create custom DocTypes or modify
the standard leave ledger.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app comp_off
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/comp_off
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit

## Setup

1. Install the app and run `bench --site <site> migrate`.
2. Ensure the selected standard Leave Type has **Is Compensatory** enabled.
3. Ensure the employee has a Holiday List, submitted Present Attendance on the
   worked holiday, and a submitted standard Compensatory Leave Request.
4. When applying for Compensatory Off, select that request in the Leave
   Application. The **Available Worked Holiday** field lists unused submitted
   Compensatory Leave Requests by worked date; selecting one sets the request
   reference and displays the worked holiday automatically.

Normal leave and Compensatory Off must be separate standard Leave Applications,
because each HRMS Leave Application has one leave type and one ledger entry.
Create one standard Compensatory Leave Request per worked holiday date; this
keeps each compensatory credit traceable to its eventual leave application.
