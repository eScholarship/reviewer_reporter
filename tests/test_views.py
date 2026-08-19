from django.test import TestCase

from plugins.reviewer_reporter import forms


class TestReviewerReporterForm(TestCase):
    def test_form_has_date_fields(self):
        form = forms.ReviewerReporterForm()
        self.assertIn("start_date", form.fields)
        self.assertIn("end_date", form.fields)

    def test_form_renders_html5_date_inputs(self):
        form = forms.ReviewerReporterForm()
        self.assertIn('type="date"', str(form["start_date"]))
        self.assertIn('type="date"', str(form["end_date"]))

    def test_widget_is_defined_by_this_plugin(self):
        # Regression guard on the dropped dependency: if the fields are ever
        # borrowed from plugins.reporting again, the widget stops being this
        # module's DateInput.
        form = forms.ReviewerReporterForm()
        self.assertIsInstance(
            form.fields["start_date"].widget,
            forms.DateInput,
        )
        self.assertIsInstance(
            form.fields["end_date"].widget,
            forms.DateInput,
        )

    def test_form_validates_a_date_range(self):
        form = forms.ReviewerReporterForm(
            data={"start_date": "2026-08-01", "end_date": "2026-08-31"},
        )
        self.assertTrue(form.is_valid())
