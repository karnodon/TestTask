__author__ = 'Frostbite'
from django.contrib import admin
from Test.models import Option,TestSession, Answer,Chapter, Student, Task

admin.site.register(Option)
admin.site.register(TestSession)
admin.site.register(Answer)
admin.site.register(Chapter)
admin.site.register(Student)
admin.site.register(Task)