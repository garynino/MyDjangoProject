"""
Creating a database that will store all the information for the test automation
Creating: User, Course, Question, TEST, TEMPLATE, TEST QUESTION LINKING TO TESTFEEDBACK TABLES
"""

from django.db import models
from django.contrib.auth.models import User  # this will automatically the user_id, username, email, or passwords
from django.utils import timezone            # allows for a default timestamp for the database values that nee it

"""
USER | ROLES  TABLE 
"""
class UserProfile(models.Model):
    role_choices = [
        ('webmaster', 'Webmaster'),
        ('publisher', 'Publisher'),
        ('teacher', 'Teacher'),]

    # this will link the the built in user model in Django
    user = models.OneToOneField(User, on_delete=models.CASCADE)     # Delete Whole profile if deleted
    role = models.CharField(max_length=20, choices=role_choices)

    # This is how to create a readable database need this for every table
    def __str__(self):
        return f"{self.user.username} ({self.role})"


"""
COURSE TABLE
"""
class Course(models.Model):
    course_code = models.CharField(
        max_length=50,
        unique=True,
        help_text= 'e.g: CS499',  # This will give the user an example for their input
        default='CS499')  
        

    course_name = models.CharField(
        max_length=250,
        help_text='e.g: SR PROJ:TEAM SOFTWARE DESIGN',
        default='Untitled Course')

    # Textbook information
    textbook_title = models.CharField(
        max_length=300, 
        blank=True,      # These can be blank and will just be null in the database
        null=True,)
    
    textbook_author = models.CharField(
        max_length=300, 
        blank=True,
        null=True)
        
    textbook_isbn = models.CharField(
        max_length=300, 
        blank=True,
        null=True)
    
    textbook_link = models.CharField(
        max_length=300, 
        blank=True,
        null=True)

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

"""
Question Table
"""
class Question(models.Model):
    '''
                    ****** READ ME ********
    NOT SURE HOW WE WANT TO DO THIS SO MULTIPLE OPTIONS CAN CHANGE
    '''
    question_type_options = [
        ('TF', 'True/False'),
        ('MC', 'Multiple Choice'),
        ('MA', 'Matching'),
        ('FB', 'Fill in the Blank'),
        ('SA', 'Short Answer'),
        ('ES', 'Essay'),]

    # Needs to be many to one a Course can have many questions
    # also if course is deleted then we need to delete the questions from the database          
    course = models.ForeignKey( Course, on_delete=models.CASCADE)    

    question_type = models.CharField(
        max_length=50,
        choices=question_type_options)
    
    question_text = models.TextField(
        help_text='Question Prompt.',
        default='Question text.')
    
    inbedded_graphic = models.ImageField(
        max_length=200,
        null=True,
        blank=True)
    
    choices_for_question = models.TextField(
        null=True,
        blank=True,
        help_text='Answer options for the question.')
    
    correct_answer = models.TextField(
        null=True,
        blank=True,
        help_text='Correct Answer.')
    """
    READ ME: placed in the answer_graphics/ subdirectory of your MEDIA_ROOT
    Possibly need to change need to read into this and how it works exactly
    """
    correct_answer_graphic = models.ImageField(
        upload_to='answer_graphics/', 
        null=True,
        blank=True)
    
    default_points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0)
    
    estimated_time = models.IntegerField( 
        default=1,
        help_text='Estimated time to answer question.')
    
    references = models.CharField(
        max_length=200,
        null=True,
        blank=True)
    
    required_reference_material = models.TextField(null=True, blank=True)

    instructions_for_grading = models.TextField(null=True, blank=True)

    instructor_comment = models.TextField(null=True, blank=True)

    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True)

    # For quality of life shows the users when created and the last time
    # it changed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.question_text[:50]}"


"""
TEMPLATE
"""
class Template(models.Model):
    """
    Defines styling and ordering for tests.
    """
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
    # A course can have many test 1:M (in relation to course)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='test')

    title = models.CharField(
        max_length=200,
        help_text="e.g: Quiz 1, Test 1" ,
        default="Untitled Test.")
    
    # Creates a time stamp for when the test is due
    date = models.DateField(null=True, blank=True)

    filename = models.CharField(
        max_length=200, 
        null=True, 
        blank=True, 
        help_text="Generated filename for this test.")
    
    is_final = models.BooleanField(
        default=False, 
        help_text="Mark as True when test is published/finalized.")
    
    template = models.ForeignKey(
        Template, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True)
    
    attachments = models.ManyToManyField(Attachment, blank=True)

    cover_instructions = models.TextField(
        null=True, 
        blank=True, 
        help_text="Test instructions on cover page.")
    
    test_number = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="Identifier, e.g. 'Test #1'")

    created_at = models.DateTimeField(auto_now_add=True) # timestamp for when created
    updated_at = models.DateTimeField(auto_now=True)     # timestamp for last updated when edited

    def __str__(self):
        return f"{self.title} - {self.course.course_code}"
    
"""
TESTQUESTION TABLE
THIS WILL LINK THE QUESTION TO THE TEST
"""

class TestQuestion(models.Model):
    test = models.ForeignKey(
        Test, 
        on_delete=models.CASCADE, 
        related_name="test_questions")
    
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name="test_appearances")
    
    assigned_points = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True)
    
    order = models.IntegerField(
        default=1, 
        help_text="Order of question in the test.")
    
    randomize = models.BooleanField(default=False)
    special_instructions = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('test', 'question')
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order} in {self.test.title}"
    
"""
FEEDBACK TABLE
STORES THE FEED BACK TO THE QUESTIONS
"""
class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="feedbacks")
    
    test = models.ForeignKey(
        Test, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="feedbacks")
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True)
    
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.question:
            return f"Feedback on Question {self.question.id}"
        elif self.test:
            return f"Feedback on Test {self.test.title}"
        return "General Feedback"