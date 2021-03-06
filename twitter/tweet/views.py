import datetime
import itertools

from bootstrap_modal_forms.mixins import PassRequestMixin
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView
from django.db.models import Q, Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tweet.forms import *
from tweet.models import *


def date_generator():
    from_date = datetime.datetime.today()
    while True:
        yield from_date
        from_date = from_date - datetime.timedelta(days=1)


class LoginUserView(View):
    def get(self, request):
        form = LoginUserForm()
        return render(request, "tweet/login.html", locals())

    def post(self, request):
        form = LoginUserForm(request.POST)
        if form.is_valid():
            email = request.POST.get("email")
            passwd = request.POST.get("passwd")
            user = authenticate(email=email, password=passwd)
            if user:
                login(request, user)
                return redirect("add_message")
            form.add_error("email", "Zły login albo hasło")
            message = "zły login lub hasło"
        return render(request, "tweet/login.html", locals())


class LogoutUserView(View):
    def get(self, request):
        logout(request)
        return redirect("login_user")


class CreateUserView(View):
    def get(self, request):
        form = CreateUserForm()
        return render(request, "tweet/create_user.html", locals())

    def post(self, request):
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Konto zostało utworzone')
            user = authenticate(email=form.cleaned_data['email'], password=form.cleaned_data['password1'])
            if user:
                login(request, user)
            return redirect('add_message')
        return render(request, "tweet/create_user.html", locals())


class AddMessageView(LoginRequiredMixin, View):

    def get(self, request):
        form = AddMessageForm()
        messages = Message.objects.all().order_by("-creation_date")
        comments = Comment.objects.all().order_by("creation_date")
        users = User.objects.all().order_by("username")
        likes = []
        for msg in messages:
            user_likes_this = msg.like_set.filter(user=request.user)
            for like in user_likes_this:
                likes.append(like.message)
        return render(request, "tweet/posts_list.html", locals())

    def post(self, request):
        messages = Message.objects.all()
        form = AddMessageForm(request.POST)
        if form.is_valid():
            message = Message()
            user = request.user
            message.created_by = user
            message.content = request.POST.get("content")
            message.creation_date = request.POST.get("creation_date")
            message.save()
            return redirect("add_message")
        return render(request, "tweet/posts_list.html", locals())


class MarkMessageView(LoginRequiredMixin, View):
    def get(self, request, id):
        message = Message.objects.get(pk=id)
        if not message.is_read:
            message.is_read = True
        else:
            message.is_read = False
        message.save()
        return redirect("add_message")


class LikeMessageView(LoginRequiredMixin, View):
    def get(self, request, msg_id):
        to_like = Message.objects.get(pk=msg_id)
        author = to_like.created_by
        if author != request.user:
            Like.objects.get_or_create(user=request.user, message_id=msg_id)
        return redirect("add_message")


class AddCommentView(LoginRequiredMixin, PassRequestMixin, SuccessMessageMixin, CreateView):
    template_name = 'tweet/add_comment.html'
    form_class = AddCommentForm
    success_url = reverse_lazy('add_message')

    def form_valid(self, form):
        message = Message.objects.get(pk=self.kwargs['message_id'])
        form.instance.created_by = self.request.user
        form.instance.message = message
        return super(AddCommentView, self).form_valid(form)


class GetUserInfoView(LoginRequiredMixin, View):
    def get(self, request, user_id):
        form = AddPvrMsgForm()
        about_user = User.objects.get(pk=user_id)
        messages = Message.objects.filter(created_by=about_user).count()
        pvr_messages = PersonalMessage.objects.filter(Q(from_user=user_id) | Q(to_user=user_id)).order_by(
            "-creation_date")
        return render(request, "tweet/user_info.html", locals())

    def post(self, request, user_id):
        form = AddPvrMsgForm(request.POST)
        about_user = User.objects.get(pk=user_id)
        messages = Message.objects.filter(created_by=about_user).count()
        pvr_messages = PersonalMessage.objects.filter(Q(from_user=user_id) | Q(to_user=user_id))
        if form.is_valid():
            pvr_msg = PersonalMessage()
            from_user = request.user
            pvr_msg.content = request.POST.get("content")
            pvr_msg.creation_date = request.POST.get("creation_date")
            pvr_msg.from_user = from_user
            pvr_msg.to_user = about_user
            pvr_msg.save()
            return redirect("user_info", about_user.id)
        return render(request, "tweet/user_info.html", locals())


class GetUserProfileView(LoginRequiredMixin, View):
    def get(self, request, user_id):
        user_profile = User.objects.get(pk=user_id)
        msg = Message.objects.filter(created_by=user_profile).count()
        msgs = Message.objects.filter(created_by=user_profile).order_by("-creation_date")
        likes = Like.objects.filter(user=user_id)
        return render(request, "tweet/user_profile.html", locals())


class ChangeUserPasswordView(LoginRequiredMixin, View):
    def get(self, request):
        form = PasswordChangeForm(request.user)
        return render(request, 'tweet/change_password.html', locals())

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("user_profile", user.id)
        else:
            messages.error(request, "An error occured. Try again.")
        return render(request, "tweet/change_password.html", locals())


class EditUserProfileView(LoginRequiredMixin, View):
    def get(self, request, user_id):
        edit_user = User.objects.get(pk=user_id)
        form = EditUserForm(instance=edit_user)
        return render(request, "tweet/edit_profile.html", locals())

    def post(self, request, user_id):
        edit_user = User.objects.get(pk=user_id)
        form = EditUserForm(request.POST, request.FILES, instance=edit_user)
        if form.is_valid():
            edit_user.username = request.POST.get("username")
            edit_user.email = request.POST.get("email")
            edit_user.first_name = request.POST.get("first_name")
            edit_user.last_name = request.POST.get("last_name")
            edit_user.image = request.FILES.get('image')
            edit_user.twitter = request.POST.get("twitter")
            edit_user.google = request.POST.get("google")
            edit_user.facebook = request.POST.get("facebook")
            edit_user.behance = request.POST.get("behance")
            edit_user.save(
                update_fields=["username", "email", "first_name", "last_name", "image", "twitter", "google", "facebook",
                               "behance"])
            messages.success(request, "Your profile was successfully updated!")
            return redirect("user_profile", edit_user.id)
        else:
            messages.error(request, "An error occured. Try again.")
        return render(request, "tweet/edit_profile.html", locals())


class DataForAllMessagesChartsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        labels = []
        all_messages = []
        user_messages = []
        dates = itertools.islice(date_generator(), 7)
        for date in dates:
            labels.append(date.strftime('%Y-%m-%d'))
            all_messages.append(Message.objects.filter(creation_date__day=date.day, creation_date__month=date.month,
                                                        creation_date__year=date.year).count())
            user_messages.append(Message.objects.filter(creation_date__day=date.day, creation_date__month=date.month,
                                                        creation_date__year=date.year,created_by=request.user).count())
        labels.reverse()
        all_messages.reverse()
        user_messages.reverse()
        data = {
            "labels": labels,
            "all": all_messages,
            "user": user_messages
        }

        print(request.user)
        return Response(data)
