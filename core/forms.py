from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your name"}),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "you@example.com"}),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone (optional)"}),
            "subject": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Subject"}),
            "message": forms.Textarea(
                attrs={"class": "form-control", "rows": 5,
                       "placeholder": "How can we help you?"}),
        }
