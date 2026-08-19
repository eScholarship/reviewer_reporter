from django import forms


class DateInput(forms.DateInput):
    input_type = "date"


class ReviewerReporterForm(forms.Form):
    start_date = forms.DateField(widget=DateInput())
    end_date = forms.DateField(widget=DateInput())
