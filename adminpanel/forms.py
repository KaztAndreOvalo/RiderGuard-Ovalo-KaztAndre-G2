from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User


class AdminUserCreateForm(UserCreationForm):
    """Admins can create accounts of any role."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "role", "contact_number")

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


class AdminUserEditForm(forms.ModelForm):
    platforms = forms.MultipleChoiceField(
        choices=User.Platform.choices, widget=forms.CheckboxSelectMultiple, required=False
    )

    class Meta:
        model = User
        fields = (
            "first_name", "last_name", "username", "email", "role", "is_active",
            "contact_number", "city", "platforms", "vehicle_type", "plate_number",
        )
        labels = {"is_active": "Account is active"}

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        if self.editor is not None and self.instance.pk == self.editor.pk:
            if cleaned.get("role") != User.Role.ADMIN:
                self.add_error("role", "You cannot remove your own admin role.")
            if not cleaned.get("is_active"):
                self.add_error("is_active", "You cannot deactivate your own account.")
        if self.instance.is_superuser and cleaned.get("role") != User.Role.ADMIN:
            self.add_error("role", "Superuser accounts must keep the Admin role.")
        return cleaned
