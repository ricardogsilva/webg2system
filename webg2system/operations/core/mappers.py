#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

import re
import tables
from osgeo import gdal
from osgeo import osr

# FIXME
#   - Mix this file with some of the code used in the lsasaf georeferencer
#   project. That sould allow the rescaling of the values and the geotiff
#   output.


def create_mapper(fileList):
    raise NotImplementedError

class Mapper(object):

    # gdal settings
    #dataType = (gdal.GDT_Int16, 'Int16')
    dataType = (gdal.GDT_Float32, 'Float32')
    blockXSize = 200
    blockYSize = 1

    # maps the name found on the filename with the name of the main dataset 
    # inside the HDF5
    datasets = {
            'DSSF' : 'DSSF',
            'DSLF' : 'DSLF',
            'LST' : 'LST',
            'ALBEDO' : 'ALBEDO',
            'SWI' : 'SWI_01'
            }

    def create_geotiff(self, vrt, outputPath):
        raise NotImplementedError

    def create_mapfile(self, geotif, outputPath):
        raise NotImplementedError

    def create_vrt(self, fileList, outputPath):
        raise NotImplementedError


class SWIMapper(Mapper):

    def create_geotiff(self, vrt, outputPath):
        raise NotImplementedError

    def create_mapfile(self, geotif, outputPath):
        raise NotImplementedError

    def create_vrt(self, fileList, outputPath):
        raise NotImplementedError


class NGPMapper(Mapper): #crappy name

    def create_geotiff(self, vrt, outputPath):
        raise NotImplementedError

    def create_mapfile(self, geotif, outputPath):
        raise NotImplementedError

    def create_vrt(self, fileList, outputPath):
        '''
        Create a VRT file that is the union of all the input files.

        Inputs:

            fileList - A list of fullpaths to the HDF5 files that are to be
                used in the creation of the VRT file.

            outputPath - The full path to where the VRT file is to be put.
        '''

        p = self._get_parameters(fileList)
        xSize = (p['maxH'] - p['minH']) * p['nCols'] + p['nCols']
        ySize = (p['maxV'] - p['minV']) * p['nRows'] + p['nRows']
        zeroXOff = p['minH']
        zeroYOff = p['minV']
        vrtDriver = gdal.GetDriverByName("VRT")
        outDs = vrtDriver.Create(outputPath, xSize, ySize, 1, self.dataType[0])
        outBand = outDs.GetRasterBand(1)
        outDs.SetGeoTransform([p['ullon'], p['gxsize'], 0, 
                              p['ullat'], 0, -p['gysize']])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS("WGS84")
        outDs.SetProjection(srs.ExportToWkt())
        outBand.SetNoDataValue(p['missingValue'])
        for path in fileList:
            h, v = self.get_h_v(path)
            xOff, yOff = self.get_offsets(h, v, zeroXOff, 
                                          zeroYOff, p['nCols'])
            print('h: %s\tv: %s' % (h, v))
            print('xOff: %s\tyOff: %s' % (xOff, yOff))
            xmlSource = self.get_xml_source(path, p['dataset'], p['nCols'], 
                                            p['nRows'], xOff, yOff)
            outBand.SetMetadataItem("teste", xmlSource, "new_vrt_sources")
        outBand.FlushCache()
        outDs.FlushCache()
        self.fix_relativeToVRT(outputPath)

    def get_xml_source(self, fileName, dataset, xSize, ySize, 
                       dXOff, dYOff, sXOff=0, sYOff=0, band=1):
        template = """
        <SimpleSource>
        <SourceFilename relativeToVRT='0'>HDF5:%s://%s</SourceFilename>
        <SourceBand>%i</SourceBand>
        <SourceProperties RasterXSize='%i' RasterYSize='%i' DataType='%s' BlockXSize='%i' BlockYSize='%i' />
        <SrcRect xOff='%i' yOff='%i' xSize='%i' ySize='%i' />
        <DstRect xOff='%i' yOff='%i' xSize='%i' ySize='%i' />
        </SimpleSource>
        """
        return template % (fileName, dataset, band, xSize, ySize, 
                           self.dataType[1], self.blockXSize, self.blockYSize,
                           sXOff, sYOff, xSize, ySize, dXOff, dYOff, 
                           xSize, ySize)

    def fix_relativeToVRT(self, fileName, newValue=0):
        """
        A hack to fix the wrong value of the relativeToVRT attribute that gets
        assigned by GDAL. Hopefully this is not needed when using GDAL >= 1.8
        """

        fh = open(fileName, "r")
        reExpr = re.compile(r'relativeToVRT=.\d.')
        newLines = []
        for line in fh:
            reObj = reExpr.search(line)
            if reObj is not None:
                newLines.append(line[:reObj.start()] + 'relativeToVRT="%i"' % newValue + \
                                line[reObj.end():])
            else:
                newLines.append(line)
        fh.close()
        fh = open(fileName, "w")
        fh.write("\n".join(newLines))
        fh.close()

    def get_offsets(self, h, v, zeroXOff, zeroYOff,
                    nCols, nRows=None):
        if not nRows:
            nRows = nCols 
        xOff = (h - zeroXOff) * nCols
        yOff = (v - zeroYOff) * nRows
        return xOff, yOff

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
    from glob import glob
    mapper = NGPMapper()
    #fileList = glob('/home/ricardo/testData/12/*H[0-9][0-9]V[0-9][0-9]*')
    fileList = glob('/home/ricardo/testData/2010010100/*H[0-9][0-9]V[0-9][0-9]*')
    mapper.create_vrt(fileList, '/home/ricardo/testData/big.vrt')

