from django.db import models
from django.contrib.auth.models import User  # Standard Django user model.
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models import Q, Avg

"""
TEXTBOOK MODEL
Holds textbook/book details. This model serves as a key connection point for publisher content
and is referenced by teacher courses.
"""


class Textbook(models.Model):
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=300, blank=True, null=True)
    version = models.CharField(max_length=300, blank=True, null=True)
    isbn = models.CharField(max_length=300, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_feedback(self):
        """
        Retrieve all feedback related to this textbook.
        Feedback sources include:
          - Questions directly linked to this textbook.
          - Tests belonging to courses using this textbook.
          - Tests directly created for this textbook.
        """
        from .models import Feedback  # Local import to avoid circular dependency.
        return Feedback.objects.filter(
            Q(question__textbook=self) | Q(test__course__textbook=self) | Q(test__textbook=self)
        ).distinct()


"""
USER PROFILE MODEL
Extends the built-in User with a role.
Note: Originally, publishers were expected to have an associated book,
but no such field is defined here. Association is managed via the Textbook model.
"""


class UserProfile(models.Model):
    role_choices = [
        ('webmaster', 'Webmaster'),
        ('publisher', 'Publisher'),
        ('teacher', 'Teacher'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=role_choices)

    def clean(self):
        # Removed check for an associated book since no 'book' field exists in UserProfile.
        super().clean()

    def __str__(self):
        return f"{self.user.username} ({self.role})"


"""
COURSE MODEL
Represents a teacher-created course.
Each course is linked to a textbook and may have multiple teacher users.
"""


class Course(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    course_id = models.CharField(
        max_length=50,
        help_text='e.g: CS499',
        default='CS499'
    )
    name = models.CharField(
        max_length=250,
        help_text='e.g: SR PROJ:TEAM SOFTWARE DESIGN',
        default='Untitled Course'
    )
    crn = models.CharField(
        max_length=50,
        help_text='e.g: 54352',
        default='0000'
    )
    sem = models.CharField(
        max_length=50,
        help_text='e.g: Fall 2021',
        default='Fall 2021'
    )
    # Link to the associated textbook.
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Textbook associated with this course.'
    )
    teachers = models.ManyToManyField(
        User,
        related_name='courses',
        blank=True,
        limit_choices_to={'userprofile__role': 'teacher'}
    )
    published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course_id} - {self.name}"

    def get_publisher_questions(self):
        """
        Returns publisher-created questions for this course by matching the course's textbook.
        """
        if self.textbook:
            return Question.objects.filter(
                textbook=self.textbook,
                author__userprofile__role='publisher'
            )
        return Question.objects.none()


    def get_publisher_questions(self):
        """
        Returns all questions created by publishers from courses with the same textbook ISBN.
        """
        return Question.objects.filter(
            course__textbook_isbn=self.textbook_isbn,
            owner__userprofile__role='publisher'
        )


"""
QUESTION MODEL
Stores various types of questions with support for multiple formats:
- True/False, Multiple Choice, Fill in the Blank (supports multiple correct answers via Answers),
- Matching (stored as left/right pairs with optional distractors),
- Essay, Short Answer (typically no designated correct answer),
- Multiple Selection (more than one option may be correct), and Dynamic.
For publisher-created questions, link via the 'textbook' field.
For teacher-created questions, link via the 'course' field.
"""


class Question(models.Model):
    question_type_options = [
        ('tf', 'True/False'),
        ('mc', 'Multiple Choice'),
        ('sa', 'Short Answer'),  # Typically no correct answer provided.
        ('es', 'Essay'),  # Typically no correct answer provided.
        ('ma', 'Matching'),  # Saved as pairs; may include extra distractors.
        ('ms', 'Multiple Selection'),  # More than one option may be correct.
        ('fb', 'Fill in the Blank'),  # Supports multiple correct answers via Answers entries.
        ('dy', 'Dynamic')  # For questions with dynamic data.
    ]
    # For teacher-created questions.
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    # For publisher-created questions.
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="For publisher-created questions, associate with a textbook."
    )
    qtype = models.CharField(max_length=50, choices=question_type_options)
    text = models.TextField(help_text='Question prompt.', default='Question text.', null=True)

    # Common fields for visual elements and grading.
    img = models.ImageField(upload_to='graphics/', max_length=200, null=True, blank=True)  # Embedded graphic.
    ansimg = models.ImageField(upload_to='answer_graphics/', null=True, blank=True)  # Answer graphic.
    score = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    eta = models.IntegerField(default=1, help_text='Estimated time (in minutes) to answer the question.')
    directions = models.TextField(null=True, blank=True)
    reference = models.CharField(max_length=200, null=True, blank=True, help_text="Reference text (optional).")
    comments = models.TextField(null=True, blank=True)
    published = models.BooleanField(default=False)

    # Categorization fields.
    chapter = models.PositiveIntegerField(default=0,
                                          help_text="Chapter number. Must be non-negative for publisher questions.")
    section = models.PositiveIntegerField(default=0, help_text="Section number. Default is 0.")
    # For question types that require a single correct answer (e.g., True/False, Multiple Choice), this field is used.
    # For Fill in the Blank questions, use the associated Answers for multiple correct answers.
    answer = models.TextField(null=True, blank=True, help_text="Correct answer for types requiring a single answer.")

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Custom validation:
        For publisher-created questions (identified via the author's role), ensure that the chapter number is non-negative.
        """
        super().clean()
        if self.author and hasattr(self.author, 'userprofile'):
            if self.author.userprofile.role == 'publisher' and self.chapter < 0:
                raise ValidationError("Publisher-created questions must include a non-negative chapter number.")

    def __str__(self):
        return f"[{self.get_qtype_display()}] {self.text[:50]}"

    @property
    def publisher_average_rating(self):
        """
        Returns the average rating for a publisher-created question.
        Teachers can use this property to assess aggregated feedback.
        """
        if self.author and hasattr(self.author, 'userprofile') and self.author.userprofile.role == 'publisher':
            avg = self.feedbacks.aggregate(Avg('rating'))['rating__avg']
            return avg
        return None


"""
OPTIONS MODEL
Stores response options for questions such as Multiple Choice, Multiple Selection, Matching, etc.
Extra support added for an optional image in the option.
"""


class Options(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="question_options"
    )
    text = models.TextField(help_text="Answer option text", null=True)
    image = models.ImageField(upload_to='option_images/', null=True, blank=True,
                              help_text="Optional image for the option (extra support).")

    def __str__(self):
        return self.text or "Option"


"""
ANSWERS MODEL
Stores correct answers and optional response feedback.
For Fill in the Blank questions, multiple Answers entries can represent multiple correct answers.
For question types like True/False or Multiple Choice, a single answer may be provided.
Essay and Short Answer questions typically do not have correct answers.
"""


class Answers(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="question_answers"
    )
    text = models.TextField(help_text="Correct answer text", null=True)
    answer_graphic = models.ImageField(upload_to='answer_graphics/', null=True, blank=True)
    response_feedback_text = models.TextField(null=True, blank=True)
    response_feedback_graphic = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.text or "Answer"


"""
DYNAMIC QUESTION PARAMETER MODEL
Used for questions that generate answers dynamically.
Holds a formula and acceptable range, plus any additional parameters.
"""


class DynamicQuestionParameter(models.Model):
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name="dynamic_parameters"
    )
    formula = models.TextField(help_text="Formula for generating or validating the answer.")
    range_min = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum acceptable value.")
    range_max = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum acceptable value.")
    additional_params = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional parameters for dynamic generation."
    )

    def __str__(self):
        return f"Dynamic Params for QID {self.question.id}"


"""
TEMPLATE MODEL
Stores templates for test formatting.
Templates can be linked to a course (teacher content) or directly to a textbook (publisher content).
"""


class Template(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this template (teacher content)."
    )
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Textbook associated with this template (publisher content)."
    )
    name = models.CharField(max_length=200, unique=True, help_text="Template name.")
    titleFont = models.CharField(max_length=100, default="Arial")
    titleFontSize = models.IntegerField(default=48)
    subtitleFont = models.CharField(max_length=100, default="Arial")
    subtitleFontSize = models.IntegerField(default=24)
    bodyFont = models.CharField(max_length=100, default="Arial")
    bodyFontSize = models.IntegerField(default=12)
    pageNumbersInHeader = models.BooleanField(default=False)
    pageNumbersInFooter = models.BooleanField(default=False)
    headerText = models.TextField(null=True, blank=True)
    footerText = models.TextField(null=True, blank=True)
    coverPage = models.IntegerField(default=0)
    partStructure = models.JSONField(null=True, blank=True, help_text="JSON representation of the test part structure")
    bonusSection = models.BooleanField(default=False)
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.name


"""
COVER PAGE MODEL
Stores cover page details.
Cover pages can be linked to a course (teacher content) or a textbook (publisher content).
"""


class CoverPage(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this cover page (teacher content)."
    )
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Textbook associated with this cover page (publisher content)."
    )
    name = models.CharField(max_length=200, help_text="Name of the cover page.")
    testNum = models.CharField(max_length=50, help_text="Test number displayed on the cover page.")
    date = models.DateField(help_text="Date of the test.")
    file = models.CharField(max_length=200, help_text="Filename displayed on the cover page.")
    showFilename = models.BooleanField(default=False, help_text="Display the filename on the cover page?")
    STUDENT_NAME_CHOICES = [
        ('TL', 'Top Left'),
        ('TR', 'Top Right'),
        ('BT', 'Below Title'),
    ]
    blank = models.CharField(
        max_length=20,
        choices=STUDENT_NAME_CHOICES,
        default='TL',
        help_text="Location for the student's name on the cover page."
    )
    instructions = models.TextField(blank=True, null=True, help_text="Grading instructions for the answer key.")
    published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.testNum}"


"""
ATTACHMENT MODEL
Stores file attachments.
Attachments can be linked to a course (teacher content) or a textbook (publisher content).
"""


class Attachment(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Course associated with this attachment (teacher content).",
        related_name="attachment_set"
    )
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Textbook associated with this attachment (publisher content).",
        related_name="attachment_set"
    )
    name = models.CharField(max_length=300, help_text="Attachment name")
    file = models.FileField(upload_to="attachments/")
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.file.name



"""
TEST MODEL
Represents a test or quiz.
For teacher tests, linked to a course; for publisher tests, linked directly to a textbook.
Includes title, date, finalization status, and instructions.
"""


class Test(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tests',
        help_text="Course associated with this test (teacher content)."
    )
    textbook = models.ForeignKey(
        Textbook,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Textbook associated with this test (publisher content)."
    )
    name = models.CharField(max_length=200, help_text="e.g: Quiz 1, Test 1", default="Untitled Test.")
    date = models.DateField(null=True, blank=True)
    filename = models.CharField(max_length=200, null=True, blank=True, help_text="Generated filename for this test.")
    is_final = models.BooleanField(default=False, help_text="Mark as True when test is published/finalized.")
    template = models.ForeignKey(
        Template,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    attachments = models.ManyToManyField(Attachment, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    templateIndex = models.PositiveIntegerField(default=0, help_text="Associated Template ID. Default is 0.")

    def __str__(self):
        if self.course:
            return f"{self.name} - {self.course.course_id}"
        elif self.textbook:
            return f"{self.name} - {self.textbook.title}"
        return self.name


"""
TEST PART MODEL
Divides a test into parts.
"""


class TestPart(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='parts',
        help_text="Test this part belongs to"
    )
    part_number = models.IntegerField(default=1, help_text="Part number within the test")

    def __str__(self):
        return f"Part {self.part_number} of {self.test.name}"


"""
TEST SECTION MODEL
Divides a test part into sections, grouping questions by type.
"""


class TestSection(models.Model):
    part = models.ForeignKey(
        TestPart,
        on_delete=models.CASCADE,
        related_name='sections',
        help_text="Part this section belongs to"
    )
    section_number = models.IntegerField(default=1, help_text="Section number within the part")
    question_type = models.CharField(max_length=50, help_text="Type of questions in this section")

    def __str__(self):
        return f"Section {self.section_number} in Part {self.part.part_number} of {self.part.test.name}"


"""
TEST QUESTION MODEL
Links a question to a test, assigning points and order.
Ensures uniqueness of a question within a test.
"""


class TestQuestion(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="test_questions"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="test_appearances"
    )
    assigned_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    order = models.IntegerField(default=1, help_text="Order of question in the test.")
    randomize = models.BooleanField(default=False)
    special_instructions = models.TextField(null=True, blank=True)
    section = models.ForeignKey(TestSection, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('test', 'question')
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order} in {self.test.name}"


"""
FEEDBACK MODEL
Stores feedback for questions and tests with ratings (1 to 5) and optional comments.
"""


class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feedbacks"
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feedbacks"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    averageScore = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.question:
            return f"Feedback on Question {self.question.id}"
        elif self.test:
            return f"Feedback on Test {self.test.name}"
        return "General Feedback"


"""
RESPONSE MODEL
Stores responses to feedback
"""


class FeedbackResponse(models.Model):
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="responses"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Response to feedback"