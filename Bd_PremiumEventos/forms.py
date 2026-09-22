from django import forms
from .models import Testimonio

class TestimonioForm(forms.ModelForm):

    class Meta:
        model = Testimonio

        fields = [
            "calificacion",
            "comentario",
        ]

        widgets = {
            "calificacion": forms.Select(
                attrs= {"class":"form-select"}
            ),

            "comentario": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Tu opinion nos importa !ponla aqui!"
                }
            ),
        }