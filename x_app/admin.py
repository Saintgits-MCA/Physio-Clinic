from django.contrib import admin # type: ignore

# Register your models here.
from django.contrib import admin
from .models import *

# ---------------- Department ----------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# ---------------- Branch ----------------
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contact', 'incharge_name', 'incharge_phone')
    search_fields = ('name', 'incharge_name')
    filter_horizontal = ('departments',)

# ---------------- Staff Registration ----------------
@admin.register(StaffRegistration)
class StaffRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'gender', 'age', 'contact', 'email', 'branch')
    search_fields = ('name', 'email', 'contact')

# ---------------- Country ----------------
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# ---------------- State ----------------
@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country')
    search_fields = ('name',)
    list_filter = ('country',)

# ---------------- District ----------------
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'state')
    search_fields = ('name',)
    list_filter = ('state',)

# ---------------- Designation ----------------
@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('id', 'Designation')
    search_fields = ('Designation',)

# ---------------- Staff Allocation ----------------
@admin.register(StaffAllocation)
class StaffAllocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'staff', 'department', 'designation', 'status', 'branch')
    search_fields = ('email', 'staff__name')
    list_filter = ('status', 'branch', 'department', 'designation')

# ---------------- Patient ----------------
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'mr_no', 'gender', 'age', 'phone', 'branch')
    search_fields = ('name', 'mr_no', 'phone')
    list_filter = ('branch', 'state', 'district', 'country')

# ---------------- Appointment ----------------
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'token_no', 'patient', 'doctor', 'appointment_date', 'branch', 'status')
    search_fields = ('token_no', 'patient__name', 'doctor__name')
    list_filter = ('branch', 'department', 'status')

# ---------------- Hospital Data ----------------
@admin.register(Hospital_data)
class HospitalDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'registration_number', 'manager_name', 'email')
    search_fields = ('name', 'registration_number', 'manager_name', 'email')

# ---------------- Body Chart Image ----------------
@admin.register(BodyChartImage)
class BodyChartImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'uploaded_at')
    search_fields = ('title',)

# ---------------- Role ----------------
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)

# ---------------- Role Assignment ----------------
@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'role', 'branch', 'staff', 'status')
    list_filter = ('status', 'branch', 'role')
    search_fields = ('staff__name',)

# ---------------- Menu ----------------
@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'url')
    search_fields = ('name', 'category')

# ---------------- Menu Permission ----------------
@admin.register(MenuPermission)
class MenuPermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'role', 'menu', 'can_view', 'can_add', 'can_edit', 'can_delete')
    list_filter = ('role', 'menu', 'can_view', 'can_add', 'can_edit', 'can_delete')

# ---------------- Patient History ----------------
@admin.register(PatientHistory)
class PatientHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'staff', 'date_recorded', 'appointment_status')
    search_fields = ('patient__name', 'staff__name')
    list_filter = ('appointment_status',)

# ---------------- Body Chart ----------------
@admin.register(BodyChart)
class BodyChartAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'staff', 'type', 'date_uploaded')
    search_fields = ('patient__name', 'staff__name', 'type')

# ---------------- General Observation ----------------
@admin.register(GeneralObservation)
class GeneralObservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'staff', 'date_recorded')
    search_fields = ('patient__name', 'staff__name')

# ---------------- Range of Motion ----------------
@admin.register(RangeOfMotion)
class RangeOfMotionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'staff', 'joint', 'date')
    search_fields = ('patient__name', 'staff__name', 'joint')

# ---------------- Treatment Plan ----------------
@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'staff', 'date_created')
    search_fields = ('patient__name', 'staff__name')

# ---------------- Management Entry ----------------
@admin.register(ManagementEntry)
class ManagementEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'treatment_plan', 'staff', 'date', 'review_date', 'signature')
    search_fields = ('treatment_plan__patient__name', 'staff__name')

# ---------------- Outcome Measure ----------------
@admin.register(OutcomeMeasure)
class OutcomeMeasureAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'staff', 'outcome_used', 'date')
    search_fields = ('patient__name', 'staff__name', 'outcome_used')

# ---------------- Invoice ----------------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'total_amount', 'created_at')
    search_fields = ('patient__name', 'doctor__name')

# ---------------- Scoliosis Assessment ----------------
@admin.register(ScoliosisAssessment)
class ScoliosisAssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'date', 'height_cm', 'weight_kg', 'brace_used')
    search_fields = ('patient__name', 'doctor__name')
    list_filter = ('brace_used',)

# ---------------- Schroth Classification ----------------
@admin.register(SchrothClassification)
class SchrothClassificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# ---------------- HEP ----------------
@admin.register(HEP)
class HEPAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# ---------------- Manual Technique ----------------
@admin.register(ManualTechnique)
class ManualTechniqueAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
