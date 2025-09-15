from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("ai-mock-interview/", views.ai_mock_interview, name="ai_mock_interview"),
    path("bio-generator/", views.bio_generator, name="bio_generator"),
    path("generate-bio/", views.generate_bio, name="generate_bio"),
    path("resume_builder", views.resume_builder, name="resume_builder"),
    path("jobs/", views.job_list, name="job_list"),
    path("job/<int:job_id>/", views.job_detail, name="job_detail"),
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),
    path("jobs/search/", views.job_search, name="job_search"),
    path("plans/", views.plan_select, name="plan_select"),
    path("plans/<int:plan_id>/select/", views.select_plan, name="select_plan"),
    # path("confirm-courses/", views.confirm_courses, name="confirm_courses"),
    path("confirm-courses/<int:course_id>/", views.confirm_courses, name="confirm_courses_course"),


    path("profile/", views.profile_dashboard, name="profile_dashboard"),
    path("payment/callback/", views.payment_callback, name="payment_callback"),

    path('select-plan/<int:plan_id>/', views.select_plan, name='select_plan'),
    path('payment-success/', views.payment_success, name='payment_success'),
    
]

