# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Raster Reclassification
Description          : Reclassifies the values in a raster.
Date                 : 28/Dec/2018
copyright            : (C) 2015 by Minpa Lee
email                : mapplus@gmail.com
reference:
***************************************************************************/

***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBand,
                       QgsProcessingParameterRasterDestination)
from processing.algs.gdal.GdalUtils import GdalUtils
from osgeo import (gdal)
from osgeo.gdalconst import *

import processing
import sys, struct, math


class RasterReclassificationAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    BAND = 'BAND'
    RANGES = 'RANGES'
    
    OUTPUT_TYPE = 'OUTPUT_TYPE'
    OUTPUT = 'OUTPUT'
    
    OUTPUT_TYPES = ['Int32','Float32']
    RASTER_TYPES ={'Byte':'B','UInt16':'H','Int16':'h','UInt32':'I','Int32':'i','Float32':'f','Float64':'d'}
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return RasterReclassificationAlgorithm()
        
    def name(self):
        return 'RasterReclassification'.lower()
        
    def displayName(self):
        return self.tr('Raster Reclassification')
        
    def group(self):
        return self.tr('MangoSystem')
        
    def groupId(self):
        return 'mangoscripts'
        
    def shortHelpString(self):
        return self.tr('Reclassifies the values in a raster.')
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT, self.tr('Input Raster Layer')))
        self.addParameter(QgsProcessingParameterBand(self.BAND, self.tr('Band Number'), 1, self.INPUT))
        
        self.addParameter(QgsProcessingParameterString(self.RANGES, self.tr('Reclassify Ranges'), 
                                                    defaultValue='0 10 1; 10 20 2; 20 100 3', multiLine=False))
        self.addParameter(QgsProcessingParameterEnum(self.OUTPUT_TYPE, self.tr('Output Raster Type'), 
                                                     self.OUTPUT_TYPES, 0, optional=True))
        
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, self.tr('reclassified')))
        
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        band = self.parameterAsInt(parameters, self.BAND, context)
        ranges = self.parameterAsString(parameters, self.RANGES, context).replace('\n', '')
        raster_type = self.OUTPUT_TYPES[self.parameterAsEnum(parameters, self.OUTPUT_TYPE, context)]
        
        feedback.pushInfo('Ranges are {}'.format(ranges))
        if len(ranges.strip()) == 0:
            raise QgsProcessingException('Reclassify Ranges values required!')
        
        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        
        # check ranges
        min_values = []
        max_values = []
        reclass_values  = []
        for reclass in ranges.strip().split(';'):
            reclass_intervals = reclass.strip().split()
            min_values.append(float(reclass_intervals[0]))
            max_values.append(float(reclass_intervals[1]))
            reclass_values.append(float(reclass_intervals[2]))
        
        # create output raster dataset
        inputDs = gdal.Open(unicode(source.source()), GA_ReadOnly)
        inputBand = inputDs.GetRasterBand(band)
        if inputBand is None:
            raise QgsProcessingException('Cannot open raster band {}'.format(band))
        
        nodata = -9999
        gdal_output_type = gdal.GetDataTypeByName(raster_type)

        driver = gdal.GetDriverByName('GTiff')
        outputDs = driver.Create(output_raster, inputDs.RasterXSize, inputDs.RasterYSize, 1, gdal_output_type)
        outputDs.SetProjection(inputDs.GetProjection())
        outputDs.SetGeoTransform(inputDs.GetGeoTransform())
        outputBand = outputDs.GetRasterBand(1)
        outputBand.SetNoDataValue(nodata)
        
        # reclassify raster
        input_data_type  = self.RASTER_TYPES[gdal.GetDataTypeName(inputBand.DataType)]
        output_data_type = self.RASTER_TYPES[raster_type]
        for y in range(inputBand.YSize):
            if feedback.isCanceled():
                break
            feedback.setProgress(int(y / float(inputBand.YSize) * 100))
            
            scanline = inputBand.ReadRaster(0, y, inputBand.XSize, 1, inputBand.XSize, 1, inputBand.DataType)
            values = struct.unpack(input_data_type * inputBand.XSize, scanline)
            
            output = ''.encode()
            for value in values:
                reclassValue = nodata
                if value == nodata:
                    reclassValue = nodata
                else:
                    for index in range(len(reclass_values)):
                        if value >= min_values[index] and value < max_values[index]:
                            reclassValue = reclass_values[index]
                            break
                        
                reclassValue = int(reclassValue) if raster_type == 'Int32' else float(reclassValue)
                output = output + struct.pack(output_data_type, reclassValue)
                    
            # write line
            outputBand.WriteRaster(0, y, inputBand.XSize, 1, output, buf_xsize=inputBand.XSize, buf_ysize=1, buf_type=gdal_output_type)
            del output

        outputDs.FlushCache()
        outputDs = None
        inputDs = None

        return {self.OUTPUT: output_raster}