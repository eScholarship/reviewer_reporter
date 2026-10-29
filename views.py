import csv
from django.http import HttpResponse
from django.shortcuts import render
from .forms import ReviewerReporterForm
from review import models as review_models
from security.decorators import editor_user_required, has_journal


@has_journal
@editor_user_required
def reviewer_reporter(request):
    if request.method == 'POST':
        form = ReviewerReporterForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            # Fetch peer review data
            review_requests = get_peer_review_data(
                request.journal,
                start_date,
                end_date,
            )

            # Generate CSV response
            response = generate_csv_response(review_requests)
            return response

    else:  # GET request
        form = ReviewerReporterForm()

    context = {
        'form': form,
    }
    return render(request, 'reviewer_reporter/report.html', context)

def get_peer_review_data(journal, start_date, end_date):
    review_requests = review_models.ReviewAssignment.objects.filter(
        article__journal=journal,
        date_requested__date__gte=start_date,
        date_requested__date__lte=end_date,
    ).select_related('reviewer', 'article', 'reviewerrating')

    # Prepare data for CSV export
    data = []
    for assignment in review_requests:
        reviewer_name = assignment.reviewer.full_name() if assignment.reviewer else "N/A"
        manuscript_number = assignment.article.pk
        request_date = assignment.date_requested.strftime('%Y-%m-%d')

        rating = getattr(assignment, 'reviewerrating', None)
        review_rating = rating.rating if rating else "N/A"

        # Determine review request status and dates
        if assignment.date_complete and assignment.decision != 'withdrawn':
            status = "Completed"
            status_date = assignment.date_complete.strftime('%Y-%m-%d')
            withdraw_date = ""
        elif assignment.date_declined:
            status = "Declined"
            status_date = assignment.date_declined.strftime('%Y-%m-%d')
            withdraw_date = ""
        elif assignment.decision == 'withdrawn':
            status = "Withdrawn"
            status_date = ""
            withdraw_date = assignment.date_complete.strftime('%Y-%m-%d') if assignment.date_complete else ""
        else:
            status = "Pending"
            status_date = ""
            withdraw_date = ""

        accept_date = assignment.date_accepted.strftime('%Y-%m-%d') if assignment.date_accepted else ""
        complete_date = assignment.date_complete.strftime('%Y-%m-%d') if assignment.date_complete and assignment.decision != 'withdrawn' else ""

        data.append([
            reviewer_name,
            manuscript_number,
            request_date,
            status,
            status_date,
            accept_date,
            complete_date,
            withdraw_date,
            review_rating,
        ])

    return data

def generate_csv_response(review_requests):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reviewer_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Reviewer Name',
        'Manuscript Number',
        'Status of Review Request',
        'Date Review was Requested',
        'Date Review was Accepted',
        'Date Review was Declined',
        'Date Review was Withdrawn',
        'Date Review was Completed',
        'Review Rating',
    ])

    for row in review_requests:
        reviewer_name, manuscript_number, request_date, status, status_date, accept_date, complete_date, withdraw_date, review_rating = row
        writer.writerow([
            reviewer_name,
            manuscript_number,
            status,
            request_date,
            accept_date,
            status_date if status == "Declined" else "",
            withdraw_date if status == "Withdrawn" else "",
            complete_date,
            review_rating,
        ])

    return response
