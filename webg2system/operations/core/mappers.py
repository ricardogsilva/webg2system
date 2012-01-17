#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

import re
import os
import tables
from osgeo import gdal
from osgeo import osr
from subprocess import Popen, PIPE

# FIXME
#   - Mix this file with some of the code used in the lsasaf georeferencer
#   project. That sould allow the rescaling of the values and the geotiff
#   output.

class Mapper(object):

    # gdal settings
    dataType = (gdal.GDT_Float32, 'Float32')
    blockXSize = 200
    blockYSize = 200

    # maps the name found on the filename with the name of the main dataset 
    # inside the HDF5
    datasets = {
            'DSSF' : 'DSSF',
            'DSLF' : 'DSLF',
            'LST' : 'LST',
            'ALBEDO' : 'ALBEDO',
            'SWI' : 'SWI_01'
            }

    def create_global_product(self, fmt, fileList, outDir, outName, host):
        raise NotImplementedError

    def create_global_tiff(self, fileList, outDir, outName):
        raise NotImplementedError

    def create_mapfile(self, geotif, outputPath):
        raise NotImplementedError


class SWIMapper(Mapper):

    def create_global_tiff(self, fileList, outDir, outName):
        raise NotImplementedError

    def create_mapfile(self, geotif, outputPath):
        raise NotImplementedError


class NGPMapper(Mapper): #crappy name

    def create_global_tiff(self, fileList, outDir, outName):
        params = self._get_parameters(fileList)
        tilePaths = self.create_geotiffs(fileList, outDir, params)
        tempTif = self.merge_tiles(tilePaths, params['missingValue'], 
                                      'temp_nodata.tif', outDir)
        globalTiff = self._fix_nodata(tempTif, outName, params['missingValue'])
        ovrFile = self.build_overviews(globalTiff, 6)
        temps = tilePaths + [tempTif]
        self.remove_temps(temps)

    def remove_temps(self, paths):
        for path in paths:
            os.remove(path)

    def create_geotiffs(self, fileList, outputDir, params=None):
        tiles = []
        if params is None:
            params = self._get_parameters(fileList)
        for path in fileList:
            tiles.append(self._create_tile_geotiff(path, outputDir, params))
        return tiles

    def _create_tile_geotiff(self, filepath, outputDir, params, tolerance=0.1):
        '''
        Creates a geotiff for an input G2tile HDF5 file.
        '''

        fileName = os.path.basename(filepath) + '.tif'
        outputPath = os.path.join(outputDir, fileName)
        outDriver = gdal.GetDriverByName('GTiff')
        inDs = gdal.Open('HDF5:"%s"://%s' % (filepath, params['dataset']))
        la = inDs.GetRasterBand(1).ReadAsArray()
        mv = params['missingValue']
        # dealing with the missing value and scaling factor
        la[abs(la - mv) > tolerance] = la[abs(la - mv) > tolerance] / params['scalingFactor']
        la[abs(la - mv) <= tolerance] = mv
        outDs = outDriver.Create(str(outputPath), params['nCols'], 
                                 params['nRows'], 1, self.dataType[0])
        outBand = outDs.GetRasterBand(1)
        outBand.WriteArray(la, 0, 0)
        h, v = self.get_h_v(filepath)
        firstLon, firstLat = self.get_first_coords(h, v)
        ullon = firstLon * 1.0 - 0.05 / 2.0
        ullat = firstLat * 1.0 + 0.05 / 2.0
        outDs.SetGeoTransform([ullon, 0.05, 0, ullat, 0, -0.05])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS("WGS84")
        outDs.SetProjection(srs.ExportToWkt())
        outBand.SetNoDataValue(params['missingValue'])
        outBand.FlushCache()
        inDs = None
        outDs = None
        return outputPath

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

    def get_first_coords(self, h, v, tileLength=10):
        '''
        Infer the firstLat and firstLon attribute from files tiled according
        to the Geoland-2 grid without having to open them.
        '''
        firstLon = -180 + tileLength * h
        firstLat = 90 - tileLength * v
        return firstLon, firstLat

    def get_dataset_name(self, filePath):
        dataset = None
        for fName in self.datasets.keys():
            if re.search(fName, filePath) is not None:
                dataset = self.datasets.get(fName)
                break
        return dataset

    def _get_parameters(self, fileList):
        '''
        Open the relevant tiles and extract parameters for VRT creation.
        '''

        minH, maxH, minV, maxV = self._get_extreme_tile_numbers(fileList)
        minHFile = [i for i in fileList if self.get_h_v(i)[0] == minH][0]
        minVFile = [i for i in fileList if self.get_h_v(i)[1] == minV][0]
        latDS = tables.openFile(minVFile)
        nRows = int(latDS.root._v_attrs.NL) # verify the name of this attribute
        nCols = int(latDS.root._v_attrs.NC) # verify the name of this attribute
        pixelPatt = re.compile(r'\d+\.\d+')
        pixSize = latDS.root._v_attrs["PIXEL_SIZE"]
        gxsize, gysize = [float(n) for n in pixelPatt.findall(pixSize)]
        ullat = latDS.root._v_attrs.FIRST_LAT * 1.0 + gysize / 2.0
        dataset = self.get_dataset_name(minVFile)
        scalingFactor = eval("latDS.root.%s.getAttr('SCALING_FACTOR')" % dataset)
        #missingValue = int(eval("latDS.root.%s.getAttr('MISSING_VALUE')" % dataset)) / scalingFactor # why the division?
        missingValue = int(eval("latDS.root.%s.getAttr('MISSING_VALUE')" % dataset))
        latDS.close()
        lonDS = tables.openFile(minHFile)
        ullon = lonDS.root._v_attrs.FIRST_LON * 1.0 - gxsize / 2.0
        lonDS.close()
        params = {
                'minH' : minH, 'maxH' : maxH, 'minV' : minV, 'maxV' : maxV,
                'nRows' : nRows, 'nCols' : nCols, 
                'gxsize' : gxsize, 'gysize' : gysize,
                'ullat' : ullat, 'ullon' : ullon,
                'scalingFactor' : scalingFactor,
                'missingValue' : missingValue,
                'dataset' : dataset
                }
        return params

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
        return h, v

if __name__ == '__main__':
    import sys
    outName = sys.argv[1]
    fileList = sys.argv[2:]
    mapper = NGPMapper()
    mapper.create_global_tiff(fileList, '.', outName)
