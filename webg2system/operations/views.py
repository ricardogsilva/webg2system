import datetime as dt

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from models import RunningPackage

def list_daily_ops(request, timeslotStr):
    ts = datetime.dt.strptime(timeslotStr, '%Y%m%d').date()
    dailyRunPackages = RunningPackage.objects.filter(timeslot.date()==ts)
    

