from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Student (models.Model):
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    className = models.CharField(max_length=10)
    def __unicode__(self):
        return self.lastName + " " + self.firstName
    class Meta:
        ordering = ['className', 'lastName', 'firstName']

class Chapter (models.Model):
    shortName = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    active = models.BooleanField(default=False)
    timeLimit = models.IntegerField(default=0)
    def __unicode__(self):
        return self.shortName

class Task (models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=400)
    position = models.IntegerField()
    chapter = models.ForeignKey(Chapter)
    def __unicode__(self):
        return  self.title
    class Meta:
        ordering = ['position']

class Option (models.Model):
    text = models.CharField(max_length=30)
    value = models.CharField(max_length=30, blank=True)
    position = models.IntegerField()
    correct = models.BooleanField()
    task = models.ForeignKey(Task)
    def __unicode__(self):
        return self.text

class TestSession (models.Model):
    testDate = models.DateField()
    duration = models.IntegerField(blank=True)
    student = models.ForeignKey(User)
    correct = models.IntegerField(blank=True)
    total = models.IntegerField(blank=True)
    final = models.BooleanField()

class Answer (models.Model):
    testSession = models.ForeignKey(TestSession)
    selected = models.ManyToManyField(Option)
    value = models.CharField(max_length=30, blank=True)
    position = models.IntegerField()