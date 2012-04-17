import datetime as dt
import os
import json

import logging

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.servers.basehttp import FileWrapper
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from models import RunningPackage
from systemsettings.models import Package, Area, Host, File
from forms import CreatePackageForm

import systemsettings.models as ss
from core.g2packages import QuickLookGenerator, TileDistributor
import core.g2hosts as g2hosts

logger = logging.getLogger(__name__)

@csrf_exempt
def execute_package(request):
    if request.method == 'POST':
        f = CreatePackageForm(request.POST)
        if f.is_valid():
            timeslot = f.cleaned_data['timeslot']
            force = f.cleaned_data['force']
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    logger.debug(f.cleaned_data)
                    try:
                        p = Package.objects.get(name=f.cleaned_data['package'])
                        a = Area.objects.get(name=f.cleaned_data['area'])
                        rp = RunningPackage.objects.get(settings=p, 
                                                        area=a, 
                                                        timeslot=timeslot)
                    except (Package.DoesNotExist, Area.DoesNotExist):
                        logger.debug('Some of the input arguments are invalid: ' \
                                     'package or area inexistent.')
                        rp = None
                    except RunningPackage.DoesNotExist:
                        logger.info('The package does not exist. It will be ' \
                                    'created.')
                        rp = RunningPackage(settings=p, area=a, timeslot=timeslot)
                    if rp is not None:
                        runOutputList = []
                        callback = runOutputList.append
                        rp.force = force
                        runArgs = f.cleaned_data['extra']
                        if runArgs != '':
                            runkwargs = json.loads(runArgs)
                        else:
                            runkwargs = dict()
                        runResult = rp.run(callback=callback, **runkwargs)
                        result = render_to_response(
                                    'operations/run_output.html',
                                    {
                                        'result' : runResult, 
                                        'output' : runOutputList
                                    },
                                    context_instance=RequestContext(request)
                                 )
                    else:
                        pass
                    logout(request)
                else:
                    # user is not valid
                    logger.debug('Invalid user')
                    pass
            else:
                # user is none
                logger.debug('User is None')
                pass
        else:
            # form was invalid
            logger.debug('form was invalid')
            f = CreatePackageForm()
            result = render_to_response(
                        'operations/create_running_package.html',
                        {'form' : f,},
                        context_instance = RequestContext(request)
                     )
    else:
        f = CreatePackageForm()
        result = render_to_response(
                    'operations/create_running_package.html',
                    {'form' : f,},
                    context_instance = RequestContext(request)
                 )
    return result

def get_product_user_manual(request, prodName):
    hostFactory = g2hosts.HostFactory()
    theHost = hostFactory.create_host()
    theProduct = ss.Product.objects.get(short_name=prodName)
    pumPath = os.path.join(theHost.dataPath, theProduct.user_manual)
    if theHost.is_file(pumPath):
        content = open(pumPath, 'rb').read()
        response = HttpResponse(content, mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment: filename=%s' % \
                                          os.path.basename(pumPath)
        result = response
    else:
        raise Http404
    return result

def get_product_zip(request, prodName, tile, timeslot):
    ts = dt.datetime.strptime(timeslot, '%Y%m%d%H%M')
    settings = ss.Package.objects.get(codeClass__className='TileDistributor',
                                      product__short_name=prodName)
    area = ss.Area.objects.get(name='.*')
    pack = TileDistributor(settings, ts, area)
    theZip = pack.run_main(tile=tile)
    if theZip is not None:
        response = HttpResponse(FileWrapper(open(theZip)), 
                                content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=%s' \
                                          % os.path.basename(theZip)
        result = response
    else:
        raise Http404
    return result

def get_quicklook(request, prodName, tile, timeslot):
    ts = dt.datetime.strptime(timeslot, '%Y%m%d%H%M')
    settings = ss.Package.objects.get(codeClass__className='QuickLookGenerator',
                                      product__short_name=prodName)
    area = ss.Area.objects.get(name='.*')
    pack = QuickLookGenerator(settings, ts, area)
    if pack is not None:
        theQuickLook = pack.run_main(tile=tile)
        if theQuickLook is not None:
            imgData = open(theQuickLook).read()
            response = HttpResponse(imgData, mimetype='image/png')
        else:
            raise Http404
    else:
        raise Http404
    return response
