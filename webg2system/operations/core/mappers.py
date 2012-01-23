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
import Image as img
import ImageFont as imgFont
import ImageDraw as imgDraw

from osgeo import gdal
from osgeo import osr
import mapscript

# FIXME
#   - Mix this file with some of the code used in the lsasaf georeferencer
#   project. That sould allow the rescaling of the values and the geotiff
#   output.

class Mapper(object):

    # gdal settings
    #dataType = (gdal.GDT_Float32, 'Float32')
    dataType = gdal.GDT_Int16
    blockXSize = 200
    blockYSize = 200

    def __init__(self, g2File):
        '''
        Inputs:

            g2File - A operations.core.g2files.G2File object.
        '''

        self.logger = logging.getLogger(
                '.'.join((__name__, self.__class__.__name__)))
        self.nLines = int(g2File.extraSettings.get(name='nLines').string)
        self.nCols = int(g2File.extraSettings.get(name='nCols').string)
        self.product = g2File.productSettings
        self.host = g2File.host

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
        missingValue = int(ds.missingValue)
        scalingFactor = int(ds.scalingFactor)
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
            os.remove(path)

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
            self.logger.debug('(%i/%i) - Converting HDF5 to GeoTiff...' % (fNum+1, len(fileList)))
            fileName = os.path.basename(path) + '.tif'
            outputPath = os.path.join(outputDir, fileName)
            outDriver = gdal.GetDriverByName('GTiff')
            inDs = gdal.Open('HDF5:"%s"://%s' % (path, dataset.name))
            la = inDs.GetRasterBand(1).ReadAsArray()
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

    def create_mapfile(self, geotifPath, outputPath, template):
        '''
        Create a new mapfile for UMN Mapserver based on the template.

        Inputs:

            geotifPath - The full path to the geotif that is to be served
                by the mapfile.

            outputPath - The full path of the new mapfile.

            template - The full path to the template mapfile to use.
        '''

        dataPath, tifName = os.path.split(geotifPath)
        templateMap = mapscript.mapObj(template)
        mapfile = templateMap.clone()
        mapfile.shapepath = dataPath
        mapfile.name = 'quicklooks'
        mapWMSMetadata = mapfile.web.metadata
        mapWMSMetadata.set('wms_title', 'quicklooks')
        mapWMSMetadata.set('wms_onlineresource', 
                        'http://%s/cgi-bin/mapserv?map=%s&' \
                        % (self.host.host, outputPath))
        layer = mapfile.getLayerByName(self.product.shortName)
        layer.data = tifName
        layer.status = mapscript.MS_ON
        layerWMSMetadata = layer.metadata
        layerWMSMetadata.set('wms_title', self.product.shortName)
        mapfile.save(outputPath)
        return outputPath

    def generate_quicklooks(self, outputPath, mapfile, fileList):
        '''
        Generate the quicklook files.

        Inputs:

            mapfile - Full path to the mapfile to be used when generating 
                the quicklooks.

            fileList - A list of paths with the files to create quicklooks
                to.

        Returns:
            
            A list of full paths to the newly created quicklooks.
        '''

        quickLooks = []
        tileXLength = self.nCols * float(self.product.pixelSize)
        tileYLength = self.nLines * float(self.product.pixelSize)
        legendPath = os.path.join(outputPath, 'legend.png')
        legendCommand = 'legend %s %s' % (mapfile, legendPath)
        mapfileDir = os.path.dirname(mapfile)
        self.host.run_program(legendCommand, mapfileDir)
        for fNum, path in enumerate(fileList):
            self.logger.debug('(%i/%i) - Creating quicklook...' % 
                              (fNum+1, len(fileList)))
            dirPath, fname = os.path.split(path)
            firstLat, firstLon = self._get_corner_coordinates(path, 
                                                              tileXLength, 
                                                              tileYLength)
            minx = firstLon
            miny = firstLat + tileYLength
            maxx = firstLon + tileXLength
            maxy = firstLat
            rawQuickPath = os.path.join(outputPath, 'rawquicklook_%s.png' % fname)
            command = 'shp2img -m %s -o %s -e %i %i %i %i -s '\
                      '400 400 -l %s' % (mapfile, rawQuickPath, minx, miny, 
                                         maxx, maxy, self.product.shortName)
            self.host.run_program(command)
            outPath = self._complete_quicklook(rawQuickPath, legendPath)
            quickLooks.append(outPath)
            self.remove_temps([rawQuickPath])
        self.remove_temps([legendPath])
        return quickLooks

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

if __name__ == '__main__':
    import sys
    outName = sys.argv[1]
    fileList = sys.argv[2:]
    mapper = NGPMapper()
    mapper.create_global_tiff(fileList, '.', outName)
