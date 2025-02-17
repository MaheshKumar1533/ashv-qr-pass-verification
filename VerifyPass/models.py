from django.db import models

class event(models.Model):
    category = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    members = models.IntegerField(default=1)

class GatePass(models.Model):
    pass_number = models.CharField(max_length=50, unique=True)
    holder_name = models.CharField(max_length=100)
    valid_until = models.DateField(default='2025-02-23')
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15, null=True, blank=True)
    id_proof = models.CharField(max_length=100, null=True, blank=True)
    event = models.ForeignKey(event, on_delete=models.CASCADE, related_name='gate_pass')

    def __str__(self):
        return f"{self.pass_number} - {self.holder_name}"

class checkin(models.Model):
    holder = models.ForeignKey(GatePass, on_delete=models.CASCADE,related_name='checkin')
    checkin_time = models.DateTimeField(auto_now_add=True)
    checkin_members = models.IntegerField(null=True,blank=True,default=1)
    def __str__(self):
        return f"{self.pass_number} - {self.holder_name} - {self.checkin_time}"
