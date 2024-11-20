from django.contrib import admin
from .models import Company, CompanyMembership

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'nit', 'email', 'phone', 'created_by', 'created_at')
    search_fields = ('name', 'nit', 'email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CompanyMembership)
class CompanyMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'invitation_accepted', 'joined_at')
    search_fields = ('user__username', 'user__email', 'company__name')
    list_filter = ('role', 'invitation_accepted')
    ordering = ('-joined_at',)
    readonly_fields = ('joined_at',)
