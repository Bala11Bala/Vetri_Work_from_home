from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import *

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

# --- Custom AdminSite ---
class MyAdminSite(AdminSite):
    site_header = "My Custom Admin"

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        for app in app_list:
            if app['app_label'] == 'myapp':
                # reorder models manually
                model_order = ['Course', 'Job', 'Plan', 'Topic', 'JobVideo', 'InterviewQuestion', 'PlacementSession', 'UserProfile',  'Application', 
                'Doubt']
                app['models'].sort(key=lambda x: model_order.index(x['object_name']))
        return app_list

admin_site = MyAdminSite(name='myadmin')

# ✅ Register auth models so Users & Groups appear
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)

# --- Register your app models ---
admin_site.register(UserProfile)
admin_site.register(Job)
admin_site.register(Application)
admin_site.register(Plan)

@admin.register(Course, site=admin_site)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Topic, site=admin_site)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    ordering = ('course', 'order')

@admin.register(Doubt, site=admin_site)
class DoubtAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "doubt_text", "created_at")
    search_fields = ("name", "email", "doubt_text")
    list_filter = ("created_at",)

@admin.register(JobVideo, site=admin_site)
class JobVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'video_file') 
    search_fields = ("title",)

@admin.register(InterviewQuestion, site=admin_site)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "tool_name", "pdf_file", "icon")
    search_fields = ("tool_name",)

@admin.register(PlacementSession, site=admin_site)
class PlacementSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "time", "session_type", "mode")
    list_filter = ("date", "mode")
    search_fields = ("session_type", "mode")
