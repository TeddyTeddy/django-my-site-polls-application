import datetime
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions
        whose pub_date is in future
        :return: None
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(question_text='Future Question', pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions
        whose pub_date is older than 1 day
        :return: None
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(question_text='Old Question', pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_wih_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day
        :return: None
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(question_text='Recent Question', pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Create a question with the given 'question_text' and published the
    given number of 'days' offset to now (negative for questions published
    in the past, positive for questions that have yet to be published
    :param question_text:
    :param days: days offset taking now as reference point
    :return: None
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed
        :return: None
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No polls are available.')
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question_with_a_choice(self):
        """
        Questions with a pub_date in the past and with at least one choice are displayed on the index page
        :return: None
        """
        past_question = create_question(question_text='Past Question', days=-30)
        choice = Choice(question=past_question, choice_text='A choice', votes=0)
        choice.save()
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past Question>']
        )

    def test_future_question_with_a_choice(self):
        """
        Questions with a choice but also with a pub_date in the future aren't displayed on
        the index page. This is because pub_date is in the future
        """
        future_question = create_question(question_text="Future question.", days=30)
        choice = Choice(question=future_question, choice_text='A choice', votes=0)
        choice.save()

        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question_both_with_a_choice(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed. Note that all questions have at least one choice
        """
        past_question = create_question(question_text="Past question.", days=-30)
        choice = Choice(question=past_question, choice_text='A choice', votes=0)
        choice.save()

        future_question = create_question(question_text="Future question.", days=30)
        choice = Choice(question=future_question, choice_text='A choice', votes=0)
        choice.save()

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_two_past_questions_both_with_a_choice(self):
        """
        The questions index page may display multiple questions if they are both in the past
        and they both have at least one choice.
        """
        past_question_1 = create_question(question_text="Past question 1.", days=-30)
        choice = Choice(question=past_question_1, choice_text='A choice', votes=0)
        choice.save()

        past_question_2 = create_question(question_text="Past question 2.", days=-5)
        choice = Choice(question=past_question_2, choice_text='A choice', votes=0)
        choice.save()

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )

    def test_two_past_questions_both_without_a_choice(self):
        """
        The questions index page displays an appropriate message, if
        there are more than two past questions either without any choice
        """
        past_question_1 = create_question(question_text="Past question 1.", days=-30)
        past_question_2 = create_question(question_text="Past question 2.", days=-5)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            []
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No polls are available.')


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_with_no_choices(self):
        """
        The detail view of a question with a pub_date in the past and without any choices
        returns a 404 not found
        """
        past_question = create_question(question_text='Past Question with no choices.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_with_choices(self):
        """
        The detail view of a question with a pub_date in the past and with choices returns
        the question.question_text in the response body
        """
        past_question_with_choices = create_question(question_text='Past Question with 2 choices.', days=-5)
        choice1 = Choice(question=past_question_with_choices, choice_text='Choice 1', votes=0)
        choice1.save()
        choice2 = Choice(question=past_question_with_choices, choice_text='Choice 2', votes=0)
        choice2.save()
        url = reverse('polls:detail', args=(past_question_with_choices.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Past Question with 2 choices.')


class QuestionResultsViewTests(TestCase):
    def test_future_question_with_a_choice(self):
        """
        The result view of a question with a pub_date in the future and with a choice
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        choice = Choice(question=future_question, choice_text='Choice', votes=0)
        choice.save()

        url = reverse('polls:results', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_with_a_choice(self):
        """
        The results view of a question with a pub_date in the past and with a choice
        displays the question's text and gets 200 status code
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        choice = Choice(question=past_question, choice_text='Choice', votes=0)
        choice.save()

        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, past_question.question_text)

    def test_future_and_past_question_both_with_a_choice(self):
        """
        The results view of two questions: Future question with a pub_date in the future
        and past question with a pub_date in the past. Both questions have a Choice.
        The view returns 200; in the response content there is past question's text
        """
        future_question = create_question(question_text='Future question.', days=5)
        choice = Choice(question=future_question, choice_text='Choice', votes=0)
        choice.save()

        past_question = create_question(question_text='Past Question.', days=-5)
        choice = Choice(question=past_question, choice_text='Choice', votes=0)
        choice.save()

        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, past_question.question_text)

    def test_past_question_without_a_choice(self):
        """
        The results view of a question with a pub_date in the past and WITHOUT a choice
        gets 404 status code.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


def create_question_with_choices(question_text, days):
    question = create_question(question_text=question_text, days=days)
    choice_1 = Choice(question=question, choice_text='Choice 1', votes=0)
    choice_1.save()
    choice_2 = Choice(question=question, choice_text='Choice 2', votes=0)
    choice_2.save()
    choice_3 = Choice(question=question, choice_text='Choice 3', votes=0)
    choice_3.save()
    return question, choice_2.id


class QuestionVoteViewTests(TestCase):
    def test_question_id_not_found(self):
        """
        To test, when an invalid question id is passed as question_id to the view, the view returns 404
        """
        # empty database
        invalid_question_id = 10000
        url = reverse('polls:vote', args=(invalid_question_id,))
        response = self.client.post(url, {'choice': 10})
        self.assertEqual(response.status_code, 404)

    def test_future_question_with_choices(self):
        """
        When a future question's id is passed to the view, the view returns 404.
        Note that future question has choices
        """
        future_question_with_choices, choice_id = create_question_with_choices(question_text='Future question', days=30)
        url = reverse('polls:vote', args=(future_question_with_choices.id,))
        response = self.client.post(url, {'choice': choice_id})
        self.assertEqual(response.status_code, 404)

    def test_voting_with_no_choice_provided(self):
        """
        A past question has choices. When a POST request is made to the view with the URL (i.e. /polls/5/vote/)
        we do NOT provide a choice_id in the request body (i.e. there is no choice=10 in the request body).
        We expect that view returns 400 status code.
        """
        past_question_with_choices, choice_id = create_question_with_choices(question_text='Past question', days=-30)
        url = reverse('polls:vote', args=(past_question_with_choices.id,))
        response = self.client.post(url)  # note that we do not provide {'choice':choice_id} in the POST request
        self.assertEqual(response.status_code, 400)

    def test_voting_with_non_existing_choice_id(self):
        """
        A past question has Choices. When a POST request is made to the view with a valid URL (i.e. /polls/5/vote/)
        and we do provide an non-existing choice_id in the request body (i.e. choice=10000 in the request body).
        We expect that view returns 200 status code. Note that in the response body should exist the request URL
        and there has to be 'Vote' button in the response body
        """
        past_question_with_choices, choice_id = create_question_with_choices(question_text='Past question', days=-30)
        url = reverse('polls:vote', args=(past_question_with_choices.id,))
        response = self.client.post(url, {'choice': 10000})  # note that there is no Choice with an id 10000
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, url)
        self.assertContains(response, 'Vote')

    def test_past_question_with_choices(self):
        """
        A past question has choices. We select a choice with choice_id to be voted for.
        When a POST request is made to the view with URL (i.e. /polls/5/vote), we also pass the choice_id
        in the request body (i.e. choice=10). We expect the view to answer us with 302 (Redirect) with a
        URL (i.e. /polls/5/results). We make a new GET request with the provided url and check that
        the status code is 200 and the response contains question_text in its body
        """
        past_question_with_choices, choice_id = create_question_with_choices(question_text='Past question', days=-30)
        url = reverse('polls:vote', args=(past_question_with_choices.id,))
        response = self.client.post(url, {'choice': choice_id})
        self.assertEqual(response.status_code, 302)

        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, past_question_with_choices.question_text)


