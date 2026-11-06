from django.contrib import admin

from .models import EscalationRule, SLAConfig, WorkflowRule

admin.site.register(WorkflowRule)
admin.site.register(SLAConfig)
admin.site.register(EscalationRule)