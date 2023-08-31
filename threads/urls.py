from django.urls import path

from .views import (
    ThreadDetailView,
    ThreadEditView,
    ThreadDeleteView,
    ThreadCreateView,
    thread_view,
    like_thread,
    dislike_thread,
    # CategoryView,
    search_result,
    watch_thread,
    CommentDelete,
    SortedCategoryView,
)

urlpatterns = [
    path("<int:pk>/", ThreadDetailView.as_view(), name="thread_detail"),
    path("<int:pk>/edit/", ThreadEditView.as_view(), name="thread_edit"),
    path("<int:pk>/delete/", ThreadDeleteView.as_view(), name="thread_delete"),
    path("delete_comment/", CommentDelete, name="delete_comment"),
    path("new/", ThreadCreateView.as_view(), name="thread_new"),
    path("like/", like_thread, name="like_thread"),
    path("dislike/", dislike_thread, name="dislike_thread"),
    path("watch/",  watch_thread, name="watch"),
    # path("category/<str:cats>/", CategoryView, name="category"),
    path("category/<str:cats>/<str:whatSort1>/<str:whatSort2>",
         SortedCategoryView, name="sortCategory"),
    path("search_result/", search_result, name="search_result"),
    path("", thread_view, name="thread_list"),
]
