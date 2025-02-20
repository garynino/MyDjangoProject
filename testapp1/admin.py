from django.contrib import admin
from .models import UserProfile, Course, Question, Template, Attachment, Test, TestQuestion, Feedback

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Question)
admin.site.register(Template)
admin.site.register(Attachment)
admin.site.register(Test)
admin.site.register(TestQuestion)
admin.site.register(Feedback)
