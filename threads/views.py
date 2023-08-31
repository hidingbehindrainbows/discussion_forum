from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin  # new
from django.views.generic import ListView, DetailView, FormView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy, reverse
from .forms import CommentForm, ThreadForm, sortingOptions1, sortingOptions2, now
from .models import Thread, Likes, Dislikes, Category, WatchThread, Comment
from django.shortcuts import redirect, render, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage


# defines the page that shows our threads, it does this by using ListView, which generates an iterable variable
class ThreadView(LoginRequiredMixin, ListView):
    model = Thread
    template_name = "thread_list.html"


class CommentGet(DetailView):  # GETting the comment info
    model = Thread
    template_name = "thread_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        return context


class CommentPost(SingleObjectMixin, FormView):  # POSTing the comment info
    model = Thread
    form_class = CommentForm
    template_name = "thread_detail.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.thread = self.object
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        thread = self.get_object()
        return reverse("thread_detail", kwargs={"pk": thread.pk})


# A wrap view that uses both CommentGet and CommentPost
class ThreadDetailView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        view = CommentGet.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = CommentPost.as_view()
        return view(request, *args, **kwargs)


# allows users to edit their threads
class ThreadEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Thread
    fields = (
        "title",
        "body",
    )
    template_name = "thread_edit.html"

    def test_func(self):
        obj = self.get_object()
        # allow superuser and user to update thread.
        return obj.author == self.request.user or self.request.user.is_superuser


# allows them to delete their threads
class ThreadDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Thread
    template_name = "thread_delete.html"
    success_url = reverse_lazy("thread_list")

    def test_func(self):  # new
        obj = self.get_object()
        # Allow superuser to delete thread.
        return obj.author == self.request.user or self.request.user.is_superuser


# allows users to create new threads
class ThreadCreateView(LoginRequiredMixin, CreateView):
    model = Thread
    template_name = "thread_new.html"
    form_class = ThreadForm

    def form_valid(self, form):  # new
        form.instance.author = self.request.user
        return super().form_valid(form)


@login_required(login_url="login")
def thread_view(request):
    qs = Thread.objects.all()
    user = request.user
    context = {
        "qs": qs,
        "user": user,
    }
    return render(request, "thread_list.html", context)


@login_required(login_url="login")
def like_thread(request):
    try:
        user = request.user
        if request.method == "POST":
            thread_id = request.POST.get("thread_id")
            thread_obj = Thread.objects.get(id=thread_id)

            if user in thread_obj.liked.all():
                thread_obj.liked.remove(user)
            else:
                thread_obj.liked.add(user)
            try:
                like, created = Likes.objects.get_or_create(
                    user=user, thread_id=thread_id)
            except Exception as e:
                print(e)

            if not created:
                if like.value == 'Like':
                    like.value = "Unlike"
                else:
                    like.value = "Like"
                    # like.delete()
                like.save()
            if user not in thread_obj.liked.all():
                like.delete()
        return redirect("thread_detail", pk=thread_id)
    except:
        return HttpResponseRedirect(reverse_lazy("thread_detail", kwargs={"pk": thread_id}))


@login_required(login_url="login")
def dislike_thread(request):
    try:
        user = request.user
        if request.method == "POST":
            thread_id = request.POST.get("thread_id")
            thread_obj = Thread.objects.get(id=thread_id)

            if user in thread_obj.dislike.all():
                thread_obj.dislike.remove(user)
            else:
                thread_obj.dislike.add(user)
            try:
                dislike, created = Dislikes.objects.get_or_create(
                    user=user, thread_id=thread_id)
            except Exception as e:
                print(e)

            if not created:
                if dislike.value == 'Dislike':
                    dislike.value = "Undo"
                else:
                    dislike.value = "Dislike"
                dislike.save()
            if user not in thread_obj.dislike.all():
                dislike.delete()

        return redirect("thread_detail", pk=thread_id)
    except:
        return HttpResponseRedirect(reverse_lazy("thread_detail", kwargs={"pk": thread_id}))


# @login_required(login_url="login")
# def CategoryView(request, cats):
#     choices = Category.objects.all().values_list("name")
#     all_cats = [item for items in choices for item in items]
#     cats = cats.replace("-", " ")
#     if cats in all_cats:
#         p = Paginator(Thread.objects.filter(
#             category=cats), 5)  # TODO changable
#         page = request.GET.get("page")
#         cat_thread = p.get_page(page)
#         return render(request, "categories.html", {"cats": cats, "cat_threads": cat_thread})
#     return redirect("home")


@login_required(login_url="login")
def SortedCategoryView(request, cats, whatSort1="New", whatSort2="allTime"):
    # if whatSort1 == "New" and whatSort2 == "allTime":
    #     return CategoryView(request, cats)
    choices = Category.objects.all().values_list("name")
    all_cats = [item for items in choices for item in items]
    cats = cats.replace("-", " ")
    if cats in all_cats and whatSort1 in sortingOptions1 and whatSort2 in sortingOptions2:
        p = Thread.objects.filter(
            category=cats)
        if whatSort1 == "Top":
            p = p.annotate(
                like_count=(Count('liked'))).order_by('-like_count')

        if whatSort2 == "pastYear":
            p = p.filter(date__year__gt=now.year-1)  # greater than gt
        elif whatSort2 == "pastMonth":
            p = p.filter(date__month__gt=now.month-1)  # greater than gt
        elif whatSort2 == "past24":
            p = p.filter(date__day__gte=now.day - 1)  # greater than gt

        page = request.GET.get("page")
        p = Paginator(p, 5)
        cat_thread = p.get_page(page)
        return render(request, "categories.html", {"cats": cats, "cat_threads": cat_thread, "sw1": whatSort1, "sw2": whatSort2})
    return redirect("home")


@login_required(login_url="login")
def search_result(request):
    if request.method == "POST":

        # page functionality has been implemented inside the html file, but rn sending the context from here is shows there's some error, since there's only one page coming.
        searched = request.POST["searched"]
        result = Thread.objects.filter(title__contains=searched).annotate(
            like_count=(Count('liked')-Count('dislike'))).order_by('-like_count')
        # p = Paginator(result, 1) #TODO changable
        # page = request.GET.get("page")
        # cat_thread = p.get_page(page)
        return render(request, "search/search_result.html", {"searched": searched, "cat_threads": result})
    return render(request, "search/search_result.html", {})


@login_required(login_url="login")
def watch_thread(request):
    try:
        user = request.user
        if request.method == "POST":
            thread_id = request.POST.get("thread_id")
            # print(request.method)
            thread_obj = Thread.objects.get(id=thread_id)

            if user in thread_obj.watched.all():
                thread_obj.watched.remove(user)
            else:
                thread_obj.watched.add(user)
            try:
                watch, created = WatchThread.objects.get_or_create(
                    user=user, thread_id=thread_id)
            except Exception as e:
                print(e)

            if not created:
                if watch.value == 'Watch':
                    watch.value = "Unwatch"
                else:
                    watch.value = "Watch"
                watch.save()
            if user not in thread_obj.watched.all():
                watch.delete()
        return redirect("thread_detail", pk=thread_id)
    except:
        return HttpResponseRedirect(reverse_lazy("thread_detail", kwargs={"pk": thread_id}))


@login_required(login_url="login")
def CommentDelete(request):
    user = request.user
    thread_id = request.POST.get("thread_id")
    comment_by_user = Comment.objects.filter(author=user, thread__id=thread_id)
    comment_by_user.delete()
    return redirect("thread_detail", pk=thread_id)
