from django.forms import ModelForm
from .models import GatePass, event, checkin

class CheckinForm(ModelForm):
    class Meta:
        model = checkin
        fields = ['holder', 'checkin_members']

class GatePassForm(ModelForm):
    class Meta:
        model = GatePass
        fields = ['pass_number', 'holder_name', 'name', 'email', 'phone', 'id_proof', 'event']