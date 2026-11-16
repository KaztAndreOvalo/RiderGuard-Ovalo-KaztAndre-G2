from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class StyledFormMixin:
    """Adds placeholder text so plain Django widgets look consistent."""

    placeholders = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.placeholders:
                field.widget.attrs.setdefault("placeholder", self.placeholders[name])


class RegistrationForm(StyledFormMixin, UserCreationForm):
    """Self-registration for riders. Every new public account gets the Rider role."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    contact_number = forms.CharField(
        max_length=13, required=False, help_text="Optional. Example: 09171234567"
    )
    platforms = forms.MultipleChoiceField(
        choices=User.Platform.choices,
        widget=forms.CheckboxSelectMultiple,
        help_text="Which platforms do you currently ride for?",
    )

    placeholders = {
        "first_name": "Juan",
        "last_name": "Dela Cruz",
        "username": "juandc",
        "email": "juan@example.com",
        "contact_number": "09171234567",
    }

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "contact_number", "platforms")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.RIDER
        user.platforms = self.cleaned_data["platforms"]
        if commit:
            user.save()
        return user
