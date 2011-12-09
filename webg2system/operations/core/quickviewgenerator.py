#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
Script's doctring goes here.
"""

import sys
import os
import logging
import tables
from osgeo import gdal
from osgeo import osr

class HDF5TileQuickviewGenerator(object):

    def __init__(self, filePath):
        self.logger = logging.getLogger()
        ds = tables.openFile(filePath)
        self.filePath = filePath
        self.ullat = ds.root._v_attrs.FIRST_LAT * 1.0 + 0.05 / 2.
        self.ullon = ds.root._v_attrs.FIRST_LON * 1.0 - 0.05 / 2.
        self.datasetName= ds.root._f_getChild(ds.root._v_attrs[\
                              "PRODUCT"]).name
        self.logger.debug("self.datasetName: %s" % self.datasetName)
        npArray = eval("ds.root.%s.read()" % self.datasetName)
        self.scalingFactor = eval("ds.root.%s.getAttr('SCALING_FACTOR')" % self.datasetName)
        self.missingValue = int(eval("ds.root.%s.getAttr('MISSING_VALUE')" % self.datasetName)) / self.scalingFactor
        self.minimum = npArray.min() / self.scalingFactor
        self.maximum = npArray.max() / self.scalingFactor
        ds.close()

    def create_quickview(self, fileFormat="GTiff", outputName=None,
                         outputDir=None):
        """
        Inputs:
            fileFormat - A string specifying the name of the output format.
                         It must conform to the GDAL code names, as available
                         on http://gdal.org/formats_list.html
        """

        self.logger.debug("create_quickview method called.")
        outDriver = gdal.GetDriverByName(fileFormat)
        inDs = gdal.Open('HDF5:"%s"://%s' % (self.filePath, self.datasetName),
                         gdal.GA_ReadOnly)
        cols = inDs.RasterXSize
        rows = inDs.RasterYSize
        originalLayer = inDs.GetRasterBand(1).ReadAsArray()
        layer = originalLayer / self.scalingFactor
        if outputName is None:
            outputName = "%s.tif" % os.path.basename(self.filePath).rsplit(".")[0]
        if outputDir is None:
            outputDir = os.path.dirname(self.filePath)
        outputPath = os.path.join(outputDir, outputName)
        outDs = outDriver.Create(outputPath, cols, 
                                 rows, 1, gdal.GDT_Float32)
        outBand = outDs.GetRasterBand(1)
        outBand.WriteArray(layer, 0, 0)
        outDs.SetGeoTransform([self.ullon, 0.05, 0, self.ullat, 0, -0.05])
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS("WGS84")
        outDs.SetProjection(srs.ExportToWkt())
        outBand.SetNoDataValue(self.missingValue)
        outBand.FlushCache()
        inDs = None
        outDs = None
        self.logger.debug("create_quickview method exiting.")
        return outputPath

    def __repr__(self):
        return "%s(filePath=%r)" % (self.__class__.__name__, self.filePath)


def main(argList):
    pass

if __name__ == "__main__":
    main(sys.argv[1:])

