from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from .forms import AdminLoginForm, EditPhoneNumberForm, AssignAdminForm
from myapp.models import PhoneNumber, Token, CommunityMember
from django.db import transaction, IntegrityError


class AdminLoginView(View):
    template_name = 'custom_admin/login.html'
    form_class = AdminLoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('custom_admin:dashboard')
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                if user.is_staff:
                    login(request, user)
                    return redirect('custom_admin:dashboard')
                form.add_error(None, 'You do not have admin privileges.')
            else:
                form.add_error(None, 'Invalid username or password.')
        return render(request, self.template_name, {'form': form})


class AdminLogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('custom_admin:login')


class AdminDashboardView(LoginRequiredMixin, View):
    template_name = 'custom_admin/dashboard.html'

    def get(self, request):
        selected_community = request.GET.get('community', 'all')
        communities = CommunityMember.COMMUNITY_CHOICES
        phone_numbers = PhoneNumber.objects.select_related('token').filter(
            community_members__community=selected_community
        ).distinct() if selected_community != 'all' else PhoneNumber.objects.select_related('token').all()

        page_obj = Paginator(phone_numbers, 10).get_page(request.GET.get('page'))
        
        community_data = [
            {'id': value, 'name': name, 'count': CommunityMember.objects.filter(community=value).count()}
            for value, name in communities
        ]

        context = {
            'phone_numbers': page_obj.object_list,
            'page_obj': page_obj,
            'communities': communities,
            'selected_community': selected_community,
            'community_data': community_data,
        }
        return render(request, self.template_name, context)


class ViewPhoneNumberView(LoginRequiredMixin, View):
    template_name = 'custom_admin/view_phone.html'

    def get(self, request, number):
        phone = get_object_or_404(PhoneNumber, number=number)
        context = {'phone': phone, 'community_members': phone.community_members.all()}
        return render(request, self.template_name, context)


class AssignAdminView(LoginRequiredMixin, View):
    template_name = 'custom_admin/assign_admin.html'
    form_class = AssignAdminForm

    def get(self, request, number, community_id):
        phone = get_object_or_404(PhoneNumber, number=number)
        community_member = get_object_or_404(CommunityMember, phone_number=phone, community=community_id)
        form = self.form_class(instance=community_member)
        return render(request, self.template_name, {'form': form, 'phone': phone, 'community_member': community_member})

    def post(self, request, number, community_id):
        phone = get_object_or_404(PhoneNumber, number=number)
        community_member = get_object_or_404(CommunityMember, phone_number=phone, community=community_id)
        form = self.form_class(request.POST, instance=community_member)

        if form.is_valid():
            try:
                with transaction.atomic():
                    if form.cleaned_data['role'] == 'admin':
                        CommunityMember.objects.filter(community=community_id, role='admin').exclude(id=community_member.id).update(role='user')
                    form.save()
                    messages.success(request, f"Role updated to '{form.cleaned_data['role']}' for {phone.number} in {community_member.get_community_display()}.")
                    return redirect('custom_admin:dashboard')
            except IntegrityError:
                form.add_error(None, 'An error occurred while assigning the admin role. Please try again.')

        return render(request, self.template_name, {'form': form, 'phone': phone, 'community_member': community_member})


class DeletePhoneNumberView(LoginRequiredMixin, View):
    def post(self, request, number):
        phone = PhoneNumber.objects.filter(number=number).first()
        if phone:
            phone.delete()
            messages.success(request, f'Phone number {number} has been deleted.')
        else:
            messages.error(request, f'Phone number {number} does not exist.')
        return redirect('custom_admin:dashboard')


class EditPhoneNumberView(LoginRequiredMixin, View):
    template_name = 'custom_admin/edit_phone.html'

    def get(self, request, number):
        phone = get_object_or_404(PhoneNumber, number=number)
        form = EditPhoneNumberForm(instance=phone)
        return render(request, self.template_name, {'form': form, 'phone': phone})

    def post(self, request, number):
        phone = get_object_or_404(PhoneNumber, number=number)
        form = EditPhoneNumberForm(request.POST, instance=phone)
        if form.is_valid():
            form.save()
            messages.success(request, f'Phone number {phone.number} has been updated.')
            return redirect('custom_admin:dashboard')
        return render(request, self.template_name, {'form': form, 'phone': phone})
