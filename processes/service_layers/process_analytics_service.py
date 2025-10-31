from typing import List, Optional, Dict, Any
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from processes.models import Process, ProcessStep
from processes.repository import ProcessRepository, ProcessProgressRepository, ProcessStepCompletionRepository
from submissions.models import ProcessProgress, ProcessStepCompletion
from analytics.models import ProcessView
from shared.exceptions import NotFoundError


class ProcessAnalyticsService:
    """
    Service class for Process analytics business logic.
    Handles analytics calculations and reporting for process owners.
    """

    def __init__(self):
        self.process_repository = ProcessRepository()
        self.progress_repository = ProcessProgressRepository()
        self.completion_repository = ProcessStepCompletionRepository()

    def get_analytics_overview(self, user, slug: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics overview for a process.
        
        Args:
            user: Owner user
            slug: Process unique slug
            
        Returns:
            Dictionary with analytics overview
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        total_views = ProcessView.objects.filter(process=process).count()
        
        progress_records = ProcessProgress.objects.filter(process=process)
        total_started = progress_records.count()
        total_completed = progress_records.filter(status='completed').count()
        total_abandoned = progress_records.filter(status='abandoned').count()
        
        completion_rate = 0.0
        if total_started > 0:
            completion_rate = (total_completed / total_started) * 100

        avg_completion_time = self._calculate_average_completion_time(process)
        
        unique_users = progress_records.filter(user__isnull=False).values('user').distinct().count()
        anonymous_count = progress_records.filter(user__isnull=True).count()
        
        steps_data = []
        steps = process.steps.all().order_by('order_index')
        for step in steps:
            step_progress_count = ProcessStepCompletion.objects.filter(
                step=step,
                progress__process=process
            ).count()
            step_completed_count = ProcessStepCompletion.objects.filter(
                step=step,
                progress__process=process,
                status='completed'
            ).count()
            
            step_completion_rate = 0.0
            if step_progress_count > 0:
                step_completion_rate = (step_completed_count / step_progress_count) * 100
            
            steps_data.append({
                'step_id': str(step.id),
                'title': step.title,
                'order_index': step.order_index,
                'started_count': step_progress_count,
                'completed_count': step_completed_count,
                'completion_rate': round(step_completion_rate, 2)
            })

        return {
            'process_id': str(process.id),
            'process_title': process.title,
            'process_slug': process.unique_slug,
            'total_views': total_views,
            'total_started': total_started,
            'total_completed': total_completed,
            'total_abandoned': total_abandoned,
            'completion_rate': round(completion_rate, 2),
            'average_completion_time_minutes': round(avg_completion_time, 2) if avg_completion_time else None,
            'unique_users': unique_users,
            'anonymous_count': anonymous_count,
            'steps_analytics': steps_data,
            'last_viewed_at': self._get_last_view_time(process),
            'last_completed_at': self._get_last_completion_time(process)
        }

    def get_views_over_time(
        self,
        user,
        slug: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get view count over time.
        
        Args:
            user: Owner user
            slug: Process unique slug
            days: Number of days to analyze (default 30)
            
        Returns:
            Dictionary with views over time data
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        start_date = timezone.now() - timedelta(days=days)
        
        views_by_date = ProcessView.objects.filter(
            process=process,
            viewed_at__gte=start_date
        ).annotate(
            date=TruncDate('viewed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        views_data = {
            str(item['date']): item['count']
            for item in views_by_date
        }

        return {
            'process_id': str(process.id),
            'process_slug': process.unique_slug,
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': timezone.now().isoformat(),
            'total_views': sum(views_data.values()),
            'views_by_date': views_data
        }

    def get_completions_over_time(
        self,
        user,
        slug: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get completion count over time.
        
        Args:
            user: Owner user
            slug: Process unique slug
            days: Number of days to analyze (default 30)
            
        Returns:
            Dictionary with completions over time data
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        start_date = timezone.now() - timedelta(days=days)
        
        completions_by_date = ProcessProgress.objects.filter(
            process=process,
            status='completed',
            completed_at__gte=start_date,
            completed_at__isnull=False
        ).annotate(
            date=TruncDate('completed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        completions_data = {
            str(item['date']): item['count']
            for item in completions_by_date
        }

        return {
            'process_id': str(process.id),
            'process_slug': process.unique_slug,
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': timezone.now().isoformat(),
            'total_completions': sum(completions_data.values()),
            'completions_by_date': completions_data
        }

    def get_completion_rate(self, user, slug: str) -> Dict[str, Any]:
        """
        Get overall completion rate.
        
        Args:
            user: Owner user
            slug: Process unique slug
            
        Returns:
            Dictionary with completion rate data
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        progress_records = ProcessProgress.objects.filter(process=process)
        
        total_started = progress_records.count()
        total_completed = progress_records.filter(status='completed').count()
        total_abandoned = progress_records.filter(status='abandoned').count()
        total_in_progress = progress_records.filter(status='in_progress').count()
        
        completion_rate = 0.0
        if total_started > 0:
            completion_rate = (total_completed / total_started) * 100

        abandonment_rate = 0.0
        if total_started > 0:
            abandonment_rate = (total_abandoned / total_started) * 100

        return {
            'process_id': str(process.id),
            'process_slug': process.unique_slug,
            'total_started': total_started,
            'total_completed': total_completed,
            'total_abandoned': total_abandoned,
            'total_in_progress': total_in_progress,
            'completion_rate': round(completion_rate, 2),
            'abandonment_rate': round(abandonment_rate, 2)
        }

    def get_step_drop_off(self, user, slug: str) -> Dict[str, Any]:
        """
        Get drop-off analysis by step.
        
        Args:
            user: Owner user
            slug: Process unique slug
            
        Returns:
            Dictionary with drop-off data per step
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        steps = process.steps.all().order_by('order_index')
        total_started = ProcessProgress.objects.filter(process=process).count()
        
        drop_off_data = []
        previous_completion_count = total_started
        
        for step in steps:
            step_started = ProcessStepCompletion.objects.filter(
                step=step,
                progress__process=process
            ).count()
            
            step_completed = ProcessStepCompletion.objects.filter(
                step=step,
                progress__process=process,
                status='completed'
            ).count()
            
            drop_off_count = previous_completion_count - step_started
            drop_off_percentage = 0.0
            if previous_completion_count > 0:
                drop_off_percentage = (drop_off_count / previous_completion_count) * 100
            
            retention_rate = 0.0
            if previous_completion_count > 0:
                retention_rate = (step_started / previous_completion_count) * 100
            
            drop_off_data.append({
                'step_id': str(step.id),
                'step_title': step.title,
                'order_index': step.order_index,
                'started_count': step_started,
                'completed_count': step_completed,
                'drop_off_count': drop_off_count,
                'drop_off_percentage': round(drop_off_percentage, 2),
                'retention_rate': round(retention_rate, 2)
            })
            
            previous_completion_count = step_completed

        return {
            'process_id': str(process.id),
            'process_slug': process.unique_slug,
            'total_started': total_started,
            'steps_drop_off': drop_off_data
        }

    def get_average_completion_time(self, user, slug: str) -> Dict[str, Any]:
        """
        Get average completion time for the process.
        
        Args:
            user: Owner user
            slug: Process unique slug
            
        Returns:
            Dictionary with average completion time data
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        avg_time_minutes = self._calculate_average_completion_time(process)
        
        completed_progress = ProcessProgress.objects.filter(
            process=process,
            status='completed',
            completed_at__isnull=False
        )
        
        times_data = []
        for progress in completed_progress:
            if progress.completed_at and progress.started_at:
                delta = (progress.completed_at - progress.started_at).total_seconds() / 60
                times_data.append(delta)
        
        min_time = min(times_data) if times_data else None
        max_time = max(times_data) if times_data else None
        median_time = self._calculate_median(times_data) if times_data else None

        return {
            'process_id': str(process.id),
            'process_slug': process.unique_slug,
            'average_time_minutes': round(avg_time_minutes, 2) if avg_time_minutes else None,
            'min_time_minutes': round(min_time, 2) if min_time else None,
            'max_time_minutes': round(max_time, 2) if max_time else None,
            'median_time_minutes': round(median_time, 2) if median_time else None,
            'sample_size': len(times_data)
        }

    def get_all_progress(
        self,
        user,
        slug: str,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all progress records for a process.
        
        Args:
            user: Owner user
            slug: Process unique slug
            status_filter: Optional status filter
            
        Returns:
            List of progress records
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        queryset = ProcessProgress.objects.filter(process=process).select_related('user')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        progress_list = []
        for progress in queryset.order_by('-created_at'):
            progress_list.append({
                'id': str(progress.id),
                'user_email': progress.user.email if progress.user else None,
                'session_id': progress.session_id,
                'status': progress.status,
                'current_step_index': progress.current_step_index,
                'completion_percentage': float(progress.completion_percentage),
                'started_at': progress.started_at.isoformat(),
                'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                'last_activity_at': progress.last_activity_at.isoformat()
            })

        return progress_list

    def get_progress_details(self, user, slug: str, progress_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific progress record.
        
        Args:
            user: Owner user
            slug: Process unique slug
            progress_id: Progress record ID
            
        Returns:
            Dictionary with detailed progress information
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        progress = self.progress_repository.get_by_id(progress_id)
        if not progress or progress.process != process:
            raise NotFoundError(f"Progress record not found")

        completions = self.completion_repository.get_by_progress(progress)
        
        step_completions = []
        for completion in completions:
            step_completions.append({
                'step_id': str(completion.step.id),
                'step_title': completion.step.title,
                'step_order': completion.step.order_index,
                'status': completion.status,
                'completed_at': completion.completed_at.isoformat() if completion.completed_at else None,
                'has_submission': completion.submission is not None
            })

        return {
            'id': str(progress.id),
            'process_id': str(process.id),
            'process_title': process.title,
            'user_email': progress.user.email if progress.user else None,
            'session_id': progress.session_id,
            'status': progress.status,
            'current_step_index': progress.current_step_index,
            'completion_percentage': float(progress.completion_percentage),
            'started_at': progress.started_at.isoformat(),
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'last_activity_at': progress.last_activity_at.isoformat(),
            'step_completions': step_completions
        }

    def get_abandoned_progress(self, user, slug: str) -> List[Dict[str, Any]]:
        """
        List all abandoned progress records.
        
        Args:
            user: Owner user
            slug: Process unique slug
            
        Returns:
            List of abandoned progress records
        """
        process = self.process_repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")

        abandoned_progress = ProcessProgress.objects.filter(
            process=process,
            status='abandoned'
        ).select_related('user').order_by('-last_activity_at')

        abandoned_list = []
        for progress in abandoned_progress:
            hours_inactive = None
            if progress.last_activity_at:
                delta = timezone.now() - progress.last_activity_at
                hours_inactive = round(delta.total_seconds() / 3600, 2)
            
            abandoned_list.append({
                'id': str(progress.id),
                'user_email': progress.user.email if progress.user else None,
                'session_id': progress.session_id,
                'current_step_index': progress.current_step_index,
                'completion_percentage': float(progress.completion_percentage),
                'started_at': progress.started_at.isoformat(),
                'last_activity_at': progress.last_activity_at.isoformat(),
                'hours_inactive': hours_inactive
            })

        return abandoned_list

    def _calculate_average_completion_time(self, process: Process) -> Optional[float]:
        """Calculate average completion time in minutes"""
        completed_progress = ProcessProgress.objects.filter(
            process=process,
            status='completed',
            completed_at__isnull=False
        )
        
        times = []
        for progress in completed_progress:
            if progress.completed_at and progress.started_at:
                delta = (progress.completed_at - progress.started_at).total_seconds() / 60
                times.append(delta)
        
        if times:
            return sum(times) / len(times)
        return None

    def _get_last_view_time(self, process: Process) -> Optional[str]:
        """Get last view time"""
        last_view = ProcessView.objects.filter(process=process).order_by('-viewed_at').first()
        return last_view.viewed_at.isoformat() if last_view else None

    def _get_last_completion_time(self, process: Process) -> Optional[str]:
        """Get last completion time"""
        last_completion = ProcessProgress.objects.filter(
            process=process,
            status='completed'
        ).order_by('-completed_at').first()
        return last_completion.completed_at.isoformat() if last_completion and last_completion.completed_at else None

    def _calculate_median(self, values: List[float]) -> float:
        """Calculate median value"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        return sorted_values[n//2]

