# Create your views here.
# coding=UTF-8
from cStringIO import StringIO
from datetime import datetime
#import logging
from itertools import chain
import random
import time
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from Test.forms import SearchTest

from Test.models import Chapter, Task, Option, TestSession, TestSequence
import settings
#l = logging.getLogger('django.db.backends')
#l.setLevel(logging.DEBUG)
#l.addHandler(logging.StreamHandler())
class Summary:
    def __init__(self, taskText, correctText, actualText, link = None):
        self.task = taskText
        self.correct = correctText
        self.actual = actualText
        self.link = link

def get_params(request, additional= None):
    params = {}
    if request.user.is_authenticated():
        params = {'teacher': (bool(request.user.groups.filter(name='teacher'))),
                  'chapter_list': Chapter.objects.filter(active=True)}
    if additional:
        params.update(additional)
    return params
def chapter_id_for_test_session(test_session):
    try:
        return test_session.answer_set.all()[0].selected.all()[0].task.chapter_id
    except Exception:
        return -1

#@login_required
def chapters(request, chapterId=None, final = None):
    if chapterId and not (final is None):
        try:
            del request.session['test']
        except KeyError:
            pass
        if final:
            request.session['final'] = final
            try:
                final_tests = TestSession.objects.filter(student = request.user, final = True)
                for final_test in final_tests:
                    if chapter_id_for_test_session(final_test) == int(chapterId):
                        return test_detail(request, final_test.id)
            except TestSession.DoesNotExist:
                pass
        testSession = TestSession()
        testSession.testDate = datetime.now()
        testSession.duration = 0
        testSession.student = request.user
        testSession.final = request.session.get('final', None)
        testSession.save()
        request.session['test'] = testSession
        #generate random list of tasks
        chapter = Chapter.objects.get(id = chapterId)
        easy = Task.objects.filter(chapter = chapterId, complexity = 1).order_by('?')[:chapter.easy]
        medium = Task.objects.filter(chapter = chapterId, complexity = 2).order_by('?')[:chapter.medium]
        hard = Task.objects.filter(chapter = chapterId, complexity = 3).order_by('?')[:chapter.hard]
        tasks = list(chain(easy, medium, hard))
        random.shuffle(tasks)
        k = 0
        for t in tasks:
            elem = TestSequence()
            elem.position = k
            elem.task = t
            elem.test_session = testSession
            elem.save()
            k += 1
        return task(request, 1)
    else:
        params = get_params(request)
        if chapterId:
            params['chapterId'] = chapterId
        return render_to_response("chapter.html", params, context_instance=RequestContext(request))
@login_required
def task(request, task_num):
    task_num  = int(task_num)
    isTeacher =  bool(request.user.groups.filter(name='teacher'))
    if isTeacher:
        return redirect("/chapter/")
    testSession = request.session.get('test')
    testSession.duration = (datetime.now() - testSession.testDate).seconds
    testSession.save()
    test_sequence = TestSequence.objects.filter(test_session = testSession).order_by('position')
    task_list = []
    type = 0
    for ts in test_sequence:
        task_list.append(ts.task)
    task = test_sequence[task_num - 1].task
    options = task.option_set.all()
    for opt in options:
        if opt.correct:
            type += 1
        if opt.value:
            type = -1

    return render_to_response("task.html", {'task': task, 'options_list' : options,
                                            'type': type,
                                            'list' : task_list,
                                            'next' : task_num + 1,
                                            'tictac' : testSession.duration,
                                            'limit' : task.chapter.timeLimit,
                                            'chapter_list' : Chapter.objects.filter(active = True)},
                              context_instance=RequestContext(request))
@login_required
def add_answer(request, task_num):
    task_num = int(task_num)
    try:
        if request.method == 'POST':
            try:
                testSession = request.session['test']
            except KeyError :
                testSession = None
            tsStep = TestSequence.objects.filter(test_session = testSession, position = task_num - 2)[0]#current task

            chosen = request.POST.getlist('option')
            answers = testSession.answer_set.all()
            answer  = None
            for ans in answers:
                if ans.selected.all()[0].task == tsStep.task:
                    answer = ans
            if answer is None:
                answer = testSession.answer_set.create()
            else:
                answer.selected.clear()
            for optId in chosen:
                try:
                    opt = Option.objects.get(id = int(optId))
                    if opt.task != tsStep.task or (opt.task == tsStep.task and opt.value != '' and opt.value is not None):#a chance that entered value is ID of another option
                        raise ValueError
                    if opt.value is not None:
                        answer.selected.add(opt)#value from form is not ID but entered data
                except (Option.DoesNotExist, ValueError):
                    answer.value = optId
            answer.position = task_num
            answer.save()
            if TestSequence.objects.filter(test_session = testSession).count() < task_num:
                task_num = 0
            return redirect('/chapter/{0:d}/task/{1:d}/'.format(tsStep.task.chapter_id, task_num), context_instance=RequestContext(request))
        else:
            return redirect("/chapter/")
    except Task.DoesNotExist:
        return redirect("/chapter/")

def get_test_session_data(testSession):
    answers = testSession.answer_set.all()
    aggregate = []
    testSession.correct = 0
    for a in answers:
        opts = a.selected.all()
        correctTexts = []
        actualTexts = []
        if len(opts) > 0:
            task = opts[0].task
            taskOpts = task.option_set.filter(correct=True)
            for opt in taskOpts:
                if opt.value is None or opt.value == '':
                    correctTexts.append(opt.text)
                else:
                    correctTexts.append(opt.value)
            if a.value is not None and opts[0].value != a.value:
                actualTexts.append(a.value)
            elif opts.count() == 1 and not opts[0].correct:
                actualTexts.append(opts[0].text)
            elif len(correctTexts) > 1 and set(opts).intersection(taskOpts) != set(taskOpts):
                for o in opts:
                    actualTexts.append(o.text)
            else:
                testSession.correct += 1
        aggregate.append(Summary(taskText=task.title,
                                 correctText=correctTexts, actualText=actualTexts, link = task.theoryLink))
    testSession.total = len(aggregate)
    testSession.save()
    return aggregate

@login_required
def end(request, chapter_id):
    chapter = Chapter.objects.get(id = chapter_id)
    try:
        testSession = request.session['test']
        testSession.duration = (datetime.now() - testSession.testDate).seconds
        aggregate = get_test_session_data(testSession)
        if settings.SEND_EMAIL:
            send_mail(u"Тестирование завершено", testSession.student.username + u' завершил тестирование по теме ' + chapter.shortName,
                      'frostbeast@mail.ru', [User.objects.get(username='teacher').email])
        del request.session['test']
        params = get_params(request, {'chapter' : chapter, 'session' : testSession,
                                      'time' :  time.strftime('%H:%M:%S', time.gmtime(testSession.duration)),
                                      'answers' : aggregate})
        return render_to_response("end.html", params, context_instance=RequestContext(request))
    except (KeyError, Chapter.DoesNotExist):
        return redirect("/chapter/")


@login_required
def test_detail(request, testId):
    try:
        testSession = TestSession.objects.get(id = testId)
        chapter = Chapter.objects.get(id = chapter_id_for_test_session(testSession))
        aggregate = get_test_session_data(testSession)
        params = get_params(request, {'chapter' : chapter, 'session' : testSession,
                        'time' :  time.strftime('%H:%M:%S', time.gmtime(testSession.duration)),
                        'answers' : aggregate})
        return render_to_response("end.html", params,  context_instance=RequestContext(request))
    except TestSession.DoesNotExist:
        return redirect("/chapter/")

@login_required
def students(request):
    try:
        studentGroup = Group.objects.get(name='student')
        students = studentGroup.user_set.all()
        stats = []
        start = None
        end = None
        page = None
        pagesize = 10
        if request.method == 'GET':
            form = SearchTest(request.GET)
            if form.is_valid():
                names = form.cleaned_data['name'].split()
                if len(names) > 0:
                    students = students.filter(Q(first_name__icontains = names[0]) | Q(last_name__icontains = names[0]))
                if len(names) > 1:
                    students = students.filter(Q(first_name__icontains = names[1]) | Q(last_name__icontains = names[1]))
                start = form.cleaned_data['start']
                end = form.cleaned_data['end']
                page = form.cleaned_data['page']
                try:
                    pagesize = int(form.cleaned_data['pagesize'])
                except ValueError:
                    if form.cleaned_data['pagesize'] ==u'':
                        pagesize = 10
                    else:
                        pagesize = 100000
                        page = 1
        else:
            form = SearchTest()
        ts = TestSession.objects.filter(student__in=students, answer__isnull=False).distinct()
        if start:
            ts = ts.filter(testDate__gte = start)
        if end:
            ts = ts.filter(testDate__lte = end)
        if ts.count() > 0:
            stats = list(ts.order_by('student','testDate'))
            paginator = Paginator(stats, pagesize)
            if page is None:
                page = ""
            try:
                stats = paginator.page(page)
            except PageNotAnInteger:
                    # If page is not an integer, deliver first page.
                stats  = paginator.page(1)
            except EmptyPage:
                 # If page is out of range (e.g. 9999), deliver last page of results.
                stats = paginator.page(paginator.num_pages)
        params = get_params(request, {'stats' : stats, 'form' : form})
        return render_to_response("students.html", params, context_instance=RequestContext(request))
    except ValueError:
        return redirect("/chapter/")

@login_required
def tests(request):
    try:
        stats = {}
        finalTests = TestSession.objects.filter(final = True).exclude(total = None)
        if request.method == 'GET':
            form = SearchTest(request.GET)
            if form.is_valid():
                names = form.cleaned_data['name'].split()
                if len(names) > 0:
                    finalTests = finalTests.filter(Q(student__first_name__icontains = names[0]) | Q(student__last_name__icontains = names[0]))
                if len(names) > 1:
                    finalTests = finalTests.filter(Q(student__first_name__icontains = names[1]) | Q(student__last_name__icontains = names[1]))
                start = form.cleaned_data['start']
                end = form.cleaned_data['end']
                if start:
                    finalTests = finalTests.filter(testDate__gte = start)
                if end:
                    finalTests = finalTests.filter(testDate__lte = end)
                if finalTests.count() > 0:
                    finalTests = finalTests.order_by('student', 'testDate')
        else:
            form = SearchTest()
        chapters  = Chapter.objects.filter(active = True)
        if finalTests.count() > 0:
            for chapter in chapters:
                try:
                    forChapter = stats[chapter]
                except KeyError:
                    forChapter = []
                    stats[chapter] = forChapter
                for ft in finalTests:
                    if chapter_id_for_test_session(ft) == chapter.id:
                        testAggregate = get_test_session_data(ft)
                        taskResults = []
                        for ta in testAggregate:
                            taskResults.append(len(ta.actual) == 0)
                        forChapter.append([ft, taskResults])
        params = get_params(request, {'stats' : stats, 'form' : form})
        return render_to_response("tests.html", params, context_instance=RequestContext(request))
    except ValueError:
        return redirect("/chapter/")

@login_required
def theory_reader(request):
    return render_to_response(request.get_full_path()[1:], get_params(request),
                              context_instance=RequestContext(request))#cut off leading slash

def tests_to_pdf(request, chapterId = None):
    registerFont(TTFont('Calibri', 'Calibri.ttf'))
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=tests.pdf'
    response['Content-Encoding'] = 'cp1251'

    buffer = StringIO()

    # Create the PDF object, using the StringIO object as its "file."
    p = canvas.Canvas(buffer)
    p.setFont('Calibri', 14)
    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    line = 25
    k = 0
    p.drawString(40, 820, u"Учащийся")
    finalTests = TestSession.objects.filter(final = True).order_by('student', 'testDate')
    for ft in finalTests:
        if chapter_id_for_test_session(ft) == chapterId:
            testAggregate = get_test_session_data(ft)
            p.drawString(40, 800 - line * k, ft.student.first_name + " " + ft.student.last_name)
            i = 0
            for ta in testAggregate:
                p.drawString(140 + i * 20, 800 - line * k, '+' if  not len(ta.actual) else '-')
                i += 1
            k += 1
            # Close the PDF object cleanly.
    p.showPage()
    p.save()

    # Get the value of the StringIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

def test_chart(request, chapterId = None, studentId = None):
    try:
        stats = []
        std = User.objects.get(id=int(studentId))
        tests = TestSession.objects.filter(final = False, student = std).order_by('testDate')
        for ft in tests:
            if chapter_id_for_test_session(ft) == int(chapterId):
                stats.append([ft.testDate, ft.correct])
        params = get_params(request,
                {'student' : (User.objects.get(id=studentId)), 'chapter' : Chapter.objects.get(id = chapterId),
                 'stats' : stats})
        return render_to_response("charts.html", params, context_instance=RequestContext(request))
    except (ValueError, User.DoesNotExist, Chapter.DoesNotExist):
        return redirect("/chapter/")

def bio(request):
    return render_to_response("bio.html", get_params(request), context_instance=RequestContext(request))
