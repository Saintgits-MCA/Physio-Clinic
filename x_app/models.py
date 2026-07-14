import json
from django.db import models # type: ignore
from django.utils.timezone import now # type: ignore
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100)
    
    
class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    contact = models.CharField(max_length=15)
    incharge_name = models.CharField(max_length=100)
    incharge_phone = models.CharField(max_length=15)
    address = models.TextField(max_length=200)
    departments = models.ManyToManyField('Department', blank=True) 


    
class StaffRegistration(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)
    age = models.PositiveIntegerField()
    contact = models.CharField(max_length=10,default='0')
    qualification_details = models.TextField(default='null')
    joining_date = models.DateField(default=now)
    pancard = models.CharField(max_length=10,default='NA')
    address = models.TextField(default='null')
    email = models.EmailField(unique=True)
    branch=models.ForeignKey(Branch,on_delete=models.SET_NULL,null=True)
    status=models.CharField(max_length=20,default="Active")


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
class State(models.Model):
    country=models.ForeignKey(Country,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100, unique=True)
    
    
class District(models.Model):
    state=models.ForeignKey(State,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100, unique=True)
    
    
class Designation(models.Model):
    Designation = models.CharField(max_length=100, unique=True)

    

class StaffAllocation(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True)
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE, related_name="allocations")
    status = models.CharField(max_length=10, default='active')
    branch=models.ForeignKey(Branch,on_delete=models.SET_NULL,null=True)

    
class Patient(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    age = models.PositiveIntegerField()
    address = models.TextField()
    email = models.EmailField()
    date_of_admission = models.DateField(default=now)
    mr_no = models.CharField(max_length=50, unique=True,null=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    staff = models.ForeignKey(StaffRegistration, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    city=models.CharField(max_length=20,blank=True,null=True)

    
class Appointment(models.Model):
    token_no = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    appointment_date = models.DateField(default=now)
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("Department", on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey("StaffRegistration", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50)
    contact_no = models.CharField(max_length=15)
    appoinment_time=models.TimeField(blank=True,null=True)

    
    
class Hospital_data(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='hospital_logos/', blank=True, null=True)
    registration_number = models.CharField(max_length=100, unique=True)
    gst_number = models.CharField(max_length=50)
    manager_name = models.CharField(max_length=100)
    manager_contact = models.CharField(max_length=10)
    email = models.EmailField()
    address = models.TextField()
    def save(self, *args, **kwargs):
        if not self.pk and Hospital_data.objects.exists():
            raise ValueError("Only one Hospital instance is allowed.")
        return super().save(*args, **kwargs)


    
class BodyChartImage(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='body_charts/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=True)

    
class RoleAssignment(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)


class Menu(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    url = models.CharField(max_length=200, blank=True, null=True)


class MenuPermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    
# ..................................................................................................
    
class PatientHistory(models.Model):
    staff=models.ForeignKey(StaffRegistration, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    chief_complaints = models.TextField(blank=True)
    past_medical_history = models.TextField(blank=True)
    present_history = models.TextField(blank=True)
    drug_history = models.TextField(blank=True)
    date_recorded = models.DateField(auto_now_add=True)
    appointment_status=models.CharField(max_length=50,default='Consultation')
    provisional_diagnosis=models.TextField(blank=True)

# Body Chart
class BodyChart(models.Model):
    history = models.ForeignKey(PatientHistory, on_delete=models.CASCADE,null=True, related_name="body_charts")
    staff=models.ForeignKey(StaffRegistration, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    pain_assessment = models.TextField(blank=True)
    pain_area = models.TextField(blank=True)
    type=models.CharField(max_length=10,default=None)
    pain_history=models.TextField(blank=True,default=None)
    pain_severity=models.IntegerField(blank=True,default=None)
    date_uploaded = models.DateField(auto_now_add=True)


class GeneralObservation(models.Model):
    history = models.ForeignKey(PatientHistory, on_delete=models.CASCADE,null=True, related_name="observations")
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE)   # who logged in
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)           # patient being observed
    built = models.CharField(max_length=255, blank=True, null=True)
    swelling = models.CharField(max_length=255, blank=True, null=True)
    deformities = models.CharField(max_length=255, blank=True, null=True)
    tropical_changes = models.CharField(max_length=255, blank=True, null=True)
    skin = models.CharField(max_length=255, blank=True, null=True)
    edema = models.CharField(max_length=255, blank=True, null=True)
    warmth = models.CharField(max_length=255, blank=True, null=True)
    contractures = models.TextField(blank=True, null=True)
    light_touch = models.CharField(
        max_length=20,
        blank=True, null=True
    )
    crude_touch = models.CharField(
        max_length=20,
        blank=True, null=True
    )
    balance_sitting = models.CharField(
        max_length=30,
        blank=True, null=True
    )
    balance_standing = models.CharField(
        max_length=30,
        blank=True, null=True
    )
    date_recorded = models.DateTimeField(auto_now_add=True)

# Range of Motion
class RangeOfMotion(models.Model):
    history = models.ForeignKey(PatientHistory, on_delete=models.CASCADE,null=True, related_name="motions")
    staff=models.ForeignKey(StaffRegistration, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date=models.DateField()
    joint = models.CharField(max_length=100)
    arom = models.CharField(max_length=50, blank=True)
    prom = models.CharField(max_length=50, blank=True)
    fall_risk = models.TextField(blank=True)
    muscle_power = models.TextField(blank=True)
    recorded_on = models.DateField(auto_now_add=now)




# Treatment Plan
class TreatmentPlan(models.Model):
    history = models.ForeignKey(PatientHistory, on_delete=models.CASCADE,null=True, related_name="treatments")
    staff=models.ForeignKey(StaffRegistration, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    short_term_goals = models.TextField(blank=True)
    long_term_goals = models.TextField(blank=True)
    date_created = models.DateField(auto_now_add=True)



class ManagementEntry(models.Model):
    staff=models.ForeignKey(StaffRegistration, on_delete=models.CASCADE)
    treatment_plan = models.ForeignKey(TreatmentPlan, on_delete=models.CASCADE, related_name='management_entries')
    date = models.DateField()
    management = models.TextField()
    review_date = models.DateField()
    signature = models.CharField(max_length=100)
    

class OutcomeMeasure(models.Model):
    date = models.DateField()
    outcome_used = models.CharField(max_length=100)
    pretest_score = models.CharField(max_length=50, blank=True, null=True)
    posttest_score = models.CharField(max_length=50, blank=True, null=True)
    history = models.ForeignKey(PatientHistory, on_delete=models.CASCADE,null=True)
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE,null=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE,null=True)
    
class Invoice(models.Model):
    particulars = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateField(default=now, null=False, blank=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True)
    doctor = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE, null=True)
    amount = models.TextField()
    qty = models.TextField()
    rate = models.TextField()
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    payment_mode=models.CharField(max_length=100,null=True,blank=True,default="Cash")
    status=models.CharField(max_length=20,default="Active",null=True)
    def get_particulars(self):
        """Return list of dicts [{'particular':..., 'qty':..., 'rate':..., 'amount':...}]"""
        try:
            particulars_list = json.loads(self.particulars)
            qty_list = json.loads(self.qty)
            rate_list = json.loads(self.rate)
            amount_list = json.loads(self.amount)
            
            items = []
            for p, q, r, a in zip(particulars_list, qty_list, rate_list, amount_list):
                items.append({
                    "particular": p,
                    "qty": float(q),
                    "rate": float(r),
                    "amount": float(a)
                })
            return items
        except Exception as e:
            return []

class ScoliosisAssessment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(StaffRegistration, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=now)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    
    # Clinical
    diagnosis_pattern = models.CharField(max_length=255, blank=True,null=True)
    uev = models.CharField(max_length=100, blank=True,null=True)
    lev = models.CharField(max_length=100, blank=True,null=True)
    lumbar_lev = models.CharField(max_length=100, blank=True,null=True)
    cobbs_angle = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    scoliometer_ut = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    scoliometer_t = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    scoliometer_l = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    brace_used = models.BooleanField(default=False)

    # Additional details
    menses_since = models.CharField(max_length=100, blank=True,null=True)
    other_diseases = models.CharField(max_length=255, blank=True,null=True)
    shoe_lift = models.CharField(max_length=100, blank=True,null=True)
    family_history = models.TextField(blank=True,null=True)
    # Schroth classification
    schroth_classification = models.CharField(max_length=255, blank=True,null=True)
    # Uploads
    xray = models.FileField(upload_to='scoliosis/xray/', blank=True, null=True)
    diagram = models.FileField(upload_to='scoliosis/diagram/', blank=True, null=True)
    # HEP (multiple checkboxes)
    hep = models.JSONField(default=list, blank=True,null=True)
    # Manual technique (single radio)
    manual_technique = models.CharField(max_length=100, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cobbs_angle_L = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    def __str__(self):
        return f"{self.patient.name} - {self.date.strftime('%d-%m-%Y')}"
    
    
    
    
class SchrothClassification(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class HEP(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ManualTechnique(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Expense_Type(models.Model):
    expense_type=models.CharField(max_length=100,unique=True)
    active=models.CharField(max_length=10,default="active")
    def __str__(self):
        return self.expense_type
    
class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=now)
    status = models.CharField(max_length=10, default='active')
    expense_type = models.ForeignKey(Expense_Type, on_delete=models.SET_NULL, null=True)
    staff = models.ForeignKey(StaffRegistration, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.expense_type} - {self.amount}"
    
class ScoliosisFollowUp(models.Model):
    scoliosis = models.ForeignKey(ScoliosisAssessment, on_delete=models.CASCADE, related_name="followups")
    followup_date = models.DateField(default=timezone.now)
    diagnosis_pattern = models.CharField(max_length=255, blank=True)
    uev = models.CharField(max_length=100, blank=True)
    lev = models.CharField(max_length=100, blank=True)
    lumbar_lev = models.CharField(max_length=100, blank=True)
    cobbs_angle = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    cobbs_angle_L = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    scoliometer_ut = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    scoliometer_t = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    scoliometer_l = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    brace_used = models.BooleanField(default=False)
    pain_level = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Follow-up on {self.followup_date} for {self.scoliosis}"
    
    
    
class Medicine_Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=True)
    
    
class Medical_Store(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='medical_store/', blank=True, null=True)
    registration_number = models.CharField(max_length=100, unique=True)
    gst_number = models.CharField(max_length=50)
    manager_name = models.CharField(max_length=100)
    manager_contact = models.CharField(max_length=10)
    email = models.EmailField()
    address = models.TextField()
    def save(self, *args, **kwargs):
        if not self.pk and Medical_Store.objects.exists():
            raise ValueError("Only one Medical Store instance is allowed.")
        return super().save(*args, **kwargs)
    
    
class TaxMaster(models.Model):
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tax_name} ({self.tax_percent}%)"


class MedicineMaster(models.Model):
    staff = models.ForeignKey('StaffRegistration', on_delete=models.SET_NULL, null=True, blank=True)
    item_code = models.CharField(max_length=100)
    hsn_code = models.CharField(max_length=100)
    medicine_name = models.CharField(max_length=200)
    category = models.ForeignKey('Medicine_Category', on_delete=models.SET_NULL, null=True, blank=True)
    generic_name = models.CharField(max_length=200)
    rack_number = models.CharField(max_length=50)
    base_unit = models.CharField(max_length=50)
    side_effects = models.TextField(blank=True, null=True)
    tax = models.ForeignKey(TaxMaster, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.medicine_name
    
class Company(models.Model):
    name = models.CharField(max_length=100)
    
    
class SupplierMaster(models.Model):
    staff = models.ForeignKey(StaffRegistration, on_delete=models.SET_NULL, null=True, blank=True)
    supplier_code = models.CharField(max_length=50, unique=True)
    supplier_name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.supplier_name
    
class PhysicalStock(models.Model):
    staff = models.ForeignKey(StaffRegistration, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(SupplierMaster, on_delete=models.SET_NULL, null=True, blank=True)
    supplier_contact = models.CharField(max_length=15, blank=True, null=True)
    medicine_company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    item = models.ForeignKey(MedicineMaster, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    batch_number = models.CharField(max_length=100)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item} - {self.batch_number}"
    
    
class GSTInvoice(models.Model):
    medical_store = models.ForeignKey(Medical_Store, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    invoice_no = models.CharField(max_length=50, unique=True)
    date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 💡 before tax
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    payment_mode = models.CharField(max_length=30, blank=True, null=True,default="Cash")
    status=models.CharField(max_length=20,blank=False,default="Active")
    deleted_by = models.ForeignKey(StaffRegistration, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return f"Invoice {self.invoice_no} - {self.patient.name if self.patient else 'NA'}"


class GSTInvoiceItem(models.Model):
    invoice = models.ForeignKey(GSTInvoice, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(MedicineMaster, on_delete=models.SET_NULL, null=True, blank=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    company_name = models.ForeignKey(Company,on_delete=models.CASCADE, null=True,blank=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    qty = models.PositiveIntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    each_taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 💡 before tax
    each_cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    each_sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    def __str__(self):
        return f"{self.item.medicine_name if self.item else 'Item'} - {self.invoice.invoice_no}"
    
    
class BankDetails(models.Model):
    medical_store = models.ForeignKey('Medical_Store', on_delete=models.CASCADE, related_name='bank_details')
    bank_name = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=15)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    qr_code = models.ImageField(upload_to='bank_qr/', blank=True, null=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"
    
    
class PurchaseInvoice(models.Model):
        medical_store = models.ForeignKey(Medical_Store, on_delete=models.CASCADE)
        supplier = models.ForeignKey(SupplierMaster, on_delete=models.CASCADE)
        purchase_no = models.CharField(max_length=50, unique=True)
        date = models.DateField()
        total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        created_by = models.ForeignKey(StaffRegistration, on_delete=models.SET_NULL, null=True)
        bill_number = models.CharField(max_length=50,blank=True,null=True)

        
class PurchaseInvoiceItem(models.Model):
        invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name="items")
        item = models.ForeignKey(MedicineMaster, on_delete=models.SET_NULL, null=True)
        batch_number = models.CharField(max_length=50, blank=True, null=True)
        expiry_date = models.DateField(blank=True, null=True)
        company_name = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
        unit = models.CharField(max_length=50, blank=True, null=True)
        qty = models.PositiveIntegerField(default=1)
        rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
        each_taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        each_cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        each_sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        

class InvoiceParticular(models.Model):
    hospital = models.ForeignKey('Hospital_data', on_delete=models.CASCADE)
    created_by = models.ForeignKey(StaffRegistration, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=150)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name