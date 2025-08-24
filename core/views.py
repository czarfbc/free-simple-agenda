from datetime import datetime
from .models import TimeOption, Appointment, Service

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.urls import reverse
from django.http import HttpResponseBadRequest

from django.contrib.auth.hashers import check_password, make_password

from .models import TimeOption, Service, Appointment, Manager
from .forms import ManagerLoginForm, TimeOptionForm, ServiceForm
from .auth import manager_required, SESSION_KEY
from datetime import datetime, date
from django.utils import timezone

# ---------------------- ÁREA PÚBLICA (já existentes) ----------------------


@require_http_methods(["GET"])
def book_form(request):
    date_str = request.GET.get("booking_date", "")
    time_id = request.GET.get("time_id", "")
    if not date_str or not time_id:
        return HttpResponseBadRequest("Faltou data ou horário.")

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Data inválida (use YYYY-MM-DD).")

    time_option = get_object_or_404(
        TimeOption, pk=time_id, disable=False, trashed=False)

    # ainda disponível?
    if Appointment.objects.filter(booking_date=dt, booking_time=time_option).exists():
        return HttpResponseBadRequest("Este horário não está mais disponível.")

    # ✅ definir 'services' antes do render
    services = Service.objects.filter(
        disable=False, trashed=False).order_by("name")

    return render(request, "core/_book_form.html", {
        "selected_date": dt,
        "time_option": time_option,
        "services": services,
    })


@require_http_methods(["GET"])
def booking_page(request):
    selected_date = request.GET.get("date")
    return render(request, "core/booking.html", {"selected_date": selected_date})


@require_http_methods(["POST"])
def available_times(request):
    date_str = request.POST.get("date", "").strip()
    if not date_str:
        return HttpResponseBadRequest("Data obrigatória")
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Data inválida (use YYYY-MM-DD)")

    qs = (TimeOption.objects
          .filter(disable=False, trashed=False)
          .exclude(appointment__booking_date=selected_date)
          .order_by("horario"))

    return render(request, "core/_available_times.html", {
        "times": qs,
        "selected_date": selected_date,
    })


@require_POST
def create_appointment(request):
    client_name = request.POST.get("client_name", "").strip()
    client_phone = request.POST.get("client_phone", "").strip()
    observation = request.POST.get("observation", "").strip()
    booking_date = request.POST.get("booking_date", "").strip()
    time_id = request.POST.get("time_id", "").strip()
    service_id = request.POST.get("service_id", "").strip()  # obrigatório

    if not (client_name and client_phone and booking_date and time_id and service_id):
        return HttpResponseBadRequest("Preencha todos os campos.")

    # parse da data (define dt)
    try:
        dt = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Data inválida (use YYYY-MM-DD).")

    time_option = get_object_or_404(
        TimeOption, pk=time_id, disable=False, trashed=False)
    service = get_object_or_404(
        Service, pk=service_id, disable=False, trashed=False)

    # checar concorrência
    if Appointment.objects.filter(booking_date=dt, booking_time=time_option).exists():
        return HttpResponseBadRequest("Este horário não está mais disponível.")

    appointment = Appointment.objects.create(
        client_name=client_name,
        client_phone=client_phone,
        booking_date=dt,
        booking_time=time_option,
        service=service,
        observation=observation,
    )

    return render(request, "core/_book_success.html", {"appointment": appointment})

# ---------------------- AUTH MANAGER ----------------------


@require_http_methods(["GET", "POST"])
def manager_login(request):
    if request.session.get(SESSION_KEY):
        return redirect("core:manager_dashboard")

    form = ManagerLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip()
        password = form.cleaned_data["password"]

        try:
            mgr = Manager.objects.get(email=email)
        except Manager.DoesNotExist:
            mgr = None

        ok = False
        if mgr:
            # Se você já salvou hash (recomendado): use check_password
            ok = check_password(password, mgr.password) or (
                mgr.password == password)  # fallback caso esteja em texto

        if ok and mgr:
            request.session[SESSION_KEY] = str(mgr.id)
            next_url = request.GET.get("next") or reverse(
                "core:manager_dashboard")
            return redirect(next_url)
        else:
            messages.error(request, "Credenciais inválidas.")

    return render(request, "core/manager/login.html", {"form": form})


@require_http_methods(["POST", "GET"])
def manager_logout(request):
    request.session.pop(SESSION_KEY, None)
    return redirect("core:manager_login")


@manager_required
@require_http_methods(["GET"])
def manager_dashboard(request):
    return render(request, "core/manager/dashboard.html")

# ---------------------- CRUD: Time Options ----------------------


@manager_required
@require_http_methods(["GET", "POST"])
def manager_time_options(request):
    if request.method == "POST":
        form = TimeOptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Horário criado com sucesso.")
            return redirect("core:manager_time_options")
    else:
        form = TimeOptionForm()

    times = TimeOption.objects.filter(trashed=False).order_by("horario")
    return render(request, "core/manager/time_options.html", {
        "form": form,
        "times": times,
    })

# ---------------------- CRUD: Services ----------------------


@manager_required
@require_http_methods(["GET", "POST"])
def manager_services(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço criado com sucesso.")
            return redirect("core:manager_services")
    else:
        form = ServiceForm()

    services = Service.objects.order_by("name")
    return render(request, "core/manager/services.html", {
        "form": form,
        "services": services,
    })

# ---------------------- CRUD: Appointment  ----------------------


@manager_required
@require_http_methods(["GET"])
def manager_appointments(request):
    # pega ?date=YYYY-MM-DD; se vazio, usa hoje
    date_str = request.GET.get("date")
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return HttpResponseBadRequest("Data inválida (use YYYY-MM-DD).")
    else:
        selected_date = date.today()

    appointments = (
        Appointment.objects
        .filter(booking_date=selected_date)
        .select_related("booking_time", "service")
        .order_by("booking_time__horario", "created_at")
    )

    return render(request, "core/manager/appointments.html", {
        "selected_date": selected_date,
        "appointments": appointments,
        "total": appointments.count(),
    })


@manager_required
@require_POST
def manager_time_option_toggle(request, pk):
    obj = get_object_or_404(TimeOption, pk=pk, trashed=False)
    obj.disable = not obj.disable
    obj.save(update_fields=["disable", "updated_at"])
    if obj.disable:
        messages.info(request, f"Horário {obj.horario} desativado.")
    else:
        messages.success(request, f"Horário {obj.horario} reativado.")
    return redirect("core:manager_time_options")


@manager_required
@require_POST
def manager_time_option_trash(request, pk):
    obj = get_object_or_404(TimeOption, pk=pk, trashed=False)
    obj.trashed = True
    obj.trashed_at = timezone.now()
    obj.save(update_fields=["trashed", "trashed_at", "updated_at"])
    messages.warning(request, f"Horário {obj.horario} enviado para lixeira.")
    return redirect("core:manager_time_options")


@manager_required
@require_POST
def manager_service_toggle(request, pk):
    obj = get_object_or_404(Service, pk=pk, trashed=False)
    obj.disable = not obj.disable
    obj.save(update_fields=["disable", "updated_at"])
    return redirect("core:manager_services")


@manager_required
@require_POST
def manager_service_trash(request, pk):
    obj = get_object_or_404(Service, pk=pk, trashed=False)
    obj.trashed = True
    obj.save(update_fields=["trashed", "updated_at"])
    return redirect("core:manager_services")
