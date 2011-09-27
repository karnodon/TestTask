# coding=cp1251
from django import forms

__author__ = 'Frostbite'
class SearchTest(forms.Form):
    name = forms.CharField(max_length = 100, required=False, label="",
                           widget=forms.widgets.TextInput(attrs={'placeholder': u'Учащийся'}))
    em = {"required": u"Введите дату", "invalid": u"Неправильный формат даты"}
    start = forms.DateField(widget=forms.widgets.DateInput(format="%d.%m.%Y", attrs={'placeholder': u'От'}),
                            required=False, label="", input_formats = ["%d.%m.%Y"], error_messages = em)

    end = forms.DateField(widget=forms.widgets.DateInput(format="%d.%m.%Y", attrs={'placeholder': u'До'}),
                          required=False, label="", input_formats= ["%d.%m.%Y"], error_messages= em)

    def clean(self):
        cleaned_data = self.cleaned_data
        s = cleaned_data.get("start")
        e = cleaned_data.get("end")

        if s and e and s > e:
            raise forms.ValidationError(u"Начальная дата не должна быть позже  конечной.")
        # Always return the full collection of cleaned data.
        return cleaned_data