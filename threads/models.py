from django.conf import settings
from django.db import models
from django.urls import reverse
from accounts.models import CustomUser
from notis.models import Notification


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("thread_detail", kwargs={"pk": self.pk})


class Thread(models.Model):  # model for our threads feature
    title = models.CharField(max_length=255)
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    thread_image = models.ImageField(
        null=True, blank=True, upload_to="images/")
    liked = models.ManyToManyField(
        settings.AUTH_USER_MODEL, default=None, blank=True, related_name="liked")
    dislike = models.ManyToManyField(
        settings.AUTH_USER_MODEL, default=None, blank=True, related_name="disliked")
    category = models.CharField(max_length=255, default="General")
    watched = models.ManyToManyField(
        settings.AUTH_USER_MODEL, default=None, blank=True, related_name="watched")
    # reversing the listview

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.title

    @property  # added so it is treated as a field
    def num_likes(self):
        return self.liked.all().count()

    @property
    def num_dislikes(self):
        return self.dislike.all().count()

    @property
    def num_watches(self):
        return self.watched.all().count()

    def get_absolute_url(self):
        return reverse("thread_detail", kwargs={"pk": self.pk})


class Comment(models.Model):  # the model for our comments section
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    comment = models.CharField(max_length=5000)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.comment

    def get_absolute_url(self):
        return reverse("thread_detail", kwargs={"pk": self.pk})

    def user_commented_thread(sender, instance, *args, **kwargs):
        comment = instance
        thread = comment.thread
        sender = comment.author
        ref = WatchThread.objects.filter(thread=thread)
        text_preview = f"{comment.author} commented on '{ comment.thread }'!"

        notify = Notification(thread=thread, sender=sender, reciever=thread.author,
                              text_preview=text_preview, notification_type=2)
        notify.save()


# the choices the user will have, to like and unlike some post
LIKE_CHOICES = (
    ('Like', 'Like'),
    ('Unlike', 'Unlike'),
)


class Likes(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
    )
    value = models.CharField(choices=LIKE_CHOICES,
                             default="Like", max_length=10)

    # the notifications
    def user_liked_thread(sender, instance, *args, **kwargs):

        like = instance
        if like.value == "Like":
            thread = like.thread
            sender = like.user
            text_preview = f"{like.user} liked your thread, { like.thread }!"

            notify = Notification(thread=thread, sender=sender, reciever=thread.author,
                                  text_preview=text_preview, notification_type=1)
            notify.save()

    def __str__(self):
        return str(self.thread)


# not sure if actually required, delete if not
DISLIKE_CHOICES = (
    ("Dislike", "Dislike"),
    ("Undo", "Undo")
)


class Dislikes(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
    )
    value = models.CharField(choices=DISLIKE_CHOICES,
                             default="Dislike", max_length=10)

    def __str__(self):
        return str(self.thread)


class Profile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        null=True,
        on_delete=models.CASCADE,
    )
    bio = models.TextField()
    pfp = models.ImageField(null=True, blank=True, upload_to="images/profile/")

    def __str__(self):
        return str(self.user)

    def get_absolute_url(self):
        return reverse("user_profile", kwargs={"pk": self.pk})


WATCH_CHOICES = (
    ("Watch", "Watch"),
    ("Unwatch", "Unwatch"),
)


class WatchThread(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
    )
    value = models.CharField(choices=WATCH_CHOICES,
                             default="Watch", max_length=10)

    def user_watch_thread(sender, instance, *args, **kwargs):
        watch = instance
        if watch.value == "Watch":
            thread = watch.thread
            sender = watch.user
            text_preview = f"{watch.user} has watched your thread, { watch.thread }!"

            notify = Notification(thread=thread, sender=sender, reciever=thread.author,
                                  text_preview=text_preview, notification_type=3)
            notify.save()

    def __str__(self):
        return self.thread.title


# signals for likes:
models.signals.post_save.connect(Likes.user_liked_thread, sender=Likes)
# signals for the comments
models.signals.post_save.connect(Comment.user_commented_thread, sender=Comment)
# signals for the watches
models.signals.post_save.connect(
    WatchThread.user_watch_thread, sender=WatchThread)
