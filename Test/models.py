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
    easy = models.IntegerField(blank=True)
    medium = models.IntegerField(blank=True)
    hard = models.IntegerField(blank=True)
    grade = models.IntegerField(blank=True)
    def __unicode__(self):
        return self.shortName
    class Meta:
        ordering = ['shortName']

class Task (models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=600)
    position = models.IntegerField()
    chapter = models.ForeignKey(Chapter)
    complexity = models.IntegerField()
    theoryLink = models.CharField(blank=True, max_length=400)
    def __unicode__(self):
        return  self.title
    class Meta:
        ordering = ['chapter', 'position']

class Option (models.Model):
    text = models.CharField(max_length=80)
    value = models.CharField(max_length=30, blank=True)
    position = models.IntegerField()
    correct = models.BooleanField()
    task = models.ForeignKey(Task)
    def __unicode__(self):
        return self.text
    class Meta:
        ordering = ['task', 'position']

class TestSession (models.Model):
    testDate = models.DateField()
    duration = models.IntegerField(blank=True)
    student = models.ForeignKey(User)
    correct = models.IntegerField(blank=True)
    total = models.IntegerField(blank=True)
    final = models.BooleanField()

class TestSequence (models.Model):
    task = models.ForeignKey(Task)
    position = models.IntegerField()
    test_session = models.ForeignKey(TestSession)

class Answer (models.Model):
    testSession = models.ForeignKey(TestSession)
    selected = models.ManyToManyField(Option)
    value = models.CharField(max_length=30, blank=True)
    position = models.IntegerField()
    class Meta:
        ordering = ['position']

class Feedback (models.Model):
    email = models.EmailField(blank=False)
    message = models.CharField(blank=False, max_length=500)
    post_date = models.DateTimeField(blank=False)
    def __unicode__(self):
        return self.post_date.strftime('%d %b %Y') + ' ' + self.email + ' ' + self.message
    class Meta:
        ordering = ['post_date']