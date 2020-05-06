from django import forms

from api.utils import is_data_valid, md5reader


class FileUploadForm(forms.Form):
    username = forms.CharField(max_length=255)
    method = forms.CharField(max_length=255)
    filename = forms.CharField(max_length=255)
    sent_md5 = forms.CharField(max_length=32)
    file = forms.FileField()

    @property
    def base_return(self):
        if self.is_bound:
            return {"md5": self.md5_, "error": self._errors}

    @property
    def status_code(self):
        error_types = [list(error.keys())[0] for error in self._errors]
        status = 200
        if "sent_md5" in error_types or "schema" in error_types:
            status = 400
        elif "filename" in error_types:
            status = 415

        return status

    def clean_sent_md5(self):
        sent_md5 = self.cleaned_data["sent_md5"]
        file_ = self.files["file"]
        self.md5_ = md5reader(file_)
        if sent_md5 != self.md5_:
            raise forms.ValidationError("valor md5 não confere!")

        return sent_md5

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
            cleaned_data["username"],
            cleaned_data["method"],
            self.files["file"]
        )
        if not valid_data:
            self._errors["schema"] = self.error_class(
                ["arquivo apresentou estrutura de dados inválida"]
            )

        return cleaned_data
