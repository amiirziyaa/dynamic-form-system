import csv
import json
import io
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
# from my_project.storage_backends import public_storage

from .models import ReportSchedule, ReportInstance
from submissions.models import FormSubmission, SubmissionAnswer
# from .services import send_report_email, send_report_webhook

@shared_task(name="notifications.tasks.generate_scheduled_report")
def generate_scheduled_report(schedule_id):
    try:
        schedule = ReportSchedule.objects.get(id=schedule_id)
    except ReportSchedule.DoesNotExist:
        print(f"ReportSchedule {schedule_id} not found. Deleting task.")
        return

    instance = ReportInstance.objects.create(
        schedule=schedule,
        report_type=schedule.report_type,
        status='running',
        started_at=timezone.now()
    )
    
    try:
        file_content, filename = _generate_report_file(schedule)
        
        # file_path = public_storage.save(f"reports/{filename}", ContentFile(file_content))
        # file_url = public_storage.url(file_path)
        
        file_url = f"https://example.com/reports/{filename}" 
        
        instance.status = 'completed'
        instance.completed_at = timezone.now()
        instance.file_url = file_url
        instance.file_size = len(file_content)
        instance.save()
        
        if schedule.send_to_email:
            pass
        if schedule.send_to_webhook:
            pass
            
    except Exception as e:
        instance.status = 'failed'
        instance.error_message = str(e)
        instance.completed_at = timezone.now()
        instance.save()
        
    return f"Report instance {instance.id} finished with status {instance.status}"


def _generate_report_file(schedule: ReportSchedule):
    filename = f"report_{schedule.report_type}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{schedule.output_format}"
    submissions = FormSubmission.objects.filter(status='submitted').order_by('-submitted_at')
    
    if schedule.output_format == 'json':
        data = [
            {
                'id': str(s.id),
                'form_title': s.form.title,
                'submitted_at': s.submitted_at.isoformat(),
                'user': s.user.email if s.user else 'Anonymous'
            } for s in submissions
        ]
        content = json.dumps(data, indent=2)
        return content.encode('utf-8'), filename

    elif schedule.output_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Submission ID', 'Form Title', 'Submitted At', 'User'])
        
        for s in submissions:
            writer.writerow([
                str(s.id),
                s.form.title,
                s.submitted_at.isoformat(),
                s.user.email if s.user else 'Anonymous'
            ])
            
        return output.getvalue().encode('utf-8'), filename
        
    raise ValueError(f"Unsupported format: {schedule.output_format}")