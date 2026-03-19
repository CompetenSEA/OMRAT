"""URL configuration for standalone OMRAT backend."""

from django.urls import path

from omrat_api.web.workbench_views import workbench_action_view

urlpatterns = [
    path('api/workbench/<str:action>', workbench_action_view, name='workbench-action'),
]
