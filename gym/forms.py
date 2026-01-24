from django import forms
from core.models import (
    WorkoutVideo, DietPlan, LeaveRequest, MemberProfile, 
    CustomUser, BrandingConfig, Payment, Expense
)

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['member', 'amount', 'date', 'payment_type', 'remarks']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'date', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class VideoForm(forms.ModelForm):
    class Meta:
        model = WorkoutVideo
        fields = ['title', 'video_file', 'description', 'target_audience']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'video_file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'target_audience': forms.Select(attrs={'class': 'form-control'}),
        }

class DietPlanForm(forms.ModelForm):
    class Meta:
        model = DietPlan
        fields = ['member', 'title', 'content']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MemberAddForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Minimum 8 characters'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm Password'
    )
    
    class Meta:
        model = MemberProfile
        fields = ['membership_type', 'age', 'occupation', 'image', 'phone_number',
                 'registration_date', 'registration_amount', 'monthly_amount', 'allotted_slot', 'address']
        widgets = {
            'membership_type': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'registration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'registration_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'monthly_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'allotted_slot': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 6:00 AM - 7:00 AM'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match!")
            
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long!")
        
        return cleaned_data


class MemberEditForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = MemberProfile
        fields = ['membership_type', 'age', 'occupation', 'image', 'phone_number',
                 'next_payment_date', 'monthly_amount', 'allotted_slot', 'address']
        widgets = {
            'membership_type': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'next_payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monthly_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'allotted_slot': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class WhatsAppMessageForm(forms.Form):
    """Form for sending WhatsApp messages to members by time slot"""
    time_slot = forms.ChoiceField(
        label='Target Group',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select a time slot or send to all members'
    )
    message = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter your message here...'
        }),
        help_text='Message will be sent via WhatsApp to all members in the selected group'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate time slot choices
        from core.models import MemberProfile
        slots = MemberProfile.objects.values_list(
            'allotted_slot', flat=True
        ).distinct().order_by('allotted_slot')
        
        choices = [('all', 'All Members')]
        choices.extend([(slot, slot) for slot in slots if slot])
        
        self.fields['time_slot'].choices = choices

class BulkPhoneImportForm(forms.Form):
    """Form for bulk importing phone numbers from CSV"""
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with columns: username, phone_number',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        
        # Check file extension
        if not file.name.endswith('.csv'):
            raise forms.ValidationError('File must be a CSV file (.csv)')
        
        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 5MB')
        
        return file


class BulkMemberImportForm(forms.Form):
    """Form for bulk importing members from CSV"""
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with columns: username, email, first_name, last_name, password, membership_type, age, phone_number, registration_amount, monthly_amount, allotted_slot, address',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError('File must be a CSV file (.csv)')
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 10MB')
        return file


class BrandingForm(forms.ModelForm):
    class Meta:
        model = BrandingConfig
        fields = ['app_name', 'primary_color', 'secondary_color', 'accent_color', 'logo', 'enable_auto_whatsapp_reminders', 'whatsapp_reminder_days_before']
        widgets = {
            'app_name': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'enable_auto_whatsapp_reminders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'whatsapp_reminder_days_before': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30}),
        }

class TrainerAddForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Minimum 8 characters'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm Password'
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match!")
            
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long!")
        
        return cleaned_data

class TrainerEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class StaffAddForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Minimum 8 characters'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm Password'
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match!")
            
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long!")
        
        return cleaned_data


class StaffEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
