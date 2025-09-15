# myapp/models.py
from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta

class Plan(models.Model):
    name = models.CharField(max_length=100)  # Basic / Standard / Premium
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=50, default="Yearly")
    features = models.TextField(help_text="Comma separated features", blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Plan Details Upload"
        verbose_name_plural = "Plan Details Upload"

    def feature_list(self):
        return [f.strip() for f in self.features.split(",") if f.strip()]

    def __str__(self):
        return self.name
    

class Job(models.Model):
    course = models.ForeignKey("Course", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=100, default="Remote")
    job_type = models.CharField(max_length=100, default="Full-time")
    salary_range = models.CharField(max_length=50)
    posted_days = models.CharField(max_length=50, default="1 day ago")
    openings = models.IntegerField(default=1)
    applicants = models.IntegerField(default=0)
    responsibilities = models.TextField(help_text="Use line breaks for bullet points")
    role = models.CharField(max_length=100)
    candidate_type = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=100)
    education = models.CharField(max_length=100)
    skills = models.CharField(max_length=300, help_text="Comma separated skills")
    about_company = models.TextField()

    def skill_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def __str__(self):
        return f"{self.title} - {self.company}"
    



class Application(models.Model):
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    job = models.ForeignKey("Job", on_delete=models.SET_NULL, null=True, blank=True, related_name="applications")
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    city = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    languages = models.CharField(max_length=255)
    work_status = models.CharField(max_length=200)
    experience_years = models.CharField(max_length=50)
    qualification = models.CharField(max_length=200)
    passed_out_year = models.CharField(max_length=4)
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)
    updates_optin = models.BooleanField(default=False)

    plan = models.ForeignKey("Plan", on_delete=models.SET_NULL, null=True, blank=True)
    plan_start = models.DateField(null=True, blank=True)  # ✅ Add this
    plan_end = models.DateField(null=True, blank=True)    # ✅ Add this

    created_at = models.DateTimeField(auto_now_add=True)

    def is_plan_active(self):
        from datetime import date
        return bool(self.plan_end and self.plan_end >= date.today())

    def remaining_days(self):
        from datetime import date
        if self.plan_end:
            remaining = (self.plan_end - date.today()).days
            return max(remaining, 0)
        return 0

    def __str__(self):
        return f"{self.full_name} ({self.plan.name if self.plan else 'No Plan'})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    # Basic Info
    full_name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, unique=True, null=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    languages = models.CharField(max_length=255, null=True, blank=True)
    work_status = models.CharField(max_length=50, blank=True, null=True)

    # Education
    education = models.CharField(max_length=200, null=True, blank=True)
    university = models.CharField(max_length=200, null=True, blank=True)
    course = models.CharField(max_length=200, null=True, blank=True)
    course_start = models.CharField(max_length=20, null=True, blank=True)
    course_end = models.CharField(max_length=20, null=True, blank=True)

    # IT Skills
    skill = models.CharField(max_length=200, null=True, blank=True)
    software = models.CharField(max_length=200, null=True, blank=True)
    skill_experience = models.CharField(max_length=100, null=True, blank=True)

    # Projects
    project_title = models.CharField(max_length=200, null=True, blank=True)
    project_link = models.URLField(null=True, blank=True)
    project_details = models.TextField(null=True, blank=True)
    project_file = models.FileField(upload_to="projects/", null=True, blank=True)

    # Career Profile
    current_industry = models.CharField(max_length=200, null=True, blank=True)
    current_role = models.CharField(max_length=200, null=True, blank=True)
    exp_start = models.CharField(max_length=20, null=True, blank=True)
    exp_end = models.CharField(max_length=20, null=True, blank=True)
    certificate = models.FileField(upload_to="certificates/", null=True, blank=True)

    # Resume + Profile
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True)

    plan = models.ForeignKey("Plan", on_delete=models.SET_NULL, null=True, blank=True)
    plan_start = models.DateField(null=True, blank=True)
    plan_end = models.DateField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def completion_percentage(self):
        # ... existing
        fields = [
            self.full_name, self.email, self.mobile, self.city,
            self.education, self.university, self.course,
            self.skill, self.software,
            self.project_title, self.project_details,
            self.current_industry, self.current_role,
            self.resume
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)

    def assign_plan(self, plan):
        """Helper: assign plan and set 1 year validity from today."""
        self.plan = plan
        start = date.today()
        self.plan_start = start
        self.plan_end = start + timedelta(days=365)
        self.save()

    def remaining_days(self):
        """Return number of days left in plan validity (0 if expired or no plan)."""
        if self.plan and self.plan_end:
            today = date.today()
            return max((self.plan_end - today).days, 0)
        return 0

    def remaining_applications_today(self):
        """Return how many job applications the user can still submit today."""
        if not self.plan:
            return None  # no plan yet

        plan_name = self.plan.name.strip().lower()
        if plan_name == "basic":
            from .models import Application  # avoid circular import
            apps_today_count = Application.objects.filter(
                user=self.user, created_at__date=date.today()
            ).count()
            return max(5 - apps_today_count, 0)
        # unlimited for other plans
        return None
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.mobile or 'No Mobile'}"
        return f"Orphan Profile - {self.mobile or 'N/A'}"




# Course Topics
class Course(models.Model):
    name = models.CharField(max_length=200, unique=True)
    course_tools = models.CharField(max_length=250, null=True)
    video_thumbnail = models.ImageField(upload_to="course_thumbnails/", null=True, blank=True)

    class Meta:
        verbose_name = "Course name"
        verbose_name_plural = "Courses name"

    def __str__(self):
        return self.name


class Topic(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=255, null=True, blank=True)
    order = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Course Topics adding section"
        verbose_name_plural = "Courses Topics adding section "

    def __str__(self):
        return f"{self.order}. {self.title}"


# Job Preparation Videos (linked to a course)
class JobVideo(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="job_videos")
    title = models.CharField(max_length=200, null=True)
    video_file = models.FileField(upload_to="job_videos/", null=True)  # Upload actual video file
    thumbnail = models.ImageField(upload_to="job_video_thumbnails/", null=True, blank=True)  # optional

    class Meta:
        verbose_name = "Job Video Upload"
        verbose_name_plural = "Job Video Uploads"

    def __str__(self):
        return self.title


# Interview Questions (linked to a course)
class InterviewQuestion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="interview_questions")
    tool_name = models.CharField(max_length=100)   
    icon = models.ImageField(upload_to="tool_icons/")
    pdf_file = models.FileField(upload_to="interview_pdfs/")

    class Meta:
        verbose_name = "Interview Questions & PDF"
        verbose_name_plural = "Interview Questions & PDF"

    def __str__(self):
        return self.tool_name


# Placement Sessions (linked to a course)
class PlacementSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="placement_sessions")
    date = models.DateField()
    time = models.CharField(max_length=100)
    session_type = models.CharField(max_length=50, default="1 to 1 Session")
    mode = models.CharField(max_length=100, default="Online (Microsoft Teams)")

    class Meta:
        verbose_name = "Placement Session Date & Time"
        verbose_name_plural = "Placement Sessions Date & Time"

    def __str__(self):
        return f"{self.date} - {self.time}"


# Doubts (optional, can also link to course if needed)
class Doubt(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="doubts", null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)  
    email = models.EmailField(null=True, blank=True)              
    doubt_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Doubt Clear Form"
        verbose_name_plural = "Doubt Clear Forms"

    def __str__(self):
        return f"Doubt #{self.id} - {self.doubt_text[:30]}"


# ----------------------------
# Payment Model (for Razorpay)
# ----------------------------
class Payment(models.Model):
    STATUS_CHOICES = (
        ("CREATED", "Created"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=255)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.TextField(blank=True, null=True)
    amount = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="CREATED")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"

    def __str__(self):
        return f"{self.user.username} | {self.plan.name} | {self.status}"
