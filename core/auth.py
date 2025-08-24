from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

SESSION_KEY = "manager_id"


def manager_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get(SESSION_KEY):
            return redirect(f"{reverse('core:manager_login')}?next={request.get_full_path()}")
        return view_func(request, *args, **kwargs)
    return _wrapped
