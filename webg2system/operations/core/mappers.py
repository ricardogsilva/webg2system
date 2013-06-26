#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

import re
import os
import logging
from subprocess import Popen, PIPE
import numpy as np
from PIL import Image as img
from PIL import ImageFont as imgFont
from PIL import ImageDraw as imgDraw
from osgeo import gdal
from osgeo import osr
import mapscript

import utilities

# FIXME
#   - Mix this file with some of the code used in the lsasaf georeferencer
#   project. That sould allow the rescaling of the values and the geotiff
#   output.

class Mapper(object):

    # gdal settings
    blockXSize = 200
    blockYSize = 200

    gdal_np_dtypes = {
        gdal.GDT_Int16 : np.int16,
        gdal.GDT_Float32 : np.float32,
    }

    def __init__(self, g2File, productSettings, logger=None):
        '''
        Inputs:

            g2File - A operations.core.g2files.G2File object.

            productSettings - The settings of the product that is to be
                generated.
        '''

        #self.logger = logging.getLogger(
        #        '.'.join((__name__, self.__class__.__name__)))
        self.logger = logger
        self.nLines = int(g2File.nLines)
        self.nCols = int(g2File.nCols)
        self.product = productSettings
        self.host = g2File.host
        self.timeslot = g2File.timeslot
        if self.product.geotiff_dtype == 'float':
            self.dataType = gdal.GDT_Float32
        elif self.product.geotiff_dtype == 'int':
            self.dataType = gdal.GDT_Int16

    def create_global_tiff(self, fileList, outDir, outName):
        raise NotImplementedError

    def create_mapfile(self, geotifPath, outputPath, template):
        raise NotImplementedError


class NGPMapper(Mapper): #crappy name

    # FIXME - Move IO operations to the G2Host classes
    def create_global_tiff(self, fileList, outDir, outName, dataset=None):
        '''
        Inputs

            fileList

            outDir

            outName

            dataset - The name of the dataset to use for creating the global 
                tiff file. If None (the default) the main dataset will be 
                used.
        '''

        if dataset is None:
            ds = self.product.dataset_set.filter(isMainDataset=True)[0]
        else:
            ds = self.product.dataset_set.get(name=dataset)
        #missingValue = int(ds.missingValue)
        #scalingFactor = int(ds.scalingFactor)
        missingValue = float(ds.missingValue)
        scalingFactor = float(ds.scalingFactor)
        tilePaths = self.create_geotiffs(fileList, outDir, ds, missingValue, 
                                         scalingFactor)
        self.logger.debug('Merging individual tiles into a global tiff...')
        tempTif = self.merge_tiles(tilePaths, missingValue, 'temp_nodata.tif',
                                   outDir)
        globalTiff = self._fix_nodata(tempTif, outName, missingValue)
        ovrFile = self.build_overviews(globalTiff, 6)
        temps = tilePaths + [tempTif]
        self.remove_temps(temps)
        return globalTiff

    def _get_corner_coordinates(self, filePath, tileXLength, tileYLength):
        h, v = self.get_h_v(filePath)
        if h is None:
            # this is a continental tile
            raise NotImplementedError
        else:
            # this is a small tile
            firstLat = -v * tileYLength + 90
            firstLon = tileXLength * h - 180
        return firstLat, firstLon

    def remove_temps(self, paths):
        for path in paths:
            if os.path.isfile(path):
                os.remove(path)
            else:
                pass

    def create_geotiffs(self, fileList, outputDir, dataset, missingValue, 
                        scalingFactor, tolerance=0.1):
        '''
        Creates geotiffs from a list of G2File HDF5 filepaths.

        Inputs:

            fileList - A list of files

            outputDir - 

            dataset - A systemsettings.models.Dataset object

            missingValue - An integer

            scalingFactor - 

            tolerance - 
        '''

        outputPaths = []
        for fNum, path in enumerate(fileList):
            #self.logger.debug('(%i/%i) - Converting HDF5 to GeoTiff...' % (fNum+1, len(fileList)))
            fileName = os.path.basename(path) + '.tif'
            outputPath = os.path.join(outputDir, fileName)
            outDriver = gdal.GetDriverByName('GTiff')
            #inDs = gdal.Open('HDF5:"%s"://%s' % (path, dataset.name))
            inDs = gdal.Open(str("HDF5:%s://%s" % (path, dataset.name)))
            #la = inDs.GetRasterBand(1).ReadAsArray()
            numpy_type = self.gdal_np_dtypes.get(self.dataType)
            la = inDs.GetRasterBand(1).ReadAsArray().astype(numpy_type)
            # dealing with the missing value and scaling factor
            la[abs(la - missingValue) > tolerance] = la[abs(la - missingValue) > tolerance] / scalingFactor
            la[abs(la - missingValue) <= tolerance] = missingValue
            outDs = outDriver.Create(str(outputPath), self.nCols, self.nLines,
                                     1, self.dataType)
            outBand = outDs.GetRasterBand(1)
            outBand.WriteArray(la, 0, 0)
            # BEWARE: self.pixelSize is measured in degrees
            tileXLength = self.nCols * float(self.product.pixelSize)
            tileYLength = self.nLines * float(self.product.pixelSize)
            firstLat, firstLon = self._get_corner_coordinates(path, 
                                                              tileXLength, 
                                                              tileYLength)
            ullon = firstLon * 1.0 - 0.05 / 2.0
            ullat = firstLat * 1.0 + 0.05 / 2.0
            outDs.SetGeoTransform([ullon, 0.05, 0, ullat, 0, -0.05])
            srs = osr.SpatialReference()
            srs.SetWellKnownGeogCS("WGS84")
            outDs.SetProjection(srs.ExportToWkt())
            outBand.SetNoDataValue(missingValue)
            outBand.FlushCache()
            inDs = None
            outDs = None
            outputPaths.append(outputPath)
        return outputPaths

    def _fix_nodata(self, filePath, outputName, noData):
        '''
        Use gdal_translate to assign a noData value to filePath.
        '''

        dirName, fName = os.path.split(filePath)
        outputPath = os.path.join(dirName, outputName)
        cmdList = ['gdal_translate', '-co', 'TILED=YES', 
                   '-a_nodata', '%f' % noData, filePath, outputPath]
        newProcess = Popen(cmdList, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout,stderr = newProcess.communicate()
        return outputPath

    def merge_tiles(self, tilePaths, noData=0, outName=None, outDir=None):
        '''
        Call gdal_merge utility and create a global TIFF file mosaicing all 
        the tiles.

        Inputs:

            tilePaths - A list with the full paths to the tiles to merge.
                These tiles must already be georeferenced geotiffs.

            noData - An integer specifying the noData value.

            outName - The name of the new tiff file to create. If None 
                (the default), the name of the new file will be the same as
                the individual tiles, without the HXXVYY section.

            outDir - The directory where the new tiff should be created. If
                None (the default), the output directory will be the same
                as the input one.
        '''

        namePatt = re.compile(r'_H\d{2}V\d{2}')
        if outName is None:
            outName = namePatt.sub('',os.path.basename(tilePaths[0]))
        if outDir is None:
            outDir = os.path.dirname(tilePaths[0])
        outPath = os.path.join(outDir, outName)
        cmdList = [
                'gdal_merge.py', 
                '-o', '%s' % outPath,
                '-n', '%f' % noData,
                '-init', '%f' % noData,
                '-co', 'TILED=YES'] + tilePaths
        newProcess = Popen(cmdList, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout,stderr = newProcess.communicate()
        return outPath

    def build_overviews(self, filePath, levels=6):
        '''
        Use gdaladdo for building external overviews for the input filePath.

        Inputs:

            filePath - A string with the full path to the file.

            levels - An integer specifying how many levels of overviews should
                be created.
        '''

        levelList = [str(pow(2, n)) for n in range(1, levels+1)]
        cmdList = ['gdaladdo', '-ro', filePath] + levelList
        #return ' '.join(cmdList)
        newProcess = Popen(cmdList, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout,stderr = newProcess.communicate()
        return newProcess.returncode

    def get_dataset_name(self, filePath):
        dataset = None
        for fName in self.datasets.keys():
            if re.search(fName, filePath) is not None:
                dataset = self.datasets.get(fName)
                break
        return dataset

    def _get_extreme_tile_numbers(self, fileList):
        hs = [self.get_h_v(f)[0] for f in fileList]
        vs = [self.get_h_v(f)[1] for f in fileList]
        minH, maxH = min(hs), max(hs)
        minV, maxV = min(vs), max(vs)
        return minH, maxH, minV, maxV

    def get_h_v(self, fileName):
        hvPatt = re.compile(r'H(\d{2})V(\d{2})')
        reObj = hvPatt.search(fileName)
        if reObj is not None:
            h = int(reObj.group(1))
            v = int(reObj.group(2))
        else:
            h = None
            v = None
        return h, v

    def get_area(self, fileName):
        hvPatt = re.compile(r'H(\d{2})V(\d{2})')
        reObj = hvPatt.search(fileName)
        if reObj is not None:
            area = reObj.group()
        else:
            try:
                area = os.path.baseName(fileName).split('_')[4]
            except IndexError:
                self.logger.error('Couldn\'t find area from the file name.')
                area = None
        return area

    def create_mapfile(self, geotifRelativePath, geotifCommonDir, outputPath, template):
        '''
        Create a new mapfile for UMN Mapserver based on the template.

        Inputs:

            geotifRelativePath - The relative path to the geotif file.
                This path is relative to 'geotifCommonDir'.

            geotifCommonDir - A common directory that is parent to all the
                generated geotiffs, so that mapserver can find the
                files that belong to different layers.

            outputPath - The full path of the new mapfile.

            template - The full path to the template mapfile to use.
        '''

        templateMap = mapscript.mapObj(template)
        # look for the file, it may already be there
        if self.host.is_file(outputPath):
            mapfile = mapscript.mapObj(outputPath)
        else:
            mapfile = templateMap.clone()
        mapfile.shapepath = geotifCommonDir
        mapfile.name = 'quicklooks'
        mapWMSMetadata = mapfile.web.metadata
        mapWMSMetadata.set('wms_title', 'quicklooks')
        mapWMSMetadata.set('wms_onlineresource', 
                        'http://%s/cgi-bin/mapserv?map=%s&' \
                        % (self.host.host, outputPath))
        layer = mapfile.getLayerByName(self.product.short_name)
        if layer is None:
            layerIndex = mapfile.insertLayer(templateMap.getLayerByName(
                                             self.product.short_name))
            layer = mapfile.getLayer(layerIndex)
        layer.data = geotifRelativePath
        layer.status = mapscript.MS_ON
        layerWMSMetadata = layer.metadata
        layerWMSMetadata.set('wms_title', self.product.short_name)
        for i in range(mapfile.numlayers):
            otherLayer = mapfile.getLayer(i)
            if otherLayer.name != layer.name:
                otherLayer.status = mapscript.MS_OFF
        mapfile.save(outputPath)
        return outputPath

    def update_latest_mapfile(self, mapfile, shapePath, geotifRelativePath):
        '''
        Update the 'latest' mapfile.

        Inputs:

            mapfile - Full path to the mapfile.

            shapePath - Value to attribute to the mapfile's 'shapepath' 
                variable.

            geotifRelativePath - Relative path to the geotiff. This path 
                is relative to the shapePath argument.
        '''

        
        mapObj = mapscript.mapObj(mapfile)
        mapObj.shapepath = shapePath
        mapWMSMetadata = mapObj.web.metadata
        mapWMSMetadata.set('wms_onlineresource', 
                           'http://%s/cgi-bin/mapserv?map=%s&' \
                            % (self.host.host, mapfile))
        layer = mapObj.getLayerByName(self.product.short_name)
        layer.data = geotifRelativePath
        layerAbstract = '%s product generated for the %s timeslot.' % \
                        (self.product.short_name, 
                         self.timeslot.strftime('%Y-%m-%d %H:%M'))
        layer.metadata.set('wms_abstract', layerAbstract)
        mapObj.save(mapfile)
        return mapfile

    def generate_legend(self, mapfile, layers, outputDir):
        '''
        Generate a legend png for the input mapfile.

        Inputs:

            mapfile - The path to the mapfile.

            layers - A list of layer names that are to be included in the 
                legend.

            outputDir - The directory where the legend file is to be created.

        Returns:

            The full path to the newly generated legend file.
        '''

        self._select_mapfile_layers(mapfile, layers)
        legendPath = os.path.join(outputDir, 'legend.png')
        legendCommand = 'legend %s %s' % (mapfile, legendPath)
        mapfileDir = os.path.dirname(mapfile)
        self.host.run_program(legendCommand, mapfileDir)
        return legendPath

    def _select_mapfile_layers(self, mapfile, layers):
        '''
        Turn the selected layers ON and all the others OFF.

        Inputs:

            mapfile - The path to the mapfile.

            layers - A list of layer names that are to be included in the 
                legend.
        '''
            
        mapfileObj = mapscript.mapObj(mapfile)
        for i in range(mapfileObj.numlayers):
            layer = mapfileObj.getLayer(i)
            if layer.name in layers:
                layer.status = mapscript.MS_ON
            else:
                layer.status = mapscript.MS_OFF
        mapfileObj.save(mapfile)

    # FIXME
    # - Use mapscript.imageObj to generate the quicklooks instead of
    #   launching the shp2img external process       
    def generate_quicklook(self, outputDir, mapfile, filePath, legendPath):
        '''
        Generate the quicklook file.

        Inputs:

            outputDir - directory where the quicklook file is to be saved to.

            mapfile - Full path to the mapfile to be used when generating 
                the quicklooks.

            filePath - The file for which the quicklook is to be created.

            legendPath - Path to the legend file.

        Returns:
            
            A list of full paths to the newly created quicklooks.
        '''

        dirPath, fname = os.path.split(filePath)
        minx, miny, maxx, maxy = self.get_bounds(filePath)
        rawQuickPath = os.path.join(outputDir, 'rawquicklook_%s.png' % fname)
        command = 'shp2img -m %s -o %s -e %i %i %i %i -s '\
                  '400 400 -l %s' % (mapfile, rawQuickPath, minx, miny, 
                                     maxx, maxy, self.product.short_name)
        stdout, stderr, retcode = self.host.run_program(command)
        outPath = self._complete_quicklook(rawQuickPath, legendPath)
        self.remove_temps([rawQuickPath])
        return outPath

    def get_bounds(self, path):
        '''Return a 4-element tuple with minx, miny, maxx, maxy.'''

        tileXLength = self.nCols * float(self.product.pixelSize)
        tileYLength = self.nLines * float(self.product.pixelSize)
        firstLat, firstLon = self._get_corner_coordinates(path, tileXLength,
                                                          tileYLength)
        minx = firstLon
        miny = firstLat - tileYLength
        maxx = firstLon + tileXLength
        maxy = firstLat
        return minx, miny, maxx, maxy

    def _complete_quicklook(self, filePath, legendPath, title=None, 
                            cleanRaw=True):
        '''
        Create the final quicklook file by incorporating the extra elements.

        Inputs:

            filePath - Full path to the raw quicklook.

            legendPath - Full path to the legend image.

            title - Title for the quicklook.
        '''

        rawPatt = re.compile(r'rawquicklook_')
        if title is None:
            fname = os.path.basename(filePath).rpartition('.')[0]
            title = rawPatt.sub('', fname).replace('_', ' ')
        quicklook = self._stitch_images([img.open(p) for p in filePath, \
                                        legendPath])
        quicklook = self._expand_image(quicklook, 0, 30, keep='bl')
        quicklook = self._expand_image(quicklook, 20, 20, keep='middle')
        self._write_text(quicklook, title, position=(quicklook.size[0]/2, 20))
        outPath = rawPatt.sub('', filePath)
        quicklook.save(outPath)
        return outPath

    def _stitch_images(self, ims):
        sizes = np.asarray([i.size for i in ims])
        newRows = np.max(sizes[:,1])
        newCols = np.sum(sizes[:,0])
        final = np.ones((newRows, newCols, 3)) * 255
        accumRIndex = 0
        accumCIndex = 0
        for i in ims:
            arr = np.asarray(i)
            endRow = accumRIndex + arr.shape[0]
            endCol = accumCIndex + arr.shape[1]
            final[accumRIndex: endRow, accumCIndex:endCol] = arr
            accumCIndex = endCol
        return img.fromarray(final.astype(arr.dtype))

    def _expand_image(self, im, width=0, height=0, keep='ul', padValue=255):
        n1 = np.asarray(im)
        oldHeight, oldWidth, bands = n1.shape
        newHeight = oldHeight + height
        newWidth = oldWidth + width
        n2 = np.ones((newHeight, newWidth, bands)) * padValue
        if keep == 'ul':
            n2[:oldHeight, :oldWidth] = n1
        elif keep == 'ur':
            n2[:oldHeight, newWidth-oldWidth:] = n1
        elif keep == 'bl':
            n2[newHeight-oldHeight:, :oldWidth] = n1
        elif keep == 'br':
            n2[newHeight-oldHeight:, newWidth-oldWidth:] = n1
        elif keep == 'middle':
            startHeight = (newHeight - oldHeight) / 2
            endHeight = startHeight + oldHeight
            startWidth = (newWidth - oldWidth) / 2
            endWidth = startWidth + oldWidth
            n2[startHeight:endHeight, startWidth:endWidth] = n1
        newIm = img.fromarray(n2.astype(n1.dtype))
        return newIm

    def _write_text(self, im, txt, fontSize=16, position=(0,0)):
        #font = imgFont.load_default()
        fontFile = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
        font = imgFont.truetype(fontFile, fontSize)
        imgText = img.new('L', font.getsize(txt), 255)
        drawText = imgDraw.Draw(imgText)
        drawText.text((0, 0), txt, font=font, fill=0)
        posX = position[0] - font.getsize(txt)[0] / 2
        posY = position[1] - font.getsize(txt)[1] / 2
        im.paste(imgText, (posX, posY))


class NewNGPMapper(object):

    dataType = gdal.GDT_Int16
    blockXSize = 200
    blockYSize = 200

    def generate_quicklook(self, outputDir, mapfile, filePath, legendPath, 
                           product, host):
        '''
        Generate the quicklook file.

        Inputs:

            outputDir - directory where the quicklook file is to be saved to.

            mapfile - Full path to the mapfile to be used when generating 
                the quicklooks.

            filePath - The file for which the quicklook is to be created.

            legendPath - Path to the legend file.

            product - systemsettings.Product instance with the settings of
                the product that this quicklook shows.

            host - operations.core.g2hosts.G2Host instance.

        Returns:
            
            A list of full paths to the newly created quicklooks.
        '''

        dirPath, fname = os.path.split(filePath)
        minx, miny, maxx, maxy = self.get_bounds(filePath, product.pixelSize)
        if maxx < minx:
            maxx += 360
        rawQuickPath = os.path.join(outputDir, 'rawquicklook_%s.png' % fname)
        command = 'shp2img -m %s -o %s -e %i %i %i %i -s '\
                  '400 400 -l %s' % (mapfile, rawQuickPath, minx, miny, 
                                     maxx, maxy, product.short_name)
        stdout, stderr, retcode = host.run_program(command)
        outPath = self._complete_quicklook(rawQuickPath, legendPath)
        self.remove_temps([rawQuickPath], host)
        return outPath

    def generate_legend(self, mapfile, layers, outputDir, host):
        '''
        Generate a legend png for the input mapfile.

        Inputs:

            mapfile - The path to the mapfile.

            layers - A list of layer names that are to be included in the 
                legend.

            outputDir - The directory where the legend file is to be created.

            host - operations.core.g2hosts.G2Host instance.

        Returns:

            The full path to the newly generated legend file.
        '''

        self._select_mapfile_layers(mapfile, layers)
        legendPath = os.path.join(outputDir, 'legend.png')
        legendCommand = 'legend %s %s' % (mapfile, legendPath)
        mapfileDir = os.path.dirname(mapfile)
        host.run_program(legendCommand, mapfileDir)
        return legendPath

    def get_bounds(self, filePath, pixelSize):
        fileSettings = utilities.get_file_settings(filePath)
        if fileSettings is not None:
            smallTile = fileSettings.fileextrainfo_set.filter(name='smallTile')
            if len(smallTile) == 1:
                # it's a grid tile
                minx, miny, maxx, maxy = self._get_tile_bbox(filePath, 
                                                             fileSettings, 
                                                             pixelSize)
            elif len(smallTile) == 0:
                # it's a continental tile
                areaName = utilities.get_tile_name(filePath)
                ulTile = fileSettings.fileextrainfo_set.get(name='%s_upper_left_tile' % areaName).string
                ulTileFile = filePath.replace(areaName, ulTile)
                ulSettings = utilities.get_file_settings(ulTileFile)
                lrTile = fileSettings.fileextrainfo_set.get(name='%s_lower_right_tile' % areaName).string
                lrTileFile = filePath.replace(areaName, lrTile)
                lrSettings = utilities.get_file_settings(lrTileFile)
                ulBBox = self._get_tile_bbox(ulTileFile, ulSettings, pixelSize)
                lrBBox = self._get_tile_bbox(lrTileFile, lrSettings, pixelSize)
                minx = ulBBox[0]
                miny = lrBBox[1]
                maxx = lrBBox[2]
                maxy = ulBBox[3]
        return minx, miny, maxx, maxy

    def get_h_v(self, fileName):
        hvPatt = re.compile(r'H(\d{2})V(\d{2})')
        reObj = hvPatt.search(fileName)
        if reObj is not None:
            h = int(reObj.group(1))
            v = int(reObj.group(2))
        else:
            h = None
            v = None
        return h, v

    def get_lines_cols(self, filePath):
        fileSettings = utilities.get_file_settings(filePath)
        if fileSettings is not None:
            smallTile = fileSettings.fileextrainfo_set.filter(name='smallTile')
            if len(smallTile) == 1: # grid tile
                rowSize = fileSettings.fileextrainfo_set.get(name='nLines').string
                colSize = fileSettings.fileextrainfo_set.get(name='nCols').string
            elif len(smallTile) == 0: # continental tile
                areaName = utilities.get_tile_name(filePath)
                ulTile = fileSettings.fileextrainfo_set.get(name='%s_upper_left_tile' % areaName).string
                ulTileFile = filePath.replace(areaName, ulTile)
                ulSettings = utilities.get_file_settings(ulTileFile)
                lrTile = fileSettings.fileextrainfo_set.get(name='%s_lower_right_tile' % areaName).string
                lrTileFile = filePath.replace(areaName, lrTile)
                lrSettings = utilities.get_file_settings(lrTileFile)
                ulH, ulV = self.get_h_v(ulTileFile)
                lrH, lrV = self.get_h_v(lrTileFile)
                ulNLines = int(ulSettings.fileextrainfo_set.get(name='nLines').string)
                ulNCols = int(ulSettings.fileextrainfo_set.get(name='nCols').string)
                rowSize = (lrV - ulV + 1) * ulNLines
                colSize = (lrH - ulH + 1) * ulNCols
        return rowSize, colSize

    def remove_temps(self, paths, host):
        host.delete_files(paths)

    def update_latest_mapfile(self, mapfile, shapePath, geotifRelativePath):
        '''
        Update the 'latest' mapfile.

        Inputs:

            mapfile - Full path to the mapfile.

            shapePath - Value to attribute to the mapfile's 'shapepath' 
                variable.

            geotifRelativePath - Relative path to the geotiff. This path 
                is relative to the shapePath argument.
        '''

        
        mapObj = mapscript.mapObj(mapfile)
        mapObj.shapepath = shapePath
        mapWMSMetadata = mapObj.web.metadata
        mapWMSMetadata.set('wms_onlineresource', 
                           'http://%s/cgi-bin/mapserv?map=%s&' \
                            % (self.host.host, mapfile))
        layer = mapObj.getLayerByName(self.product.short_name)
        layer.data = geotifRelativePath
        layerAbstract = '%s product generated for the %s timeslot.' % \
                        (self.product.short_name, 
                         self.timeslot.strftime('%Y-%m-%d %H:%M'))
        layer.metadata.set('wms_abstract', layerAbstract)
        mapObj.save(mapfile)
        return mapfile

    def _get_tile_bbox(self, filePath, fileSettings, pixelSize):
        nLines = int(fileSettings.fileextrainfo_set.get(name='nLines').string)
        nCols = int(fileSettings.fileextrainfo_set.get(name='nCols').string)
        tileXLength = nCols * float(pixelSize)
        tileYLength = nLines * float(pixelSize)
        h, v = self.get_h_v(filePath)
        minx = tileXLength * h - 180
        maxy = -v * tileYLength + 90
        maxx = minx + tileXLength
        miny = maxy - tileYLength
        return minx, miny, maxx, maxy

    def _complete_quicklook(self, file_path, legend_path, title=None, 
                            cleanRaw=True):
        '''
        Create the final quicklook file by incorporating the extra elements.

        Inputs:

            file_path - Full path to the raw quicklook.

            legend_path - Full path to the legend image.

            title - Title for the quicklook.
        '''

        rawPatt = re.compile(r'rawquicklook_')
        if title is None:
            fname = os.path.basename(file_path).rpartition('.')[0]
            title = rawPatt.sub('', fname).replace('_', ' ')
        print('file_path: %s' % file_path)
        print('legend_path: %s' % legend_path)
        quicklook = self._stitch_images([img.open(p) for p in file_path, \
                                        legend_path])
        quicklook = self._expand_image(quicklook, 0, 30, keep='bl')
        quicklook = self._expand_image(quicklook, 20, 20, keep='middle')
        self._write_text(quicklook, title, position=(quicklook.size[0]/2, 20))
        outPath = rawPatt.sub('', file_path)
        quicklook.save(outPath)
        return outPath

    def _stitch_images(self, ims):
        print('locals(): %s' % locals())
        sizes = np.asarray([i.size for i in ims])
        newRows = np.max(sizes[:,1])
        newCols = np.sum(sizes[:,0])
        final = np.ones((newRows, newCols, 3)) * 255
        accumRIndex = 0
        accumCIndex = 0
        for i in ims:
            arr = np.asarray(i)
            print('i: %s' % i)
            print('arr: %s' % arr)
            print('arr.shape: %s' % (arr.shape,))
            endRow = accumRIndex + arr.shape[0]
            endCol = accumCIndex + arr.shape[1]
            final[accumRIndex: endRow, accumCIndex:endCol] = arr
            accumCIndex = endCol
        return img.fromarray(final.astype(arr.dtype))

    def _expand_image(self, im, width=0, height=0, keep='ul', padValue=255):
        n1 = np.asarray(im)
        oldHeight, oldWidth, bands = n1.shape
        newHeight = oldHeight + height
        newWidth = oldWidth + width
        n2 = np.ones((newHeight, newWidth, bands)) * padValue
        if keep == 'ul':
            n2[:oldHeight, :oldWidth] = n1
        elif keep == 'ur':
            n2[:oldHeight, newWidth-oldWidth:] = n1
        elif keep == 'bl':
            n2[newHeight-oldHeight:, :oldWidth] = n1
        elif keep == 'br':
            n2[newHeight-oldHeight:, newWidth-oldWidth:] = n1
        elif keep == 'middle':
            startHeight = (newHeight - oldHeight) / 2
            endHeight = startHeight + oldHeight
            startWidth = (newWidth - oldWidth) / 2
            endWidth = startWidth + oldWidth
            n2[startHeight:endHeight, startWidth:endWidth] = n1
        newIm = img.fromarray(n2.astype(n1.dtype))
        return newIm

    def _select_mapfile_layers(self, mapfile, layers):
        '''
        Turn the selected layers ON and all the others OFF.

        Inputs:

            mapfile - The path to the mapfile.

            layers - A list of layer names that are to be included in the 
                legend.
        '''
            
        mapfileObj = mapscript.mapObj(mapfile)
        for i in range(mapfileObj.numlayers):
            layer = mapfileObj.getLayer(i)
            if layer.name in layers:
                layer.status = mapscript.MS_ON
            else:
                layer.status = mapscript.MS_OFF
        mapfileObj.save(mapfile)

    def _write_text(self, im, txt, fontSize=16, position=(0,0)):
        #font = imgFont.load_default()
        fontFile = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
        font = imgFont.truetype(fontFile, fontSize)
        imgText = img.new('L', font.getsize(txt), 255)
        drawText = imgDraw.Draw(imgText)
        drawText.text((0, 0), txt, font=font, fill=0)
        posX = position[0] - font.getsize(txt)[0] / 2
        posY = position[1] - font.getsize(txt)[1] / 2
        im.paste(imgText, (posX, posY))
