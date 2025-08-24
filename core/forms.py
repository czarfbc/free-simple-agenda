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
        # simples; você pode expor mais se quiser
        fields = ["horario", "disable"]
        widgets = {
            "horario": forms.TimeInput(attrs={"type": "time"}),
        }


class ServiceForm(forms.ModelForm):
    # Campo em reais (mostra no formulário)
    price_brl = forms.DecimalField(
        label="Preço (R$)",
        min_value=0,
        decimal_places=2,
        max_digits=12,
        required=True,
    )

    class Meta:
        model = Service
        fields = ["name", "disable"]  # NÃO inclua price_cents aqui
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full rounded-lg border px-3 py-2",
                "placeholder": "Ex.: Corte de cabelo",
            }),
            "disable": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Só pré-carrega se houver instance e price_cents não for None
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None):
            if self.instance.price_cents is not None:
                self.fields["price_brl"].initial = (
                    Decimal(self.instance.price_cents) / Decimal("100")
                )

    def save(self, commit=True):
        obj = super().save(commit=False)
        price_brl = self.cleaned_data["price_brl"]  # já é Decimal
        obj.price_cents = int(price_brl * 100)      # 12.34 -> 1234
        if commit:
            obj.save()
        return obj
