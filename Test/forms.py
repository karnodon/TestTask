# coding=UTF-8
from django import forms
from captcha.fields import CaptchaField

__author__ = 'Frostbite'
class SearchTest(forms.Form):
    name = forms.CharField(max_length = 100, required=False, label="",
                           widget=forms.widgets.TextInput(attrs={'placeholder': u'Учащийся'}))
    em = {"required": u"Введите дату", "invalid": u"Неправильный формат даты"}
    start = forms.DateField(widget=forms.widgets.DateInput(format="%d.%m.%Y", attrs={'placeholder': u'От (дд.мм.гггг)'}),
                            required=False, label="", input_formats = ["%d.%m.%Y"], error_messages = em)

    end = forms.DateField(widget=forms.widgets.DateInput(format="%d.%m.%Y", attrs={'placeholder': u'До (дд.мм.гггг)'}),
                          required=False, label="", input_formats= ["%d.%m.%Y"], error_messages= em)
    page = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput())

    pagesize = forms.ChoiceField(widget=forms.Select(attrs = {'class' : "input-mini"}),
        choices=(('10', '10'),('25', '25'),('50', '50'), (u'Все', u'Все')),
        initial="10", required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        s = cleaned_data.get("start")
        e = cleaned_data.get("end")

        if s and e and s > e:
            raise forms.ValidationError(u"Начальная дата не должна быть позже  конечной.")
        # Always return the full collection of cleaned data.
        return cleaned_data

class FeedbackForm(forms.Form):
    email = forms.EmailField(required=True, label=u'Электропочта',
                             error_messages={"required": u"Введите адрес", "invalid": u"Неправильный формат адреса"},
                             max_length=150,widget=forms.TextInput(attrs={'class' : 'field span6'}))
    message = forms.CharField(required=True, label=u'Сообщение',
                              error_messages={"required": u"Введите сообщение"},
                              widget=forms.Textarea(attrs={'rows': 10, 'cols': 85, 'class' : 'field span6'}))
    captcha = CaptchaField(required=True, label=u'Решите пример',
                           error_messages={"required": u"Решите пример правильно", "invalid": u"Неправильный ответ"})