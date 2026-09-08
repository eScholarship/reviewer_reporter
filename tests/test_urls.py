"""A URL configuration for tests that need to render the report page.

`core.include_urls` mounts a plugin's URLs only when an enabled `Plugin` row
exists at the moment that module is imported. Under the test runner it never
does: the URL configuration is imported before any fixture is created, so the
plugin's routes are absent and `reverse()` fails.

Tests that only need to exercise the view or its decorators call the view
directly with `utils.testing.helpers.get_request()`. Tests that assert on
rendered HTML use this configuration with `override_settings` instead, so the
request travels the real middleware stack. That matters here: the admin base
template loops over `messages`, which is populated by Django's
`MessageMiddleware`. A hand-built request never passes through it, so the
template renders correctly only by the accident of `_messages` being absent —
and raises `TypeError: 'Mock' object is not iterable` for anyone whose request
object supplies a mocked one.

Built on `core.urls`, the real `ROOT_URLCONF`, rather than `core.include_urls`,
so the admin, hijack and debug toolbar patterns survive — the toolbar's
middleware reverses its own `djdt` namespace on every page and 500s without it.

The mount point mirrors `core/include_urls.py`, which uses
`Plugin.best_name(slug=True)` — the slugified `DISPLAY_NAME`, so the path
segment is hyphenated even though the package is not.
"""

from django.urls import include, re_path

from core.urls import urlpatterns as core_urlpatterns

urlpatterns = core_urlpatterns + [
    re_path(
        r"^plugins/reviewer-reporter/",
        include("plugins.reviewer_reporter.urls"),
    ),
]
