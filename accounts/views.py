from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DetailView
from .forms import CustomUserCreationForm, CustomUserChangeForm, PasswordChangeingForm
from threads.models import Profile, Thread, WatchThread
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import PasswordChangeView
from django.core.paginator import Paginator

# Create your views here.


class PasswordsChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = PasswordChangeingForm
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("home")


class CreateUserProfilePageView(LoginRequiredMixin, CreateView):
    model = Profile
    template_name = "registration/create_user_profile_page.html"
    fields = ("bio", "pfp")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ShowProfilePageView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "registration/profile.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_user = get_object_or_404(Profile, id=self.kwargs['pk'])
        threads_watched_by_you = WatchThread.objects.filter(
            user=current_user.user)
        threads_watched_by_you = [item for item in threads_watched_by_you]
        qs = Thread.objects.filter(title__in=threads_watched_by_you)

        context = {
            "current_user": current_user,
            "threads_by_them": Thread.objects.filter(author=current_user.user),
            "threads_watched_by_you": qs,
        }
        # p = Paginator(context, 5)
        # page = self.request.GET.get("page")
        # information = p.get_page(page)
        return context


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class EditSettingsView(LoginRequiredMixin, UpdateView):
    form_class = CustomUserChangeForm
    template_name = "registration/edit_settings.html"
    success_url = reverse_lazy("home")

    def get_object(self):
        return self.request.user


class EditUserPageView(LoginRequiredMixin, UpdateView):
    model = Profile
    template_name = "registration/edit_profile_page.html"
    fields = ("bio", "pfp",)
