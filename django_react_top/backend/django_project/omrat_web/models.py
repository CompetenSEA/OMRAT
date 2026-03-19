"""ORM models for standalone task and AIS persistence."""

from django.db import models


class TaskRun(models.Model):
    task_id = models.CharField(max_length=64, unique=True)
    state = models.CharField(max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    progress = models.PositiveSmallIntegerField(default=0)
    message = models.CharField(max_length=255, blank=True)
    payload_json = models.JSONField(default=dict)
    result_json = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'omrat_task_runs'
        indexes = [models.Index(fields=['state'])]


class AISRecord(models.Model):
    segment_id = models.CharField(max_length=128)
    ship_category = models.CharField(max_length=128)
    annual_transits = models.FloatField()
    metadata_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'omrat_ais_records'
        indexes = [models.Index(fields=['segment_id']), models.Index(fields=['ship_category'])]


class Project(models.Model):
    project_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255, blank=True)
    settings_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'omrat_projects'


class AnalysisRun(models.Model):
    run_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='runs')
    task = models.ForeignKey(TaskRun, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=32)
    summary_json = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'omrat_analysis_runs'
        indexes = [models.Index(fields=['project', 'status'])]


class ReportArtifact(models.Model):
    report_id = models.CharField(max_length=128, unique=True)
    run = models.ForeignKey(AnalysisRun, on_delete=models.CASCADE, related_name='reports')
    path = models.CharField(max_length=1024)
    checksum = models.CharField(max_length=128, blank=True)
    metadata_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'omrat_report_artifacts'


class ApiToken(models.Model):
    token_hash = models.CharField(max_length=128, unique=True)
    role = models.CharField(max_length=32, default='viewer')
    project_scopes_json = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'omrat_api_tokens'


class AuditEvent(models.Model):
    action = models.CharField(max_length=128)
    role = models.CharField(max_length=64)
    allowed = models.BooleanField(default=False)
    outcome = models.CharField(max_length=64)
    project_id = models.CharField(max_length=128, blank=True)
    metadata_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'omrat_audit_events'
        indexes = [models.Index(fields=['created_at']), models.Index(fields=['action'])]
