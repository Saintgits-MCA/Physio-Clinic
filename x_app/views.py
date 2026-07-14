from datetime import date, datetime,time,timedelta
import json
from urllib.parse import urlencode
from django.contrib.auth import logout # type: ignore
import os
from django.db import transaction
from decimal import Decimal
from django.db.models import F, ExpressionWrapper, DecimalField # type: ignore
from django.db.models.functions import Coalesce # type: ignore
from num2words import num2words # type: ignore
from django.db import transaction # type: ignore
from django.db.models import Count # type: ignore
from django.db.models import Sum # type: ignore
from django.utils.dateparse import parse_date  # type: ignore
from django.http import JsonResponse, HttpResponse # type: ignore
from django.template.loader import render_to_string # type: ignore
from django.db import DataError # type: ignore
from django.shortcuts import get_object_or_404, render,redirect # type: ignore
from django.urls import reverse# type: ignore
from django.views.decorators.csrf import csrf_exempt# type: ignore
from .utils.permissions import * # type: ignore
from x_app.models import *# type: ignore
from django.utils.safestring import mark_safe# type: ignore
from django.contrib import messages # type: ignore
from django.core.paginator import Paginator # type: ignore
from django.http import JsonResponse,Http404 # type: ignore
from django.template.loader import get_template # type: ignore
from xhtml2pdf import pisa # type: ignore
from django.db.models import Q,F # type: ignore
from django.contrib.auth import authenticate, login as auth_login # type: ignore
from django.db.models import Subquery, OuterRef# type: ignore
from django.db.models.functions import ExtractMonth, ExtractYear# type: ignore



def login(request):
    hospital=Hospital_data.objects.filter(id=1).first()
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if StaffAllocation.objects.filter(email=email, password=password).exists() and  StaffRegistration.objects.filter(email=email).exists():
            if StaffAllocation.objects.get(email=email, password=password).password==password:
                messages.success(request, "Login Successful")
                request.session['email'] = StaffAllocation.objects.get(email=email, password=password).email
                request.session['d_email']=email
                request.session['staff_id']=StaffRegistration.objects.get(email=email).id

                return redirect('home')
            else:
                messages.error(request, "Invalid email or password")
        else:
            messages.error(request, "Invalid email or password")
            return redirect('login')
        if not StaffRegistration.objects.filter(email=email).exists():
            messages.error(request,"Invalid Username or Password")

    return render(request, 'login.html',{'hospital':hospital})


def base(request):
    hospital=Hospital_data.objects.first()
    staff_id=request.session.get("staff_id")
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    allocation = StaffAllocation.objects.get(staff=staff_id)
    is_admin = StaffAllocation.objects.filter(
        staff=allocation.staff,
        designation__Designation__iexact="Admin",
        status="active"
    ).exists()
    if not staff_id:
        return redirect('login')
    role_assignments = RoleAssignment.objects.filter(staff_id=staff_id)
    role_ids = role_assignments.values_list('role_id', flat=True)
    # Retrieve menu management entries based on the user's roles
    menu_management_entries = MenuPermission.objects.filter(role_id__in=role_ids)
    staff=StaffRegistration.objects.get(id=staff_id)
    # Prepare menu data to be sent to the template
    menu_data = {}
    for entry in menu_management_entries:
        menu = entry.menu
        heading = menu.category
        if heading not in menu_data:
            menu_data[heading] = [] 
        # Append menu item details to the respective heading
        menu_data[heading].append({
            'menu': menu,
            'url':menu.url,
            'id': entry.id,
            'view': entry.can_view == '1',
            'add': entry.can_add == '1',
            'edit': entry.can_edit == '1',
            'delete': entry.can_delete == '1',
            'is_admin':is_admin,
        })
    staff_id = request.session.get("staff_id")
    current_staff = None
    branch = None
    is_admin = False
    is_doctor = False
    today=timezone.now()
    if staff_id:
        current_staff = get_object_or_404(StaffRegistration, id=staff_id)
        allocation = StaffAllocation.objects.filter(staff=current_staff, status="active").first()
        if allocation:
            branch = allocation.branch
            is_admin = allocation.designation.Designation.lower() == "admin"
            is_doctor = allocation.designation.Designation.lower() == "doctor"

    # Base QuerySet → only today's appointments
    appointments_count = Appointment.objects.select_related('patient', 'doctor', 'branch').filter(
        appointment_date=today,doctor=staff_id
    ).count()
    if is_admin:
       appointments_count = Appointment.objects.select_related('patient', 'doctor', 'branch').filter(
        appointment_date=today
    ).count()
       
    context={"staff_id":staff_id,"staff":staff,"hospital":hospital,'menu_data': menu_data,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),"appointments_count":appointments_count}      
    return render(request, 'base.html',context)

def change_password(request):
    hospital=Hospital_data.objects.first()
    staff_id = request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    if not staff_id:
        return redirect("login")

    try:
        staff = StaffRegistration.objects.get(id=staff_id)
        allocation = StaffAllocation.objects.get(staff=staff)
    except (StaffRegistration.DoesNotExist, StaffAllocation.DoesNotExist):
        messages.error(request, "Invalid staff account. Please log in again.")
        return redirect("staff_login")

    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # 🔹 Check old password
        if allocation.password != current_password:
            messages.error(request, "Current password is incorrect.")
            return redirect("Change_Password")

        # 🔹 Check new vs confirm
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return redirect("Change_Password")

        # 🔹 Prevent reuse
        if allocation.password == new_password:
            messages.warning(request, "New password cannot be the same as the old password.")
            return redirect("Change_Password")

        # 🔹 Save plain password (your setup)
        allocation.password = new_password
        allocation.save()
        messages.success(request, "Password changed successfully.")
        return redirect("home")

    return render(request, "change_password.html",{"hospital":hospital,"staff":staff})

def department(request):
    hospital=Hospital_data.objects.first()
    if request.method == 'POST':
        dept_name = request.POST.get('deptName').strip()
        if dept_name:
            if Department.objects.filter(name__iexact=dept_name).exists():
                messages.warning(request, f"The department '{dept_name}' already exists.")
            else:
                Department.objects.create(name=dept_name)
                messages.success(request, "Department added successfully!")
                return redirect('department')  # Replace with your actual URL name
        else:
            messages.error(request, "Department name is required.")
    return render(request, 'department.html',{"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})


def departmenttable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'

    departments = Department.objects.all()
    if search_query:
        departments = departments.filter(name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(departments, 10)
        page = request.GET.get('page')
        departments = paginator.get_page(page)


    return render(request, 'department-table.html', {
        'departments': departments,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel':is_export_excel,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })

def edit_department(request, id):
    hospital=Hospital_data.objects.first()
    dept = get_object_or_404(Department, id=id)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            dept.name = name
            dept.save()
            messages.success(request, 'Department updated successfully.')
            return redirect('departmenttable')
    return render(request, 'departmentedit.html', {'department': dept,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def delete_department(request, id):
    dept = get_object_or_404(Department, id=id)
    dept.delete()
    messages.success(request, 'Department deleted successfully.')
    return redirect('departmenttable')

def branches(request):
    staff_id=request.session.get('staff_id')        
    hospital=Hospital_data.objects.first()
    if request.method == "POST":
        name = request.POST.get("branchName")
        contact = request.POST.get("branchContact")
        incharge_name = request.POST.get("inchargeName")
        incharge_phone = request.POST.get("inchargePhone")
        address = request.POST.get("branchAddress")
        department_ids = request.POST.getlist("departments")  

            
        if Branch.objects.filter(name__iexact=name).exists():
            messages.warning(request, f"The branch '{name}' already exists.")
        else:
            branch = Branch.objects.create(
            name=name,
            contact=contact,
            incharge_name=incharge_name,
            incharge_phone=incharge_phone,
            address=address
        )

        # Link departments
        Department.objects.filter(id__in=department_ids).update(branch=branch)

        return redirect("branchtable")

    departments = Department.objects.all()
    return render(request, "branches.html", {"departments": departments,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})


def branchtable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'

    branches = Branch.objects.all()
    if search_query:
        branches = branches.filter(name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(branches, 10)
        page = request.GET.get('page')
        branches = paginator.get_page(page)

    return render(request, 'branch-table.html', {
        'branches': branches,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })


def edit_branch(request, id):
    hospital=Hospital_data.objects.first()
    branch = get_object_or_404(Branch, id=id)

    if request.method == "POST":
        branch.name = request.POST.get("name")
        branch.address = request.POST.get("address")
        branch.contact = request.POST.get("contact")
        branch.incharge_name = request.POST.get("incharge_name")
        branch.incharge_phone = request.POST.get("incharge_phone")
        branch.save()

        department_ids = request.POST.getlist("departments")  # multiple departments
        branch.departments.set(department_ids)  # update many-to-many link

        return redirect("branchtable")

    departments = Department.objects.all()
    selected_departments = branch.departments.values_list('id', flat=True)  # pre-selected
    return render(request, "branch_edit.html", {
        "branch": branch,
        "departments": departments,
        "selected_departments": list(selected_departments),"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })


def delete_branch(request, id):
    branch = get_object_or_404(Branch, id=id)
    branch.delete()
    messages.success(request, 'Branch deleted successfully.')
    return redirect('branchtable')

def stafftable(request): 
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    users = StaffRegistration.objects.filter(status="Active")
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'
    staff_id = request.session.get("staff_id")
    branch_id = None
    if staff_id:
        staff_reg = StaffRegistration.objects.get(id=staff_id)
        if staff_reg:
            branch_id = staff_reg.branch
    if branch_id:
        users = StaffRegistration.objects.filter(status="Active")
        branch=Branch.objects.all()
    if search_query:
        users = users.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query))

    if not is_export and not is_export_excel:
        paginator = Paginator(users, 10)
        page = request.GET.get('page')
        users = paginator.get_page(page)

    return render(request, 'staff_registration_table.html', {
        'users': users,
        'search_query': search_query,
        'is_export': is_export,
        "branch":branch,
        'is_export_excel': is_export_excel,
        'active_tab': 'registration',"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })
    
def staff_reg(request):
    hospital=Hospital_data.objects.first()
    tab = request.GET.get("tab", "registration")
    staff_list = StaffRegistration.objects.all()
    designations = Designation.objects.all()
    staff_id=request.session.get('staff_id')
    if staff_id:
        branch_id=StaffRegistration.objects.get(id=staff_id).branch_id
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    branches=Branch.objects.all()
    departments = Department.objects.all()
    if request.method == "POST":
        name = request.POST.get('username')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        contact = request.POST.get('contact')
        email = request.POST.get('email')
        qualification_details = request.POST.get('qualification_details')
        joining_date = request.POST.get('joining_date')
        pancard = request.POST.get('pancard')
        address = request.POST.get('address')

        # Prevent duplicate email
        if StaffRegistration.objects.filter(email=email,name=name).exists():
            messages.warning(request, "Name and Email already exists!")
        elif StaffRegistration.objects.filter(email=email).exists():
            messages.warning(request,"Email already exists!")
            return redirect('staff_registration')
        else:
            StaffRegistration.objects.create(
                name=name,
                gender=gender,
                age=age,
                email=email,
                contact=contact,
                branch_id=branch_id,
                qualification_details=qualification_details,
                joining_date=joining_date,
                pancard=pancard,
                address=address,
            )
            messages.success(request, "User registered successfully!")
            
                    
        return redirect('staff_registration')

            
    staff=StaffRegistration.objects.get(id=staff_id)
    return render(request, 'staff_reg.html',{"staff_list": staff_list,
        "designations": designations,
        "departments": departments,"branches":branches,"tab":tab,"staff":staff,"hospital":hospital})
    
def staff_allocation(request):
    hospital=Hospital_data.objects.first()
    
    tab = request.GET.get("tab", "registration")
    staff_list = StaffRegistration.objects.all()
    designations = Designation.objects.all()
    departments = Department.objects.all()
    branches=Branch.objects.all()
    staffid=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staffid)
    if request.method == "POST":
        staff_id = request.POST.get('staff')
        designation_id = request.POST.get('designation')
        department_id = request.POST.get('department')
        branch_id=request.POST.get('branch')
        password = request.POST.get('password')
        email = request.POST.get('email')
        status = request.POST.get('status')

        if StaffAllocation.objects.filter(email=email,staff_id=staff_id).exists():
            messages.warning(request, "Email/User already allocated ,edit already allocated to do so.!")
        else:
            StaffAllocation.objects.create(
            staff_id=staff_id,
            email=email,
            designation_id=designation_id,
            department_id=department_id,
            branch_id=branch_id,
            status=status,
            password=password
        ) 
            if StaffRegistration.objects.get(id=staff_id):
                user = get_object_or_404(StaffRegistration, id=staff_id)
                user.branch=Branch.objects.get(id=branch_id)
                user.save()
            messages.success(request, "Staff allocation saved successfully!")
            return redirect('staff_allocation')

    return render(request, "staff_allocation.html", {
        "staff_list": staff_list,
        "designations": designations,
        "departments": departments,
        "branches":branches,
        "tab":tab,
        "staff":staff,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })
def edit_staff_allocation(request, pk):
    hospital=Hospital_data.objects.first()
    allocation = get_object_or_404(StaffAllocation, pk=pk)
    departments = Department.objects.all()
    designations = Designation.objects.all()
    branches=Branch.objects.all()
    staff_list = StaffRegistration.objects.all()

    if request.method == "POST":
        staff_id = request.POST.get("staff")
        email = request.POST.get("email")
        password = request.POST.get("password")
        designation_id = request.POST.get("designation")
        department_id = request.POST.get("department")
        branch_id=request.POST.get('branch')
        status = request.POST.get("status")

        allocation.staff_id = staff_id
        allocation.email = email
        allocation.password = password
        allocation.designation_id = designation_id
        allocation.department_id = department_id
        allocation.branch_id=Branch.objects.get(id=branch_id)
        allocation.status = status
        allocation.save()
        if StaffRegistration.objects.get(id=staff_id):
                user = get_object_or_404(StaffRegistration, id=staff_id)
                user.branch=Branch.objects.get(id=branch_id)
                user.email=email
                user.save()
        messages.success(request, "Staff allocation updated successfully!")
        return redirect('staff_registration')  # Change to your staff list page

    return render(request, 'edit_staff_allocation.html', {
        'allocation': allocation,
        'departments': departments,
        'designations': designations,
        'staff_list': staff_list,
        "branches":branches,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })
    
def staff_allocation_table(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    allocations = StaffAllocation.objects.select_related('staff', 'designation', 'branch', 'department').all()
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'
    staff_id = request.session.get("staff_id")
    branch_id = None
    if staff_id:
        staff_allocation = StaffAllocation.objects.filter(staff_id=staff_id,status='active').first()
        if staff_allocation:
            branch_id = staff_allocation.branch_id
    allocations = StaffAllocation.objects.filter(status="active")
    if search_query:
        allocations = allocations.filter(staff__name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(allocations, 10)
        page = request.GET.get('page')
        allocations = paginator.get_page(page)

    return render(request, 'staff_allocation_table.html', {
        'allocations': allocations,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,
        'active_tab': 'allocation',"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })

def edit_user(request, user_id):
    hospital=Hospital_data.objects.first()
    user = get_object_or_404(StaffRegistration, id=user_id)
    if request.method == "POST":
        try:
            user.name = request.POST.get('username')
            user.gender = request.POST.get('gender')
            user.email = request.POST.get('email')
            user.age = request.POST.get('age')
            user.contact = request.POST.get('contact')
            user.qualification_details = request.POST.get('qualification_details')
            user.joining_date = request.POST.get('joining_date')
            user.pancard = request.POST.get('pancard')
            user.address = request.POST.get('address')
            user.save()
        
        except DataError as e:
            messages.error(request, "Data too long! Please check input lengths.")
            return render(request, 'edit_user.html', {'user': user})

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'edit_user.html', {'user': user})

        messages.success(request, "User updated successfully!")
        return redirect('stafftable')

    return render(request, 'edit_user.html', {'user': user,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def delete_staff(request, user_id):
    staff = StaffRegistration.objects.get(id=user_id)

    # Check if allocation exists before accessing it
    admin_alloc = StaffAllocation.objects.filter(staff=staff, designation__Designation='Admin').first()

    if admin_alloc:
        messages.error(request, "You can't delete this Admin Allocation!!")
        return redirect('stafftable')

    # Deactivate all staff allocations
    StaffAllocation.objects.filter(staff=staff).update(status="inactive")
    # Delete staff
    StaffRegistration.objects.filter(id=staff.id).update(status="Inactive")
    RoleAssignment.objects.filter(staff=staff).update(status=0)

    messages.success(request, "Staff registration and related allocations deleted successfully.")
    return redirect('stafftable')


# Delete StaffAllocation only
def delete_staff_allocation(request, pk):
    allocation = get_object_or_404(StaffAllocation, pk=pk)
    
    # Check if this allocation's staff has an active Admin designation
    is_admin = StaffAllocation.objects.filter(
        staff=allocation.staff.id,
        designation__Designation__iexact="Admin",
        status="active"
    ).exists()
    
    if is_admin:
        messages.error(request, "You can't inactivate this Admin Allocation!!")
    else:
        allocation.status = "inactive"
        allocation.save()
        RoleAssignment.objects.filter(staff=allocation.staff).update(status=0)
        messages.success(request, "Staff allocation deleted successfully.")
    return redirect('staff_allocation_table')

def country(request):
    hospital=Hospital_data.objects.first()
    if request.method == 'POST':
        name = request.POST.get('countryName')
        if Country.objects.filter(name__iexact=name).exists():
            messages.error(request, f"Country '{name}' already exists.")
        else:
            Country.objects.create(name=name)
            messages.success(request, f"Country '{name}' added successfully.")
        return redirect('country')

    return render(request, 'country.html',{"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def countrytable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'

    countries = Country.objects.all()
    if search_query:
        countries = countries.filter(name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(countries, 10)
        page = request.GET.get('page')
        countries = paginator.get_page(page)

    return render(request, 'country-table.html', {
        'countries': countries,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })

def edit_country(request, id):
    hospital=Hospital_data.objects.first()
    country = get_object_or_404(Country, id=id)
    if request.method == 'POST':
        new_name = request.POST.get('countryName')
        if new_name:
            country.name = new_name.strip()
            country.save()
            messages.success(request, 'Country updated successfully.')
            return redirect('countrytable')
    return render(request, 'country_edit.html', {'edit_country': country,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def delete_country(request, id):
    country = get_object_or_404(Country, id=id)
    country.delete()
    messages.success(request, 'Country deleted successfully.')
    return redirect('countrytable')



def state(request):
    hospital=Hospital_data.objects.first()
    countries = Country.objects.all()
    if request.method == 'POST':
        country_id = request.POST.get("country")
        name = request.POST.get('stateName')
        if State.objects.filter(name__iexact=name).exists():
            messages.error(request, f"State '{name}' already exists.")
        else:
            country = Country.objects.get(id=country_id)
            State.objects.create(country=country,name=name)
            messages.success(request, f"State '{name}' added successfully.")
        return redirect('state')

    return render(request, 'state.html',{"countries":countries,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def statetable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'

    states = State.objects.all()
    if search_query:
        states = states.filter(name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(states, 10)
        page = request.GET.get('page')
        states = paginator.get_page(page)

    return render(request, 'state-table.html', {
        'states': states,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })
    
def edit_state(request, id):
    hospital=Hospital_data.objects.first()
    state = get_object_or_404(State, id=id)
    countries = Country.objects.all()
    if request.method == 'POST':
        country_id = request.POST.get("country")
        new_name = request.POST.get('stateName')
        if new_name and country_id:
            state.country=Country.objects.get(id=country_id)
            state.name = new_name.strip()
            state.save()
            messages.success(request, 'State updated successfully.')
            return redirect('stateTable')
    return render(request, 'state_edit.html', {'edit_state': state,"countries": countries,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def delete_state(request, id):
    state = get_object_or_404(State, id=id)
    state.delete()
    messages.success(request, 'State deleted successfully.')
    return redirect('stateTable')

def district(request):
    hospital=Hospital_data.objects.first()
    states = State.objects.all()
    if request.method == 'POST':
        state_id = request.POST.get("state")
        name = request.POST.get('districtName')
        
        if District.objects.filter(name__iexact=name).exists():
            messages.error(request, f"District '{name}' already exists.")
        else:
            state = State.objects.get(id=state_id)
            District.objects.create(state=state, name=name)
            messages.success(request, f"District '{name}' added successfully.")
        return redirect('district')

    return render(request, 'district.html',{"states":states,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def districttable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf' 
    is_export_excel = request.GET.get('export') == 'excel'

    districts = District.objects.all()
    if search_query:
        districts = districts.filter(name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(districts, 10)
        page = request.GET.get('page')
        districts = paginator.get_page(page)

    return render(request, 'district-table.html', {
        'districts': districts,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))    })
    
def edit_district(request, id):
    hospital=Hospital_data.objects.first()
    district = get_object_or_404(District, pk=id)
    states = State.objects.all()
    
    if request.method == 'POST':
        state_id=request.POST.get("state")
        state = State.objects.get(id=state_id)
        district.state = state
        district.name = request.POST['name']
        district.save()
        return redirect('districttable')
    return render(request, 'district_edit.html', {'district': district,"states":states,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def delete_district(request, id):
    district = get_object_or_404(District, id=id)
    district.delete()
    messages.success(request, 'District deleted successfully.')
    return redirect('districttable')

def designation(request):
    hospital=Hospital_data.objects.first()
    if request.method == "POST":
        designation = request.POST.get("title")
        if Designation.objects.filter(Designation=designation).exists():
            messages.warning(request, "This designation already exists.")
        else:
            Designation.objects.create(Designation=designation)
            messages.success(request, "Designation added successfully.")
    return render(request, "designation.html",{"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def designationtable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'

    designations = Designation.objects.all()
    if search_query:
        designations = designations.filter(name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(designations, 10)
        page = request.GET.get('page')
        designations = paginator.get_page(page)

    return render(request, 'designation-table.html', {
        'designations': designations,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })

def edit_designation(request, id):
    hospital=Hospital_data.objects.first()
    designation = get_object_or_404(Designation, pk=id)
    if request.method == 'POST':
        designation.Designation = request.POST['name']
        designation.save()
        return redirect('designationtable')
    return render(request, 'designation_edit.html', {'designation': designation})

def delete_designation(request,id):
    designation = get_object_or_404(Designation, id=id)
    designation.delete()
    messages.success(request, 'Designation deleted successfully.')
    return redirect('designationtable')
    
def patient(request):
    hospital=Hospital_data.objects.first()
    countries = Country.objects.all()
    states = list(State.objects.values("id", "name", "country_id"))
    districts = list(District.objects.values("id", "name", "state_id"))


    staff_id = request.session.get("staff_id")
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    branch_id = None
    if staff_id:
        staff_allocation = StaffAllocation.objects.filter(staff_id=staff_id).first()
        if staff_allocation:
            branch_id = staff_allocation.branch_id
    if request.method == 'POST':
        name = request.POST.get('patientName')
        age = request.POST.get('patientAge')
        gender = request.POST.get('patientGender')
        email = request.POST.get('email')
        phone = request.POST.get('patientPhone')
        address = request.POST.get('patientAddress')
        date_of_admission = request.POST.get('dateOfAdmission')
        country_id = request.POST.get("country")
        state_id = request.POST.get("state")
        district_id = request.POST.get("district")
        try:
            admission_date = datetime.strptime(date_of_admission, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date format for Date of Admission.")
            return redirect('patient')
        date_part = admission_date.strftime("%Y%m%d")  # Format: YYYYMMDD
        count_today = Patient.objects.filter(mr_no__startswith=f"MRNO{date_part}").count() + 1
        mr_no = f"MRNO{date_part}{count_today:03d}"
        city=request.POST.get("city")
        if name and phone and date_of_admission:
            if not Patient.objects.filter(name=name, phone=phone).exists():
                try:
                    admission_date = datetime.strptime(date_of_admission, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(request, "Invalid admission date format.")
                    return redirect('patient')

                Patient.objects.create(
                    name=name,
                    age=age,
                    gender=gender,
                    email=email,
                    phone=phone,
                    address=address,
                    date_of_admission=admission_date,
                    mr_no=mr_no,
                    country_id=country_id if country_id else None,
                    state_id=state_id if state_id else None,
                    district_id=district_id if district_id else None,
                    city=city,
                    staff_id=staff_id,
                    branch_id=branch_id
                )
                messages.success(request, f"Patient registered successfully!")
            else:
                messages.warning(request, "Patient already exists.")
        else:
            messages.error(request, "Please fill all required fields.")

        return redirect('patient')

    return render(request, 'patientreg.html',{"countries": countries,
        "states": states,
        "districts": districts,
        "staff_id": staff_id,
        "branch_id": branch_id,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def patienttable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'
    user_admin=False
    staff_id = request.session.get("staff_id")
    branch_id = None
    if staff_id:
        staff_allocation = StaffAllocation.objects.filter(staff_id=staff_id).first()
        if staff_allocation:
            branch_id = staff_allocation.branch_id

    patients = Patient.objects.all()
    if branch_id:
        patients = patients.filter(branch_id=branch_id).order_by('-id')
        branch=Branch.objects.get(id=branch_id)
        if user_is_admin(StaffRegistration.objects.get(id=staff_id)):
            patients = Patient.objects.all().order_by('-id')
            branch=Branch.objects.all()
            user_admin=True
    allocation=get_object_or_404(StaffAllocation,staff=staff_id)
    is_doctor = StaffAllocation.objects.filter(
        staff=allocation.staff,
        designation__Designation__iexact="Doctor",
        status="active"
    ).exists()
    # Search filter
    if search_query:
        patients = patients.filter(name__icontains=search_query)

    # Apply pagination only if not exporting
    if not is_export and not is_export_excel:
        paginator = Paginator(patients, 10)
        page = request.GET.get('page')
        patients = paginator.get_page(page)

    return render(request, 'patient-table.html', {
        'patients': patients,
        'search_query': search_query,
        'is_doctor':is_doctor,
        'is_export': is_export,
        "branch":branch,
        "user_admin":user_admin,
        'is_export_excel': is_export_excel,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })
    
def edit_patient(request, patient_id):
    hospital=Hospital_data.objects.first()
    patient = get_object_or_404(Patient, id=patient_id)
    countries = Country.objects.all()
    states = list(State.objects.values("id", "name", "country_id"))
    districts = list(District.objects.values("id", "name", "state_id"))
    
    if request.method == 'POST':
        city=request.POST.get("city")
        patient.name = request.POST['patientName']
        patient.age = request.POST['patientAge']
        patient.gender = request.POST['patientGender']
        patient.email = request.POST['email']
        patient.phone = request.POST['patientPhone']
        patient.date_of_admission = request.POST['dateOfAdmission']
        patient.address = request.POST['patientAddress']
        patient.country_id = request.POST['country'] if request.POST['country'] else None
        patient.state_id = request.POST['state'] if request.POST['state']  else None
        patient.district_id = request.POST['district'] if request.POST['district'] else None
        patient.city=city if city else None
        patient.save()
        return redirect('patienttable')

    return render(request, 'patientedit.html', {
        'patient': patient,
        'countries': countries,
        'states': states,
        'districts': districts,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })
    
def hospitalreg(request):
    hospital=Hospital_data.objects.first()
    if request.method == 'POST':
        name = request.POST.get('hospitalName')
        logo = request.FILES.get('hospitalLogo')
        reg_no = request.POST.get('regNo')
        gst_no = request.POST.get('gstNo')
        manager = request.POST.get('managerName')
        contact = request.POST.get('managerContact')
        email = request.POST.get('email')
        address = request.POST.get('hospitalAddress')

        if Hospital_data.objects.first():
            messages.warning(request, "Hospital already Registered.")
        else:
            Hospital_data.objects.create(
                name=name,
                logo=logo,
                registration_number=reg_no,
                gst_number=gst_no,
                manager_name=manager,
                manager_contact=contact,
                email=email,
                address=address
            )
            messages.success(request, "Hospital registered successfully!")
        return redirect('hospitalreg')

    return render(request, 'hospitalreg.html',{"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})


def hospitaltable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'

    hospitals = Hospital_data.objects.all()
    staff=StaffRegistration.objects.get(id=request.session.get("staff_id"))
    if search_query:
        hospitals = hospitals.filter(name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(hospitals, 10)
        page = request.GET.get('page')
        hospitals = paginator.get_page(page)

    return render(request, 'hospital-table.html', {
        'hospitals': hospitals,
        'hospital':hospital,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,
        'staff':staff
    })
def edit_hospital(request, id):
    hospital=Hospital_data.objects.first()
    hospital = get_object_or_404(Hospital_data, pk=id)
    staff=StaffRegistration.objects.get(id=request.session.get("staff_id"))

    if request.method == 'POST':
        hospital.name = request.POST['name']
        hospital.registration_number = request.POST['registration_number']
        hospital.gst_number = request.POST['gst_number']
        hospital.manager_name = request.POST['manager_name']
        hospital.manager_contact = request.POST['manager_contact']
        hospital.email = request.POST['email']
        hospital.address = request.POST['address']

        if 'logo' in request.FILES:
            hospital.logo = request.FILES['logo']

        hospital.save()
        return redirect('hospitaltable')

    return render(request, 'hospital_edit.html', {'hospital': hospital,"staff":staff})


def search_patients(search_query,branch_id):
    """Return patient queryset or [] based on search query length."""
    if not search_query:
        return []

    if len(search_query) < 3:
        return None  # special case for warning

    return Patient.objects.filter(
        Q(mr_no__icontains=search_query) |
        Q(name__icontains=search_query) |
        Q(phone__icontains=search_query),
        branch=branch_id
    )


def appointment(request):
    hospital=Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    patients = []
    selected_patient = None
    branches = Branch.objects.all()
    departments = Department.objects.all()
    doctors = StaffRegistration.objects.filter(
        allocations__designation__Designation__iexact="Doctor",
        allocations__status="active"
    ).distinct()
    # Token generation
    token_prefix = f"TKNO{datetime.today().strftime('%y%m%d%H%M')}"
    token_count = Appointment.objects.filter(token_no__startswith=token_prefix).count() + 1
    token_no = f"{token_prefix}{token_count:03d}"
    try:
        staff_allocation = StaffAllocation.objects.get(staff_id=staff_id)
        allowed_branch_id = staff_allocation.branch_id
        search_query_value = request.GET.get("search", "").strip()    
        search_result = search_patients(search_query_value,allowed_branch_id)
        if search_result is None and search_query_value:
            messages.warning(request, "Please enter at least 3 characters to search.")
        elif search_result:
            patients = search_result
    except StaffAllocation.DoesNotExist:
        allowed_branch_id = None
    # get selected patient from POST
    selected_patient_id = request.POST.get('selectedPatient')
    if selected_patient_id and selected_patient_id.isdigit():
        selected_patient = get_object_or_404(
            Patient,
            id=int(selected_patient_id),
            branch_id=allowed_branch_id
        )
        
    # Handle form submission
    if request.method == "POST":
        patient_id = request.POST.get('selectedPatient')
        docid=request.POST.get('doctorName')
        if not patient_id or not patient_id.isdigit():
            messages.error(request, "Please select a valid patient before saving.")
            return redirect('appoinment')

        patient = get_object_or_404(Patient, id=patient_id, branch_id=allowed_branch_id)
        Appointment.objects.create(
            token_no=request.POST.get('tokenNo'),
            patient=patient,
            appointment_date=request.POST.get('appointmentDate'),
            appoinment_time=request.POST.get('appointmentTime') if request.POST.get('appointmentTime') else datetime.today().strftime('%H:%M'),
            branch=patient.branch,  # keep branch from patient
            department_id=request.POST.get('department') if request.POST.get('department').isdigit() else None,
            doctor_id=docid if docid.isdigit() else None,
            status=request.POST.get('status'),
            contact_no=request.POST.get('contactNo')
        )
        messages.success(request, "Appointment saved successfully.")
        # return redirect('appointmenttable')

    branches = Branch.objects.all() if not allowed_branch_id else Branch.objects.filter(id=allowed_branch_id)
    return render(request, "appointment.html", {
        "patients": patients,
        "selected_patient": selected_patient,
        "now": token_no,
        "departments": departments,
        "branches": branches,
        "doctors": doctors,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })

    
def appoinmenttable(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'
    filter_date = request.GET.get('date', '') 
    appointments = Appointment.objects.select_related('patient').order_by('-id')
    staff_id = request.session.get("staff_id")
    branch_id = None
    if staff_id:
        staff_allocation = StaffAllocation.objects.filter(staff_id=staff_id).first()
        if staff_allocation:
            branch_id = staff_allocation.branch_id
    if branch_id and not StaffAllocation.objects.get(staff=staff_id).designation.Designation=='Admin':
        appointments = appointments.filter(branch_id=branch_id).order_by('-token_no')
    # if staff_allocation.designation.Designation.lower() == "doctor":
    #         appointments = appointments.filter(doctor_id=staff_id)
    branch=Branch.objects.get(id=branch_id)
    allocation = get_object_or_404(StaffAllocation, staff=staff_id)
    
    # Check if this allocation's staff has an active Admin designation
    is_admin = StaffAllocation.objects.filter(
        staff=allocation.staff,
        designation__Designation__iexact="Admin",
        status="active"
    ).exists()
    
    is_doctor = StaffAllocation.objects.filter(
        staff=allocation.staff,
        designation__Designation__iexact="Doctor",
        status="active"
    ).exists()
    if search_query:
        appointments = appointments.filter(patient__name__icontains=search_query).order_by('-token_no')
    if filter_date:
        appointments = appointments.filter(appointment_date=filter_date)
    
    selected_staff = request.GET.get("staff")

    # 🔹 doctor filter from calendar
    if selected_staff:
        appointments = appointments.filter(doctor_id=selected_staff)
        
    if not is_export and not is_export_excel:
        paginator = Paginator(appointments, 10)
        page = request.GET.get('page')
        appointments = paginator.get_page(page)

    return render(request, 'appoinment-table.html', {
        'appointments': appointments,
        "branch":branch,
        'search_query': search_query,
        'is_admin':is_admin,
        'is_doctor':is_doctor,
        'is_export': is_export,
        'is_export_excel': is_export_excel,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })

def start_prescription(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    patient_id = appointment.patient.id

    # redirect with patient_id as GET parameter
    return redirect(f"{reverse('prescription_basic')}?patient_id={patient_id}")

def edit_appointment(request, pk):
    hospital=Hospital_data.objects.first()
    appointment = get_object_or_404(Appointment, pk=pk)
    branches = Branch.objects.all()

    departments = Department.objects.filter(branch__id=appointment.branch.id) if appointment.branch else []
    doctors = StaffRegistration.objects.filter(
        allocations__branch=appointment.branch,
        allocations__department=appointment.department,
        allocations__status='active'
    ).distinct()

    if request.method == "POST":
        branch_id = request.POST.get("branch")
        department_id = request.POST.get("department")
        doctor_id = request.POST.get("doctorName")

        appointment.appointment_date = request.POST.get("appointmentDate")
        appointment.branch_id = None if branch_id in ["", "undefined"] else int(branch_id)
        appointment.department_id = None if department_id in ["", "undefined"] else int(department_id)
        appointment.doctor_id = None if doctor_id in ["", "undefined"] else int(doctor_id)
        appointment.status = request.POST.get("status")
        appointment.appoinment_time=request.POST.get('appointmentTime')
        appointment.contact_no = request.POST.get("contactNo")
        appointment.save()

        messages.success(request, "Appointment updated successfully.")
        return redirect("appointmenttable")

    return render(request, "edit-appointment.html", {
        "appointment": appointment,
        "branches": branches,
        "departments": departments,
        "doctors": doctors,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })

def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    messages.success(request, "Appointment deleted successfully.")
    return redirect('appointmenttable')

def masters(request):
    hospital=Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    return render(request,'Masters.html',{"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

basic_details = {}
health_report = ""
prescription_notes = ""
patients = Patient.objects.all()
dr=StaffAllocation.objects.filter(designation__Designation="doctor")

def prescription_home(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get("search")
    ajax = request.GET.get("ajax")
    saved_doctor = None
    selected_patient = None
    staff = request.session.get('staff_id')
    if not staff:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    dr=StaffAllocation.objects.filter(designation__Designation="doctor",staff=staff)
    branch = StaffAllocation.objects.get(staff_id=staff).branch
    # 🔹 If it's an AJAX search request, return JSON
    if ajax and search_query:
        patients = search_patients(search_query,branch)

        results = [{
            "id": p.id,
            "mr_no": p.mr_no,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "phone": p.phone,
            "address": p.address,
            "branch": p.branch.name if p.branch else ""
        } for p in patients]
        return JsonResponse(results, safe=False)

    if request.method == 'GET':
        patient_id = request.GET.get('patient_id')
        date = request.GET.get('dateofvisit')
        doctor = request.GET.get('doctor')
        d_email = request.session.get('d_email')

        if StaffAllocation.objects.filter(designation=9, email=d_email):
            saved_doctor = StaffRegistration.objects.get(email=d_email).name
        else:
            saved_doctor = request.session.get('doctor')

        request.session['patient_id'] = patient_id
        request.session['dateofvisit'] = date
        request.session['doctor'] = doctor

        selected_patient = Patient.objects.filter(id=patient_id).first() if patient_id else None
        context={
            'patients': Patient.objects.all(),
            'selected_patient': selected_patient,
            'saved_date': request.session.get('dateofvisit'),
            'saved_doctor': saved_doctor,
            "doctor": dr,
            'search_query': search_query,
            "hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
        }
    return render(request, 'prescription_home.html', context)


    
def get_patient_details(request,id=None):
    patient_id = request.GET.get('patient_id') or id
    try:
        patient = Patient.objects.get(id=patient_id)
        data = {
            'id':patient.id,
            'mr_no': patient.mr_no,
            'name': patient.name,
            'age': patient.age,
            'gender': patient.gender,
            'phone': patient.phone,
            'address': patient.address,
            "branch":patient.branch.name,
        }
    except Patient.DoesNotExist:
        data = {'error': 'Patient not found'}
    return JsonResponse(data)

@csrf_exempt
def prescription_basic(request):
    hospital=Hospital_data.objects.first()
    patient=""
    passing_patient=""
    patient_id = request.session.get('patient_id')
    if request.GET.get("patient_id"):
        passing_patient=Patient.objects.get(id=request.GET.get("patient_id"))
    saved_doctor = request.session.get('doctor')
    date = request.session.get('dateofvisit')
    d_email = request.session.get('d_email')
    staff_id = request.session.get('staff_id')
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    dr=StaffAllocation.objects.filter(designation__Designation="Doctor")

    branch = StaffAllocation.objects.get(staff_id=staff_id).branch

    # Selected patient object
    selected_patient = Patient.objects.get(id=patient_id) if patient_id else None

    # Detect if logged-in user is a doctor
    if StaffAllocation.objects.get(staff=staff_id).designation.Designation.lower()=="doctor":
        saved_doctor = StaffRegistration.objects.get(
        allocations__designation__Designation__iexact="Doctor",
        allocations__status="active",id=staff_id,
    )
    else:
        saved_doctor = request.session.get('doctor')

    if request.method == "POST" and selected_patient:
        staff = StaffRegistration.objects.filter(email=d_email).first()
        chief_complaint=request.POST.get("chief_complaint")
        present_history=request.POST.get("present_history")
        past_history=request.POST.get("past_history")
        drug_history=request.POST.get('drug_history')
        provisional_diagnosis=request.POST.get('provisional_diagnosis')
        history=PatientHistory.objects.create(
            staff=staff,
            patient=selected_patient,
            chief_complaints=chief_complaint,
            present_history=present_history,
            past_medical_history=past_history,
            drug_history=drug_history,
            provisional_diagnosis=provisional_diagnosis,
        )
        request.session['history_id'] = history.id
        messages.success(request, "Patient Basic details saved successfully.")
        return redirect('prescription_health')
    if request.method=="POST" and not selected_patient:
        messages.error(request,"Error due to incorrect data input!!")
        
    allocation = StaffAllocation.objects.filter(staff_id=staff_id, branch_id=branch, status="active").select_related('designation').first()

    if allocation and allocation.designation.Designation.lower() == "doctor":
        dr = StaffRegistration.objects.get(
        branch=branch,
        id=staff_id,
        allocations__designation__Designation__iexact="Doctor",
        allocations__status="active"
    )
    else:
        dr = StaffRegistration.objects.get(branch=branch, id=staff_id)
    if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
        if patient:
           history = PatientHistory.objects.filter(patient=patient.id).order_by("-date_recorded")
           bodycharts = BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded")
           observations = GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded")
           motions = RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on")
           treatments = TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created")
           outcomes = OutcomeMeasure.objects.filter(patient=patient_id).order_by("-date")
           context = {
        "patient": patient,
        "history": history,
        "bodycharts": bodycharts,
        "observations": observations,
        "motions": motions,
        "treatments": treatments,
        "outcomes": outcomes,
        "patient":patient,
        "patients":patients,
        "selected_patient": selected_patient,
        "saved_date": date,
        "saved_doctor": saved_doctor,
        "doctor":dr,
        "hospital":hospital,"staff":StaffRegistration.objects.get(id=staff_id),
        }
           return render(request, 'basic_details.html', context)
    context={
        "patient":patient,
        "patients":patients,
        "passing_patient":passing_patient,
        "selected_patient": selected_patient,
        "saved_date": date,
        "saved_doctor": saved_doctor,
        "doctor":dr,
        "hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
    }
    return render(request, 'basic_details.html', context)


@csrf_exempt
def Pain_Assessment(request):
    hospital=Hospital_data.objects.first()
    patient_id = request.session.get('patient_id')
    history_id = request.session.get('history_id')
    history = PatientHistory.objects.filter(id=history_id).first() if history_id else None 
    saved_doctor = request.session.get('doctor')    
    date = request.session.get('dateofvisit')
    d_email = request.session.get('d_email')
    staff_id = request.session.get('staff_id')
    branch = StaffAllocation.objects.get(staff_id=staff_id).branch
    selected_patient = Patient.objects.filter(id=patient_id).first() if patient_id else None

    if StaffAllocation.objects.filter(designation=9, email=d_email).exists():
        saved_doctor = StaffRegistration.objects.get(email=d_email,id=staff_id).name
    else:
        saved_doctor = ""

    if request.method == "POST" and selected_patient:
        staff = StaffRegistration.objects.get(email=d_email,id=staff_id)
        pain_assessment = request.POST.get("pain_assessment")
        pain_area = request.POST.get("area")
        pain_type = request.POST.get("Type")
        type_other = request.POST.get("TypeOther")
        pain_history = request.POST.get("pain_history")
        pain_severity = request.POST.get("nprs")

        if pain_type == "Other" and type_other:
            pain_type = type_other

        BodyChart.objects.create(
            staff=staff,
            patient=selected_patient,
            history=history,
            pain_assessment=pain_assessment,
            pain_area=pain_area,
            type=pain_type,
            pain_history=pain_history,
            pain_severity=pain_severity,
        )
        messages.success(request, "Body Chart saved successfully.")
        return redirect('prescription_notes')

    allocation = StaffAllocation.objects.filter(staff_id=staff_id, branch_id=branch, status="active").select_related('designation').first()

    if allocation and allocation.designation.Designation.lower() == "doctor":
        dr = StaffRegistration.objects.get(
        branch=branch,
        id=staff_id,
        allocations__designation__Designation__iexact="Doctor",
        allocations__status="active"
    )
    else:
        dr = StaffRegistration.objects.get(branch=branch, id=staff_id)
    # For GET → render template
    body_chart_images = BodyChart.objects.filter(patient=selected_patient).last()
    patient = ""
    if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
        if patient:
           history = PatientHistory.objects.filter(patient=patient.id).order_by("-date_recorded")
           bodycharts = BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded")
           observations = GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded")
           motions = RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on")
           treatments = TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created")
           outcomes = OutcomeMeasure.objects.filter(patient=patient, history=history_id).order_by("-date")
           context = {
        "patient": patient,
        "history": history,
        "bodycharts": bodycharts,
        "observations": observations,
        "motions": motions,
        "treatments": treatments,
        "outcomes": outcomes,
        "patient":patient,
        "patients":patients,
        "selected_patient": selected_patient,
        "saved_date": date,
        "saved_doctor": saved_doctor,
        "doctor":dr,
        "hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
        }
           return render(request, 'Pain_Assessment.html', context)

    return render(
        request,
        "Pain_Assessment.html",
        {   "patient":patient,
            "selected_patient": selected_patient,
            "saved_date": date,
            "doctor": dr,
            "saved_doctor": saved_doctor,
            "patients": patients,
            "body_chart_images": body_chart_images,
            "hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
        },
    )

@csrf_exempt
def prescription_general_observation(request):
    hospital=Hospital_data.objects.first()
    patient_id = request.session.get("patient_id")
    history_id = request.session.get('history_id')
    history = PatientHistory.objects.filter(id=history_id).first() if history_id else None 
    saved_doctor = request.session.get("doctor")
    date = request.session.get("dateofvisit")
    d_email = request.session.get("d_email")
    selected_patient = Patient.objects.filter(id=patient_id).first() if patient_id else None
    staff= request.session.get('staff_id')
    # Find logged-in staff
    staff = StaffRegistration.objects.filter(email=d_email).first() if d_email else None
    dr = []
    if staff:
        allocation = StaffAllocation.objects.filter(staff_id=staff).first()
        if allocation:
            dr = StaffRegistration.objects.filter(branch=allocation.branch)
    if request.method == "POST" and selected_patient and staff:
        # 🔹 Collect POST data
        built = request.POST.get("built")
        swelling = request.POST.get("swelling")
        deformities = request.POST.get("deformities")
        tropical_changes = request.POST.get("tropical_changes")
        skin = request.POST.get("skin")
        edema = request.POST.get("edema")
        warmth = request.POST.get("warmth")
        contractures = request.POST.get("contractures")
        light_touch = request.POST.get("light_touch")
        crude_touch = request.POST.get("crude_touch")
        balance_sitting = request.POST.get("balance_sitting")
        balance_standing = request.POST.get("balance_standing")

        GeneralObservation.objects.create(
            staff=staff,
            patient=selected_patient,
            history=history,
            built=built,
            swelling=swelling,
            deformities=deformities,
            tropical_changes=tropical_changes,
            skin=skin,
            edema=edema,
            warmth=warmth,
            contractures=contractures,
            light_touch=light_touch,
            crude_touch=crude_touch,
            balance_sitting=balance_sitting,
            balance_standing=balance_standing,
        )

        messages.success(request, "General Observation saved successfully.")
        return redirect("RangeofMotion")
        patient=""
    if request.method=="POST" and not selected_patient:
        messages.error(request,"Error due to incorrect data input!!")
    if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
        if patient:
           history = PatientHistory.objects.filter(patient=patient.id).order_by("-date_recorded")
           bodycharts = BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded")
           observations = GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded")
           motions = RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on")
           treatments = TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created")
           outcomes = OutcomeMeasure.objects.filter(patient=patient, history=history_id).order_by("-date")
           context = {
        "patient": patient,
        "history": history,
        "bodycharts": bodycharts,
        "observations": observations,
        "motions": motions,
        "treatments": treatments,
        "outcomes": outcomes,
        "patient":patient,
        "patients":patients,
        "selected_patient": selected_patient,
        "saved_date": date,
        "saved_doctor": saved_doctor,
        "doctor":dr,
        "hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
        }
           return render(request, 'General_Observation.html', context)
    return render(request, 'General_Observation.html', {"selected_patient": selected_patient,
        "saved_date": date,"doctor":dr,"saved_doctor": saved_doctor,"notes": prescription_notes,'patients': patients,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),})

@csrf_exempt
def rangeofmotion(request):
    hospital=Hospital_data.objects.first()
    patient_id = request.session.get("patient_id")
    saved_doctor = request.session.get("doctor")
    history_id = request.session.get('history_id')
    history = PatientHistory.objects.filter(id=history_id).first() if history_id else None 
    date = request.session.get("dateofvisit")
    d_email = request.session.get("d_email")
    staff= request.session.get('staff_id')
    branch = StaffAllocation.objects.get(staff_id=staff).branch
    if StaffAllocation.objects.filter(branch_id=branch):
        dr=StaffRegistration.objects.filter(branch=branch)
    selected_patient = Patient.objects.filter(id=patient_id).first() if patient_id else None
    staff = StaffRegistration.objects.filter(email=d_email).first() if d_email else None

    if request.method == "POST" and selected_patient and staff:
        date=request.POST.getlist("date[]")
        joints = request.POST.getlist("joint[]")
        aroms = request.POST.getlist("arom[]")
        proms = request.POST.getlist("prom[]")

        # Common fields
        fall_risk = request.POST.get("fall_risk")
        muscle_power = request.POST.get("muscle_power")

        for dt,joint, arom, prom in zip(date,joints, aroms, proms):
            parsed_date = parse_date(dt)
            if joint.strip():  # Only save if a joint name is provided
                RangeOfMotion.objects.create(
                    staff=staff,
                    patient=selected_patient,
                    joint=joint,
                    history=history,
                    arom=arom,
                    date=parsed_date,
                    prom=prom,
                    fall_risk=fall_risk,
                    muscle_power=muscle_power,
                )
        messages.success(request, "Range Of Motion saved successfully.")
        return redirect("functional_outcome")
        patient = ""
    if request.method=="POST" and not selected_patient:
        messages.error(request,"Error due to incorrect data input!!")
    if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
        if patient:
           history = PatientHistory.objects.filter(patient=patient.id).order_by("-date_recorded")
           bodycharts = BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded")
           observations = GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded")
           motions = RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on")
           treatments = TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created")
           outcomes = OutcomeMeasure.objects.filter(patient=patient, history=history_id).order_by("-date")

           context = {
        "patient": patient,
        "history": history,
        "bodycharts": bodycharts,
        "observations": observations,
        "motions": motions,
        "treatments": treatments,
        "outcomes": outcomes,
        "patient":patient,
        "patients":patients,
        "selected_patient": selected_patient,
        "saved_date": date,
        "saved_doctor": saved_doctor,
        "doctor":dr,
        "hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
        }
           return render(request, 'Rangeofmotion.html', context)
    return render(request,'Rangeofmotion.html',{"selected_patient": selected_patient,
        "saved_date": date,"doctor":dr,"saved_doctor": saved_doctor,'patients': patients,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),})

def clear_prescription_session(request):
    keys = ['dateofvisit', 'doctor', 'patient_id']
    for key in keys:
        request.session.pop(key, None)
    return redirect('home')

def functionoutcome(request):
    hospital=Hospital_data.objects.first()
    patient_id = request.session.get('patient_id')
    saved_doctor = request.session.get('doctor')
    date = request.session.get('dateofvisit')
    d_email = request.session.get('d_email')
    history_id = request.session.get('history_id')
    history = PatientHistory.objects.filter(id=history_id).first() if history_id else None 
    # Get staff object
    staff = StaffRegistration.objects.get(email=d_email,id=request.session.get('staff_id')) if d_email else None

    # Doctor override check
    if staff and StaffAllocation.objects.filter(designation=9, staff=staff.id).exists():
        saved_doctor = staff.name

    # Get selected patient
    selected_patient = Patient.objects.filter(id=patient_id).first() if patient_id else None

    if request.method == "POST" and staff and selected_patient:
        # Collect POST data
        dates = request.POST.getlist("date[]")
        outcomes = request.POST.getlist("outcome[]")
        pretests = request.POST.getlist("pretest[]")
        posttests = request.POST.getlist("posttest[]")

        for i in range(len(dates)):
            if dates[i] and outcomes[i]:  # ensure row is not empty
                OutcomeMeasure.objects.create(
                    date=dates[i],
                    outcome_used=outcomes[i],
                    pretest_score=pretests[i] if i < len(pretests) else None,
                    posttest_score=posttests[i] if i < len(posttests) else None,
                    staff=staff,
                    patient=selected_patient,
                    history=history,
                )
        messages.success(request, "Functional Outcome saved successfully.")
        return redirect("treatment_plan")
    if request.method=="POST" and not selected_patient:
        messages.error(request,"Error due to incorrect data input!!")
    staff= request.session.get('staff_id')
    branch = StaffAllocation.objects.get(staff_id=staff).branch
    allocation = StaffAllocation.objects.filter(staff_id=staff, branch_id=branch, status="active").select_related('designation').first()

    if allocation and allocation.designation.Designation.lower() == "doctor":
        dr = StaffRegistration.objects.get(
        branch=branch,
        id=staff,
        allocations__designation__Designation__iexact="Doctor",
        allocations__status="active"
    )
    else:
        dr = StaffRegistration.objects.get(branch=branch, id=staff)
    patient = ""
    if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
        if patient:
           history = PatientHistory.objects.filter(patient=patient.id).order_by("-date_recorded")
           bodycharts = BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded")
           observations = GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded")
           motions = RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on")
           treatments = TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created")
           outcomes = OutcomeMeasure.objects.filter(patient=patient, history=history_id).order_by("-date")

           context = {
        "patient": patient,
        "history": history,
        "bodycharts": bodycharts,
        "observations": observations,
        "motions": motions,
        "treatments": treatments,
        "outcomes": outcomes,
        "patient":patient,
        "patients":patients,
        "selected_patient": selected_patient,
        "saved_date": date,
        "saved_doctor": saved_doctor,
        "doctor":dr,
        "hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
        }
           return render(request, 'functional_outcome.html', context)
    return render(request,'functional_outcome.html',{"selected_patient": selected_patient,
        "saved_date": date,
        "saved_doctor": saved_doctor,'patients': patients,"doctor":dr,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
})

def treatmentplan(request):
    hospital = Hospital_data.objects.first()
    patient_id = request.session.get('patient_id')
    saved_doctor = request.session.get('doctor')
    date = request.session.get('dateofvisit')
    d_email = request.session.get('d_email')
    staff_id = request.session.get('staff_id')
    history_id = request.session.get('history_id')

    # Get staff
    staff = StaffRegistration.objects.filter(email=d_email, id=staff_id).first() if d_email and staff_id else None
    selected_patient = Patient.objects.filter(id=patient_id).first() if patient_id else None

    # ====================== CRITICAL: Prevent History Leakage ======================
    if selected_patient:
        # Check if current history_id belongs to this patient
        if history_id:
            current_history = PatientHistory.objects.filter(id=history_id).first()
            if current_history and current_history.patient_id != selected_patient.id:
                # Old history_id from previous patient → Clear it!
                request.session.pop('history_id', None)
                history_id = None
    # =============================================================================

    # Get correct history for current patient
    history = None
    if history_id:
        history = PatientHistory.objects.filter(id=history_id, patient=selected_patient).first()
    elif selected_patient and staff:
        # Auto-create new history only if patient already has previous records
        has_previous = PatientHistory.objects.filter(patient=selected_patient).exists()
        
        if has_previous:
            history = PatientHistory.objects.create(
                staff=staff,
                patient=selected_patient,
            )
            request.session['history_id'] = history.id
        # else: First visit → Do NOT create history yet

    # Doctor Object
    try:
        branch = StaffAllocation.objects.get(staff_id=staff_id).branch
        allocation = StaffAllocation.objects.filter(
            staff_id=staff_id, branch_id=branch, status="active"
        ).select_related('designation').first()

        if allocation and allocation.designation and allocation.designation.Designation.lower() == "doctor":
            dr = StaffRegistration.objects.get(
                branch=branch, id=staff_id,
                allocations__designation__Designation__iexact="Doctor",
                allocations__status="active"
            )
        else:
            dr = StaffRegistration.objects.get(branch=branch, id=staff_id)
    except:
        dr = None

    # ====================== POST Request ======================
    if request.method == "POST" and staff and selected_patient:
        short_term_goals = request.POST.get("short_term_goals", "").strip()
        long_term_goals = request.POST.get("long_term_goals", "").strip()

        if not short_term_goals and not long_term_goals:
            messages.error(request, "Please enter at least one goal before saving.")
            return redirect("treatmentplan")

        # Safety: Ensure history belongs to current patient
        if history and history.patient_id != selected_patient.id:
            messages.error(request, "History mismatch detected. Please refresh.")
            request.session.pop('history_id', None)
            return redirect("treatmentplan")

        # Create Treatment Plan
        treatment_plan = TreatmentPlan.objects.create(
            staff=staff,
            patient=selected_patient,
            history=history,
            short_term_goals=short_term_goals,
            long_term_goals=long_term_goals,
            date_created=date,
        )

        # Management Entries (same as before)
        dates = request.POST.getlist("date[]")
        managements = request.POST.getlist("management[]")
        review_dates = request.POST.getlist("review_date[]")
        signatures = request.POST.getlist("signature[]")

        for i in range(len(dates)):
            date_str = dates[i].strip()
            if not date_str or i >= len(managements) or not managements[i].strip():
                continue

            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                review_str = review_dates[i].strip() if i < len(review_dates) else ""
                review_obj = datetime.strptime(review_str, '%Y-%m-%d').date() if review_str else None
            except ValueError:
                continue

            if ManagementEntry.objects.filter(
                treatment_plan=treatment_plan, date=date_obj, management=managements[i].strip()
            ).exists():
                continue

            ManagementEntry.objects.create(
                staff=staff,
                treatment_plan=treatment_plan,
                date=date_obj,
                management=managements[i].strip(),
                review_date=review_obj,
                signature=signatures[i].strip() if i < len(signatures) else "",
            )

        # AJAX Response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": True,
                "message": "Treatment plan saved successfully."
            })

        messages.success(request, "Treatment plan saved successfully.")
        return redirect("treatmentplan")

    # ====================== GET Context ======================
    context = {
        "hospital": hospital,
        "doctor": dr,
        "staff": StaffRegistration.objects.get(id=staff_id) if staff_id else None,
        "selected_patient": selected_patient,
        "saved_date": date,
        "saved_doctor": saved_doctor,
    }

    if patient_id and selected_patient:
        patient = selected_patient
        context.update({
            "patient": patient,
            "history": PatientHistory.objects.filter(patient=patient).order_by("-date_recorded"),
            "bodycharts": BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded"),
            "observations": GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded"),
            "motions": RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on"),
            "treatments": TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created"),
            "outcomes": OutcomeMeasure.objects.filter(patient=patient).order_by("-date"),
        })

    return render(request, 'Treatmentplan.html', context)

def body_chart_master(request):
    hospital=Hospital_data.objects.first()
    if request.method == "POST" and request.FILES.get("image"):
        title = request.POST.get("title")
        image = request.FILES.get("image")
        BodyChartImage.objects.create(title=title, image=image)
        return redirect('body_chart_master')

    charts = BodyChartImage.objects.all().order_by('-uploaded_at')
    return render(request, 'body-chart-master.html', {'charts': charts,'patients': patients,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),})

def delete_body_chart(request, chart_id):
    chart = get_object_or_404(BodyChartImage, id=chart_id)

    # Delete the image file from the filesystem
    if chart.image and os.path.isfile(chart.image.path):
        os.remove(chart.image.path)

    chart.delete()
    return redirect('body_chart_master')


def role_add(request):
    hospital=Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    if request.method == "POST":
        name = request.POST.get("role_name")
        status = request.POST.get("status") == "on"
        Role.objects.create(name=name, status=status)
        return redirect('role_add')
    roles = Role.objects.all()
    return render(request, 'role_add.html', {'roles': roles,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})
def role_assign(request):
    hospital=Hospital_data.objects.first()
    branches = Branch.objects.all()
    active_allocations = StaffAllocation.objects.filter(status='active').values_list('staff_id', flat=True)
    users = StaffRegistration.objects.filter(id__in=active_allocations)

   
    roles = Role.objects.filter(status="1")

    if request.method == "POST":
        role_id = request.POST.get("role")
        branch_id = request.POST.get("branch")
        staff_id = request.POST.get("staff")
        status = request.POST.get("status") == "Active"
        if not RoleAssignment.objects.filter(staff_id=staff_id).exists():
            RoleAssignment.objects.create(
            role_id=role_id,
            branch_id=branch_id,
            staff_id=staff_id,
            status=status
        )
            messages.success(request,"Staff Allocated with a role successfully")
            return redirect('role_assign')
        else:
            messages.error(request,"Staff already once allocated with role")
    return render(request,'role_assign.html',{'roles': roles, 'branches': branches, 'users': users,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),})

def menu_add(request):
    hospital=Hospital_data.objects.last()
    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")
        url = request.POST.get("url")

        if Menu.objects.filter(name__iexact=name, category__iexact=category).exists():
            messages.warning(request, f"Menu '{name}' already exists in {category}.")
        else:
            Menu.objects.create(
                name=name,
                category=category,
                url=url
            )
            messages.success(request, "Menu added successfully!")

    return render(request, "menu_add.html",{"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def menu_table(request):
    hospital=Hospital_data.objects.first()
    
    search_query = request.GET.get("search", "").strip()
    is_export = request.GET.get("export") == "pdf"
    is_export_excel = request.GET.get("export") == "excel"

    menus = Menu.objects.all()

    if search_query:
        menus = menus.filter(name__icontains=search_query) | menus.filter(category__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(menus, 10)  
        page_number = request.GET.get("page")
        menus = paginator.get_page(page_number)

    context = {
        "menus": menus,
        "search_query": search_query,
        "is_export": is_export,
        "is_export_excel": is_export_excel,
        "hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))
    }
    return render(request, "menu_table.html", context)

def edit_menu(request, id):
    hospital=Hospital_data.objects.first()
    menu = get_object_or_404(Menu, id=id)

    if request.method == "POST":
        menu.name = request.POST.get("name")
        menu.category = request.POST.get("category")
        menu.url = request.POST.get("url")
        menu.save()
        messages.success(request, "Menu updated successfully.")
        return redirect("menu_table")

    return render(request, "menu_edit.html", {"menu": menu,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def delete_menu(request, id):
    menu = get_object_or_404(Menu, id=id)
    menu.delete()
    messages.success(request, "Menu deleted successfully.")
    return redirect("menu_table")

def menu_allocation(request):
    hospital = Hospital_data.objects.first()
    roles = Role.objects.all()
    menus = Menu.objects.all().order_by("category", "name")
    
    if request.method == "POST":
        role_id = request.POST.get("role")
        for menu in menus:
            prefix = f"menu_{menu.id}_"
            can_view = request.POST.get(prefix + "view") == "on"
            can_add = request.POST.get(prefix + "add") == "on"
            can_edit = request.POST.get(prefix + "edit") == "on"
            can_delete = request.POST.get(prefix + "delete") == "on"

            MenuPermission.objects.update_or_create(
                role_id=role_id,
                menu=menu,
                defaults={
                    "can_view": can_view,
                    "can_add": can_add,
                    "can_edit": can_edit,
                    "can_delete": can_delete,
                },
            )
        messages.success(request,"Menu Allocation Saved Successfully!")
        return redirect("menu_allocation")

    return render(
        request,
        "menu_allocation.html",
        {"roles": roles,"menus": menus,"hospital": hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),},
    )
    
def menu_permissions_edit(request, role_id):
    """
    Edit menu permissions for a specific role.
    - builds lists of menu ids for each permission for easy template checks
    - saves/updates MenuPermission objects on POST
    """
    hospital = Hospital_data.objects.first()
    role = get_object_or_404(Role, id=role_id)
    staff = None
    try:
        staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))
    except Exception:
        staff = None

    # All menus ordered by category then name
    menus = Menu.objects.all().order_by("category", "name")

    # Existing permissions for this role
    perms = MenuPermission.objects.filter(role=role)

    # Build quick lookup lists of ids for template use (no templatetags required)
    view_ids = [p.menu_id for p in perms if p.can_view]
    add_ids  = [p.menu_id for p in perms if p.can_add]
    edit_ids = [p.menu_id for p in perms if p.can_edit]
    delete_ids = [p.menu_id for p in perms if p.can_delete]

    # Build categories grouping for nicer template iteration
    menu_categories = {}
    for m in menus:
        cat = m.category or "Uncategorized"
        menu_categories.setdefault(cat, []).append(m)

    if request.method == "POST":
        # Use a transaction for safety
        with transaction.atomic():
            for m in menus:
                prefix = f"menu_{m.id}_"
                can_view = request.POST.get(prefix + "view") == "on"
                can_add  = request.POST.get(prefix + "add") == "on"
                can_edit = request.POST.get(prefix + "edit") == "on"
                can_delete = request.POST.get(prefix + "delete") == "on"

                # create or update permission row
                perm_obj, created = MenuPermission.objects.get_or_create(role=role, menu=m)
                perm_obj.can_view = can_view
                perm_obj.can_add = can_add
                perm_obj.can_edit = can_edit
                perm_obj.can_delete = can_delete
                perm_obj.save()

        messages.success(request, f"Permissions updated for role: {role.name}")
        return redirect("menu_allocation_table")

    context = {
        "hospital": hospital,
        "role": role,
        "menu_categories": menu_categories.items(),  # iterable of (category, [menus])
        "view_ids": view_ids,
        "add_ids": add_ids,
        "edit_ids": edit_ids,
        "delete_ids": delete_ids,
        "staff": staff,
    }
    return render(request, "menu_permission_edit.html", context)

def menu_permission_table(request):
    staff_id=request.session.get("staff_id")
    roles = Role.objects.all()
    hospital=Hospital_data.objects.last()
    role_id = request.GET.get("role")
    selected_role = None
    permissions = []
    if role_id:
        selected_role = Role.objects.get(id=role_id)
        permissions = MenuPermission.objects.filter(role=selected_role).select_related("menu")

    context = {
        "roles": roles,
        "selected_role": selected_role,
        "permissions": permissions,
        "hospital":hospital,
        "staff":StaffRegistration.objects.get(id=staff_id)
    }
    return render(request, "menu_allocation_table.html", context)

def role_table(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    roles_qs = Role.objects.all()
    if search_query:
        roles_qs = roles_qs.filter(name__icontains=search_query)

    paginator = Paginator(roles_qs, 10)
    page_number = request.GET.get('page')
    roles = paginator.get_page(page_number)

    return render(request, 'role_table.html', {
        'roles': roles,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
        'is_export_excel': request.GET.get('export') == 'excel',
        'is_export': request.GET.get('export') == 'pdf'
    })
def edit_role(request, role_id):
    hospital=Hospital_data.objects.first()
    role = get_object_or_404(Role, id=role_id)
    if request.method == 'POST':
        role.name = request.POST.get('role_name')
        role.status = True if request.POST.get('status') == 'Active' else False
        role.save()
        return redirect('role_table')
    return render(request, 'role_edit.html', {'role': role,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),})

def role_allocation_table(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    allocations_qs = RoleAssignment.objects.select_related('role', 'branch', 'staff').all()

    if search_query:
        allocations_qs = allocations_qs.filter(
            Q(role__name__icontains=search_query) |
            Q(branch__name__icontains=search_query) |
            Q(staff__name__icontains=search_query)
        )

    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'

    if not is_export and not is_export_excel:
        paginator = Paginator(allocations_qs, 10)
        page_number = request.GET.get('page')
        allocations = paginator.get_page(page_number)
    else:
        allocations = allocations_qs  # bypass pagination for export

    return render(request, 'role_allocation_table.html', {
        'allocations': allocations,
        'search_query': search_query,
        'is_export_excel': is_export_excel,
        'is_export': is_export,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
    })
def edit_role_allocation(request, allocation_id):
    hospital=Hospital_data.objects.first()
    allocation = get_object_or_404(RoleAssignment, id=allocation_id)
    roles = Role.objects.all()
    branches = Branch.objects.all()
    active_allocations = StaffAllocation.objects.filter(status='active').values_list('staff_id', flat=True)
    users = StaffRegistration.objects.filter(id__in=active_allocations)

    # staff=request.POST.get("staff")
    if request.method == "POST":
        allocation.role_id = request.POST.get("role")
        allocation.branch_id = request.POST.get("branch")
        # allocation.staff_id = request.POST.get("staff")
        allocation.status = True if request.POST.get("status") == "Active" else False
        allocation.save()
        messages.success(request, "Role allocation updated successfully.")
        return redirect('role_allocation_table')

    return render(request, 'role_allocation_edit.html', {
        'allocation': allocation,
        'roles': roles,
        'branches': branches,
        'users': users,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
    })

def get_departments_by_branch(request, branch_id):
    
    try:
        branch = Branch.objects.get(pk=branch_id)
    except Branch.DoesNotExist:
        return JsonResponse({"departments": []})

    # First try M2M link
    depts_qs = branch.departments.all().values("id", "name")
    departments = list(depts_qs)

    # Fallback: gather from StaffAllocation if M2M empty
    if not departments:
        dept_ids = (
            StaffAllocation.objects
            .filter(branch_id=branch_id)
            .values_list("department_id", flat=True)
            .distinct()
        )
        departments = list(
            Department.objects.filter(id__in=dept_ids).values("id", "name")
        )

    return JsonResponse({"departments": departments})

def get_doctors_by_department(request):
    branch_id = request.GET.get("branch_id")
    dept_id = request.GET.get("dept_id")
    if not branch_id or not dept_id:
        return JsonResponse({"doctors": []})
    doctors = StaffAllocation.objects.filter(
        branch_id=branch_id,
        department_id=dept_id,
        designation__Designation__icontains="Doctor",
        status="active"
    ).select_related("staff").values(
            doctor_id=F("staff__id"),
            name=F("staff__name")
        )
    return JsonResponse({"doctors": list(doctors)})
    
    
    
def clear_session(request):
    """
    Clears all session data and logs out the user.
    Can be linked/called from any page.
    """
    keys = ['dateofvisit', 'doctor', 'patient_id',"staff_id",'saved_doctor','selected_patient']
    for key in keys:
        request.session.pop(key, None)
    request.session.flush()
    request.session.clear()
    if "search" in request.POST:
        # just ignore search params (don't pass them to templates)
        request.POST = request.POST
        request.POST.clear()
        

    logout(request)
    messages.info(request, "You have been logged out.")

    return redirect("login")


def patient_history_view(request, patient_id):
    hospital = Hospital_data.objects.first()
    patient = get_object_or_404(Patient, id=patient_id)
    history = PatientHistory.objects.filter(patient=patient).order_by("-date_recorded")
    bodycharts = BodyChart.objects.filter(patient=patient).order_by("-date_uploaded")
    observations = GeneralObservation.objects.filter(patient=patient).order_by("-date_recorded")
    motions = RangeOfMotion.objects.filter(patient=patient).order_by("-recorded_on")
    treatments = TreatmentPlan.objects.filter(patient=patient.id).order_by("-date_created")
    outcomes = OutcomeMeasure.objects.filter(patient=patient).order_by("-date")
    staff = None
    staff_id = request.session.get("staff_id")
    if staff_id:
        try:
            staff = StaffRegistration.objects.get(id=staff_id)
        except StaffRegistration.DoesNotExist:
            pass
    appointments=Appointment.objects.filter(patient=patient)
    appt_map = {appt.appointment_date: appt.status for appt in appointments}

    context = {
        "patient": patient,
        "history": history,  
        "appointments":appointments,
        "bodycharts": bodycharts,
        "observations": observations,
        "motions": motions,
        "treatments": treatments,
        "outcomes": outcomes,
        "hospital": hospital,
        "staff": staff,
        "appt_map":appt_map,
    }
    return render(request, "patient_history.html", context)


def prescription_detail(request, history_id):
    hospital=Hospital_data.objects.first()
    """Show full details of a single prescription/visit"""
    history = get_object_or_404(PatientHistory, id=history_id)
    patient = history.patient

    # All linked records for this patient
    bodycharts = BodyChart.objects.filter(patient=patient,history=history_id).order_by("-date_uploaded")
    observations = GeneralObservation.objects.filter(patient=patient,history=history_id).order_by("-date_recorded")
    motions = RangeOfMotion.objects.filter(patient=patient,history=history_id).order_by("-recorded_on")
    treatments = TreatmentPlan.objects.filter(patient=patient,history=history_id).order_by("-date_created").prefetch_related("management_entries")
    functional_outcomes = OutcomeMeasure.objects.filter(patient=patient, history=history_id).order_by("-date")
    outcomes = OutcomeMeasure.objects.filter(patient=patient, history=history_id).order_by("-date")


    return render(request, "prescription_details.html", {
        "patient": patient,
        "history": history,
        "bodycharts": bodycharts,
        "observations": observations,
        "motions": motions,
        "treatments": treatments,
        "functional_outcomes": functional_outcomes,
        "outcomes": outcomes,
    })


def prescription_pdf(request, history_id):
    selected_history = get_object_or_404(PatientHistory, id=history_id)
    patient = selected_history.patient
    hospital=Hospital_data.objects.first()
    history = PatientHistory.objects.filter(patient=patient,id=history_id).order_by("-date_recorded")
    bodycharts = BodyChart.objects.filter(patient=patient,history=history_id).order_by("-date_uploaded")
    observations = GeneralObservation.objects.filter(patient=patient,history=history_id).order_by("-date_recorded")
    motions = RangeOfMotion.objects.filter(patient=patient,history=history_id).order_by("-recorded_on")
    treatments = TreatmentPlan.objects.filter(patient=patient,history=history_id).order_by("-date_created")
    outcomes = OutcomeMeasure.objects.filter(patient=patient, history=history_id).order_by("-date")


    template = get_template("prescription_pdf.html")
    html = template.render({
        "patient": patient,
        "selected_history": selected_history,   
        "history": history,                     
        "bodycharts": bodycharts,
        "observations": observations,
        "motions": motions,
        "treatments": treatments,
        "outcomes": outcomes,
        "hospital":hospital
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Prescription_{patient.mr_no}.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

def edit_patient_history(request, history_id):
    hospital = Hospital_data.objects.first()
    s_history = PatientHistory.objects.get(id=history_id)
    patient = s_history.patient
    staff = s_history.staff
    patient_id=request.POST.get('patient_id')
    bodychart = BodyChart.objects.filter(patient=patient, history=s_history).last()
    observation = GeneralObservation.objects.filter(patient=patient, history=s_history).last()
    motions = RangeOfMotion.objects.filter(patient=patient, history=s_history)
    outcome_measures = OutcomeMeasure.objects.filter(patient=patient, history=s_history)
    treatment = TreatmentPlan.objects.filter(patient=patient, history=s_history).last()
    managements = ManagementEntry.objects.filter(treatment_plan=treatment) if treatment else []

    if request.method == "POST":
        # --- Basic history ---
        s_history.chief_complaints = request.POST.get("chief_complaints")
        s_history.present_history = request.POST.get("present_history")
        s_history.past_medical_history = request.POST.get("past_medical_history")
        s_history.drug_history = request.POST.get("drug_history")
        s_history.save()

        # --- Body chart ---
        if bodychart:
            bodychart.pain_assessment = request.POST.get("pain_assessment")
            bodychart.pain_area = request.POST.get("pain_area")
            bodychart.type = request.POST.get("type")
            bodychart.pain_history = request.POST.get("pain_history")
            bodychart.pain_severity = request.POST.get("pain_severity")
            bodychart.save()
        else:
            bodychart = BodyChart.objects.create(
                staff=staff, patient=patient, history=s_history,
                pain_assessment=request.POST.get("pain_assessment"),
                pain_area=request.POST.get("pain_area"),
                type=request.POST.get("type"),
                pain_history=request.POST.get("pain_history"),
                pain_severity=request.POST.get("pain_severity"),
            )

        # --- General Observation ---
        if observation:
            observation.built = request.POST.get("built")
            observation.swelling = request.POST.get("swelling")
            observation.deformities = request.POST.get("deformities")
            observation.tropical_changes = request.POST.get("tropical_changes")
            observation.skin = request.POST.get("skin")
            observation.edema = request.POST.get("edema")
            observation.warmth = request.POST.get("warmth")
            observation.contractures = request.POST.get("contractures")
            observation.light_touch = request.POST.get("light_touch")
            observation.crude_touch = request.POST.get("crude_touch")
            observation.balance_sitting = request.POST.get("balance_sitting")
            observation.balance_standing = request.POST.get("balance_standing")
            observation.save()
        else:
            observation = GeneralObservation.objects.create(
                staff=staff, history=s_history, patient=patient,
                built=request.POST.get("built"),
                swelling=request.POST.get("swelling"),
                deformities=request.POST.get("deformities"),
                tropical_changes=request.POST.get("tropical_changes"),
                skin=request.POST.get("skin"),
                edema=request.POST.get("edema"),
                warmth=request.POST.get("warmth"),
                contractures=request.POST.get("contractures"),
                light_touch=request.POST.get("light_touch"),
                crude_touch=request.POST.get("crude_touch"),
                balance_sitting=request.POST.get("balance_sitting"),
                balance_standing=request.POST.get("balance_standing"),
            )

        # --- Range of Motion ---
        rom_ids = request.POST.getlist("rom_id[]")
        joints = request.POST.getlist("joint[]")
        aroms = request.POST.getlist("arom[]")
        proms = request.POST.getlist("prom[]")
        rom_dates=request.POST.getlist('rom_date[]')
        fall_risk = request.POST.get("fall_risk", "").strip()
        muscle_power = request.POST.get("muscle_power", "").strip()
        submitted_ids = [rid for rid in rom_ids if rid]  # Filter non-empty IDs

        if s_history:
            all_existing = RangeOfMotion.objects.filter(history=s_history)
            for existing in all_existing:
                if str(existing.id) not in submitted_ids:
                    existing.delete()
        for i in range(len(joints)):
            if not joints[i].strip():
                continue
            rom_id = rom_ids[i] if i < len(rom_ids) else None
            rom_date_str = rom_dates[i] if i < len(rom_dates) else None

            # === FIX: Ensure valid date ===
            rom_date = None
            if rom_date_str:
              try:
                rom_date = datetime.strptime(rom_date_str, '%Y-%m-%d').date()
              except ValueError:
                rom_date = date.today()   # Fallback to today if invalid
            else:
               rom_date = date.today()
            try:
                if rom_id:
                    rom = RangeOfMotion.objects.get(id=rom_id, history=s_history)
                    rom.date= rom_date
                    rom.joint = joints[i]
                    rom.arom = aroms[i]
                    rom.prom = proms[i]
                    rom.fall_risk = fall_risk
                    rom.muscle_power = muscle_power
                    rom.save()
                else:
                    RangeOfMotion.objects.create(
                staff=staff,
                patient=patient,
                history=s_history,
                date=rom_date,
                joint=joints[i].strip(),
                arom=aroms[i] if i < len(aroms) else "",
                prom=proms[i] if i < len(proms) else "",
                fall_risk=fall_risk,
                muscle_power=muscle_power,
            )
            except RangeOfMotion.DoesNotExist:
                # If ID exists in form but record not found, create as new
                RangeOfMotion.objects.create(
            staff=staff,
            patient=patient,
            history=s_history,
            date=rom_date,
            joint=joints[i].strip(),
            arom=aroms[i] if i < len(aroms) else "",
            prom=proms[i] if i < len(proms) else "",
            fall_risk=fall_risk,
            muscle_power=muscle_power,
        )

        # --- Outcome Measures ---
        om_ids = request.POST.getlist("outcome_id[]")
        om_dates = request.POST.getlist("outcome_date[]")
        om_useds = request.POST.getlist("outcome_used[]")
        om_pretests = request.POST.getlist("pre_test[]")
        om_posttests = request.POST.getlist("post_test[]")

        # Delete removed rows
        submitted_om_ids = [oid for oid in om_ids if oid]
        for existing in OutcomeMeasure.objects.filter(history=s_history):
            if str(existing.id) not in submitted_om_ids:
                existing.delete()

        # Update / Create
        for i in range(len(om_useds)):
            if not om_useds[i].strip():
                continue
            om_id = om_ids[i] if i < len(om_ids) else None

            if om_id:
                try:
                    om = OutcomeMeasure.objects.get(id=om_id, history=s_history)
                    om.date = om_dates[i] if om_dates[i] else None
                    om.outcome_used = om_useds[i]
                    om.pretest_score = om_pretests[i]
                    om.posttest_score = om_posttests[i]
                    om.save()
                except OutcomeMeasure.DoesNotExist:
                    pass
            else:
                OutcomeMeasure.objects.create(
                staff=staff, patient=patient, history=s_history,
                date=om_dates[i] if om_dates[i] else None,
                outcome_used=om_useds[i],
                pretest_score=om_pretests[i],
                posttest_score=om_posttests[i],
            )

        # --- Treatment ---
        if treatment:
            treatment.short_term_goals = request.POST.get("short_term_goals")
            treatment.long_term_goals = request.POST.get("long_term_goals")
            treatment.save()
        else:
            treatment = TreatmentPlan.objects.create(
                staff=staff, patient=patient, history=s_history,
                short_term_goals=request.POST.get("short_term_goals"),
                long_term_goals=request.POST.get("long_term_goals"),
            )

        # --- Management Entries ---
        m_ids = request.POST.getlist("management_id[]")
        m_dates = request.POST.getlist("date[]")
        m_texts = request.POST.getlist("management[]")
        m_reviews = request.POST.getlist("review_date[]")
        m_signs = request.POST.getlist("signature[]")

        # Delete removed rows
        submitted_m_ids = [mid for mid in m_ids if mid]
        for existing in ManagementEntry.objects.filter(treatment_plan=treatment):
            if str(existing.id) not in submitted_m_ids:
                existing.delete()

        # Update / Create
        for i in range(len(m_texts)):
            if not m_texts[i].strip():
                continue
            m_id = m_ids[i] if i < len(m_ids) else None

            if m_id:
                try:
                    m_entry = ManagementEntry.objects.get(id=m_id, treatment_plan=treatment)
                    m_entry.date = m_dates[i] if m_dates[i] else None
                    m_entry.management = m_texts[i]
                    m_entry.review_date = m_reviews[i] if i < len(m_reviews) else None
                    m_entry.signature = m_signs[i] if i < len(m_signs) else None
                    m_entry.save()
                except ManagementEntry.DoesNotExist:
                    pass
            else:
                ManagementEntry.objects.create(
                treatment_plan=treatment,
                staff=staff,
                date=m_dates[i] if m_dates[i] else None,
                management=m_texts[i],
                review_date=m_reviews[i] if i < len(m_reviews) else None,
                signature=m_signs[i] if i < len(m_signs) else None,
            )
        # for i in range(len(m_dates)):
        #     if not (m_dates[i] or m_texts[i]):
        #         continue
        #     m_id = m_ids[i] if i < len(m_ids) else None
        #     if m_id:
        #         try:
        #             m_entry = ManagementEntry.objects.get(id=m_id, treatment_plan=treatment)
        #             m_entry.date = m_dates[i] if m_dates[i] else None
        #             m_entry.management = m_texts[i]
        #             m_entry.review_date = m_reviews[i] if i < len(m_reviews) else None
        #             m_entry.signature = m_signs[i] if i < len(m_signs) else None
        #             m_entry.save()
        #         except ManagementEntry.DoesNotExist:
        #             pass
        #     else:
        #         ManagementEntry.objects.create(
        #             treatment_plan=treatment,
        #             staff=staff,
        #             date=m_dates[i] if m_dates[i] else None,
        #             management=m_texts[i],
        #             review_date=m_reviews[i] if i < len(m_reviews) else None,
        #             signature=m_signs[i] if i < len(m_signs) else None,
        #         )

        messages.success(request, "Patient history updated successfully.")
        return redirect("prescription_basic")

    return render(request, "patienthistory_edit.html", {
        "patient": patient,
        "s_history": s_history,
        "bodychart": bodychart,
        "observation": observation,
        "motions": motions,
        "outcome_measures": outcome_measures,
        "treatment": treatment,
        "managements": managements,
        "hospital": hospital,
        "staff": staff,
        "history": PatientHistory.objects.filter(patient=patient).order_by("-date_recorded"),
        "bodycharts": BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded"),
        "observations": GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded"),
        "motions": RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on"),
        "treatments": TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created"),
        "outcomes": OutcomeMeasure.objects.filter(patient=patient).order_by("-date"),
    })
    
def delete_patient_history(request, history_id):
    history = get_object_or_404(PatientHistory, id=history_id)

    # only allow POST for deletion
    if request.method == "POST":
        # outcome + outcome measures
        outcomes = OutcomeMeasure.objects.filter(history=history)
        for outcome in outcomes:
            OutcomeMeasure.objects.filter(history=history).delete()
        outcomes.delete()
    
        # treatments + managements
        treatments = TreatmentPlan.objects.filter(history=history)
        for treatment in treatments:
            ManagementEntry.objects.filter(treatment_plan=treatment).delete()
        treatments.delete()

        # direct models
        BodyChart.objects.filter(history=history).delete()
        GeneralObservation.objects.filter(history=history).delete()
        RangeOfMotion.objects.filter(history=history).delete()

        # finally history
        history.delete()

        messages.success(request, "Patient history and all related data deleted successfully.")
        return redirect("prescription_basic")

    # if someone GETs the delete url → just redirect back
    return redirect("prescription_basic")


def create_invoice(request):
    staff_id = request.session.get("staff_id")
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    staff = get_object_or_404(StaffRegistration, id=staff_id)
    hospital = Hospital_data.objects.first()
    patients = Patient.objects.all()
    doctors = StaffAllocation.objects.filter(designation__Designation="Doctor",status="active")
    allocation = get_object_or_404(StaffAllocation, staff=staff)
    is_doctor = StaffAllocation.objects.filter(
        staff=allocation.staff,
        designation__Designation__iexact="Doctor",
        status="active"
    ).exists()

    if request.method == "POST":
        try:
            patient_id = request.POST.get("patient_id")
            doctor_id = request.POST.get("doctor_id")
            date = request.POST.get("date")
            particulars = request.POST.getlist("particulars[]")
            qtys = request.POST.getlist("qty[]")
            rates = request.POST.getlist("rate[]")
            amounts = request.POST.getlist("amounts[]")

            patient = get_object_or_404(Patient, id=patient_id)
            doctor = get_object_or_404(StaffRegistration, id=doctor_id)

            today_str = now().strftime("%d%m%Y")
            prefix = f"INV{today_str}"
            last_invoice = Invoice.objects.filter(invoice_number__startswith=prefix).order_by("-id").first()
            next_number = (int(last_invoice.invoice_number[-3:]) + 1) if last_invoice else 1
            invoice_number = f"{prefix}{next_number:03d}"

            total = sum(float(a or (float(q or 0) * float(r or 0))) for q, r, a in zip(qtys, rates, amounts))
            payment_mode = request.POST.get("payment_mode")
            invoice = Invoice.objects.create(
                patient=patient,
                doctor=doctor,
                created_at=date,
                particulars=json.dumps(particulars),
                qty=json.dumps(qtys),
                rate=json.dumps(rates),
                amount=json.dumps(amounts),
                total_amount=total,
                invoice_number=invoice_number,
                payment_mode=payment_mode
            )
            return JsonResponse({"success": True, "invoice_id": invoice.id})

        except Exception as e:
            print("Error saving invoice:", e)
            return JsonResponse({"success": False, "error": str(e)})

    context = {
        "hospital": hospital,
        "is_doctor": is_doctor,
        "patients": patients,
        "doctors": doctors,
        "staff": staff,
    }
    return render(request, "invoice.html", context)

@csrf_exempt
def invoice_delete(request, invoice_id):
    if request.method == 'POST':
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            
            # Change status to Inactive instead of hard delete
            invoice.status = "Inactive"   # Make sure your Invoice model has a 'status' field
            invoice.save()
            
            return JsonResponse({
                "success": True,
                "message": "Invoice marked as Inactive successfully."
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=400)
    
    return JsonResponse({"success": False, "message": "Invalid request"}, status=405)

# --- Render Invoice as PDF ---
def invoice_pdf(request, pk):
    hospital = Hospital_data.objects.first()
    invoice = get_object_or_404(Invoice, pk=pk)
    amount_words = number_to_words(invoice.total_amount)
    html = render_to_string("invoice_pdf.html", {"invoice": invoice, "hospital": hospital,'amount_in_words': amount_words,})
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="Invoice_{invoice.id}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response


def invoice_list(request):
    staff_id = request.session.get("staff_id")
    staff = StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()

    search_query = request.GET.get('q', '')  # Changed from 'search' to 'q' to match template
    filter_staff = request.GET.get('staff', '')
    filter_dept = request.GET.get('department', '')
    patient_filter = request.GET.get('patient', '')  # NEW: Patient filter
    export = request.GET.get('export', None)
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    selected_payment_mode = request.GET.get("payment_mode", "")
    
    if staff_id:
        branch_id=StaffRegistration.objects.get(id=staff_id).branch_id
    allocation = StaffAllocation.objects.get(staff=staff_id)
    is_admin = StaffAllocation.objects.filter(
        staff=allocation.staff,
        designation__Designation__iexact="Admin",
        status="active"
    ).exists()
    # Staff and dept totals (use full queryset)
    if is_admin:
        invoices = Invoice.objects.all().exclude(status="Inactive")
    else:
        invoices = Invoice.objects.filter(doctor__branch=branch_id).exclude(status="Inactive")
        
    queryset = Invoice.objects.all().exclude(status="Inactive")
    if not is_admin:
        queryset = queryset.filter(doctor__branch=branch_id).select_related("doctor", "patient").order_by("-created_at").exclude(status="Inactive")

    # Apply filters dynamically - ALL FILTERS FIRST
    if search_query:
        queryset = queryset.filter(
            Q(invoice_number__icontains=search_query) |  # Fixed: use 'q' param
            Q(patient__name__icontains=search_query) |
            Q(doctor__name__icontains=search_query)
        ).exclude(status="Inactive")

    if filter_staff:
        if is_admin:
            queryset = queryset.filter(doctor__id=filter_staff).exclude(status="Inactive")
        else:
            queryset = queryset.filter(doctor__id=filter_staff, doctor__branch=branch_id).exclude(status="Inactive")

    if filter_dept:
        if is_admin:
            queryset = queryset.filter(doctor__allocations__department__id=filter_dept).exclude(status="Inactive")
        else:
            queryset = queryset.filter(
                doctor__allocations__department__id=filter_dept,
                doctor__branch=branch_id
            ).exclude(status="Inactive")

    # NEW: Apply patient filter
    if patient_filter:
        queryset = queryset.filter(patient_id=patient_filter).exclude(status="Inactive")
    
    if selected_payment_mode:
        queryset = queryset.filter(payment_mode=selected_payment_mode).exclude(status="Inactive")
        
    # Apply date filters LAST (after all other filters)
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            queryset = queryset.filter(created_at__range=[start, end]).exclude(status="Inactive")
        except ValueError:
            pass

    # NOW check for single patient - AFTER ALL FILTERS
    show_consolidated_print = False
    patient_id = None
    distinct_patients = queryset.values('patient__id').exclude(status="Inactive").distinct()
    if distinct_patients.count() == 1:
        patient_obj = distinct_patients.first()
        if patient_obj['patient__id']:
            show_consolidated_print = True
            patient_id = patient_obj['patient__id']

    # Group by date
    grouped_invoices = []
    for dt in queryset.values_list("created_at", flat=True).distinct().order_by("-created_at"):
        items = queryset.filter(created_at=dt).exclude(status="Inactive")
        total = items.aggregate(total=Sum("total_amount"))['total'] or 0
        grouped_invoices.append({
            "date": dt,
            "items": items,
            "total": total,
        })

    # Pagination (only if not exporting)
    if not export:
        paginator = Paginator(grouped_invoices, 3)  # 3 days per page
        page_num = request.GET.get("page")
        grouped_invoices = paginator.get_page(page_num)
    staff_totals = (
        queryset.values("doctor__id", "doctor__name")
        .annotate(total=Sum("total_amount"))
        .order_by("doctor__name")
    )
    # Monthly totals
    today = date.today()
    monthly_start = today.replace(day=1)
    if start_date and end_date:
        monthly_totals = (
            queryset.filter(created_at__gte=start_date, created_at__lte=end_date).exclude(status="Inactive")
            .annotate(month=ExtractMonth("created_at"), year=ExtractYear("created_at"))
            .values("month", "year")
            .annotate(total=Sum("total_amount"))
            .order_by("month", "year")
        )
        dept_totals = (
        queryset.filter(created_at__gte=start_date, created_at__lte=end_date).values("doctor__allocations__department__name")
        .annotate(total=Sum("total_amount"))
        .order_by("doctor__allocations__department__name")
    )
        staff_totals = (
        queryset.filter(created_at__gte=start_date, created_at__lte=end_date).values("doctor__id", "doctor__name")
        .annotate(total=Sum("total_amount"))
        .order_by("doctor__name")
    )
    else:
        monthly_totals = (
            queryset.filter(created_at__gte=monthly_start, created_at__lte=today)
            .annotate(month=ExtractMonth("created_at"), year=ExtractYear("created_at"))
            .values("month", "year")
            .annotate(total=Sum("total_amount"))
            .order_by("month", "year")
        )
    for m in monthly_totals:
        m["date_obj"] = date(m["year"], m["month"], 1)

    
    dept_totals = (
        queryset.values("doctor__allocations__department__name")
        .annotate(total=Sum("total_amount"))
        .order_by("doctor__allocations__department__name")
    )
    payment_mode_totals = (queryset.values("payment_mode").annotate(transaction_count=Count("id"),
        total_amount=Sum("total_amount")).order_by("payment_mode"))
    # Lists for filters
    staff_list = StaffRegistration.objects.filter(status="Active")
    dept_list = Department.objects.all()
    all_patients = Patient.objects.all().order_by('name')  # For dropdown

    total = queryset.aggregate(total=Sum("total_amount"))["total"] or 0

    context = {
        "grouped_invoices": grouped_invoices,
        "monthly_totals": monthly_totals,
        "staff_totals": staff_totals,
        "dept_totals": dept_totals,
        "staff_list": staff_list,
        "dept_list": dept_list,
        "filter_staff": filter_staff,
        "filter_dept": filter_dept,
        "total": total,
        "hospital": hospital,
        "staff": staff,
        "patients": all_patients,  # For dropdown
        'patient_id': patient_id,
        "selected_patient": patient_filter,  # For selected attribute
        'show_consolidated_print': show_consolidated_print,
        "search_query": search_query,
        'is_export_excel': export == 'excel',
        'is_export': export == 'pdf',
        'payment_mode_totals':payment_mode_totals,
        'selected_payment_mode': selected_payment_mode,

    }
    return render(request, "invoice_list.html", context)

def scoliosis(request):
    patients = Patient.objects.all()
    staff_id=request.session.get("staff_id")
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    staff=StaffRegistration.objects.get(id=staff_id)
    today = date.today().strftime("%d/%m/%Y")
    schroth_options = SchrothClassification.objects.all()
    hep_options =HEP.objects.all()
    manual_options = ManualTechnique.objects.all()
    doctors = StaffAllocation.objects.filter(designation__Designation="Doctor",status="Active")
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        doctor_id = request.POST.get('doctor_id')
        patient = Patient.objects.get(id=patient_id) if patient_id else None
        doctor = StaffRegistration.objects.get(id=doctor_id) if doctor_id else None
        
        if not patient_id or not doctor_id:
            messages.warning(
                request,
                "Please select both Patient and Doctor before saving the assessment."
            )
            return redirect(request.path) 

        scoliosis = ScoliosisAssessment.objects.create(
            patient=patient,
            doctor=doctor,
            date=request.POST.get('date'),
            height_cm=request.POST.get('height_cm') or None,
            weight_kg=request.POST.get('weight_kg') or None,
            diagnosis_pattern=request.POST.get('diagnosis_pattern') or None,
            uev=request.POST.get('uev') or None,
            lev=request.POST.get('lev') or None,
            lumbar_lev=request.POST.get('lumbar_lev') or None,
            cobbs_angle=request.POST.get('cobbs_angle') or None,
            cobbs_angle_L=request.POST.get('scoliometer_l') or None,
            scoliometer_ut=request.POST.get('scoliometer_ut') or None,
            scoliometer_t=request.POST.get('scoliometer_t') or None,
            scoliometer_l=request.POST.get('scoliometer_l') or None,
            brace_used=request.POST.get('brace_used') == "True",
            menses_since=request.POST.get('menses_since') or None,
            other_diseases=request.POST.get('other_diseases') or None,
            shoe_lift=request.POST.get('shoe_lift') or None,
            family_history=request.POST.get('family_history')  or None,
            schroth_classification=request.POST.get('schroth_classification') or request.POST.get('schroth_classification_other')  or None,
            hep=request.POST.getlist('hep')  or None,
            manual_technique=request.POST.get('manual_technique')  or None,
            xray=request.FILES.get('xray')  or None,
            diagram=request.FILES.get('diagram')  or None,
        )
        messages.success(request, "Scoliosis Assessment saved successfully.")
        return redirect('scoliosis_report',assessment_id=scoliosis.id)        
    context={'hospital':Hospital_data.objects.first(),'patients':patients,'today':today,"schroth_options": schroth_options,
        "hep_options": hep_options,
        "manual_options": manual_options,'doctors':doctors,'staff':staff}
    return render(request,'Scoliosis_Assessment.html',context)

def scoliosis_assessment_list(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    search = request.GET.get('search', '')
    hospital=Hospital_data.objects.first()
    search = request.GET.get('search', '')
    scoliosis_qs = ScoliosisAssessment.objects.all().order_by('-created_at')
    export = request.GET.get('export', None)
    if search:
        scoliosis_qs = scoliosis_qs.filter(
            models.Q(patient__name__icontains=search) |
            models.Q(doctor__name__icontains=search) |
            models.Q(diagnosis_pattern__icontains=search)
        )
    if export in ['excel', 'pdf']:
        scoliosis_list = scoliosis_qs.order_by('id')
    else:
        paginator = Paginator(scoliosis_qs.order_by('id'), 10)
        page_number = request.GET.get('page')
        scoliosis_list = paginator.get_page(page_number)
    context={"hospital":hospital,'scoliosis_list': scoliosis_list,
        'search': search,"staff":staff,'is_export_excel': export == 'excel',
        'is_export': export == 'pdf',}
    return render(request,'Scoliosis_list_view.html',context)


def number_to_words(num):
    num = float(num)
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
             "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def in_words(n):
        n = int(n)
        if n < 20:
            return units[n]
        elif n < 100:
            return tens[n // 10] + (" " + units[n % 10] if n % 10 else "")
        elif n < 1000:
            return units[n // 100] + " Hundred" + (" " + in_words(n % 100) if n % 100 else "")
        elif n < 100000:
            return in_words(n // 1000) + " Thousand" + (" " + in_words(n % 1000) if n % 1000 else "")
        elif n < 10000000:
            return in_words(n // 100000) + " Lakh" + (" " + in_words(n % 100000) if n % 100000 else "")
        else:
            return in_words(n // 10000000) + " Crore" + (" " + in_words(n % 10000000) if n % 10000000 else "")

    parts = str(round(num, 2)).split(".")
    rupees = int(parts[0])
    paise = int(parts[1]) if len(parts) > 1 else 0

    words = in_words(rupees) + " Rupees"
    if paise:
        words += " and " + in_words(paise) + " Paise"
    return words + " Only"



def schroth_classification(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    if request.method == "POST":
        name = request.POST.get("name")
        if SchrothClassification.objects.filter(name=name).exists():
            messages.error(request,"Schroth Classification Already exists");
        else:
            SchrothClassification.objects.create(name=name)
            messages.success(request, 'Schroth Classification added successfully.')
    return render(request, "scroth_add.html",{'staff':staff,'hospital':hospital})

def schroth_list(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    queryset = SchrothClassification.objects.all().order_by('id')
    export = request.GET.get('export', None)

    queryset = SchrothClassification.objects.all().order_by('id')
    if search_query:
        queryset = queryset.filter(name__icontains=search_query)

    if export in ['excel', 'pdf']:
        schroth_items = queryset.order_by('id')
    else:
        paginator = Paginator(queryset.order_by('id'), 10)
        page_number = request.GET.get('page')
        schroth_items = paginator.get_page(page_number)
    return render(request, "scroth_list.html", {
        'schroth_items': schroth_items,
        'search_query': search_query,
        'staff':staff,'hospital':hospital,'is_export_excel': export == 'excel',
        'is_export': export == 'pdf',
    })

def schroth_edit(request, id):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    item = get_object_or_404(SchrothClassification, id=id)
    if request.method == "POST":
        item.name = request.POST.get("name")
        item.save()
        messages.success(request, 'Schroth updated successfully.')
    return render(request, "scroth_edit.html", {"item": item,'staff':staff,'hospital':hospital,})

def schroth_delete(request, id):
    item = get_object_or_404(SchrothClassification, id=id)
    item.delete()
    return redirect('schroth_list')


def hep(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    if request.method == "POST":
        name = request.POST.get("name")
        if HEP.objects.filter(name=name).exists():
            messages.error(request,"This HEP option already exists.")
        else:
            HEP.objects.create(name=name)
            messages.success(request, 'HEP added successfully.')
    return render(request, "hep_add.html",{'staff':staff,'hospital':hospital,})

def hep_list(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    export = request.GET.get('export', None)

    # Only query items if not exporting to Excel/PDF or still needed
    if export not in ['excel', 'pdf']:
        hep_items = HEP.objects.all().order_by('id')
        if search_query:
            hep_items = hep_items.filter(name__icontains=search_query)
        # Pagination
        paginator = Paginator(hep_items, 10)
        page_number = request.GET.get('page')
        hep_items = paginator.get_page(page_number)
    else:
        # For export, get all filtered items without pagination
        hep_items = HEP.objects.all().order_by('id')
        if search_query:
            hep_items = hep_items.filter(name__icontains=search_query)
    return render(request, "hep_list.html", {
        'hep_items': hep_items,
        'search_query': search_query,
        'staff':staff,'hospital':hospital,'is_export': export=='pdf',
        'is_export_excel':export=='excel',
    })

def hep_edit(request, id):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    item = get_object_or_404(HEP, id=id)
    if request.method == "POST":
        item.name = request.POST.get("name")
        item.save()
        messages.success(request, 'HEP updated successfully.')
    return render(request, "hep_edit.html", {"item": item,'staff':staff,'hospital':hospital,})

def hep_delete(request, id):
    item = get_object_or_404(HEP, id=id)
    item.delete()
    return redirect('hep_list')


# --- MANUAL TECHNIQUES ---
def manual_technique(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    if request.method == "POST":
        name = request.POST.get("name")
        if ManualTechnique.objects.filter(name=name).exists():
            messages.error(request,"This Manual Technique already exists!!")
        else:
            ManualTechnique.objects.create(name=name)
            messages.success(request, 'Manual Technique added successfully.')
    return render(request, "manual_add.html",{'staff':staff,'hospital':hospital})

def manual_list(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    queryset = ManualTechnique.objects.all().order_by('id')
    export = request.GET.get('export', None)

    queryset = ManualTechnique.objects.all()
    if search_query:
        queryset = queryset.filter(name__icontains=search_query)

    if export in ['excel', 'pdf']:
        manual_items = queryset.order_by('id')
    else:
        paginator = Paginator(queryset.order_by('id'), 10)
        page_number = request.GET.get('page')
        manual_items = paginator.get_page(page_number)
    if search_query:
        queryset = queryset.filter(name__icontains=search_query)
    return render(request, "manual_list.html", {
        'manual_items': manual_items,
        'search_query': search_query,
        'staff':staff,'hospital':hospital,'is_export_excel': export == 'excel',
        'is_export': export == 'pdf',
    })

def manual_edit(request, id):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    item = get_object_or_404(ManualTechnique, id=id)
    if request.method == "POST":
        item.name = request.POST.get("name")
        item.save()
        messages.success(request, 'Manual Technique updated successfully.')
    return render(request, "manual_edit.html", {"item": item,'staff':staff,'hospital':hospital,})

def manual_delete(request, id):
    item = get_object_or_404(ManualTechnique, id=id)
    item.delete()
    return redirect('manual_list')

def scoliosis_report(request, assessment_id):
    """
    Display a detailed Scoliosis Assessment report with hospital header
    """
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    # Get the assessment record
    assessment = get_object_or_404(ScoliosisAssessment, id=assessment_id)

    # Get hospital info (assuming only one hospital record)
    hospital = Hospital_data.objects.first()


    context = {
        "assessment": assessment,
        "hospital": hospital,
        "staff":staff
    }
    return render(request, "Scholiosis_report.html", context)

def edit_scoliosis(request, pk):
    staff_id = request.session.get("staff_id")
    staff = StaffRegistration.objects.get(id=staff_id)

    hospital = Hospital_data.objects.first()
    assessment = get_object_or_404(ScoliosisAssessment, id=pk)

    schroth_options = SchrothClassification.objects.all()
    hep_options = HEP.objects.all()
    manual_options = ManualTechnique.objects.all()
    doctors = StaffAllocation.objects.filter(designation__Designation="Doctor",status="Active")

    if request.method == "POST":
        patient_id = request.POST.get("patient_id")
        doctor_id = request.POST.get("doctor_id")

        if not patient_id or not doctor_id:
            messages.error(request,"Patient or Doctor is not correctly selected")
            return redirect(request.path)

        assessment.patient_id = patient_id
        assessment.doctor_id = doctor_id
        assessment.date = request.POST.get("date")

        # Mandatory numeric
        assessment.height_cm = request.POST.get("height_cm") or None
        assessment.weight_kg = request.POST.get("weight_kg") or None

        # Optional clinical fields
        assessment.diagnosis_pattern = request.POST.get("diagnosis_pattern") or None
        assessment.uev = request.POST.get("uev") or None
        assessment.lev = request.POST.get("lev") or None
        assessment.lumbar_lev = request.POST.get("lumbar_lev") or None

        assessment.cobbs_angle = request.POST.get("cobbs_angle") or None
        assessment.cobbs_angle_L = request.POST.get("cobbs_angle_L") or None

        assessment.scoliometer_ut = request.POST.get("scoliometer_ut") or None
        assessment.scoliometer_t = request.POST.get("scoliometer_t") or None
        assessment.scoliometer_l = request.POST.get("scoliometer_l") or None

        assessment.brace_used = request.POST.get("brace_used") == "True"

        # Additional medical
        assessment.menses_since = request.POST.get("menses_since") or None
        assessment.other_diseases = request.POST.get("other_diseases") or None
        assessment.shoe_lift = request.POST.get("shoe_lift") or None
        assessment.family_history = request.POST.get("family_history") or None

        # Classification & therapy
        assessment.schroth_classification = request.POST.get("schroth_classification") or None
        assessment.hep = request.POST.getlist("hep") or None
        assessment.manual_technique = request.POST.get("manual_technique") or None

        # Optional file replace
        if request.FILES.get("xray"):
            assessment.xray = request.FILES["xray"]

        if request.FILES.get("diagram"):
            assessment.diagram = request.FILES["diagram"]

        assessment.save()
        return redirect("scoliosis_list")

    context = {
        "assessment": assessment,
        "schroth_options": schroth_options,
        "hep_options": hep_options,
        "manual_options": manual_options,
        "doctors": doctors,
        "hospital": hospital,
        "staff": staff,
    }

    return render(request, "scoliosis_edit.html", context)


def add_expense_type(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    if request.method == "POST":
        expense_type=request.POST.get('expense_type')
        if Expense_Type.objects.filter(expense_type=expense_type).exists():
            messages.error(request,'This Expense Type is already exists!!')
        else:
            Expense_Type.objects.create(expense_type=expense_type)
            messages.success(request,"New Expense type added successfully!")
    return render(request,"expensetype_add.html",{"hospital":hospital,
        "staff":staff})


def expensetype_table(request):
    hospital = Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'

    expense_types = Expense_Type.objects.all()

    if search_query:
        expense_types = expense_types.filter(expense_type__icontains=search_query)

    # Apply pagination only when not exporting
    if not is_export and not is_export_excel:
        paginator = Paginator(expense_types, 10)
        page = request.GET.get('page')
        expense_types = paginator.get_page(page)

    return render(request, 'ExpenseType_Table.html', {
        'expense_types': expense_types,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,
        'hospital': hospital,
        'staff': StaffRegistration.objects.get(id=request.session.get("staff_id"))
    })
    
def delete_expense_type(request, id):
    expense_type = get_object_or_404(Expense_Type, id=id)
    
    # Assuming the model has a field `active` (Boolean) or `status` (CharField)
    if hasattr(expense_type, 'active'):
        expense_type.active = 'inactive' if isinstance(expense_type.active, str) else False
    elif hasattr(expense_type, 'status'):
        expense_type.status = 'inactive'
    else:
        messages.error(request, "No status/active field found on ExpenseType model.")
        return redirect('expensetype_table')

    expense_type.save()
    messages.success(request, f"Expense type '{expense_type.expense_type}' deleted successfully.")
    return redirect('expensetype_table')

def edit_expense_type(request, id):
    hospital = Hospital_data.objects.first()
    staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))
    expense_type = get_object_or_404(Expense_Type, id=id)

    if request.method == "POST":
        expense_type.expense_type = request.POST.get("expense_type")
        expense_type.active = request.POST.get("status")
        expense_type.save()
        messages.success(request, "Expense Type updated successfully.")
        return redirect("expensetype_table")

    return render(request, "expensetype_edit.html", {
        "expense_type": expense_type,
        "hospital": hospital,
        "staff": staff,
    })
    
def add_expense(request):
    hospital = Hospital_data.objects.first()
    staff_id=request.session.get("staff_id")
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))

    expense_types = Expense_Type.objects.filter(active="active")

    if request.method == "POST":
        expense_type_id = request.POST.get("expense_type")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        date=request.POST.get("date")

        if not expense_type_id or not amount:
            messages.error(request, "Please select expense type and enter amount.")
            return redirect("add_expense")
        
        Expense.objects.create(
            expense_type_id=expense_type_id,
            amount=amount,
            description=description,
            staff=staff,
            date=date
        )
        messages.success(request, "Expense saved successfully.")
        return redirect("add_expense")

    return render(request, "expense_add.html", {"expense_types": expense_types,"hospital":hospital,"staff":staff})


def expense_table(request):
    hospital = Hospital_data.objects.first()
    staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))

    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    export_type = request.GET.get('export')
    is_export_excel = export_type == 'excel'
    is_export_pdf = export_type == 'pdf'

     # ------------------------------------------------------------------------------
    # BASE QUERYSET
    # ------------------------------------------------------------------------------
    expenses = (
        Expense.objects.filter(status="active")
        .select_related("expense_type", "staff")
        .order_by("-date", "-id")
    )

    # Search filter
    if search_query:
        expenses = expenses.filter(expense_type__expense_type__icontains=search_query)

    # Date filter
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            expenses = expenses.filter(date__range=[start, end])
        except ValueError:
            pass

    # ------------------------------------------------------------------------------
    # MONTH → DATE GROUPING
    # ------------------------------------------------------------------------------
    grouped_months = []

    # Get unique months
    months = (
        expenses.annotate(
            year=ExtractYear("date"),
            month=ExtractMonth("date")
        )
        .values("year", "month")
        .distinct()
        .order_by("-year", "-month")
    )

    for m in months:
        year = m["year"]
        month = m["month"]

        # Get all items in this month
        month_items = expenses.filter(date__year=year, date__month=month)

        # Get unique dates
        dates = (
            month_items.values_list("date", flat=True)
            .distinct()
            .order_by("-date")
        )

        date_groups = []
        for d in dates:
            day_items = month_items.filter(date=d)
            day_total = day_items.aggregate(total=Sum("amount"))["total"] or 0

            date_groups.append({
                "date": d,
                "items": day_items,
                "daily_total": day_total,
            })

        month_total = month_items.aggregate(total=Sum("amount"))["total"] or 0

        grouped_months.append({
            "month_name": date(year, month, 1).strftime("%B %Y"),
            "dates": date_groups,
            "month_total": month_total,
        })

    # ------------------------------------------------------------------------------
    # MONTHLY TOTAL (FOOTER)
    # ------------------------------------------------------------------------------
    if start_date and end_date:
        monthly_total = expenses.aggregate(total=Sum("amount"))["total"] or 0
    else:
        today = date.today()
        monthly_start = today.replace(day=1)

        monthly_total = (
            Expense.objects.filter(
                status="active",
                date__range=[monthly_start, today]
            ).aggregate(total=Sum("amount"))["total"] or 0
        )

    # ------------------------------------------------------------------------------
    # PAGINATION – NOT FOR EXPORT
    # ------------------------------------------------------------------------------
    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(grouped_months, 2)  # 2 months per page
        page = request.GET.get("page")
        grouped_months = paginator.get_page(page)

    context = {
        "grouped_months": grouped_months,
        "hospital": hospital,
        "staff": staff,
        "search_query": search_query,
        "start_date": start_date,
        "end_date": end_date,
        "monthly_total": monthly_total,
        "is_export_excel": is_export_excel,
        "is_export": is_export_pdf,
    }

    return render(request, "expense_table.html", context)


def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.status = "inactive"
    expense.save()
    messages.success(request, "Expense marked as inactive successfully.")
    return redirect("expense_table")


def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense_types = Expense_Type.objects.filter(active="active")
    hospital = Hospital_data.objects.first()
    staff = None
    if request.session.get("staff_id"):
        staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))

    if request.method == "POST":
        expense.expense_type_id = request.POST.get("expense_type")
        expense.amount = request.POST.get("amount")
        expense.date = request.POST.get("date")
        expense.description = request.POST.get("description")
        expense.staff=staff
        expense.save()
        messages.success(request, "Expense updated successfully.")
        return redirect("expense_table")

    return render(request, "expense_edit.html", {
        "expense": expense,
        "expense_types": expense_types,
        "hospital": hospital,
        "staff": staff
    })
    
def calendar(request):
    staff_id = request.session.get("staff_id")
    if not staff_id:
        return redirect("login")

    hospital = Hospital_data.objects.first()

    allocation = StaffAllocation.objects.filter(
        staff_id=staff_id,
        status="active"
    ).select_related("designation").first()

    is_admin = allocation and allocation.designation.Designation.lower() == "admin"

    # ✅ STAFF SELECTION LOGIC (VERY IMPORTANT)
    if "staff" in request.GET:
        selected_staff = request.GET.get("staff")  # '' means All Staff
    else:
        # first load
        selected_staff = "" if is_admin else str(staff_id)

    appointments_qs = Appointment.objects.all()

    # ✅ Filter ONLY if staff explicitly selected
    if selected_staff:
        appointments_qs = appointments_qs.filter(doctor_id=selected_staff)

    appointments = appointments_qs.values(
        "appointment_date"
    ).annotate(count=Count("id"))

    appointments_per_date = {
        a["appointment_date"].isoformat(): a["count"]
        for a in appointments
    }

    staff_list = StaffAllocation.objects.filter(
        designation__Designation__iexact="Doctor",
        status="active"
    ).select_related("staff")

    context = {
        "hospital": hospital,
        "appointments_per_date": appointments_per_date,
        "staff_list": staff_list,
        "selected_staff": selected_staff,
        "staff": StaffRegistration.objects.get(id=staff_id),
        "is_admin": is_admin,
    }

    return render(request, "calendar.html", context)

def add_scoliosis_followup(request, scoliosis_id):
    scoliosis = get_object_or_404(ScoliosisAssessment, id=scoliosis_id)
    staff_id = request.session.get("staff_id")
    if not staff_id:
        messages.error(request, "Staff not found in session.")
        return redirect("login")

    staff = get_object_or_404(StaffRegistration, id=staff_id)
    hospital = Hospital_data.objects.first()

    if request.method == "POST":
        followup = ScoliosisFollowUp.objects.create(
            scoliosis=scoliosis,
            followup_date=request.POST.get("followup_date") or timezone.now().date(),
            diagnosis_pattern=request.POST.get("diagnosis_pattern"),
            uev=request.POST.get("uev"),
            lev=request.POST.get("lev"),
            lumbar_lev=request.POST.get("lumbar_lev"),
            cobbs_angle=request.POST.get("cobbs_angle") or None,
            cobbs_angle_L=request.POST.get("cobbs_angle_L") or None,
            scoliometer_ut=request.POST.get("scoliometer_ut") or None,
            scoliometer_t=request.POST.get("scoliometer_t") or None,
            scoliometer_l=request.POST.get("scoliometer_l") or None,
            brace_used=bool(request.POST.get("brace_used")),
            pain_level=request.POST.get("pain_level") or None,
            notes=request.POST.get("notes"),
        )
        messages.success(request, "Follow-up added successfully!")

    return render(request, "add_followup.html", {"scoliosis": scoliosis,"hospital":hospital,"staff":staff})

def medicine_category(request):
    hospital=Hospital_data.objects.first()
    if request.method == "POST":
        name = request.POST.get("medicine_category")
        status = 1
        Medicine_Category.objects.create(name=name, status=status)
    medicine_category = Medicine_Category.objects.all()
    return render(request, 'medicine_category_master.html', {"category":medicine_category,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})


def medicine_category_list(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    category_qs = Medicine_Category.objects.all()
    if search_query:
        category_qs = category_qs.filter(name__icontains=search_query)
    medical_store=Medical_Store.objects.first()
    if not request.GET.get('export'):
        paginator = Paginator(category_qs, 10)
        page_number = request.GET.get('page')
        category = paginator.get_page(page_number)

    return render(request, 'medicine_category_list.html', {
        'category': category,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
        'is_export_excel': request.GET.get('export') == 'excel',
        'is_export': request.GET.get('export') == 'pdf',
        'medical_store':medical_store,
    })
    
    
def medical_store(request):
    hospital=Hospital_data.objects.first()
    store=Medical_Store.objects.first()
    if request.method == 'POST':
        name = request.POST.get('storeName')
        logo = request.FILES.get('storeLogo')
        reg_no = request.POST.get('regNo')
        gst_no = request.POST.get('gstNo')
        manager = request.POST.get('managerName')
        contact = request.POST.get('managerContact')
        email = request.POST.get('email')
        address = request.POST.get('storeAddress')

        if Medical_Store.objects.first():
            messages.warning(request, "Medical Store already Registered.")
        else:
            Medical_Store.objects.create(
                name=name,
                logo=logo,
                registration_number=reg_no,
                gst_number=gst_no,
                manager_name=manager,
                manager_contact=contact,
                email=email,
                address=address
            )
            messages.success(request, "Medical Store registered successfully!")
        return redirect('medical_store')

    return render(request, 'medical_store.html',{"hospital":hospital,"store":store,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def Medical_store_list(request):
    hospital=Hospital_data.objects.first()
    search_query = request.GET.get('search', '')
    is_export = request.GET.get('export') == 'pdf'
    is_export_excel = request.GET.get('export') == 'excel'
    medical_store=Medical_Store.objects.first()
    stores = Medical_Store.objects.all()
    staff=StaffRegistration.objects.get(id=request.session.get("staff_id"))
    if search_query:
        stores = stores.filter(name__icontains=search_query)

    if not is_export and not is_export_excel:
        paginator = Paginator(stores, 10)
        page = request.GET.get('page')
        stores = paginator.get_page(page)

    return render(request, 'medical_store_list.html', {
        'stores': stores,
        'hospital':hospital,
        'search_query': search_query,
        'is_export': is_export,
        'is_export_excel': is_export_excel,
        'staff':staff,
        'medical_store':medical_store

    })
    
    
def medicine_category_edit(request, category_id):
    hospital=Hospital_data.objects.first()
    medicine_category = get_object_or_404(Medicine_Category, id=category_id)
    if request.method == 'POST':
        medicine_category.name = request.POST.get('medicine_category_name')
        medicine_category.status = True if request.POST.get('status') == 'Active' else False
        medicine_category.save()
        return redirect('medicine_category_list')
    return render(request, 'medicine_category_edit.html', {'medicine_category': medicine_category,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),})


def medicine_store_edit(request, store_id):
    store = get_object_or_404(Medical_Store, id=store_id)
    hospital=Hospital_data.objects.first()
    if request.method == 'POST':
        store.name = request.POST.get('storeName')
        store.registration_number = request.POST.get('regNo')
        store.gst_number = request.POST.get('gstNo')
        store.manager_name = request.POST.get('managerName')
        store.manager_contact = request.POST.get('managerContact')
        store.email = request.POST.get('email')
        store.address = request.POST.get('storeAddress')

        # Handle optional logo update
        if 'storeLogo' in request.FILES:
            store.logo = request.FILES['storeLogo']

        store.save()
        messages.success(request, "Medical Store details updated successfully.")
        return redirect('medical_store_list')  # or wherever your list page is

    return render(request, 'medical_store_edit.html', {'store': store,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id"))})

def tax_master(request):
    hospital = Hospital_data.objects.first()
    staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))
    taxes = TaxMaster.objects.all()

    if request.method == "POST":
        tax_percent = request.POST.get('tax_percent')
        if TaxMaster.objects.filter(tax_percent=tax_percent).exists():
            messages.error(request, "Tax already exists!")
        else:
            TaxMaster.objects.create(
            tax_percent=tax_percent
        )
            messages.success(request, "Tax added successfully!")
            return redirect('tax_master')

    return render(request, 'tax_master.html', {'taxes': taxes,"hospital":hospital,"staff":staff})


def medicine_master(request):
    hospital = Hospital_data.objects.first()
    staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))
    tax_master = TaxMaster.objects.all()
    category=Medicine_Category.objects.all()
    if request.method == "POST":
        item_code = request.POST.get('item_code')
        hsn_code = request.POST.get('hsn_code')
        medicine_name = request.POST.get('medicine_name')
        category_id = request.POST.get('category')
        generic_name = request.POST.get('generic_name')
        rack_number = request.POST.get('rack_number')
        base_unit = request.POST.get('base_unit')
        side_effects = request.POST.get('side_effects')
        tax_percentage = request.POST.get('tax_percentage')
        if MedicineMaster.objects.filter(item_code=item_code,medicine_name=medicine_name).exists():
            messages.error(request, "Medicine already exists!")  
        else:
            try:
                selected_category = Medicine_Category.objects.get(id=category_id)
            except Medicine_Category.DoesNotExist:
                messages.error(request, "Invalid category selected.")
                return redirect('medicine_master')
            MedicineMaster.objects.create(
            staff=staff,
            item_code=item_code,
            hsn_code=hsn_code,
            medicine_name=medicine_name,
            category=selected_category,
            generic_name=generic_name,
            rack_number=rack_number,
            base_unit=base_unit,
            side_effects=side_effects,
            tax_id=tax_percentage
        )
            messages.success(request, "Medicine registered successfully!")
            return redirect('medicine_master')
    return render(request, 'medicine_master.html', {"category":category,'tax_master': tax_master,"hospital":hospital,"staff":staff})



def medicine_table(request):
    search_query = request.GET.get('search', '').strip()
    hospital=Hospital_data.objects.first()
    medicines = MedicineMaster.objects.all().order_by('id')

    if search_query:
        medicines = medicines.filter(medicine_name__icontains=search_query)

    medical_store=Medical_Store.objects.first()
    if not request.GET.get('export'):
        paginator = Paginator(medicines, 10)
        page_number = request.GET.get('page')
        medicines = paginator.get_page(page_number)

    return render(request, 'medicine_list.html', {
        'medicines': medicines,"medical_store":medical_store,"hospital":hospital,"staff":StaffRegistration.objects.get(id=request.session.get("staff_id")),
        'is_export_excel': request.GET.get('export') == 'excel',
        'is_export': request.GET.get('export') == 'pdf',
    })
    
    
def edit_medicine(request, pk):
    medicine = get_object_or_404(MedicineMaster, id=pk)
    taxes = TaxMaster.objects.all()
    hospital=Hospital_data.objects.first()
    categories = Medicine_Category.objects.all()
    staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))

    if request.method == "POST":
        medicine.item_code = request.POST.get('item_code')
        medicine.hsn_code = request.POST.get('hsn_code')
        medicine.medicine_name = request.POST.get('medicine_name')
        category_id = request.POST.get('category')
        try:
            selected_category = Medicine_Category.objects.get(id=category_id)
            medicine.category = selected_category  # ✅ Assign object, not ID
        except Medicine_Category.DoesNotExist:
            messages.error(request, "Invalid category selected.")
            return redirect('edit_medicine', pk=medicine.id)
        medicine.generic_name = request.POST.get('generic_name')
        medicine.rack_number = request.POST.get('rack_number')
        medicine.base_unit = request.POST.get('base_unit')
        medicine.tax_id = request.POST.get('tax')
        medicine.staff_id = request.POST.get('staff')
        medicine.save()
        messages.success(request, "Medicine updated successfully.")
        return redirect('medicine_table')

    context = {
        "medicine": medicine,
        "taxes": taxes,
        "categories": categories,
        "staff": staff,
        "hospital":hospital,        
    }
    return render(request, "medicine_edit.html", context)


def company_master(request):
    hospital = Hospital_data.objects.first()
    staff = StaffRegistration.objects.get(id=request.session.get("staff_id"))

    if request.method == "POST":
        company = request.POST.get('company')
        if Company.objects.filter(name=company).exists():
            messages.error(request, "Company already exists!")
        else:
            Company.objects.create(
            name=company
        )
            messages.success(request, "Company added successfully!")
            return redirect('company_master')

    return render(request, 'company_master.html', {"hospital":hospital,"staff":staff})




def tax_table(request):
    search_query = request.GET.get('search', '').strip()
    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'
    hospital = Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    staff = StaffRegistration.objects.get(id=staff_id)
    taxes = TaxMaster.objects.all().order_by('-id')
    medical_store=Medical_Store.objects.first()
    if search_query:
        taxes = taxes.filter(
            Q(tax_name__icontains=search_query) |
            Q(tax_percent__icontains=search_query)
        )   

    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(taxes, 10)
        page_number = request.GET.get('page')
        taxes = paginator.get_page(page_number)

    context = {
        'taxes': taxes,
        'is_export_excel': is_export_excel,
        'is_export': is_export_pdf,
        'hospital': hospital,
        'staff': staff,
        'medical_store':medical_store
    }
    return render(request, 'tax_table.html', context)


def company_table(request):
    search_query = request.GET.get('search', '').strip()
    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'
    hospital = Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    staff = StaffRegistration.objects.get(id=staff_id)
    company = Company.objects.all().order_by('-id')
    medical_store=Medical_Store.objects.first()
    if search_query:
        company = company.filter(
            Q(name__icontains=search_query) 
            )   

    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(company, 10)
        page_number = request.GET.get('page')
        company = paginator.get_page(page_number)

    context = {
        'company': company,
        'is_export_excel': is_export_excel,
        'is_export': is_export_pdf,
        'hospital': hospital,
        'staff': staff,
        'medical_store':medical_store
    }
    return render(request, 'company_table.html', context)


def company_edit(request, company_id):
    hospital = Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    staff = StaffRegistration.objects.get(id=staff_id)
    company = get_object_or_404(Company, id=company_id)
    medical_store=Medical_Store.objects.first()
    if request.method == 'POST':
        company.name = request.POST.get('name')
        company.save()
        return redirect('company_table')

    return render(request, 'company_edit.html', {
        'company': company,
        'hospital': hospital,
        'staff': staff,
        "medical_store":medical_store,
    })

def tax_edit(request, tax_id):
    hospital = Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    staff = StaffRegistration.objects.get(id=staff_id)
    tax = get_object_or_404(TaxMaster, id=tax_id)
    medical_store=Medical_Store.objects.first()
    if request.method == 'POST':
        tax.tax_name = request.POST.get('tax_name')
        tax.tax_percentage = request.POST.get('tax_percentage')
        tax.status = True if request.POST.get('status') == 'on' else False
        tax.hospital = hospital
        tax.staff = staff
        tax.save()
        return redirect('tax_table')

    return render(request, 'tax_edit.html', {
        'tax': tax,
        'hospital': hospital,
        'staff': staff,
        "medical_store":medical_store,
    })
    

def supplier_master(request):
    hospital = Hospital_data.objects.first()
    staff = None
    if request.session.get('staff_id'):
        staff = StaffRegistration.objects.filter(id=request.session.get('staff_id')).first()

    if request.method == "POST":
        supplier_code = request.POST.get('supplier_code')
        supplier_name = request.POST.get('supplier_name')
        contact_number = request.POST.get('contact_number')
        email = request.POST.get('email')
        address = request.POST.get('address')

        SupplierMaster.objects.create(
            staff=staff,
            supplier_code=supplier_code,
            supplier_name=supplier_name,
            contact_number=contact_number,
            email=email,
            address=address
        )
        messages.success(request, "Supplier added successfully.")
        return redirect('supplier_list')

    return render(request, 'supplier_master.html', {'hospital': hospital, 'staff': staff})


def supplier_list(request):
    search_query = request.GET.get('search', '').strip()
    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'
    supplier = SupplierMaster.objects.all().order_by('-id')
    hospital = Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    staff = StaffRegistration.objects.get(id=staff_id)
    medical_store=Medical_Store.objects.first()
    if search_query:
        supplier = supplier.filter(
            Q(supplier_name__icontains=search_query) 
            )   

    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(supplier, 10)
        page_number = request.GET.get('page')
        supplier = paginator.get_page(page_number)

    return render(request, 'supplier_list.html', {"medical_store":medical_store,"is_export_excel":is_export_excel,"is_export":is_export_pdf,'suppliers': supplier,"hospital":hospital,"staff":staff})


def edit_supplier(request, pk):
    hospital = Hospital_data.objects.first()
    staff = None
    if request.session.get('staff_id'):
        staff = StaffRegistration.objects.filter(id=request.session.get('staff_id')).first()
    supplier=SupplierMaster.objects.get(id=pk)
    if request.method == "POST" and supplier:
        supplier.supplier_code = request.POST.get('supplier_code')
        supplier.supplier_name = request.POST.get('supplier_name')
        supplier.contact_number = request.POST.get('contact_number')
        supplier.email = request.POST.get('email')
        supplier.address = request.POST.get('address')
        supplier.save()
        messages.success(request, "Supplier updated successfully.")
        return redirect('supplier_list')

    return render(request, 'supplier_edit.html', {
        'supplier': SupplierMaster.objects.get(id=pk), 'edit_mode': True, 'hospital': hospital, 'staff': staff
    })


def delete_supplier(request, pk):
    supplier = get_object_or_404(SupplierMaster, id=pk)
    supplier.delete()
    messages.success(request, "Supplier deleted successfully.")
    return redirect('supplier_list')

def get_supplier_contact(request, supplier_id):
    try:
        supplier = SupplierMaster.objects.get(id=supplier_id)
        return JsonResponse({'contact': supplier.contact_number})
    except SupplierMaster.DoesNotExist:
        return JsonResponse({'contact': None})
    
def get_item_unit(request, item_id):
    try:
        item = MedicineMaster.objects.get(id=item_id)
        return JsonResponse({'unit': item.base_unit})
    except MedicineMaster.DoesNotExist:
        return JsonResponse({'unit': None})

def physical_stock_add(request):
    hospital = Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    staff = StaffRegistration.objects.get(id=staff_id)    
    suppliers = SupplierMaster.objects.all()
    medicines = MedicineMaster.objects.all()
    store=Medical_Store.objects.all()
    company=Company.objects.all()
    Medicine=MedicineMaster.objects.all()
    if request.method == "POST":
        medicine_company_id=request.POST.get('medicine_company')
        medicine_company=Company.objects.get(id=medicine_company_id)
        PhysicalStock.objects.create(
            staff=staff,
            supplier_id=request.POST.get('supplier'),
            supplier_contact=request.POST.get('supplier_contact'),
            medicine_company=medicine_company,
            item_id=request.POST.get('item'),
            unit=request.POST.get('unit'),
            batch_number=request.POST.get('batch_number'),
            manufacture_date=request.POST.get('manufacture_date') or None,
            expiry_date=request.POST.get('expiry_date') or None,
            rate=request.POST.get('rate') or 0,
            quantity=request.POST.get('quantity') or 0,
        )
        messages.success(request, "Physical stock added successfully!")
        return redirect('physical_stock_list')

    return render(request, 'physical_stock_form.html', {
        'hospital': hospital,
        'staff': staff,
        'suppliers': suppliers,
        'medicines': medicines,
        "medical_store":store,
        "company":company,
        "medicine":Medicine,
    })

def physical_stock_edit(request, pk):
    stock = get_object_or_404(PhysicalStock, id=pk)
    hospital = Hospital_data.objects.first()
    staff = StaffRegistration.objects.get(id=request.session.get('staff_id'))
    suppliers = SupplierMaster.objects.all()
    medicines = MedicineMaster.objects.all()
    company = Company.objects.all()

    if request.method == "POST":
        medicine_company_id=request.POST.get('medicine_company')
        medicine_company=Company.objects.get(id=medicine_company_id)
        stock.store = request.POST.get('store')
        stock.supplier_id = request.POST.get('supplier')
        stock.supplier_contact = request.POST.get('supplier_contact')
        stock.medicine_company = medicine_company
        stock.item_id = request.POST.get('item')
        stock.unit = request.POST.get('unit')
        stock.batch_number = request.POST.get('batch_number')
        stock.manufacture_date = request.POST.get('manufacture_date') or None
        stock.expiry_date = request.POST.get('expiry_date') or None
        stock.rate = request.POST.get('rate') or 0
        stock.quantity = request.POST.get('quantity') or 0
        stock.save()
        messages.success(request, "Stock updated successfully!")
        return redirect('physical_stock_list')

    return render(request, 'physical_stock_form.html', {
        'stock': stock,
        'edit_mode': True,
        'hospital': hospital,
        'staff': staff,
        'suppliers': suppliers,
        'medicines': medicines,
        'company':company,
    })
    
def physical_stock_delete(request, pk):
    stock = get_object_or_404(PhysicalStock, id=pk)
    stock.delete()
    messages.success(request, "Stock deleted successfully!")
    return redirect('physical_stock_list')


def physical_stock_list(request):
    search_query = request.GET.get('search', '').strip()
    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'
    hospital = Hospital_data.objects.first()
    staff_id=request.session.get('staff_id')
    staff = StaffRegistration.objects.get(id=staff_id)
    medical_store=Medical_Store.objects.first()
    if search_query:
        medical_store = medical_store.filter(
            Q(name__icontains=search_query) 
            )   
    stocks = PhysicalStock.objects.all().order_by('-id')
    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(stocks, 10)
        page_number = request.GET.get('page')
        stocks = paginator.get_page(page_number)
    return render(request, 'physical_stock_list.html', {"medical_store":medical_store,"staff":staff,"is_export":is_export_pdf,"is_export_excel":is_export_excel,'physical_stock': stocks, 'hospital': hospital})


def pharmacy_invoice(request):
    tax = TaxMaster.objects.all()
    hospital = Hospital_data.objects.first()
    store = Medical_Store.objects.first()
    staff_id = request.session.get("staff_id")
    if not staff_id:
        messages.error(request, 'Login to continue!!')
        return redirect('login')
    if staff_id:
        staff = StaffRegistration.objects.get(id=staff_id)
    patients = Patient.objects.all()
    medicines = MedicineMaster.objects.all()
    company = Company.objects.all()
    passing_patient = ""
    patient_id = request.session.get('patient_id')

    if request.GET.get("patient_id"):
        passing_patient = Patient.objects.get(id=request.GET.get("patient_id"))

    if request.method == "POST":
        try:
            # ← START ATOMIC TRANSACTION
            with transaction.atomic():
                customer_type = request.POST.get("customerType")
                patient_id = None
                unreg_name = None
                unreg_phone = None

                if customer_type == "registered":
                    patient_id = request.POST.get("patient_id")
                else:
                    patient_id = None
                    unreg_name = request.POST.get("unreg_name")
                    unreg_phone = request.POST.get("unreg_phone") or ""
                
                if customer_type == "registered" and not patient_id:
                    return JsonResponse(
                        {"success": False, "error": "Please select a registered patient"},
                        status=400
                    )

                if customer_type != "registered" and not unreg_name:
                    return JsonResponse(
                        {"success": False, "error": "Please enter customer name"},
                        status=400
                    )
            
                date = request.POST.get('invoice_date')
                invoice_no = f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"

                total_amount = float(request.POST.get("total_amount") or 0)
                taxable_amount = float(request.POST.get("taxable_amount") or 0)
                cgst = float(request.POST.get("cgst") or 0)
                sgst = float(request.POST.get("sgst") or 0)
                discount = float(request.POST.get("discount") or 0)

                # ✅ Create main invoice record
                invoice = GSTInvoice.objects.create(
                    medical_store=store,
                    patient_id=patient_id,
                    invoice_no=invoice_no,
                    date=date,
                    total_amount=total_amount,
                    taxable_amount=taxable_amount,
                    cgst=cgst,
                    sgst=sgst,
                    discount=discount,
                    customer_name=unreg_name,
                    customer_phone=unreg_phone,
                    payment_mode=request.POST.get('payment_mode') or None,
                )

                # ✅ Parse items JSON
                items_json = request.POST.get("items_json", "[]")
                items = json.loads(items_json)

                for item in items:
                    try:
                        medicine_obj = MedicineMaster.objects.get(
                            medicine_name=item.get("item_name")
                        )
                    except MedicineMaster.DoesNotExist:
                        medicine_obj = None

                    # ✅ Create Invoice Item
                    inv_item = GSTInvoiceItem.objects.create(
                        invoice=invoice,
                        item=medicine_obj,
                        batch_number=item.get("batch_number"),
                        expiry_date=item.get("expiry_date") or None,
                        unit=item.get("unit"),
                        company_name_id=item.get("company_name") or None,
                        qty=item.get("qty") or 0,
                        rate=Decimal(item.get("rate", '0')),
                        each_sgst=item.get("each_sgst") or 0,
                        each_cgst=item.get('each_cgst') or 0,
                        each_taxable_amount=Decimal(item.get("qty")) * Decimal(item.get("rate")),
                        tax_percent=item.get("tax_percent") or 0,
                        amount=item.get("amount") or 0
                    )

                    # ✅ Deduct physical stock
                    if medicine_obj and item.get("batch_number"):
                        batch_no = item.get("batch_number")
                        qty_to_deduct = int(item.get("qty") or 0)
                        company_id = item.get("company_name")

                        stock_entry = PhysicalStock.objects.filter(
                            item=medicine_obj,
                            batch_number=batch_no,
                            medicine_company_id=company_id
                        ).first()

                        if stock_entry:
                            if stock_entry.quantity >= qty_to_deduct:
                                stock_entry.quantity -= qty_to_deduct
                            else:
                                stock_entry.quantity = 0  # Prevent negatives
                            stock_entry.save()
                        else:
                            print(f"⚠️ No PhysicalStock found for {medicine_obj} batch {batch_no}")

                # ← SUCCESS RETURN (inside transaction — commit happens on exit)
                return JsonResponse({
                    "success": True,
                    "invoice_id": invoice.id,
                    "pdf_url": reverse("pharmacy_invoice_pdf", args=[invoice.id])
                })

        # ← ORIGINAL EXCEPT BLOCK PRESERVED (catches any error → rollback automatic)
        except Exception as e:
            transaction.set_rollback(True)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    # 🧭 Render invoice form
    return render(request, "pharmacy_invoice.html", {
        "hospital": hospital,
        "passing_patient": passing_patient,
        "store": store,
        "staff": staff,
        "tax": tax,
        "company": company,
        "patients": patients,
        "medicines": medicines,
    })

def get_patient_for_invoice(request):
    query = request.GET.get("q", "")
    patients = Patient.objects.filter(
        Q(mr_no__icontains=query) | Q(phone__icontains=query) | Q(name__icontains=query)
    )[:5]
    results = [{"id": p.id, "mr_no": p.mr_no, "name": p.name, "phone": p.phone} for p in patients]
    return JsonResponse(results, safe=False)

def search_medicine(request):
    """
    AJAX search for medicines with stock > 0
    Filters by medicine name (min 3 chars) and joins PhysicalStock table.
    """
    query = request.GET.get("q", "").strip()
    results = []

    if len(query) >= 3:
        # ✅ Join with PhysicalStock and filter only non-zero stock
        stocks = (
            PhysicalStock.objects
            .filter(
                item__medicine_name__icontains=query,
                quantity__gt=0  # Only stock available
            )
            .select_related("item", "medicine_company")
            .order_by("item__medicine_name", "batch_number")
        )

        for s in stocks:
            results.append({
                "name": s.item.medicine_name,
                "unit": s.unit or "",
                "batch": s.batch_number,
                "expiry": s.expiry_date.strftime("%Y-%m-%d") if s.expiry_date else "",
                "tax": s.item.tax.tax_percent,
                "company": s.medicine_company.name if s.medicine_company else "",
                "company_id": s.medicine_company.id if s.medicine_company else "",
                "rate": str(s.rate),
                "net_quantity": s.quantity,  # 🧮 available stock
            })

    return JsonResponse(results, safe=False)



def pharmacy_invoice_list(request):
    hospital = Hospital_data.objects.first()
    medical_store = Medical_Store.objects.first()

    search_query = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'

    staff_id = request.session.get("staff_id")
    if not staff_id:
        messages.error(request, 'Login to continue!!')
        return redirect('login')

    staff = StaffRegistration.objects.get(id=staff_id)

    is_admin = StaffAllocation.objects.filter(
        staff=staff_id,
        designation__Designation__iexact="Admin",
        status="active"
    ).exists()

    # ================= BASE QUERY =================
    invoices = GSTInvoice.objects.filter(status="Active").select_related(
        'patient', 'medical_store'
    ).order_by('-id')

    cancelled_invoices = GSTInvoice.objects.filter(status="Inactive")

    # ================= SEARCH FILTER =================
    if search_query:
        search_filter = (
            Q(invoice_no__icontains=search_query) |
            Q(patient__name__icontains=search_query) |
            Q(patient__phone__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )
        invoices = invoices.filter(search_filter)
        cancelled_invoices = cancelled_invoices.filter(search_filter)

    # ================= DATE FILTER =================
    try:
        if from_date:
            from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
            invoices = invoices.filter(date__gte=from_date_obj)
            cancelled_invoices = cancelled_invoices.filter(date__gte=from_date_obj)

        if to_date:
            to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
            invoices = invoices.filter(date__lte=to_date_obj)
            cancelled_invoices = cancelled_invoices.filter(date__lte=to_date_obj)
    except ValueError:
        pass  # invalid date → ignore filter safely

    # ================= QUERY STRING FOR PAGINATION =================
    query_params = {}
    if search_query:
        query_params["search"] = search_query
    if from_date:
        query_params["from_date"] = from_date
    if to_date:
        query_params["to_date"] = to_date

    query_string = urlencode(query_params)

    cancelled_count = cancelled_invoices.count()

    # ================= PAGINATION =================
    if not is_export_excel and not is_export_pdf:
        paginator = Paginator(invoices, 10)
        page_number = request.GET.get('page')
        invoices = paginator.get_page(page_number)

    context = {
        "invoices": invoices,
        "search_query": search_query,
        "from_date": from_date,
        "to_date": to_date,
        "hospital": hospital,
        "medical_store": medical_store,
        "staff": staff,
        "is_admin": is_admin,
        "is_export": is_export_pdf,
        "is_export_excel": is_export_excel,
        "cancelled_count": cancelled_count,
        "cancelled_invoices": cancelled_invoices.order_by('-id')[:5],
        "query_string": query_string,   
    }

    return render(request, "pharmacy_invoice_list.html", context)
    

def pharmacy_invoice_report(request, pk):
    invoice = get_object_or_404(GSTInvoice, pk=pk)
    items = GSTInvoiceItem.objects.filter(invoice=invoice).select_related('item', 'company_name')
    store = Medical_Store.objects.first()
    bank_details = BankDetails.objects.filter(medical_store=store).first()
    amount_in_words = num2words(invoice.total_amount, to='cardinal', lang='en').title() + " Rupees Only"
    if invoice.patient:
        customer = {
            'name': invoice.patient.name,
            'address': invoice.patient.address or '',
            'phone': invoice.patient.phone or ''
        }
    else:
        customer = {
            'name': invoice.customer_name or 'Unregistered Customer',
            'address': '',  # No address for unregistered
            'phone': invoice.customer_phone or ''
        }
    context = {
        'invoice': invoice,
        'items': items,
        'store': store,
        'total_amount':invoice.total_amount,
        'customer': customer,     
        'bank_details':bank_details,
        'amount_in_words': amount_in_words,
    }

    html = render_to_string('pharmacy_invoice_pdf.html', context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=GSTInvoice_{invoice.invoice_no}.pdf'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF")
    return response

def bank_details_list(request):
    hospital = Hospital_data.objects.first()
    store = Medical_Store.objects.first()
    staff=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff)
    search_query = request.GET.get('search', '')
    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'

    # 🔍 Filtering across multiple fields
    bank_details = BankDetails.objects.filter(medical_store=store)
    if search_query:
        bank_details = bank_details.filter(
            Q(bank_name__icontains=search_query) |
            Q(account_holder_name__icontains=search_query) |
            Q(account_number__icontains=search_query) |
            Q(ifsc_code__icontains=search_query) |
            Q(branch_name__icontains=search_query) |
            Q(upi_id__icontains=search_query)
        )

   
    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(bank_details.order_by('-id'), 10)
        page_number = request.GET.get('page')
        bank_details = paginator.get_page(page_number)

    context = {
        'hospital': hospital,
        'store': store,
        'bank_details': bank_details,
        'search_query': search_query,
        'is_export':is_export_pdf,
        'staff':staff,
        "is_export_excel":is_export_excel,
    }
    return render(request, 'bank_details_list.html', context)


# ✅ Add new bank details
def bank_details_add(request):
    hospital = Hospital_data.objects.first()
    store = Medical_Store.objects.first()
    staff=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff)
    if request.method == "POST":
        BankDetails.objects.create(
            medical_store=store,
            bank_name=request.POST.get('bank_name'),
            account_holder_name=request.POST.get('account_holder_name'),
            account_number=request.POST.get('account_number'),
            ifsc_code=request.POST.get('ifsc_code'),
            branch_name=request.POST.get('branch_name'),
            upi_id=request.POST.get('upi_id'),
            qr_code=request.FILES.get('qr_code')
        )
        messages.success(request, "✅ Bank details added successfully.")
        return redirect('bank_details_list')

    return render(request, 'bank_details.html', {
        'hospital': hospital,
        'store': store,
        'staff':staff,
        'title':"Add Bank Details",
    })


# ✅ Edit existing bank details
def bank_details_edit(request, pk):
    hospital = Hospital_data.objects.first()
    staff=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff)
    store = Medical_Store.objects.first()
    bank = get_object_or_404(BankDetails, pk=pk)

    if request.method == "POST":
        bank.bank_name = request.POST.get('bank_name')
        bank.account_holder_name = request.POST.get('account_holder_name')
        bank.account_number = request.POST.get('account_number')
        bank.ifsc_code = request.POST.get('ifsc_code')
        bank.branch_name = request.POST.get('branch_name')
        bank.upi_id = request.POST.get('upi_id')
        if request.FILES.get('qr_code'):
            bank.qr_code = request.FILES.get('qr_code')
        bank.save()
        messages.success(request, "✅ Bank details updated successfully.")
        return redirect('bank_details_list')

    return render(request, 'bank_details.html', {
        'hospital': hospital,
        'store': store,
        'bank': bank,
        'title': 'Edit Bank Details',
        'staff':staff,
    })
    
    
def GST_Report(request):
    staff_id=request.session.get("staff_id")
    if not staff_id:
        messages.error(request,'Login to continue!!')
        return redirect('login')
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    medical_store = Medical_Store.objects.first()
    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'
    month = request.GET.get("month")  # e.g. '2025-11'
    search = request.GET.get("search", "").strip()
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    invoices = GSTInvoice.objects.all().select_related("patient")

    # 🔹 Month filter
    if month:
        try:
            year, month_num = month.split("-")
            invoices = invoices.filter(date__year=year, date__month=month_num)
        except ValueError:
            pass
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            invoices = invoices.filter(date__range=[start_dt, end_dt])
        except ValueError:
            pass
    elif start_date:
        invoices = invoices.filter(date__gte=start_date)
    elif end_date:
        invoices = invoices.filter(date__lte=end_date)
        
    # 🔹 Search filter (by patient name, invoice no, or MR no)
    if search:
        invoices = invoices.filter(
            Q(patient__name__icontains=search)
            | Q(invoice_no__icontains=search)
            | Q(patient__mr_no__icontains=search)
        )

    # 🔹 Annotate total tax
    invoices = invoices.annotate(
        total_tax=ExpressionWrapper(
            Coalesce(F("sgst"), 0) + Coalesce(F("cgst"), 0),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    ).order_by("-date", "-id")
    
    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(invoices, 10)
        page = request.GET.get("page")
        invoices= paginator.get_page(page)

    context = {
        "hospital": hospital,
        "medical_store": medical_store,
        "gst_invoices": invoices,
        "selected_month": month,
        "search": search,
        "staff":staff,
        'is_export':is_export_pdf,
        "is_export_excel":is_export_excel,
    }
    return render(request, "GST_Report.html", context)


def supplier_search(request):
    query = request.GET.get("q", "").strip()

    suppliers = SupplierMaster.objects.all()
    if query:
        suppliers = suppliers.filter(
            Q(supplier_name__icontains=query) |
            Q(contact_number__icontains=query)
        )

    data = [
        {
            "id": s.id,
            "supplier_name": s.supplier_name,
            "contact_number": s.contact_number,
            "email": s.email or "",
        }
        for s in suppliers[:20]
    ]

    return JsonResponse({"results": data})

def purchase_invoice(request):
    hospital = Hospital_data.objects.first()
    staff_id = request.session.get("staff_id")
    staff = None
    if staff_id:
        staff = StaffRegistration.objects.get(id=staff_id)
    if not staff_id:
        return redirect('login')
    
    store = Medical_Store.objects.first()
    companies = Company.objects.all()
    taxes = TaxMaster.objects.all()
    
    context = {
        'store': store,
        'companies': companies,
        'taxes': taxes,
        'hospital': hospital,
        'staff': staff
    }

    if request.method == 'POST':
        try:
            # Parse JSON items
            items_json = request.POST.get('items_json', '[]')
            items_data = json.loads(items_json)
            
            if not items_data:
                messages.error(request, "No items provided.")
                return render(request, 'purchase_invoice.html', context)
            
            supplier_id = request.POST.get('supplier_id')
            if not supplier_id:
                messages.error(request, "Supplier is required.")
                return render(request, 'purchase_invoice.html', context)
            
            supplier = get_object_or_404(SupplierMaster, id=supplier_id)
            purchase_date_str = request.POST.get('purchase_date')
            bill_number = request.POST.get('bill_number', '').strip() or None
            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else timezone.now().date()
            discount_percent = Decimal(request.POST.get('discount_percent', '0')) or Decimal('0')
            
            # Totals calculation
            taxable_total = Decimal('0')
            cgst_total = Decimal('0')
            sgst_total = Decimal('0')
            grand_total = Decimal('0')
            
            for item_data in items_data:
                qty = int(item_data.get('qty', 0))
                rate = Decimal(str(item_data.get('rate', '0')))
                each_cgst = Decimal(str(item_data.get('each_cgst', '0')))
                each_sgst = Decimal(str(item_data.get('each_sgst', '0')))
                amount = Decimal(str(item_data.get('amount', '0')))
                taxable_total += qty * rate
                cgst_total += each_cgst
                sgst_total += each_sgst
                grand_total += amount  # amount already includes qty in JS

            # Apply discount
            discount_amount = grand_total * (discount_percent / Decimal('100'))
            final_total = grand_total - discount_amount
            
            # Generate purchase_no
            last_invoice = PurchaseInvoice.objects.order_by('-id').first()
            last_num = int(last_invoice.purchase_no.split('/')[-1]) if last_invoice else 0
            purchase_no = f"PI/{purchase_date.strftime('%Y/%m/%d')}/{last_num + 1:04d}"
            if bill_number:
                if PurchaseInvoice.objects.filter(supplier=supplier,bill_number=bill_number).exists():
                    messages.error(request,"This supplier bill number already exists.")
                    return render(request, 'purchase_invoice.html', context)
            # Create PurchaseInvoice
            purchase_invoice = PurchaseInvoice.objects.create(
                medical_store=store,
                bill_number=bill_number,
                date=purchase_date,
                supplier=supplier,
                purchase_no=purchase_no,
                taxable_amount=taxable_total,
                cgst=cgst_total,
                sgst=sgst_total,
                discount=discount_amount,
                total_amount=final_total,
                created_by_id=staff_id
            )
            purchase_invoice.save()
            
            # Create items and update stock
            for item_data in items_data:
                medicine_id = item_data.get('medicine_id')
                if not medicine_id:
                    continue
                
                medicine = get_object_or_404(MedicineMaster, id=medicine_id)
                qty = int(item_data.get('qty', 0))
                rate = Decimal(str(item_data.get('rate', '0')))
                tax_percent = Decimal(str(item_data.get('tax_percent', '0')))
                each_cgst = Decimal(str(item_data.get('each_cgst', '0')))
                each_sgst = Decimal(str(item_data.get('each_sgst', '0')))
                amount = Decimal(str(item_data.get('amount', '0')))
                
                # Create PurchaseInvoiceItem
                PurchaseInvoiceItem.objects.create(
                    invoice=purchase_invoice,
                    item=medicine,
                    batch_number=item_data.get('batch_number', ''),
                    expiry_date=item_data.get('expiry_date') or None,
                    company_name_id=item_data.get('company_name') or None,
                    unit=item_data.get('unit', ''),
                    qty=qty,
                    rate=rate,
                    tax_percent=tax_percent,
                    each_taxable_amount=rate * qty,
                    each_cgst=each_cgst,  # per unit
                    each_sgst=each_sgst,  # per unit
                    amount=amount  # total for row
                )
                
                # Update or create PhysicalStock
                batch_number = item_data.get('batch_number', '')
                expiry_date = item_data.get('expiry_date') or None
                manufacture_date = item_data.get('manufacture_date') or None
                company_id = item_data.get('company_name') or None
                
                stock, created = PhysicalStock.objects.get_or_create(
                    item=medicine,
                    batch_number=batch_number,
                    defaults={
                        'supplier_id': supplier.id,
                        'medicine_company_id': company_id,
                        'unit': item_data.get('unit', ''),
                        'manufacture_date': manufacture_date,
                        'expiry_date': expiry_date,
                        'rate': rate,
                        'quantity': qty
                    }
                )
                if not created:
                    stock.quantity = F('quantity') + qty
                    stock.save()
            
            messages.success(request, f"Purchase invoice {purchase_no} created successfully!")
            return redirect('purchase_invoice_list')
        
        except ValueError as ve:
            messages.error(request, f"Invalid data: {str(ve)}")
        except Exception as e:
            messages.error(request, f"Error creating purchase: {str(e)}")
            return render(request, 'purchase_invoice.html', context)
    
    return render(request, 'purchase_invoice.html', context)


def purchase_invoice_list(request):
    hospital = Hospital_data.objects.first()
    staff_id = request.session.get("staff_id")
    medical_store=Medical_Store.objects.first()
    staff = None
    if staff_id:
        staff = StaffRegistration.objects.get(id=staff_id)
    if not staff_id:
        return redirect('login')
    
    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'
    search_query = request.GET.get("search", "").strip()
    
    # Query PurchaseInvoice (once model is added)
    purchases = PurchaseInvoice.objects.select_related('supplier', 'created_by').order_by('-date','-purchase_no')
    
    if search_query:
        purchases = purchases.filter(
            Q(supplier__supplier_name__icontains=search_query) |
            Q(purchase_no__icontains=search_query)
        )
    
    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(purchases, 10)
        page = request.GET.get("page")
        purchases = paginator.get_page(page)
    
    context = {
        'purchases': purchases,
        'search_query': search_query,
        'is_export': is_export_pdf,
        'is_export_excel': is_export_excel,
        'hospital':hospital,
        'staff':staff,
        "medical_store": medical_store,

    }
    
    return render(request, 'purchase_list.html', context)

def search_medic(request):
    """
    AJAX search for medicines with stock > 0
    """
    query = request.GET.get("q", "").strip()
    results = []

    if len(query) >= 2:  # 🟢 match JS minimum
        stocks = (
            PhysicalStock.objects
            .filter(
                item__medicine_name__icontains=query,
                quantity__gt=0
            )
            .select_related("item", "medicine_company", "item__tax")
            .order_by("item__medicine_name", "batch_number")
        )

        for s in stocks:
            results.append({
                "id": s.item.id, 
                "medicine_name": s.item.medicine_name, 
                "unit": s.unit or "",
                "hsn_code": s.item.hsn_code or "",
                "batch": s.batch_number or "",
                "expiry": s.expiry_date.strftime("%Y-%m-%d") if s.expiry_date else "",
                "tax": s.item.tax.tax_percent if s.item.tax else 0,
                "company": s.medicine_company.name if s.medicine_company else "",
                "company_id": s.medicine_company.id if s.medicine_company else "",
                "net_quantity": s.quantity,
            })

    return JsonResponse(results, safe=False)

def purchase_invoice_view(request, pk):
    purchase_invoice = get_object_or_404(PurchaseInvoice, pk=pk)
    items = PurchaseInvoiceItem.objects.filter(invoice=purchase_invoice)
    medical_store = Medical_Store.objects.first()

    context = {
        "invoice": purchase_invoice,
        "items": items,
        "store": medical_store
    }
    return render(request, "purchase_invoice_view.html", context)


def consolidated_invoice_pdf(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department = request.GET.get('department')
    staff = request.GET.get('staff')
    q = request.GET.get('q')

    # Base queryset
    qs = Invoice.objects.filter(patient=patient)

    # Apply filters
    if start_date:
        qs = qs.filter(created_at__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__lte=end_date)
    if department:
        qs = qs.filter(doctor__allocations__department__id=department)
    if staff:
        qs = qs.filter(doctor__id=staff)
    if q:
        qs = qs.filter(
            Q(invoice_number__icontains=q) |
            Q(doctor__name__icontains=q)
        )

    invoices = qs.order_by('created_at')

    total_amount = invoices.aggregate(
        Sum('total_amount')
    )['total_amount__sum'] or 0

    amount_in_words = (
        num2words(total_amount)
        .replace('point zero', '')
        .replace(',','')
        .strip()
        if total_amount else 'Zero'
    )
    
    hospital = Hospital_data.objects.first()

    context = {
        'hospital': hospital,
        'patient': patient,
        'invoices': invoices,
        'total_amount': total_amount,
        'amount_in_words': amount_in_words.capitalize(),
    }

    response = render_to_pdf('consolidated_invoice_pdf.html', context)

    if not response:
        return HttpResponse(
            "Error generating PDF",
            status=500
        )

    response['Content-Disposition'] = (
        f'attachment; filename="consolidated_invoice_{patient.mr_no}.pdf"'
    )

    return response

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)

    response = HttpResponse(content_type='application/pdf')
    result = pisa.CreatePDF(
        src=html,
        dest=response,
        encoding='UTF-8'
    )

    if result.err:
        return None
    return response

def invoice_particular_add(request):
    hospital = Hospital_data.objects.first()
    staff_id = request.session.get("staff_id")
    staff = None
    if staff_id:
        staff = StaffRegistration.objects.get(id=staff_id)
    if not staff_id:
        return redirect('login')
    if request.method == 'POST':
        InvoiceParticular.objects.create(
            hospital=hospital,
            created_by=staff,
            name=request.POST.get('name'),
        )
        messages.success(request,"Invoice Particular Added successfully!!")
        return redirect('invoice_particular_list')

    return render(request, 'invoice_particular_add.html', {
        'hospital': hospital,
        'staff': staff
    })


# LIST
def invoice_particular_list(request):
    hospital = Hospital_data.objects.first()
    staff_id = request.session.get("staff_id")
    staff = None
    if staff_id:
        staff = StaffRegistration.objects.get(id=staff_id)
    if not staff_id:
        return redirect('login')
    search = request.GET.get('search', '')

    particulars = InvoiceParticular.objects.all()

    if search:
        particulars = particulars.filter(
            Q(name__icontains=search)        )

    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'
    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(particulars, 10)
        page = request.GET.get("page")
        particulars = paginator.get_page(page)

    return render(request, 'invoice_particular_list.html', {
        'hospital': hospital,
        'staff': staff,
        'particulars': particulars,
        'search': search,
        "is_export":is_export_pdf,
        "is_export_excel":is_export_excel,
    })


# EDIT
def invoice_particular_edit(request, pk):
    hospital = Hospital_data.objects.first()
    staff_id = request.session.get("staff_id")
    staff = None
    if staff_id:
        staff = StaffRegistration.objects.get(id=staff_id)
    if not staff_id:
        return redirect('login')

    particular = get_object_or_404(
        InvoiceParticular, pk=pk, hospital=hospital
    )

    if request.method == 'POST':
        particular.name = request.POST.get('name')
        particular.status = True
        particular.save()
        messages.success(request,"Invoice Particular Added successfully!!")
        return redirect('invoice_particular_list')

    return render(request, 'invoice_particular_edit.html', {
        'hospital': hospital,
        'staff': staff,
        'particular': particular
    })
    
    
def invoice_particular_delete(request, pk):
    particular = get_object_or_404(InvoiceParticular, pk=pk)
    particular.status = False
    particular.save()
    return redirect('invoice_particular_list')

def search_invoice_particular(request):
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    particulars = InvoiceParticular.objects.filter(
        status=True,
        name__icontains=q
    ).values_list("name", flat=True)[:10]

    return JsonResponse(list(particulars), safe=False)

def pharmacy_invoice_soft_delete(request, invoice_id):
    staff_id = request.session.get("staff_id")
    staff = None
    if staff_id:
        staff = StaffRegistration.objects.get(id=staff_id)
    if not staff_id:
        return redirect('login')
    try:
        with transaction.atomic():

            invoice = get_object_or_404(GSTInvoice, id=invoice_id)

            if invoice.status == "Inactive":
                return JsonResponse({
                    "success": False,
                    "message": "Invoice already inactive"
                }, status=400)

            items = GSTInvoiceItem.objects.filter(invoice=invoice)

            for item in items:
                if not item.item or not item.batch_number:
                    continue

                stock = PhysicalStock.objects.select_for_update().filter(
                    item=item.item,
                    batch_number=item.batch_number,
                    medicine_company=item.company_name
                ).first()

                if stock:
                    stock.quantity += int(item.qty or 0)
                    stock.save()
                else:
                    PhysicalStock.objects.create(
                        item=item.item,
                        batch_number=item.batch_number,
                        medicine_company=item.company_name,
                        quantity=int(item.qty or 0)
                    )

            invoice.status = "Inactive"
            invoice.deleted_by=staff
            invoice.save(update_fields=["status"])

            return JsonResponse({
                "success": True,
                "message": "Invoice cancelled and stock restored successfully"
            })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
        
def today_appointment(request):
    staff_id=request.session.get("staff_id")
    staff=StaffRegistration.objects.get(id=staff_id)
    hospital = Hospital_data.objects.first()
    search_query = request.GET.get('search', '').strip()
    export_pdf = request.GET.get('export') == 'pdf'
    export_excel = request.GET.get('export') == 'excel'

    today = date.today()

    # Get current user staff info
    staff_id = request.session.get("staff_id")
    current_staff = None
    branch = None
    is_admin = False
    is_doctor = False

    if staff_id:
        current_staff = get_object_or_404(StaffRegistration, id=staff_id)
        allocation = StaffAllocation.objects.filter(staff=current_staff, status="active").first()
        if allocation:
            branch = allocation.branch
            is_admin = allocation.designation.Designation.lower() == "admin"
            is_doctor = allocation.designation.Designation.lower() == "doctor"

    # Base QuerySet → only today's appointments
    appointments = Appointment.objects.select_related('patient', 'doctor', 'branch').filter(
        appointment_date=today
    ).order_by('token_no')

    # Apply branch restriction for non-admins
    if branch and not is_admin:
        appointments = appointments.filter(branch=branch)

    # Auto-filter: Doctors see only their own appointments
    if is_doctor and not is_admin:
        appointments = appointments.filter(doctor=current_staff)

    # Search by patient name
    if search_query:
        appointments = appointments.filter(patient__name__icontains=search_query)

    # Optional date override
    filter_date = request.GET.get('date')
    if filter_date:
        try:
            filter_date_obj = timezone.datetime.strptime(filter_date, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date=filter_date_obj)
        except ValueError:
            pass  # ignore invalid date

    # Doctor filter (only if admin or if they choose to filter themselves)
    selected_doctor_id = request.GET.get("staff")  # Note: using 'staff' as in your template
    if selected_doctor_id:
        appointments = appointments.filter(doctor_id=selected_doctor_id)

    # Doctor-wise count (for badges) - based on today's appointments
    count_qs = Appointment.objects.filter(appointment_date=today)
    if branch and not is_admin:
        count_qs = count_qs.filter(branch=branch)

    doctor_counts = count_qs.values('doctor__id', 'doctor__name').annotate(
        count=Count('id')
    ).order_by('doctor__name')

    total_today_count = appointments.count()

    # Pagination
    page_obj = appointments
    if not export_pdf and not export_excel:
        paginator = Paginator(appointments, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    # Doctors for dropdown (only active doctors)
    doctors = StaffRegistration.objects.filter(
        allocations__designation__Designation__iexact="Doctor",
        status="Active"
    ).distinct().order_by('name')
    appointments_count=appointments.count()
    context = {
        'appointments': page_obj,
        'page_obj': page_obj,
        'hospital': hospital,
        'branch': branch,
        'current_staff': current_staff,
        'is_admin': is_admin,
        'is_doctor': is_doctor,
        'search_query': search_query,
        'today': today,
        'filter_date': filter_date or today.strftime('%Y-%m-%d'),
        'total_today_count': total_today_count,
        'doctor_counts': doctor_counts,
        'doctors': doctors,
        'selected_staff': selected_doctor_id,
        'is_export': export_pdf,
        'is_export_excel': export_excel,
        'staff':staff,
        "appointments_count":appointments_count
    }

    return render(request, 'today_appointment.html', context)


def treatment_plan_table(request):
    """View to list treatment plans for a specific patient only"""
    hospital = Hospital_data.objects.first()
    staff_id = request.session.get("staff_id")
    
    if not staff_id:
        messages.error(request, 'Login to continue!!')
        return redirect('login')
    
    staff = StaffRegistration.objects.get(id=staff_id)
    
    # Get patient_id from URL parameter
    patient_id = request.GET.get('patient_id', '')
    search_query = request.GET.get('search', '').strip()
    export = request.GET.get('export', '')
    is_export_excel = export == 'excel'
    is_export_pdf = export == 'pdf'
    
    # Get the selected patient
    selected_patient = None
    treatments = TreatmentPlan.objects.none()
    
    if patient_id:
        try:
            selected_patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            messages.error(request, 'Patient not found.')
            return redirect('patienttable')
    
    # If patient is selected, get their treatment plans
    if selected_patient:
        treatments = TreatmentPlan.objects.filter(
            patient=selected_patient
        ).select_related('patient', 'staff').order_by('-id')
        
        # Apply branch restriction based on user role
        allocation = StaffAllocation.objects.filter(staff_id=staff_id, status="active").first()
        is_admin = False
        branch_id = None
        
        if allocation:
            branch_id = allocation.branch_id
            is_admin = allocation.designation.Designation.lower() == "admin"
        
        if not is_admin and branch_id:
            treatments = treatments.filter(patient__branch_id=branch_id)
        
        # Apply search filter (by doctor name or goals)
        if search_query:
            treatments = treatments.filter(
                Q(staff__name__icontains=search_query) |
                Q(short_term_goals__icontains=search_query) |
                Q(long_term_goals__icontains=search_query)|
                Q(date_created__icontains=search_query)
            )
    
    # Pagination (only if not exporting)
    start_index = 0
    if not is_export_pdf and not is_export_excel:
        paginator = Paginator(treatments, 10)
        page_number = request.GET.get('page')
        treatments = paginator.get_page(page_number)
        start_index = (treatments.number - 1) * paginator.per_page if treatments.has_previous else 0
    
    context = {
        'treatments': treatments,
        'selected_patient': selected_patient,
        'search_query': search_query,
        'start_index': start_index,
        'is_export': is_export_pdf,
        'is_export_excel': is_export_excel,
        'hospital': hospital,
        'staff': staff,
    }
    if patient_id and selected_patient:
        patient = selected_patient
        context.update({
            "patient": patient,
            "history": PatientHistory.objects.filter(patient=patient).order_by("-date_recorded"),
            "bodycharts": BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded"),
            "observations": GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded"),
            "motions": RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on"),
            "treatments": TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created"),
            "outcomes": OutcomeMeasure.objects.filter(patient=patient).order_by("-date"),
        })
    
    return render(request, 'treatment_plan_table.html', context)


def treatment_plan_view(request, treatment_id):
    """View single treatment plan details"""
    patient_id = request.GET.get('patient_id', '')
    hospital = Hospital_data.objects.first()
    staff_id = request.session.get("staff_id")
    selected_patient = None
    if patient_id:
        try:
            selected_patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            messages.error(request, 'Patient not found.')
            return redirect('patienttable')
    if not staff_id:
        messages.error(request, 'Login to continue!!')
        return redirect('login')
    
    staff = StaffRegistration.objects.get(id=staff_id)
    treatment = get_object_or_404(TreatmentPlan, id=treatment_id)
    management_entries = ManagementEntry.objects.filter(treatment_plan=treatment).order_by('date')
    
    context = {
        'treatment': treatment,
        'management_entries': management_entries,
        'hospital': hospital,
        'staff': staff,
    }
    if patient_id and selected_patient:
        patient = selected_patient
        context.update({
            "patient": patient,
            "history": PatientHistory.objects.filter(patient=patient).order_by("-date_recorded"),
            "bodycharts": BodyChart.objects.filter(patient=patient_id).order_by("-date_uploaded"),
            "observations": GeneralObservation.objects.filter(patient=patient_id).order_by("-date_recorded"),
            "motions": RangeOfMotion.objects.filter(patient=patient_id).order_by("-recorded_on"),
            "treatments": TreatmentPlan.objects.filter(patient=patient_id).order_by("-date_created"),
            "outcomes": OutcomeMeasure.objects.filter(patient=patient).order_by("-date"),
        })
    return render(request, 'treatment_plan_details.html', context)


def delete_treatment_plan_ajax(request):
    """AJAX endpoint to delete a treatment plan"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            treatment_id = data.get('treatment_id') or request.POST.get('treatment_id')
            
            if not treatment_id:
                return JsonResponse({'success': False, 'message': 'Treatment ID required'})
            
            treatment = get_object_or_404(TreatmentPlan, id=treatment_id)
            treatment.delete()
            
            return JsonResponse({'success': True, 'message': 'Treatment plan deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def edit_invoice(request):
    staff_id = request.session.get("staff_id")
    if not staff_id:
        messages.error(request, 'Login to continue!!')
        return redirect('login')
    
    staff = get_object_or_404(StaffRegistration, id=staff_id)
    
    # Get invoice_id from GET parameter
    invoice_id = request.GET.get('invoice_id')
    if not invoice_id:
        messages.error(request, 'Invoice ID is required.')
        return redirect('invoice_list')
    
    invoice = get_object_or_404(Invoice, id=invoice_id, status="Active")
    hospital = Hospital_data.objects.first()
    
    # # Check if staff has permission to edit
    # if invoice.doctor.id != staff.id and not StaffAllocation.objects.filter(
    #     staff=staff, designation__Designation__iexact="Admin", status="active"
    # ).exists():
    #     messages.error(request, "You don't have permission to edit this invoice.")
    #     return redirect('invoice_list')
    
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get only the particulars from POST
            particulars = request.POST.getlist("particulars[]")
            
            # Get the existing qtys, rates, amounts from the invoice (they are read-only)
            existing_qtys = json.loads(invoice.qty) if invoice.qty else []
            existing_rates = json.loads(invoice.rate) if invoice.rate else []
            existing_amounts = json.loads(invoice.amount) if invoice.amount else []
            
            # Update only the particulars
            invoice.particulars = json.dumps(particulars)
            
            # Keep existing qty, rate, amount values
            invoice.qty = json.dumps(existing_qtys)
            invoice.rate = json.dumps(existing_rates)
            invoice.amount = json.dumps(existing_amounts)
            
            # Calculate new total from existing amounts
            total = sum(float(a) for a in existing_amounts if a)
            invoice.total_amount = total
            
            invoice.save()
            
            return JsonResponse({"success": True, "invoice_id": invoice.id})
            
        except Exception as e:
            print("Error updating invoice:", e)
            return JsonResponse({"success": False, "error": str(e)})
    
    # Convert stored JSON strings to lists for template rendering
    try:
        particulars_list = json.loads(invoice.particulars) if invoice.particulars else []
        qty_list = json.loads(invoice.qty) if invoice.qty else []
        rate_list = json.loads(invoice.rate) if invoice.rate else []
        amount_list = json.loads(invoice.amount) if invoice.amount else []
    except:
        particulars_list = []
        qty_list = []
        rate_list = []
        amount_list = []
    
    # Create list of items for template
    items = []
    for i in range(len(particulars_list)):
        items.append({
            'particular': particulars_list[i] if i < len(particulars_list) else '',
            'qty': qty_list[i] if i < len(qty_list) else 0,
            'rate': rate_list[i] if i < len(rate_list) else 0,
            'amount': amount_list[i] if i < len(amount_list) else 0
        })
    
    context = {
        "hospital": hospital,
        "invoice": invoice,
        "items": items,  # Pass items separately for better rendering
        "staff": staff,
    }
    return render(request, "invoice_edit.html", context)