import uuid
from django.db import models
from decimal import Decimal, ROUND_HALF_UP


class Manager(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    email = models.TextField(unique=True)
    password = models.TextField()  # cuidado: use hash de senha, não texto puro
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TimeOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    horario = models.TimeField()
    disable = models.BooleanField(default=False)
    trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.horario)


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    price_cents = models.IntegerField()
    disable = models.BooleanField(default=False)
    trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def price_brl(self):
        cents = self.price_cents or 0
        return (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def __str__(self):
        return self.name


class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_name = models.TextField()
    client_phone = models.TextField()
    observation = models.TextField(blank=True, null=True)
    booking_date = models.DateField()
    booking_time = models.ForeignKey(TimeOption, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client_name} - {self.booking_date} {self.booking_time}"
