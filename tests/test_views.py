import datetime

from django.test import TestCase
from django.utils import timezone

from plugins.reviewer_reporter import forms
from plugins.reviewer_reporter import views
from utils.testing import helpers


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


class TestReviewerReporterScoping(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()

        cls.assignment_one = helpers.create_review_assignment(
            journal=cls.journal_one,
        )
        cls.assignment_two = helpers.create_review_assignment(
            journal=cls.journal_two,
        )

        cls.today = timezone.now().date()
        cls.yesterday = cls.today - datetime.timedelta(days=1)

    def test_only_returns_assignments_from_the_given_journal(self):
        data = views.get_peer_review_data(
            self.journal_one,
            self.yesterday,
            self.today,
        )
        manuscript_numbers = [row[1] for row in data]
        self.assertIn(self.assignment_one.article.pk, manuscript_numbers)
        self.assertNotIn(self.assignment_two.article.pk, manuscript_numbers)

    def test_end_date_includes_assignments_requested_that_day(self):
        # date_requested is auto_now_add, so both fixtures are stamped today.
        # A date-to-datetime comparison would treat end_date as midnight and
        # drop them.
        data = views.get_peer_review_data(
            self.journal_one,
            self.today,
            self.today,
        )
        self.assertEqual(len(data), 1)

    def test_returns_nothing_outside_the_range(self):
        long_ago = self.today - datetime.timedelta(days=30)
        data = views.get_peer_review_data(
            self.journal_one,
            long_ago,
            long_ago,
        )
        self.assertEqual(data, [])
