from django.shortcuts import render
from .models import *
from applications.globals.models import ExtraInfo
from applications.globals.models import *
from django.db.models import Q
from django.http import Http404
from .forms import EditDetailsForm, EditConfidentialDetailsForm, EditServiceBookForm, NewUserForm, AddExtraInfo
from django.contrib import messages
from applications.eis.models import *
from django.http import HttpResponse, HttpResponseRedirect
from applications.establishment.models import *
from applications.establishment.views import *
from applications.eis.models import *
from applications.globals.models import ExtraInfo, HoldsDesignation, DepartmentInfo
from html import escape
from io import BytesIO

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import (get_object_or_404, redirect, render,
                              render)


def edit_employee_details(request, id):
    """ Views for edit details"""
    template = 'hr2Module/editDetails.html'

    try:
        employee = ExtraInfo.objects.get(pk=id)
    except:
        raise Http404("Post does not exist")

    if request.method == "POST":
        form = EditDetailsForm(request.POST, request.FILES)
        conf_form = EditConfidentialDetailsForm(request.POST, request.FILES)

        if form.is_valid() and conf_form.is_valid():
            form.save()
            conf_form.save()
            try:
                edit_employee = ExtraInfo.objects.get(pk=id)
                edit_employee.user_status = "PRESENT"
                edit_employee.save()

            except:
                pass
            messages.success(request, "Employee details edited successfully")
        else:

            messages.warning(request, "Error in submitting form")
            pass

    form = EditDetailsForm(initial={'extra_info': employee.id})
    conf_form = EditConfidentialDetailsForm(initial={'extra_info': employee})
    context = {'form': form, 'confForm': conf_form, 'employee': employee
               }

    return render(request, template, context)


def hr_admin(request):
    """ Views for HR2 Admin page """

    user = request.user
    # extra_info = ExtraInfo.objects.select_related().get(user=user)
    designat = HoldsDesignation.objects.select_related().get(user=user)

    if designat.designation.name == 'hradmin':
        template = 'hr2Module/hradmin.html'
        # searched employee
        query = request.GET.get('search')
        if(request.method == "GET"):
            if(query != None):
                emp = ExtraInfo.objects.filter(
                    Q(user__first_name__icontains=query) |
                    Q(user__last_name__icontains=query) |
                    Q(id__icontains=query)
                ).distinct()
                emp = emp.filter(user_type="faculty")
            else:
                emp = ExtraInfo.objects.all()
                emp = emp.filter(user_type="faculty")
        else:
            emp = ExtraInfo.objects.all()
            emp = emp.filter(user_type="faculty")
        emp_present = emp.filter(user_status="PRESENT")
        emp_new = emp.filter(user_status="NEW")
        context = {'emps': emp, "emp_present": emp_present, "emp_new": emp_new}
        return render(request, template, context)
    else:
        return HttpResponse('Unauthorized', status=401)


def service_book(request):
    """
    Views for service book page
    """
    user = request.user
    extra_info = ExtraInfo.objects.select_related().get(user=user)

    lien_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="LIEN").order_by('-start_date')
    deputation_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="DEPUTATION").order_by('-start_date')
    other_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="OTHER").order_by('-start_date')
    appraisal_form = EmpAppraisalForm.objects.filter(
        extra_info=extra_info).order_by('-year')
    pf = extra_info.id
    work_assignemnt = WorkAssignemnt.objects.filter(
        extra_info_id=pf).order_by('-start_date')

    emp_projects = emp_research_projects.objects.filter(
        pf_no=pf).order_by('-start_date')
    visits = emp_visits.objects.filter(pf_no=pf).order_by('-entry_date')
    conferences = emp_confrence_organised.objects.filter(
        pf_no=pf).order_by('-date_entry')
    template = 'hr2Module/servicebook.html'
    awards = emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry')
    thesis = emp_mtechphd_thesis.objects.filter(
        pf_no=pf).order_by('-date_entry')
    context = {'lienServiceBooks': lien_service_book, 'deputationServiceBooks': deputation_service_book, 'otherServiceBooks': other_service_book,
               'appraisalForm': appraisal_form,
               'empproject': emp_projects,
               'visits': visits,
               'conferences': conferences,
               'awards': awards,
               'thesis': thesis,
               'extrainfo': extra_info,
               'workassignment': work_assignemnt
               }

    return HttpResponseRedirect("/eis/profile/")
    # return render(request, template, context)


def view_employee_details(request, id):
    """ Views for edit details"""
    extra_info = ExtraInfo.objects.get(pk=id)
    lien_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="LIEN").order_by('-start_date')
    deputation_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="DEPUTATION").order_by('-start_date')
    other_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="OTHER").order_by('-start_date')
    appraisal_form = EmpAppraisalForm.objects.filter(
        extra_info=extra_info).order_by('-year')
    pf = extra_info.id
    work_assignemnt = WorkAssignemnt.objects.filter(
        extra_info_id=pf).order_by('-start_date')

    emp_projects = emp_research_projects.objects.filter(
        pf_no=pf).order_by('-start_date')
    visits = emp_visits.objects.filter(pf_no=pf).order_by('-entry_date')
    conferences = emp_confrence_organised.objects.filter(
        pf_no=pf).order_by('-date_entry')
    awards = emp_achievement.objects.filter(pf_no=pf).order_by('-date_entry')
    thesis = emp_mtechphd_thesis.objects.filter(
        pf_no=pf).order_by('-date_entry')

    response = {}
    # Check if establishment variables exist, if not create some fields or ask for them
    response.update(initial_checks(request))
    if is_eligible(request) and request.method == "POST":
        handle_appraisal(request)

    if is_eligible(request):
        response.update(generate_appraisal_lists(request))

    # If user has designation "HOD"
    if is_hod(request):
        response.update(generate_appraisal_lists_hod(request))

    # If user has designation "Director"
    if is_director(request):
        response.update(generate_appraisal_lists_director(request))

    response.update({'cpda': False, 'ltc': False,
                     'appraisal': True, 'leave': False})

    template = 'hr2Module/viewdetails.html'
    context = {'lienServiceBooks': lien_service_book, 'deputationServiceBooks': deputation_service_book, 'otherServiceBooks': other_service_book, 'user': extra_info.user, 'extrainfo': extra_info,
               'appraisalForm': appraisal_form,
               'empproject': emp_projects,
               'visits': visits,
               'conferences': conferences,
               'awards': awards,
               'thesis': thesis,
               'workassignment': work_assignemnt

               }
    context.update(response)

    return render(request, template, context)


def edit_employee_servicebook(request, id):
    """ Views for edit Service Book details"""
    template = 'hr2Module/editServiceBook.html'

    try:
        employee = ExtraInfo.objects.get(pk=id)
    except:
        raise Http404("Post does not exist")

    if request.method == "POST":
        form = EditServiceBookForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(
                request, "Employee Service Book details edited successfully")
        else:
            messages.warning(request, "Error in submitting form")
            pass

    form = EditServiceBookForm(initial={'extra_info': employee.id})
    context = {'form': form, 'employee': employee
               }

    return render(request, template, context)


def administrative_profile(request, username=None):
    user = get_object_or_404(
        User, username=username) if username else request.user
    extra_info = get_object_or_404(ExtraInfo, user=user)
    if extra_info.user_type != 'faculty' and extra_info.user_type != 'staff':
        return redirect('/')
    pf = extra_info.id

    lien_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="LIEN").order_by('-start_date')
    deputation_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="DEPUTATION").order_by('-start_date')
    other_service_book = ForeignService.objects.filter(
        extra_info=extra_info).filter(service_type="OTHER").order_by('-start_date')

    response = {}

    response.update(initial_checks(request))
    if is_eligible(request) and request.method == "POST":
        handle_appraisal(request)

    if is_eligible(request):
        response.update(generate_appraisal_lists(request))

    # If user has designation "HOD"
    if is_hod(request):
        response.update(generate_appraisal_lists_hod(request))

    # If user has designation "Director"
    if is_director(request):
        response.update(generate_appraisal_lists_director(request))

    response.update({'cpda': False, 'ltc': False,
                     'appraisal': True, 'leave': False})
    work_assignemnt = WorkAssignemnt.objects.filter(
        extra_info_id=pf).order_by('-start_date')

    context = {'user': user,
               'pf': pf,
               'lienServiceBooks': lien_service_book, 'deputationServiceBooks': deputation_service_book, 'otherServiceBooks': other_service_book,
               'extrainfo': extra_info,
               'workassignment': work_assignemnt
               }

    context.update(response)
    template = 'hr2Module/dashboard_hr.html'
    return render(request, template, context)


def add_new_user(request):
    """ Views for edit Service Book details"""
    template = 'hr2Module/add_new_employee.html'

    if request.method == "POST":
        form_newuser = NewUserForm(request.POST)
        extrainfo_form = AddExtraInfo(request.POST)
        if form.is_valid():
            user = form_newuser.save()
            messages.success(request, "New User added Successfully")
        elif not form_newuser.is_valid:
            print(form_newuser.errors)
            messages.error(request,"Some error occured please try again later")

        elif extrainfo_form.is_valid():
            extrainfo_form.save()
            messages.success(request, "Extra info of user saved successfully")
        elif not extrainfo_form.is_valid:
        
            print(extrainfo_form.errors)
            messages.error(request,"Some error occured please try again later")

    form_newuser = NewUserForm
    extrainfo_form = AddExtraInfo

    try:
        employee = ExtraInfo.objects.all().first()
    except:
        raise Http404("Post does not exist")

    # if request.method == "POST":
    #     form = EditServiceBookForm(request.POST, request.FILES)

    #     if form.is_valid():
    #         form.save()
    #         messages.success(
    #             request, "Employee Service Book details edited successfully")
    #     else:
    #         messages.warning(request, "Error in submitting form")
    #         pass

    # form = EditServiceBookForm(initial={'extra_info': employee.id})
    context = {'employee': employee, "register_form": form_newuser, "extrainfo_form": extrainfo_form
               }

    return render(request, template, context)
