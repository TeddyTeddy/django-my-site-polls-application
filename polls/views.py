from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.http import Http404, HttpResponseBadRequest

from .models import Choice, Question


# def index(request):
#     latest_question_list = Question.objects.order_by('-pub_date')[:5]
#     context = {
#         'latest_question_list': latest_question_list
#     }
#     return render(request, 'polls/index.html', context)

class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """ Return the last five published questions (not including those set to be
        published in the future"""
        query_set = Question.objects.filter(pub_date__lte=timezone.now())
        for q in query_set:
            if not q.choice_set.all():  # if the question does not have any choices
                query_set = query_set.exclude(pk=q.id)
        return query_set.order_by('-pub_date')[:5]

# def detail(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)
#     return render(request, 'polls/detail.html', {'question': question})


class DetailView(generic.DetailView):
    model = Question
    context_object_name = 'question'
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that are not published yet
        """
        query_set = Question.objects.filter(pub_date__lte=timezone.now())
        for q in query_set:
            if not q.choice_set.all():  # if there are no choices in the question
                query_set = query_set.exclude(pk=q.id)
        return query_set

# def results(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)
#     return render(request, 'polls/results.html', {'question': question})


class ResultsView(generic.DetailView):
    model = Question
    context_object_name = 'question'
    template_name = 'polls/results.html'

    def get_queryset(self):
        """
        Excludes any questions that are not published yet
        """
        query_set = Question.objects.filter(pub_date__lte=timezone.now())
        for q in query_set:
            if not q.choice_set.all():  # if there are no choices in the question
                query_set = query_set.exclude(pk=q.id)
        return query_set


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if timezone.now() < question.pub_date:  # the question is published in the future, you can't vote on it
        raise Http404('Poll will be published in the future; it cant be voted now')

    # at this point, we got a past question
    if 'choice' in request.POST and request.POST['choice'].isdigit():
        try:
            choice_id = int(request.POST['choice'])
            selected_choice = question.choice_set.get(pk=choice_id)
        except (KeyError, Choice.DoesNotExist):
            # Redisplay the question voting form
            return render(request, 'polls/detail.html', {
                'question': question,
                'error_message': "You didn't select a choice with a valid id",
            })  # returns 200
        else:
            selected_choice.votes += 1
            selected_choice.save()  # TODO: if many users attempt this at the same time, there is a race condition
            # Always return an HttpResponseRedirect after successfully dealing
            # with POST data. This prevents data from being posted twice if a
            # user hits the Back button
            # This returns 302 - Found redirect message back to client
            return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
    else:  # post request body does not have a choice id or the provided 'choice' value contains non-digit chars
        return HttpResponseBadRequest()  # return 400 status code


