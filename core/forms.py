from django import forms
from .models import TimeOption, Service
from decimal import Decimal
from django import forms
from .models import Service


class ManagerLoginForm(forms.Form):
    email = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class TimeOptionForm(forms.ModelForm):
    class Meta:
        model = TimeOption
        fields = ["horario"]
        widgets = {
            "horario": forms.TimeInput(attrs={"type": "time", "class": "w-full rounded-lg border px-3 py-2"}),
        }


class ServiceForm(forms.ModelForm):
    price_brl = forms.DecimalField(
        label="Preço (R$)",
        min_value=0,
        decimal_places=2,
        max_digits=12,
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "w-full rounded-lg border px-3 py-2",
            "placeholder": "Ex.: 99,90",
        }),
    )

    class Meta:
        model = Service
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full rounded-lg border px-3 py-2",
                "placeholder": "Ex.: Corte de cabelo",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None):
            if self.instance.price_cents is not None:
                self.fields["price_brl"].initial = (
                    Decimal(self.instance.price_cents) / Decimal("100")
                )

    def save(self, commit=True):
        obj = super().save(commit=False)
        price_brl = self.cleaned_data["price_brl"]
        obj.price_cents = int(price_brl * 100)
        if commit:
            obj.save()
        return obj
