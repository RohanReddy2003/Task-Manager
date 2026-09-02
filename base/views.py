# from django.shortcuts import render, redirect
# from django.views.generic.list import ListView
# from django.views.generic.detail import DetailView
# from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
# from django.urls import reverse_lazy

# from django.contrib.auth.views import LoginView
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth import login

# # Imports for Reordering Feature
# from django.views import View
# from django.shortcuts import redirect
# from django.db import transaction

# from .models import Task
# from .forms import PositionForm


# class CustomLoginView(LoginView):
#     template_name = 'base/login.html'
#     fields = '__all__'
#     redirect_authenticated_user = True

#     def get_success_url(self):
#         return reverse_lazy('tasks')


# class RegisterPage(FormView):
#     template_name = 'base/register.html'
#     form_class = UserCreationForm
#     redirect_authenticated_user = True
#     success_url = reverse_lazy('tasks')

#     def form_valid(self, form):
#         user = form.save()
#         if user is not None:
#             login(self.request, user)
#         return super(RegisterPage, self).form_valid(form)

#     def get(self, *args, **kwargs):
#         if self.request.user.is_authenticated:
#             return redirect('tasks')
#         return super(RegisterPage, self).get(*args, **kwargs)


# class TaskList(LoginRequiredMixin, ListView):
#     model = Task
#     context_object_name = 'tasks'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['tasks'] = context['tasks'].filter(user=self.request.user)
#         context['count'] = context['tasks'].filter(complete=False).count()

#         search_input = self.request.GET.get('search-area') or ''
#         if search_input:
#             context['tasks'] = context['tasks'].filter(
#                 title__contains=search_input)

#         context['search_input'] = search_input

#         return context


# class TaskDetail(LoginRequiredMixin, DetailView):
#     model = Task
#     context_object_name = 'task'
#     template_name = 'base/task.html'


# class TaskCreate(LoginRequiredMixin, CreateView):
#     model = Task
#     fields = ['title', 'description', 'complete']
#     success_url = reverse_lazy('tasks')

#     def form_valid(self, form):
#         form.instance.user = self.request.user
#         return super(TaskCreate, self).form_valid(form)


# class TaskUpdate(LoginRequiredMixin, UpdateView):
#     model = Task
#     fields = ['title', 'description', 'complete']
#     success_url = reverse_lazy('tasks')


# class DeleteView(LoginRequiredMixin, DeleteView):
#     model = Task
#     context_object_name = 'task'
#     success_url = reverse_lazy('tasks')
#     def get_queryset(self):
#         owner = self.request.user
#         return self.model.objects.filter(user=owner)

# class TaskReorder(View):
#     def post(self, request):
#         form = PositionForm(request.POST)

#         if form.is_valid():
#             positionList = form.cleaned_data["position"].split(',')

#             with transaction.atomic():
#                 self.request.user.set_task_order(positionList)

#         return redirect(reverse_lazy('tasks'))

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import (
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)
from django.urls import reverse_lazy
from django.contrib import messages

from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from django.views import View
from django.db import transaction
from django.db.models import Q, Count

from .models import Task
from .forms import PositionForm


# ============================================================
# LOGIN
# ============================================================

class CustomLoginView(LoginView):
    template_name = 'base/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('tasks')

    def form_valid(self, form):
        messages.success(
            self.request,
            'Welcome back! You have successfully logged in.'
        )
        return super().form_valid(form)


# ============================================================
# REGISTRATION
# ============================================================

class RegisterPage(FormView):
    template_name = 'base/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('tasks')

    def form_valid(self, form):
        user = form.save()

        if user is not None:
            login(self.request, user)

            messages.success(
                self.request,
                'Your account has been created successfully.'
            )

        return super(RegisterPage, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('tasks')

        return super(RegisterPage, self).get(*args, **kwargs)


# ============================================================
# TASK LIST
# ============================================================

class TaskList(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = 'tasks'
    template_name = 'base/task_list.html'
    paginate_by = 20

    def get_queryset(self):
        """
        Return only tasks belonging to the currently
        authenticated user.
        """

        queryset = Task.objects.filter(
            user=self.request.user
        )

        search_input = self.request.GET.get(
            'search-area',
            ''
        ).strip()

        status = self.request.GET.get(
            'status',
            ''
        ).strip()

        sort_by = self.request.GET.get(
            'sort',
            ''
        ).strip()

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        if search_input:
            queryset = queryset.filter(
                Q(title__icontains=search_input) |
                Q(description__icontains=search_input)
            )

        # ----------------------------------------------------
        # Status filter
        # ----------------------------------------------------

        if status == 'completed':
            queryset = queryset.filter(
                complete=True
            )

        elif status == 'pending':
            queryset = queryset.filter(
                complete=False
            )

        # ----------------------------------------------------
        # Sorting
        # ----------------------------------------------------

        if sort_by == 'title':
            queryset = queryset.order_by('title')

        elif sort_by == 'title_desc':
            queryset = queryset.order_by('-title')

        elif sort_by == 'newest':
            queryset = queryset.order_by('-id')

        elif sort_by == 'oldest':
            queryset = queryset.order_by('id')

        elif sort_by == 'completed':
            queryset = queryset.order_by('-complete')

        else:
            queryset = queryset.order_by('id')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_tasks = Task.objects.filter(
            user=self.request.user
        )

        # ----------------------------------------------------
        # Basic statistics
        # ----------------------------------------------------

        total_tasks = user_tasks.count()

        completed_tasks = user_tasks.filter(
            complete=True
        ).count()

        pending_tasks = user_tasks.filter(
            complete=False
        ).count()

        context['total_tasks'] = total_tasks
        context['completed_tasks'] = completed_tasks
        context['pending_tasks'] = pending_tasks

        # ----------------------------------------------------
        # Completion percentage
        # ----------------------------------------------------

        if total_tasks > 0:
            completion_percentage = int(
                (completed_tasks / total_tasks) * 100
            )
        else:
            completion_percentage = 0

        context['completion_percentage'] = completion_percentage

        # ----------------------------------------------------
        # Search values
        # ----------------------------------------------------

        context['search_input'] = self.request.GET.get(
            'search-area',
            ''
        )

        context['current_status'] = self.request.GET.get(
            'status',
            ''
        )

        context['current_sort'] = self.request.GET.get(
            'sort',
            ''
        )

        # ----------------------------------------------------
        # Extra task information
        # ----------------------------------------------------

        context['has_tasks'] = total_tasks > 0

        context['has_completed_tasks'] = (
            completed_tasks > 0
        )

        context['has_pending_tasks'] = (
            pending_tasks > 0
        )

        # ----------------------------------------------------
        # Dashboard message
        # ----------------------------------------------------

        if total_tasks == 0:
            context['dashboard_message'] = (
                'You currently have no tasks.'
            )

        elif pending_tasks == 0:
            context['dashboard_message'] = (
                'Great job! You completed all your tasks.'
            )

        elif completed_tasks == 0:
            context['dashboard_message'] = (
                'You have some tasks waiting for you.'
            )

        else:
            context['dashboard_message'] = (
                'Keep going! You are making progress.'
            )

        return context


# ============================================================
# TASK DETAIL
# ============================================================

class TaskDetail(LoginRequiredMixin, DetailView):
    model = Task
    context_object_name = 'task'
    template_name = 'base/task.html'

    def get_queryset(self):
        """
        Prevent users from viewing another user's task.
        """

        return Task.objects.filter(
            user=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        task = self.object

        context['is_completed'] = task.complete

        if task.complete:
            context['task_status'] = 'Completed'
        else:
            context['task_status'] = 'Pending'

        return context


# ============================================================
# CREATE TASK
# ============================================================

class TaskCreate(LoginRequiredMixin, CreateView):
    model = Task

    fields = [
        'title',
        'description',
        'complete',
    ]

    template_name = 'base/task_form.html'
    success_url = reverse_lazy('tasks')

    def form_valid(self, form):
        form.instance.user = self.request.user

        messages.success(
            self.request,
            'Task created successfully.'
        )

        return super(TaskCreate, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'There was a problem creating the task.'
        )

        return super(TaskCreate, self).form_invalid(form)


# ============================================================
# UPDATE TASK
# ============================================================

class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task

    fields = [
        'title',
        'description',
        'complete',
    ]

    template_name = 'base/task_form.html'
    success_url = reverse_lazy('tasks')

    def get_queryset(self):
        """
        Users can update only their own tasks.
        """

        return Task.objects.filter(
            user=self.request.user
        )

    def form_valid(self, form):
        messages.success(
            self.request,
            'Task updated successfully.'
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Unable to update the task.'
        )

        return super().form_invalid(form)


# ============================================================
# DELETE TASK
# ============================================================

class DeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    context_object_name = 'task'
    template_name = 'base/task_confirm_delete.html'
    success_url = reverse_lazy('tasks')

    def get_queryset(self):
        owner = self.request.user

        return self.model.objects.filter(
            user=owner
        )

    def delete(self, request, *args, **kwargs):
        messages.success(
            request,
            'Task deleted successfully.'
        )

        return super().delete(
            request,
            *args,
            **kwargs
        )


# ============================================================
# TOGGLE TASK
# ============================================================

class TaskToggleComplete(LoginRequiredMixin, View):

    def post(self, request, pk):
        task = get_object_or_404(
            Task,
            pk=pk,
            user=request.user
        )

        task.complete = not task.complete
        task.save()

        if task.complete:
            messages.success(
                request,
                f'"{task.title}" marked as complete.'
            )
        else:
            messages.info(
                request,
                f'"{task.title}" marked as pending.'
            )

        return redirect('tasks')


# ============================================================
# DUPLICATE TASK
# ============================================================

class TaskDuplicate(LoginRequiredMixin, View):

    def post(self, request, pk):
        original_task = get_object_or_404(
            Task,
            pk=pk,
            user=request.user
        )

        new_task = Task.objects.create(
            user=request.user,
            title=f'{original_task.title} (Copy)',
            description=original_task.description,
            complete=False,
        )

        messages.success(
            request,
            f'Task "{new_task.title}" was created.'
        )

        return redirect('tasks')


# ============================================================
# COMPLETE ALL TASKS
# ============================================================

class CompleteAllTasks(LoginRequiredMixin, View):

    def post(self, request):
        updated_count = Task.objects.filter(
            user=request.user,
            complete=False
        ).update(
            complete=True
        )

        messages.success(
            request,
            f'{updated_count} task(s) marked as complete.'
        )

        return redirect('tasks')


# ============================================================
# REOPEN ALL TASKS
# ============================================================

class ReopenAllTasks(LoginRequiredMixin, View):

    def post(self, request):
        updated_count = Task.objects.filter(
            user=request.user,
            complete=True
        ).update(
            complete=False
        )

        messages.info(
            request,
            f'{updated_count} task(s) reopened.'
        )

        return redirect('tasks')


# ============================================================
# DELETE COMPLETED TASKS
# ============================================================

class DeleteCompletedTasks(LoginRequiredMixin, View):

    def post(self, request):

        deleted_count, _ = Task.objects.filter(
            user=request.user,
            complete=True
        ).delete()

        messages.success(
            request,
            f'{deleted_count} completed task(s) deleted.'
        )

        return redirect('tasks')


# ============================================================
# TASK REORDER
# ============================================================

class TaskReorder(LoginRequiredMixin, View):

    def post(self, request):
        form = PositionForm(
            request.POST
        )

        if form.is_valid():

            position_list = (
                form.cleaned_data[
                    "position"
                ].split(',')
            )

            # Remove empty values
            position_list = [
                position.strip()
                for position in position_list
                if position.strip()
            ]

            with transaction.atomic():

                request.user.set_task_order(
                    position_list
                )

            messages.success(
                request,
                'Task order updated.'
            )

        else:
            messages.error(
                request,
                'Unable to update task order.'
            )

        return redirect(
            reverse_lazy('tasks')
        )


# ============================================================
# TASK SEARCH
# ============================================================

class TaskSearch(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = 'tasks'
    template_name = 'base/task_search.html'

    def get_queryset(self):

        query = self.request.GET.get(
            'q',
            ''
        ).strip()

        queryset = Task.objects.filter(
            user=self.request.user
        )

        if not query:
            return queryset

        return queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        context['query'] = self.request.GET.get(
            'q',
            ''
        )

        context['result_count'] = (
            context['tasks'].count()
        )

        return context


# ============================================================
# TASK DASHBOARD
# ============================================================

class TaskDashboard(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'base/dashboard.html'
    context_object_name = 'tasks'

    def get_queryset(self):

        return Task.objects.filter(
            user=self.request.user
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        tasks = self.get_queryset()

        context['total'] = tasks.count()

        context['completed'] = tasks.filter(
            complete=True
        ).count()

        context['pending'] = tasks.filter(
            complete=False
        ).count()

        context['recent_tasks'] = tasks.order_by(
            '-id'
        )[:5]

        context['completed_tasks'] = tasks.filter(
            complete=True
        ).order_by('-id')[:5]

        context['pending_tasks'] = tasks.filter(
            complete=False
        ).order_by('id')[:5]

        return context


# ============================================================
# QUICK ADD TASK
# ============================================================

class QuickAddTask(LoginRequiredMixin, View):

    def post(self, request):

        title = request.POST.get(
            'title',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        if not title:
            messages.error(
                request,
                'Task title cannot be empty.'
            )

            return redirect('tasks')

        Task.objects.create(
            user=request.user,
            title=title,
            description=description,
            complete=False,
        )

        messages.success(
            request,
            'Quick task added successfully.'
        )

        return redirect('tasks')


# ============================================================
# REMOVE EMPTY TASKS
# ============================================================

class RemoveEmptyTasks(LoginRequiredMixin, View):

    def post(self, request):

        empty_tasks = Task.objects.filter(
            user=request.user
        ).filter(
            Q(title__isnull=True) |
            Q(title__exact='')
        )

        count = empty_tasks.count()

        empty_tasks.delete()

        messages.info(
            request,
            f'{count} empty task(s) removed.'
        )

        return redirect('tasks')


# ============================================================
# TASK SUMMARY
# ============================================================

class TaskSummary(LoginRequiredMixin, View):

    def get(self, request):

        tasks = Task.objects.filter(
            user=request.user
        )

        total = tasks.count()

        completed = tasks.filter(
            complete=True
        ).count()

        pending = tasks.filter(
            complete=False
        ).count()

        if total:
            percentage = round(
                completed / total * 100
            )
        else:
            percentage = 0

        context = {
            'total': total,
            'completed': completed,
            'pending': pending,
            'percentage': percentage,
        }

        return render(
            request,
            'base/summary.html',
            context
        )

