"""
URL configuration for the JMCFI AMS project.

Each feature lives in its own app with its own urls.py. This file only
wires apps together under a namespace/prefix, so new modules (e.g. a
future `submissions` app) can be added here without touching anything
else.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('dashboard.urls')),
    path('', include('core.urls')),
    path('accreditation/', include('accreditation.urls')),
    path('resources/', include('resources.urls')),
    path('intelligence/', include('intelligence.urls')),
    path('account/', include('accounts.urls')),
]
