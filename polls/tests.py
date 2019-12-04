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
