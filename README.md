# Reviewer Reporter

A Janeway plugin that exports a CSV of all review requests sent for a journal
during a chosen date range, listing the reviewer, the manuscript, the status of
the request, the relevant dates and any reviewer rating.

The report is scoped to the journal it is run from, and is available to editors,
journal managers and staff.

## Requirements

Janeway 1.3.8 or later. This plugin has no dependencies on other plugins.

Versions before this one imported `plugins.reporting` for its date fields and
would not load unless the Reporting plugin was also installed. That requirement
is gone — if you are upgrading an existing install, Reporting is no longer
needed for this plugin to work, though you may of course still want it.

## Install

1. Clone into `src/plugins/` so the directory is named `reviewer_reporter`.
   The directory name must match `SHORT_NAME` in `plugin_settings.py`.
2. Run the install command:

   ```
   python src/manage.py install_plugins reviewer_reporter
   ```

3. Restart the server. Plugin URLs are registered when the URL configuration is
   imported, so a running server will not pick the plugin up until it restarts.

The report is then available from Manager → Plugins within a journal, at
`/plugins/reviewer-reporter/`. Note the hyphen: the URL slug is derived from
`DISPLAY_NAME`, not `SHORT_NAME`.

## Tests

```
python src/manage.py test plugins.reviewer_reporter
```
