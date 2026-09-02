"""Lightweight audit-trail helper shared across apps.

Call sites that need a permanent, tamper-evident record should also log to the
application logger; this helper stores the canonical record that is displayed
in the Admin > Audit History page. Anonymous actors (e.g. failed sign-ins) are
kept with a null actor so the trail is complete.
"""

from .models import AuditLog


def record_audit(request, action, object_type='', object_id='', details=None, submission=None):
    """Create an AuditLog entry from the current request and actor."""
    actor = None
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        actor = user

    entry = AuditLog.objects.create(
        actor=actor,
        submission=submission,
        action=action,
        object_type=object_type,
        object_id=str(object_id)[:64],
        details=(details or {}),
    )
    return entry
