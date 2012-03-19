import datetime as dt

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from models import RunningPackage
from systemsettings.models import Package, Area, Host, File
from forms import PartialRunningPackageForm

def create_running_package(request):
    if request.method == 'POST':
        form = PartialRunningPackageForm(request.POST)
        if form.is_valid():
            pack = Package.objects.get(name=form.cleaned_data['package'])
            host = Host.objects.get(name=form.cleaned_data['host'])
            area = Area.objects.get(name=form.cleaned_data['defaultArea'])
            timeslot = form.cleaned_data['timeslot']
            rp = RunningPackage(settings=pack, timeslot=timeslot, area=area, 
                                host=host)
            rp.save()
            return HttpResponseRedirect(reverse('operations_list'))
    else:
        form = PartialRunningPackageForm()
    return render_to_response('create_running_package.html', 
                              {'form' : form,},
                              context_instance=RequestContext(request))

def get_product(request):
    ts = dt.datetime.strptime(request.timeslot, '%Y%m%d%H%M')
    name = request.prodName
    theArea = '.*' # temporary hack
    files = File.objects.filter(product__short_name=name, fileType='hdf5')
    try:
        runningPackage = RunningPackage.objects.filter(
                timeslot=ts, 
                area__name=theArea,
                settings__codeClass__className='WebDisseminator',
                settings__packageOutput_systemsettings_packageoutput_related__outputItem__file__product__short_name=name).distinct()[0]
    except IndexError:
        # couldn't find the package
        raise
    pack = RunningPackage.create_package()
    tileZip = pack.disseminate_web(request.area)
    if tileZip is not None:
        # make django return a zip file
        pass
    pass
