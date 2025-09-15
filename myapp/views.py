from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
import razorpay

from .models import (
    UserProfile, Job, Application, Plan, Course, JobVideo,
    InterviewQuestion, PlacementSession, Doubt
)

# -------------------- AUTH --------------------

def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        mobile = request.POST.get("mobile")
        status = request.POST.get("status")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )
        UserProfile.objects.create(user=user, mobile=mobile, work_status=status)

        login(request, user)
        return redirect("home")

    return render(request, "myapp/register.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid email or password")
            return redirect("login")

    return render(request, "myapp/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def home_view(request):
    return render(request, "myapp/home.html")

# -------------------- AI TOOLS -------------------- 

def ai_mock_interview(request):
    return render(request, "myapp/mock_interview.html")


def bio_generator(request):
    return render(request, "myapp/bio_generator.html")


def generate_bio(request):
    if request.method == "POST":
        name = request.POST.get("fullName")
        exp = request.POST.get("experience")
        skills = request.POST.get("skills")
        highlights = request.POST.get("highlights")
        tone = request.POST.get("tone")
        length = request.POST.get("length")
        lang = request.POST.get("language")

        bio1 = f"{name} is a {exp} professional skilled in {skills}. {highlights}. Known for a {tone.lower()} approach with {length.lower()} impactful communication. ({lang})"
        bio2 = f"With experience at the {exp}, {name} specializes in {skills}. {highlights}. Delivering results with a {tone.lower()} style and {length.lower()} summaries. ({lang})"

        return JsonResponse({"bio1": bio1, "bio2": bio2})


def resume_builder(request):
    data = None
    if request.method == "POST":
        skills = request.POST.get("skills", "")
        keywords = request.POST.get("keywords", "")
        data = {
            "full_name": request.POST.get("full_name"),
            "experience_level": request.POST.get("experience_level"),
            "skills": [s.strip() for s in skills.split(",") if s.strip()],
            "career_highlights": request.POST.get("career_highlights"),
            "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
        }
    return render(request, "myapp/resume_builder.html", {"data": data})

# -------------------- JOBS --------------------

@login_required
def job_list(request):
    jobs = Job.objects.all()
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, "myapp/job_list.html", {"jobs": jobs, "profile": profile})


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    responsibilities = job.responsibilities.split("\n")

    # Get related course dynamically
    course = job.course
    if not course:
        course = Course.objects.filter(name__iexact=job.role).first() or \
                 Course.objects.filter(name__iexact=job.title).first()

    # ✅ Get user plan (if logged in)
    user_plan = None
    if request.user.is_authenticated:
        try:
            user_plan = request.user.userprofile.plan.name.lower()  # "basic", "standard", "premium"
        except:
            user_plan = None

    return render(request, "myapp/job_detail.html", {
        "job": job,
        "responsibilities": responsibilities,
        "course": course,
        "user_plan": user_plan,  # ✅ Pass to template
    })


from datetime import date
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from datetime import date
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # get-or-create profile
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Check for Basic plan daily limit
        if profile.plan and profile.plan.name and profile.plan.name.strip().lower() == "basic":
            today = date.today()
            apps_today_count = Application.objects.filter(user=request.user, created_at__date=today).count()
            
            if apps_today_count >= 5:
                messages.error(
                    request,
                    "You have reached the daily limit of 5 job applications for Basic plan. You can apply again tomorrow."
                )
                return redirect("job_detail", job_id=job.id)

        # Create the application
        application = Application.objects.create(
            user=request.user,
            job=job,
            full_name=request.POST.get("full_name"),
            email=request.POST.get("email"),
            mobile=request.POST.get("mobile"),
            city=request.POST.get("city"),
            gender=request.POST.get("gender"),
            languages=request.POST.get("languages"),
            work_status=request.POST.get("work_status"),
            experience_years=request.POST.get("experience_years"),
            qualification=request.POST.get("qualification"),
            passed_out_year=request.POST.get("passed_out_year"),
            updates_optin=request.POST.get("updates_optin") == "on",
            profile_image=request.FILES.get("profile_image"),
            resume=request.FILES.get("resume"),
        )

        request.session["job_id"] = job.id
        request.session["application_id"] = application.id

        # Redirect based on whether user has a plan
        if not profile.plan:
            return redirect("plan_select")

        return redirect("confirm_courses_course", course_id=job.course.id)

    return render(request, "myapp/apply_form.html", {"job": job})


@login_required
def plan_select(request):
    plans = Plan.objects.all()
    application_id = request.session.get("application_id")

    if request.method == "POST":
        selected_plan_id = request.POST.get("plan_id")
        if not application_id:
            messages.error(request, "No application found in session.")
            return redirect("job_search")

        application = get_object_or_404(Application, id=application_id)
        if selected_plan_id:
            selected_plan = get_object_or_404(Plan, id=selected_plan_id)
            application.plan = selected_plan
            application.save()

            # store chosen plan in session (useful for confirm page)
            request.session["selected_plan_id"] = selected_plan.id

            # now go to checkout (select_plan will create order)
            return redirect("select_plan", plan_id=selected_plan.id)

        messages.error(request, "Please select a plan.")
        return redirect("plan_select")

    return render(request, "myapp/plan_select.html", {"plans": plans})


# @login_required
# def select_plan(request, plan_id):
#     plan = get_object_or_404(Plan, id=plan_id)

#     # Attach plan to Application (if present in session)
#     application_id = request.session.get("application_id")
#     if application_id:
#         try:
#             application = Application.objects.get(id=application_id)
#             if application.plan_id != plan.id:
#                 application.plan = plan
#                 application.save()
#         except Application.DoesNotExist:
#             pass

#     # Save the plan to the user's profile (so daily-limit / features apply)
#     profile, _ = UserProfile.objects.get_or_create(user=request.user)
#     # assign_plan will set plan_start and plan_end to 1 year
#     profile.assign_plan(plan)

#     # --- Create razorpay order and render checkout ---
#     client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

#     order_amount = int(plan.price * 100)
#     order_currency = "INR"

#     razorpay_order = client.order.create(dict(amount=order_amount, currency=order_currency, payment_capture="1"))

#     context = {
#         "plan": plan,
#         "razorpay_order_id": razorpay_order["id"],
#         "razorpay_key_id": settings.RAZORPAY_KEY_ID,
#         "amount": order_amount,
#         "currency": order_currency,
#     }
#     return render(request, "myapp/checkout.html", context)
import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from myapp.models import Plan, Application, UserProfile, Payment

@login_required
def select_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)

    # Attach plan to Application (if present in session)
    application_id = request.session.get("application_id")
    if application_id:
        try:
            application = Application.objects.get(id=application_id)
            if application.plan_id != plan.id:
                application.plan = plan
                application.save()
        except Application.DoesNotExist:
            pass

    # Save plan to user profile (so daily-limit/features apply)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.assign_plan(plan)

    # --- Razorpay Order Creation ---
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order_amount = int(plan.price * 100)  # Razorpay accepts amount in paise
    order_currency = "INR"

    razorpay_order = client.order.create(dict(
        amount=order_amount,
        currency=order_currency,
        payment_capture="1"
    ))

    # Save payment details in DB (Optional but Recommended)
    payment = Payment.objects.create(
        user=request.user,
        plan=plan,
        razorpay_order_id=razorpay_order["id"],
        amount=order_amount / 100,
        status="CREATED"
    )

    context = {
        "plan": plan,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount": order_amount,
        "currency": order_currency,
        "callback_url": request.build_absolute_uri("/payment/callback/"),
    }
    return render(request, "myapp/checkout.html", context)


@csrf_exempt
def payment_callback(request):
    """
    Handles the Razorpay callback after payment.
    """
    if request.method == "POST":
        data = request.POST
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_signature = data.get("razorpay_signature")

        try:
            # Verify the signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # ✅ Update payment status
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = "SUCCESS"
            payment.save()

            return redirect("payment_success")

        except razorpay.errors.SignatureVerificationError:
            return HttpResponseBadRequest("Payment verification failed")
    return HttpResponseBadRequest("Invalid request")


from datetime import date, timedelta

@login_required
def payment_success(request):
    job_id = request.session.get("job_id")
    if not job_id:
        messages.error(request, "Job not found in session.")
        return redirect("job_search")

    job = get_object_or_404(Job, id=job_id)

    course = job.course or \
             Course.objects.filter(name__iexact=job.role).first() or \
             Course.objects.filter(name__iexact=job.title).first()

    if not course:
        messages.error(request, f"No course found matching '{job.role}' or '{job.title}'")
        return redirect("job_search")

    selected_plan_id = request.session.get("selected_plan_id")
    if selected_plan_id:
        try:
            plan = Plan.objects.get(id=selected_plan_id)
            application, _ = Application.objects.get_or_create(
                job=job, email=request.user.email,
                defaults={"user": request.user, "full_name": request.user.get_full_name()}
            )
            application.plan = plan
            application.plan_start = date.today()
            application.plan_end = date.today() + timedelta(days=365)  # ✅ 1-year validity
            application.save()
        except Plan.DoesNotExist:
            messages.error(request, "Selected plan not found.")
            return redirect("choose_plan")
    else:
        messages.error(request, "No plan was selected.")
        return redirect("choose_plan")

    request.session["job_id"] = job.id
    request.session.pop("application_data", None)

    return redirect("confirm_courses_course", course_id=course.id)


# -------------------- CONFIRM COURSES --------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date

@login_required
def confirm_courses(request, course_id=None):
    if not course_id:
        return redirect("job_search")

    course = get_object_or_404(Course, id=course_id)
    courses = [course]

    # Get the relevant job
    job_id = request.session.get("job_id")
    job = None
    user_application = None
    user_plan = None

    if job_id:
        job = Job.objects.filter(id=job_id).first()
    if not job:
        job = Job.objects.filter(course=course).first() \
              or Job.objects.filter(role__iexact=course.name).first() \
              or Job.objects.filter(title__iexact=course.name).first()

    # Get user application if exists
    if job:
        user_application = Application.objects.filter(
            job=job, email=request.user.email, plan__isnull=False
        ).first()

    # Set user_plan safely
    if user_application:
        user_plan = user_application.plan.name.lower().strip()  # lowercase + remove spaces
    else:
        user_plan = None

    # Fetch course-related data
    job_videos = JobVideo.objects.filter(course=course)
    interview_qs = InterviewQuestion.objects.filter(course=course)
    placement = PlacementSession.objects.filter(course=course).first()

    # Handle doubt form submission
    if request.method == "POST":
        doubt_text = request.POST.get("doubt")
        name = request.POST.get("name")
        email = request.POST.get("email")
        if doubt_text:
            Doubt.objects.create(course=course, name=name, email=email, doubt_text=doubt_text)
            messages.success(request, "Your doubt has been submitted!")
        return redirect("confirm_courses_course", course_id=course.id)

    return render(request, "myapp/confirm_courses.html", {
        "courses": courses,
        "job": job,
        "job_videos": job_videos,
        "interview_qs": interview_qs,
        "placement": placement,
        "user_plan": user_plan,  # None if no plan
        "remaining_days": user_application.remaining_days() if user_application else 0,
    })


# -------------------- PROFILE --------------------

@login_required
def profile_dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    remaining_days = profile.remaining_days()
    remaining_today = profile.remaining_applications_today()


    if request.method == "POST":
        section = request.POST.get("section")

        if section == "personal":
            profile.full_name = request.POST.get("full_name")
            profile.email = request.POST.get("email")
            profile.mobile = request.POST.get("mobile")
            profile.city = request.POST.get("city")
            profile.gender = request.POST.get("gender")
            profile.languages = request.POST.get("languages")

        elif section == "education":
            profile.education = request.POST.get("education")
            profile.university = request.POST.get("university")
            profile.course = request.POST.get("course")
            profile.course_start = request.POST.get("course_start")
            profile.course_end = request.POST.get("course_end")

        elif section == "skills":
            profile.skill = request.POST.get("skill")
            profile.software = request.POST.get("software")
            profile.skill_experience = request.POST.get("skill_experience")

        elif section == "projects":
            profile.project_title = request.POST.get("project_title")
            profile.project_link = request.POST.get("project_link")
            profile.project_details = request.POST.get("project_details")
            if request.FILES.get("project_file"):
                profile.project_file = request.FILES["project_file"]

        elif section == "career":
            profile.current_industry = request.POST.get("current_industry")
            profile.current_role = request.POST.get("current_role")
            profile.exp_start = request.POST.get("exp_start")
            profile.exp_end = request.POST.get("exp_end")
            if request.FILES.get("certificate"):
                profile.certificate = request.FILES["certificate"]

        elif section == "resume":
            if request.FILES.get("resume"):
                profile.resume = request.FILES["resume"]
            if request.FILES.get("profile_image"):
                profile.profile_image = request.FILES["profile_image"]

        profile.save()
        return redirect("profile_dashboard")

    return render(request, "myapp/profile_dashboard.html", {
        "profile": profile,
        "remaining_days": remaining_days,
        "remaining_today": remaining_today,
        })

# -------------------- JOB SEARCH --------------------

def job_search(request):
    jobs = Job.objects.all()

    keyword = request.GET.get("keyword", "")
    course = request.GET.get("course", "")
    location = request.GET.get("location", "")
    salary = request.GET.get("salary", "")

    if keyword:
        jobs = jobs.filter(title__icontains=keyword) | jobs.filter(skills__icontains=keyword)
    if course:
        jobs = jobs.filter(role__icontains=course) | jobs.filter(skills__icontains=course)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if salary:
        jobs = jobs.filter(salary_range__icontains=salary)

    return render(request, "myapp/job_search.html", {"jobs": jobs})

