import datetime

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
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


class TestReviewerReporterAccess(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()

        cls.editor = helpers.create_editor(
            cls.journal_one,
            email="reviewer_reporter_editor@janeway.systems",
        )
        cls.regular_user = helpers.create_user(
            "reviewer_reporter_regular@janeway.systems",
        )
        cls.regular_user.is_active = True
        cls.regular_user.save()

        cls.staff_user = helpers.create_user(
            "reviewer_reporter_staff@janeway.systems",
            is_staff=True,
            is_active=True,
        )
        cls.staff_user.save()

    def test_press_level_request_is_not_found(self):
        request = helpers.get_request(
            user=self.editor,
            press=self.press,
        )
        with self.assertRaises(Http404):
            views.reviewer_reporter(request)

    def test_editor_can_access_the_report(self):
        request = helpers.get_request(
            user=self.editor,
            press=self.press,
            journal=self.journal_one,
        )
        response = views.reviewer_reporter(request)
        self.assertEqual(response.status_code, 200)

    def test_regular_user_is_denied(self):
        request = helpers.get_request(
            user=self.regular_user,
            press=self.press,
            journal=self.journal_one,
        )
        with self.assertRaises(PermissionDenied):
            views.reviewer_reporter(request)

    def test_anonymous_user_is_redirected_to_login(self):
        request = helpers.get_request(
            user=AnonymousUser(),
            press=self.press,
            journal=self.journal_one,
        )
        response = views.reviewer_reporter(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_staff_user_cannot_reach_press_level_report(self):
        # Regression guard: before the @has_journal decorator, a Django staff
        # account could reach this view at press level (request.journal is None)
        # via editor_user_required's staff_override and Account.check_role's
        # staff_override, and export every review assignment on the install.
        request = helpers.get_request(
            user=self.staff_user,
            press=self.press,
        )
        with self.assertRaises(Http404):
            views.reviewer_reporter(request)
