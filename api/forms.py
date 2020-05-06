from django import forms
from django.forms.utils import ErrorDict

from api.utils import is_data_valid, md5reader


class FileUploadForm(forms.Form):
    nome = forms.CharField(max_length=255)
    method = forms.CharField(max_length=255)
    filename = forms.CharField(max_length=255)
    md5 = forms.CharField(max_length=32)
    file = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.md5_ = md5reader(self.files["file"])

    # Os métodos _clean_fields e full_clean foram alterados para que a
    # validação pare no primeiro erro
    def _clean_fields(self):
        for name, field in self.fields.items():
            # value_from_datadict() gets the data from the data dictionaries.
            # Each widget type knows how to retrieve its own data, because some
            # widgets split data over several HTML fields.
            if field.disabled:
                value = self.get_initial_for_field(field, name)
            else:
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, forms.FileField):
                    initial = self.get_initial_for_field(field, name)
                    value = field.clean(value, initial)
                else:
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except forms.ValidationError as e:
                self.add_error(name, e)
                break

    def full_clean(self):
        """
        Clean all of self.data and populate self._errors and self.cleaned_data.
        """
        self._errors = ErrorDict()
        if not self.is_bound:  # Stop further processing.
            return
        self.cleaned_data = {}
        # If the form is permitted to be empty, and none of the form data has
        # changed from the initial data, short circuit any validation.
        if self.empty_permitted and not self.has_changed():
            return

        clean_methods = [
            self._clean_fields,
            self._clean_form,
            self._post_clean,
        ]
        for clean_method in clean_methods:
            clean_method()
            if self._errors:
                break

    @property
    def base_return(self):
        if self.is_bound:
            return {"md5": self.md5_, "error": self._errors}

    @property
    def status_code(self):
        error_types = [error for error in self._errors]
        status = 400
        if not self._errors:
            status = 201
        elif "md5" in error_types or "schema" in error_types:
            status = 400
        elif "filename" in error_types:
            status = 415

        return status

    def clean_md5(self):
        md5 = self.cleaned_data["md5"]
        file_ = self.files["file"]
        if md5 != self.md5_:
            raise forms.ValidationError("valor md5 não confere!")

        return md5

    def clean_filename(self):
        filename = self.cleaned_data["filename"]
        if not filename.endswith(".gz") and not self.files[
            "file"
        ].name.endswith(".gz"):
            raise forms.ValidationError("arquivo deve ser GZIP!")

        return filename

    def clean(self):
        cleaned_data = super().clean()
        valid_data, status = is_data_valid(
            cleaned_data["nome"],
            cleaned_data["method"],
            self.files["file"]
        )
        if not valid_data:
            self._errors["schema"] = self.error_class(
                ["arquivo apresentou estrutura de dados inválida"]
            )

        return cleaned_data
