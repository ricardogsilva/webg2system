import datetime as dt
import os

from django.http import HttpResponseRedirect, HttpResponse, Http404
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

#FIXME - This view is not done yet
def get_product_zip(request):
    ts = dt.datetime.strptime(request.timeslot, '%Y%m%d%H%M')
    name = request.prodName
    theArea = '.*' # temporary hack
    files = File.objects.filter(product__short_name=name, fileType='hdf5')
    try:
        rp = RunningPackage.objects.filter(
                timeslot=ts, 
                area__name=theArea,
                settings__codeClass__className='WebDisseminator',
                settings__packageOutput_systemsettings_packageoutput_related__outputItem__file__product__short_name=name).distinct()[0]
    except IndexError:
        # couldn't find the package
        raise
    pack = rp.create_package()
    tileZip = pack.disseminate_web(request.area)
    if tileZip is not None:
        # make django return a zip file
        pass
    pass

def get_quicklook(request, prodName, area, timeslot):
    pack = _create_package(prodName, timeslot)
    theQuickLook = None
    if pack is not None:
        qLookPattern = os.path.join(pack.quickviewOutDir, 
                                    '.*%s.*' % area)
        qLookList = pack.host.find([qLookPattern])
        if len(qLookList) == 1:
            # the quicklook is already available
            theQuickLook = qLookList[0]
        elif len(qLookList) == 0:
            # generate a new quicklook
            mapfile = pack.get_quicklooks_mapfile()
            tilePath = pack._get_tile(area)[0]
            theQuickLook = pack.generate_quicklook(mapfile, tilePath, 
                                                   pack.quickviewOutDir)
        if theQuickLook is not None:
            imgData = open(theQuickLook).read()
            response = HttpResponse(imgData, mimetype='image/png')
        else:
            raise Http404
    else:
        raise Http404
    return response



#FIXME - use django's get_list_or_404 to handle undefined packages
def _create_package(prodName, timeslot):
    '''
    Create an operations.core.g2packages.G2Package
    '''

    ts = dt.datetime.strptime(timeslot, '%Y%m%d%H%M')
    name = prodName
    theArea = '.*' # temporary hack
    files = File.objects.filter(product__short_name=name, fileType='hdf5')
    try:
        rp = RunningPackage.objects.filter(
                timeslot=ts, 
                area__name=theArea,
                settings__codeClass__className='WebDisseminator',
                settings__packageOutput_systemsettings_packageoutput_related__outputItem__file__product__short_name=name).distinct()[0]
        pack = rp.create_package()
    except IndexError:
        # couldn't find the package
        pack = None
    return pack

