from django.db.models import Count, Avg, Min, Max, Q
from django.db.models.functions import Trunc
from django.utils import timezone
from datetime import timedelta
from django.db import models
from submissions.models import FormSubmission, SubmissionAnswer
from analytics.models import FormView
from forms.models import Form, FormField

def get_overview_stats(form: Form) -> dict:
    total_views = FormView.objects.filter(form=form).count()
    total_submissions = FormSubmission.objects.filter(
        form=form, 
        status=FormSubmission.STATUS_CHOICES[1][0] # 'submitted'
    ).count()
    
    completion_rate = 0.0
    if total_views > 0:
        completion_rate = (total_submissions / total_views) * 100
        
    return {
        "total_views": total_views,
        "total_submissions": total_submissions,
        "completion_rate": round(completion_rate, 2),
        "last_viewed_at": FormView.objects.filter(form=form).latest('viewed_at').viewed_at if total_views > 0 else None,
        "last_submitted_at": FormSubmission.objects.filter(form=form, status='submitted').latest('submitted_at').submitted_at if total_submissions > 0 else None
    }

def get_timeseries_report(queryset, date_field: str, period: str = 'day') -> models.QuerySet:
    valid_periods = ['day', 'hour', 'week', 'month']
    if period not in valid_periods:
        period = 'day'
        
    return queryset.annotate(
        period_group=Trunc(date_field, period)
    ).values("period_group").annotate(
        count=Count("id")
    ).order_by("period_group")

def get_drop_off_report(form: Form) -> dict:
    total_views = FormView.objects.filter(form=form).count()
    
    total_started = FormSubmission.objects.filter(form=form).values('session_id').distinct().count()
    
    total_submitted = FormSubmission.objects.filter(
        form=form, 
        status='submitted'
    ).count()
    
    return {
        "views": total_views,
        "started_submission": total_started, # (Drafts + Submissions)
        "completed_submission": total_submitted
    }

def get_summary_report(form: Form) -> list:
    report = []
    
    for field in form.fields.all().order_by('order_index'):
        field_report = {
            "field_id": field.id,
            "label": field.label,
            "field_type": field.field_type,
            "total_responses": SubmissionAnswer.objects.filter(
                field=field, 
                submission__form=form, 
                submission__status='submitted'
            ).count(),
            "aggregation": {}
        }
        
        if field.field_type == 'number':
            agg_data = SubmissionAnswer.objects.filter(
                field=field, 
                submission__form=form, 
                submission__status='submitted'
            ).aggregate(
                average=Avg('numeric_value'),
                min=Min('numeric_value'),
                max=Max('numeric_value'),
                sum=models.Sum('numeric_value')
            )
            field_report["aggregation"] = agg_data
            
        elif field.field_type in ['select', 'radio', 'checkbox']:
            if field.field_type in ['select', 'radio']:
                 agg_data = SubmissionAnswer.objects.filter(
                    field=field, 
                    submission__form=form, 
                    submission__status='submitted'
                ).values('text_value').annotate(
                    count=Count('id')
                ).order_by('-count')
                 field_report["aggregation"] = list(agg_data)

        report.append(field_report)
        
    return report

def get_field_specific_report(field: FormField) -> dict:
    report = {
        "field_id": field.id,
        "label": field.label,
        "field_type": field.field_type,
        "total_responses": SubmissionAnswer.objects.filter(
            field=field, 
            submission__status='submitted'
        ).count(),
        "aggregation": {}
    }
    
    if field.field_type == 'number':
        agg_data = SubmissionAnswer.objects.filter(
            field=field, 
            submission__status='submitted'
        ).aggregate(
            average=Avg('numeric_value'),
            min=Min('numeric_value'),
            max=Max('numeric_value'),
            sum=models.Sum('numeric_value')
        )
        report["aggregation"] = agg_data
        
    elif field.field_type in ['select', 'radio']:
         agg_data = SubmissionAnswer.objects.filter(
            field=field, 
            submission__status='submitted'
        ).values('text_value').annotate(
            count=Count('id')
        ).order_by('-count')
         report["aggregation"] = list(agg_data)

    return report