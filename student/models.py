from django.db import models
import random 
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError 
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.core.validators import FileExtensionValidator

# Create your models here
class LoginForm(models.Model):
    name = models.CharField(null=False,max_length=50)
    email = models.EmailField(null=False,max_length=100,default=' ')
    user_password = models.CharField(null=False, max_length=8)
    confirm_password = models.CharField(null=False, max_length=8)
    is_active = models.BooleanField(default=True)
    user_otp = models.CharField(max_length=6, blank=True, null=True)
    generated_otp = models.CharField(max_length=6, blank=True, null=True)  
    otp_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.email})'

    class Meta:
        verbose_name_plural = 'Sign-Up Student Account' 

        
    def generate_otp(self):
    
        self.generated_otp = str(random.randint(100000, 999999))
        self.otp_expiry = datetime.now() + timedelta(minutes=5)  
        self.save()

        self.send_otp_email()

    def send_otp_email(self):
        subject = 'Your OTP for Login'
        message = f'Hello {self.name},\n\nYour OTP for login is {self.generated_otp}. It will expire in 5 minutes.'
        from_email = 'jhss12ahariharan@gmail.com'
        
        send_mail(
            subject,
            message,
            from_email,
            [self.email],
            fail_silently=False,
        )
    def set_password(self, password):
        """Hashes and stores the password securely."""
        from django.contrib.auth.hashers import make_password
        self.user_password = make_password(password)
        self.save()

    def check_password(self, password):
        """Compares a plain text password with the stored hashed password."""
        from django.contrib.auth.hashers import check_password
        return check_password(password, self.user_password)
    

YEAR = [
    ('1', '1st Year'),
    ('2', '2nd Year'),
    ('3', '3rd Year'),
    ('4', '4th Year'),
    ('5', '5th Year'),
]

CHOOSE = [
    ('Beginner', 'Beginner'),
    ('Intermediate', 'Intermediate'),
    ('Advance', 'Advance'),
]

MARK_TYPE = [
    ('percentage', 'Percentage'),
    ('cgpa', 'CGPA'),
]

class Home(models.Model):
    student_name = models.OneToOneField(LoginForm,null=True,on_delete=models.CASCADE,related_name='Login_student')
    college_name = models.CharField(null=False,max_length=100)
    course = models.CharField(null=False, max_length=30)
    year = models.CharField(choices=YEAR, max_length=2) 
    CGPA = models.CharField(choices=MARK_TYPE, max_length=10)  
    student_choice = models.CharField(choices=CHOOSE, max_length=20) 
    
    cgpa_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cgpa_number = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.CGPA == 'percentage' and self.cgpa_percentage is None:
            raise ValueError("Percentage CGPA is required when CGPA type is 'percentage'")
        elif self.CGPA == 'cgpa' and self.cgpa_number is None:
            raise ValueError("Numeric CGPA is required when CGPA type is 'cgpa'")
        
        if self.CGPA == 'percentage' and self.cgpa_number is not None:
            raise ValueError("Please provide only CGPA percentage, not CGPA number.")
        elif self.CGPA == 'cgpa' and self.cgpa_percentage is not None:
            raise ValueError("Please provide only CGPA number, not CGPA percentage.")
        
        super(Home, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.college_name} - {self.course} - {self.year} - {self.CGPA}"
    
    class Meta:
        verbose_name_plural = 'Student Information'


class StudentID(models.Model):
    student = models.OneToOneField(LoginForm,on_delete=models.CASCADE,related_name='student_name')
    unique_id = models.CharField(max_length=4,unique=True,editable=False)
    password = models.CharField(max_length=8)

    def save(self,*args,**kwargs):
        if not self.unique_id:
            while True:
                random_id = str(random.randint(1000, 9999))
                if not StudentID.objects.filter(unique_id=random_id).exists():
                    self.unique_id = random_id
                    break
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_student_id():
        while True:
            random_id = get_random_string(length=4, allowed_chars='0123456789')
            if not StudentID.objects.filter(student_id=random_id).exists():
                return random_id
            
    def __str__(self):
        return f"StudentID: {self.unique_id} - {self.student.name}"
            
    class Meta:
        verbose_name_plural = 'Sign-In Student Account'


STUDENT_CHOICE = [
    ('Summary','Summary'),
    ('Keywords','Keywords'),
    ('Full-Text','Full-Text'),
]

class UploadFile(models.Model):
    upload_file = models.FileField(null=False,upload_to='documents/',validators=[FileExtensionValidator(['pdf', 'docx'])])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    student_options = models.CharField(choices=STUDENT_CHOICE,max_length=30)
