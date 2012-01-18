#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

import re
import os
import logging
from subprocess import Popen, PIPE

from osgeo import gdal
from osgeo import osr

# FIXME
#   - Mix this file with some of the code used in the lsasaf georeferencer
#   project. That sould allow the rescaling of the values and the geotiff
#   output.

class Mapper(object):

    # gdal settings
    dataType = (gdal.GDT_Float32, 'Float32')
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

    def create_mapfile(self, geotif, outputPath):
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
        tempTif = self.merge_tiles(tilePaths, missingValue, 'temp_nodata.tif',
                                   outDir)
        globalTiff = self._fix_nodata(tempTif, outName, missingValue)
        ovrFile = self.build_overviews(globalTiff, 6)
        temps = tilePaths + [tempTif]
        self.remove_temps(temps)

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
                                     1, self.dataType[0])
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

    def create_mapfile(self, geotif, outputPath):
        raise NotImplementedError

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


if __name__ == '__main__':
    import sys
    outName = sys.argv[1]
    fileList = sys.argv[2:]
    mapper = NGPMapper()
    mapper.create_global_tiff(fileList, '.', outName)
