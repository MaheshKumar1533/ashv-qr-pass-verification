from django.forms import ModelForm
from .models import GatePass, event, checkin

class CheckinForm(ModelForm):
    class Meta:
        model = checkin
        fields = ['holder']

class GatePassForm(ModelForm):
    class Meta:
        model = GatePass
        fields = ['holder_name', 'phone', 'id_proof', 'event']