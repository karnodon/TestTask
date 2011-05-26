# Create your views here.
# coding=cp1251
from cStringIO import StringIO
from datetime import datetime
import time
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String, Image
from reportlab.pdfgen import canvas

from Test.models import Chapter, Task, Option, TestSession
import settings

class Summary:
    def __init__(self, taskText, correctText, actualText):
        self.task = taskText
        self.correct = correctText
        self.actual = actualText
@login_required
def chapters(request, chapterId=None, final = False):
    if chapterId:
        try:
            del request.session['test']
        except KeyError:
            pass
        if final:
            request.session['final'] = final
            try:
                final_tests = TestSession.objects.filter(student = request.user, final = True)
                for final_test in final_tests:
                    if final_test.answer_set.all()[0].selected.all()[0].task.chapter_id == int(chapterId):
                        return test_detail(request, final_test.id)
            except TestSession.DoesNotExist:
                pass
        firstTask = Task.objects.filter(chapter = chapterId)[0]
        return task(request, firstTask.id)
    else:
        chapterList = Chapter.objects.filter(active = True)
        isTeacher =  bool(request.user.groups.filter(name='teacher'))
        return render_to_response("chapter.html", {'chapter_list' : chapterList, 'teacher' : isTeacher},
                                  context_instance=RequestContext(request))
@login_required
def task(request, taskId):
    task = Task.objects.get(id = taskId)
    type = 0
    options = task.option_set.all()
    for opt in options:
        if opt.correct:
            type += 1
        if opt.value:
            type = -1
    taskList = Task.objects.filter(chapter = task.chapter.id)
    return render_to_response("task.html", {'task': task, 'options_list' : options,
                                            'type': type,
                                            'list' : taskList},context_instance=RequestContext(request))
@login_required
def add_answer(request, taskId):
    task = Task.objects.get(id = taskId)#current task
    if request.method == 'POST':
        try:
            testSession = request.session['test']
        except KeyError :
            testSession = None
        if task.position == 1 and testSession is None:
            try:
                final = request.session['final']
            except KeyError:
                final = False
            testSession = TestSession()
            testSession.testDate = datetime.now()
            testSession.duration = 0
            testSession.student = request.user
            testSession.final = final
            testSession.save()
            request.session['test'] = testSession
        chosen = request.POST.getlist('option')
        answers = testSession.answer_set.all()
        answer  = None
        for ans in answers:
            if ans.selected.all()[0].task == task:
                answer = ans
        if answer is None:
            answer = testSession.answer_set.create()
        else:
            answer.selected.clear()
        for optId in chosen:
            try:
                opt = Option.objects.get(id = int(optId))
                if opt.task != task or (opt.task == task and opt.value != '' and opt.value is not None):#a chance that entered value is ID of another option
                    raise ValueError
            except (Option.DoesNotExist, ValueError):
                answer.value = optId
                opt = task.option_set.all()[0]#value from form is not ID but entered data
            if opt.value is not None:
                answer.selected.add(opt)
        answer.position = task.position
        answer.save()
    nextTask = Task.objects.filter(chapter = task.chapter, position = task.position + 1)
    nextTaskId = 0
    if nextTask.count() > 0:
        nextTaskId = nextTask[0].id
    return redirect('/chapter/%d/task/%d/'%(task.chapter_id,nextTaskId), context_instance=RequestContext(request))


def get_test_session(testSession):
    answers = testSession.answer_set.order_by('position')
    aggregate = []
    incorrect = 0
    for a in answers:
        opts = a.selected.all()
        task = opts[0].task
        correctTexts = []
        actualTexts = []
        taskOpts = task.option_set.filter(correct=True)
        for opt in taskOpts:
            if opt.correct:
                if opt.value is None or opt.value == '':
                    correctTexts.append(opt.text)
                else:
                    correctTexts.append(opt.value)
        if a.value is not None and opts[0].value != a.value:
            actualTexts.append(a.value)
            incorrect += 1
        if opts.count() == 1 and not opts[0].correct:
            actualTexts.append(opts[0].text)
            incorrect += 1
        elif len(correctTexts) > 1 and set(opts).intersection(taskOpts) != set(taskOpts):
            incorrect += 1
            actualTexts = []
            for o in opts:
                actualTexts.append(o.text)
        aggregate.append(Summary(taskText=task.title,
                                 correctText=correctTexts, actualText=actualTexts))
        testSession.correct = len(aggregate) - incorrect
        testSession.total = len(aggregate)
        testSession.save()
    return aggregate


@login_required
def end(request, chapterId):
    chapter = Chapter.objects.get(id = chapterId)
    try:
        testSession = request.session['test']
        testSession.duration = (datetime.now() - testSession.testDate).seconds
        testSession.save()
        aggregate = get_test_session(testSession)
        if settings.SEND_EMAIL:
            send_mail(u"������������ ���������", testSession.student.username + u' �������� ������������ �� ���� ' + chapter.shortName,
                      'frostbeast@mail.ru', [User.objects.get(username='teacher').email], fail_silently=False)
        del request.session['test']
        return render_to_response("end.html", {'chapter' : chapter, 'session' : testSession, 'teacherMode': False,
                                           'time' :  time.strftime('%H:%M:%S', time.gmtime(testSession.duration)),
                                           'answers' : aggregate}, context_instance=RequestContext(request))
    except KeyError :
        return redirect("/chapter/")


@login_required
def test_detail(request, testId):
    testSession = TestSession.objects.get(id = testId)
    chapter = Chapter.objects.get(id = testSession.answer_set.all()[0].selected.all()[0].task.chapter_id)
    aggregate = get_test_session(testSession)
    return render_to_response("end.html", {'chapter' : chapter, 'session' : testSession, 'teacherMode': True,
                                           'time' :  time.strftime('%H:%M:%S', time.gmtime(testSession.duration)),
                                           'answers' : aggregate}, context_instance=RequestContext(request))

@login_required
def students(request):
    try:
        studentGroup = Group.objects.get(name='student')
        students = studentGroup.user_set.all()
        stats = {}
        for st in students:
            tests = TestSession.objects.filter(student = st.id).order_by('testDate')
            stats[st] = tests
        return render_to_response("students.html", {'stats' : stats}, context_instance=RequestContext(request))
    except ValueError:
        return redirect("/chapter/")

@login_required
def tests(request):
    try:
        stats = {}
        finalTests = TestSession.objects.filter(final = True)
        chapters  = Chapter.objects.filter(active = True)
        for chapter in chapters:
            try:
                forChapter = stats[chapter]
            except KeyError:
                forChapter = []
                stats[chapter] = forChapter
            for ft in finalTests:
                if ft.answer_set.all()[0].selected.all()[0].task.chapter_id == chapter.id:
                    testAggregate = get_test_session(ft)
                    taskResults = []
                    for ta in testAggregate:
                        taskResults.append(len(ta.actual) == 0)
                    forChapter.append([ft, taskResults])
        return render_to_response("tests.html", {'stats' : stats}, context_instance=RequestContext(request))
    except ValueError:
        return redirect("/chapter/")

def tests_to_pdf(request, chapterId = None):
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
    p.drawString(40, 820, u"��������")
    finalTests = TestSession.objects.filter(final = True)
    for ft in finalTests:
        if ft.answer_set.all()[0].selected.all()[0].task.chapter_id == chapterId:
            testAggregate = get_test_session(ft)
            p.drawString(40, 800 - line * k, ft.student.username)
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
        std = User.objects.get(id=studentId)
        return render_to_response("charts.html", {
            'student' : std,
            'chapter' : Chapter.objects.get(id = chapterId)},
                                  context_instance=RequestContext(request))
    except ValueError:
        return redirect("/chapter/")

def draw_chart(request, chapterId = None, studentId = None):
    class TestBarChart(Drawing):
        def __init__(self, width=500, height=300, *args, **kw):
            Drawing.__init__(self,width,height,*args,**kw)
            self.add(VerticalBarChart(), name='chart')

            self.add(String(200,180, ''), name='title')
            self.chart.valueAxis.valueMin = 0
            #set any shapes, fonts, colors you want here.  We'll just
            #set a title font and place the chart within the drawing
            self.chart.x = 20
            self.chart.y = 20
            self.chart.width = self.width - 20
            self.chart.height = self.height - 40

            self.title.fontName = 'Calibri'
            self.title.fontSize = 12

            #self.chart.data = [[100,150,200,235]]

    #extract the request params of interest.
    #I suggest having a default for everything.
    try:
        stats = []
        std = User.objects.get(id=int(studentId))
        d = TestBarChart()
        d.chart.categoryAxis.categoryNames = []
        tests = TestSession.objects.filter(final = False, student = std).order_by('testDate')
        for ft in tests:
            if ft.answer_set.all()[0].selected.all()[0].task.chapter_id == int(chapterId):
                stats.append(ft.correct)
                d.chart.categoryAxis.categoryNames.append(str(ft.testDate))
        #d.title.text = unicode(Chapter.objects.get(id = chapterId))
        d.chart.data = [stats]
    #get a GIF (or PNG, JPG, or whatever)
        binaryStuff = d.asString('png')
        return HttpResponse(binaryStuff, 'image/png')
    except ValueError:
        return redirect("/chapter/")