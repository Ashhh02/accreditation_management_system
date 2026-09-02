"""
URL configuration for the JMCFI AMS project.

Each feature lives in its own app with its own urls.py. This file only
wires apps together under a namespace/prefix, so new modules (e.g. a
future `submissions` app) can be added here without touching anything
else.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts import views as account_views

from . import views as config_views

handler400 = config_views.bad_request
handler403 = config_views.permission_denied
handler404 = config_views.not_found
handler500 = config_views.server_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', account_views.PortalLoginView.as_view(), name='login'),
    path('logout/', account_views.PortalLogoutView.as_view(next_page='/login/'), name='logout'),
    path('register/', account_views.RegisterView.as_view(), name='register'),

    path('', include('dashboard.urls')),
    path('', include('core.urls')),
    path('accreditation/', include('accreditation.urls')),
    path('resources/', include('resources.urls')),
    path('intelligence/', include('intelligence.urls')),
    path('account/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
