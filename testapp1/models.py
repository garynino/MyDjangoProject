"""
Creating a database that will store all the information for the test automation
Creating: User, Course, Question, TEST, TEMPLATE, TEST QUESTION LINKING TO TESTFEEDBACK TABLES
"""

from django.db import models
from django.contrib.auth.models import User  # provides user_id, username, email, etc.
from django.core.exceptions import ValidationError
from django.utils import timezone

"""
USER / ROLES TABLE 
"""


class UserProfile(models.Model):
    role_choices = [
        ('webmaster', 'Webmaster'),
        ('publisher', 'Publisher'),
        ('teacher', 'Teacher'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Delete whole profile if user is deleted
    role = models.CharField(max_length=20, choices=role_choices)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


"""
COURSE TABLE
"""


class Course(models.Model):
    course_code = models.CharField(
        max_length=50,
        unique=True,
        help_text='e.g: CS499',
        default='CS499'
    )
    course_name = models.CharField(
        max_length=250,
        help_text='e.g: SR PROJ:TEAM SOFTWARE DESIGN',
        default='Untitled Course'
    )
    # Textbook information
    textbook_title = models.CharField(max_length=300, blank=True, null=True)
    textbook_author = models.CharField(max_length=300, blank=True, null=True)
    textbook_isbn = models.CharField(max_length=300, blank=True, null=True)
    textbook_link = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

    def get_publisher_questions(self):
        """
        Returns all questions created by publishers from courses with the same textbook ISBN.
        """
        return Question.objects.filter(
            course__textbook_isbn=self.textbook_isbn,
            owner__userprofile__role='publisher'
        )


"""
QUESTION TABLE
"""


class Question(models.Model):
    question_type_options = [
        ('TF', 'True/False'),
        ('MC', 'Multiple Choice'),
        ('MA', 'Matching'),
        ('FB', 'Fill in the Blank'),
        ('SA', 'Short Answer'),
        ('ES', 'Essay'),
        ('MS', 'Multiple Selection'),
        ('DY', 'Dynamic')  # For questions that use formulas or dynamic data
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question_type = models.CharField(max_length=50, choices=question_type_options)
    question_text = models.TextField(help_text='Question Prompt.', default='Question text.')
    inbedded_graphic = models.ImageField(max_length=200, null=True, blank=True)

    # Removed these fields to avoid storing all answer info as text:
    # choices_for_question = models.TextField(null=True, blank=True, help_text='Answer options for the question.')
    # correct_answer = models.TextField(null=True, blank=True, help_text='Correct Answer.')

    correct_answer_graphic = models.ImageField(upload_to='answer_graphics/', null=True, blank=True)
    default_points = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    estimated_time = models.IntegerField(default=1, help_text='Estimated time to answer question.')
    references = models.CharField(max_length=200, null=True, blank=True)
    required_reference_material = models.TextField(null=True, blank=True)
    instructions_for_grading = models.TextField(null=True, blank=True)
    instructor_comment = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    chapter_num = models.PositiveIntegerField(null=True, blank=True,
                                              help_text="Required for publisher-created questions.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Enforce that if the owner is a publisher, then a chapter number is provided.
        """
        super().clean()
        if self.owner and hasattr(self.owner, 'userprofile'):
            if self.owner.userprofile.role == 'publisher' and self.chapter_num is None:
                raise ValidationError("Questions created by publishers must include a chapter number.")

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.question_text[:50]}"


"""
ANSWER OPTION TABLE
Used for questions with multiple responses or multiple correct answers.
"""


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_options")
    text = models.TextField(help_text="Answer option text")
    is_correct = models.BooleanField(default=False, help_text="Designates if this option is a correct answer.")

    def __str__(self):
        return self.text


"""
DYNAMIC QUESTION PARAMETER TABLE
Used for questions that generate their answers dynamically using a formula and range.
"""


class DynamicQuestionParameter(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name="dynamic_parameters")
    formula = models.TextField(help_text="Formula for generating or validating the answer.")
    range_min = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum acceptable value.")
    range_max = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum acceptable value.")
    additional_params = models.JSONField(null=True, blank=True,
                                         help_text="Any additional parameters for dynamic generation.")

    def __str__(self):
        return f"Dynamic Params for QID {self.question.id}"


"""
TEST BANK TABLE
"""


class Template(models.Model):
    name = models.CharField(max_length=200, unique=True)
    font_name = models.CharField(max_length=100, default="Arial")
    font_size = models.IntegerField(default=12)
    header_text = models.TextField(null=True, blank=True)
    footer_text = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


"""
ATTACHMENT TABLE
"""


class Attachment(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to="attachments/")

    def __str__(self):
        return self.name


"""
TEST TABLE
"""


class Test(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='test')
    title = models.CharField(max_length=200, help_text="e.g: Quiz 1, Test 1", default="Untitled Test.")
    date = models.DateField(null=True, blank=True)
    filename = models.CharField(max_length=200, null=True, blank=True, help_text="Generated filename for this test.")
    is_final = models.BooleanField(default=False, help_text="Mark as True when test is published/finalized.")
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True)
    attachments = models.ManyToManyField(Attachment, blank=True)
    cover_instructions = models.TextField(null=True, blank=True, help_text="Test instructions on cover page.")
    test_number = models.CharField(max_length=50, null=True, blank=True, help_text="Identifier, e.g. 'Test #1'")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.course_code}"


"""
TESTQUESTION TABLE
Links a question to a test.
"""


class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="test_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="test_appearances")
    assigned_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    order = models.IntegerField(default=1, help_text="Order of question in the test.")
    randomize = models.BooleanField(default=False)
    special_instructions = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('test', 'question')
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order} in {self.test.title}"


"""
FEEDBACK TABLE
Stores feedback for questions and tests.
"""


class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name="feedbacks")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True, blank=True, related_name="feedbacks")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.question:
            return f"Feedback on Question {self.question.id}"
        elif self.test:
            return f"Feedback on Test {self.test.title}"
        return "General Feedback"