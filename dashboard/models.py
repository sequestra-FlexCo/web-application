from django.db import models

class Session(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('ended', 'Ended'),
    )
    name = models.CharField(max_length=100, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    rpm = models.IntegerField(default=1000)
    weight_log = models.CharField(max_length=500, blank=True, null=True) 

    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"

# Create your models here.
class ScriptLog(models.Model):
    script_name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    output = models.TextField()
    error = models.TextField(blank=True, null=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE,  null=False, blank=False)
    

class TemperatureLog(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='temperature_logs')
    temperature = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.temperature}°C at {self.timestamp}"
    
class StirrerLog(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='stirrer_logs')
    rpm = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rpm}RPM at {self.timestamp}"