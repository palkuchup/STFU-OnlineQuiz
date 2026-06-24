from django.db.models.signals import post_save
from django.dispatch import receiver
from subjects.models import Enrollment, Subject
from accounts.models import CustomUser

# Note: The logic for auto-promotion is currently handled directly in the
# SubmitFinalGradeView API in subjects.views, which makes it synchronous 
# and easy to return the result to the caller. 
# We can use signals in the future if we need side effects triggered by other means.
