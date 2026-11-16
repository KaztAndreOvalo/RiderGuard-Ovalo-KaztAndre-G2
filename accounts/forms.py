from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(label="Username or email", max_length=254)

    placeholders = {"username": "juandc or juan@example.com", "password": "Your password"}

    error_messages = {
        "invalid_login": "Invalid username/email or password. Please try again.",
        "inactive": "This account has been deactivated. Please contact an administrator.",
    }


class ProfileForm(StyledFormMixin, forms.ModelForm):
    """Lets a logged-in user update their own profile details."""

    MAX_PHOTO_MB = 2

    platforms = forms.MultipleChoiceField(
        choices=User.Platform.choices, widget=forms.CheckboxSelectMultiple, required=False,
        help_text="Platforms you currently ride for.",
    )
    remove_photo = forms.BooleanField(required=False, label="Remove current photo")

    placeholders = {"contact_number": "09171234567", "city": "Cebu City", "plate_number": "ABC 1234"}

    class Meta:
        model = User
        fields = (
            "profile_photo", "first_name", "last_name", "email", "contact_number",
            "city", "platforms", "vehicle_type", "plate_number",
        )
        widgets = {"profile_photo": forms.FileInput(attrs={"accept": "image/*"})}
        help_texts = {"profile_photo": "JPG or PNG, up to 2 MB."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True
        if not self.instance.is_rider:
            # Ride-related details only make sense for riders.
            for name in ("platforms", "vehicle_type", "plate_number"):
                self.fields.pop(name)
        if not self.instance.profile_photo:
            self.fields.pop("remove_photo")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")
        if photo and hasattr(photo, "size") and photo.size > self.MAX_PHOTO_MB * 1024 * 1024:
            raise forms.ValidationError(f"Photo must be {self.MAX_PHOTO_MB} MB or smaller.")
        return photo

    def clean_plate_number(self):
        return self.cleaned_data.get("plate_number", "").strip().upper()

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("remove_photo") and "profile_photo" not in self.changed_data:
            user.profile_photo.delete(save=False)
            user.profile_photo = ""
        if commit:
            user.save()
        return user
