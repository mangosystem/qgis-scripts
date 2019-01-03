# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Raster Fuzzy Membership Function
Description          : Transforms the input raster into a 0 to 1 scale, 
                       indicating the strength of a membership in a set, 
                       based on a specified fuzzification algorithm.
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
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBand,
                       QgsProcessingParameterRasterDestination)
from osgeo import (gdal)
from osgeo.gdalconst import *

import processing
import sys, struct, math


class RasterFuzzyMembershipFunctionAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    BAND = 'BAND'
    SCALE = 'SCALE'
    FUNCTION = 'FUNCTION'
    ISDECREASE = 'ISDECREASE'
    OUTPUT = 'OUTPUT'
    
    FUNCTIONS = ['Linear', 'Jshaped', 'Sigmoidal']
    TYPES ={'Byte':'B','UInt16':'H','Int16':'h','UInt32':'I','Int32':'i','Float32':'f','Float64':'d'}
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return RasterFuzzyMembershipFunctionAlgorithm()
        
    def name(self):
        return 'RasterFuzzyMembershipFunction'.lower()
        
    def displayName(self):
        return self.tr('Raster Fuzzy Membership Function')
        
    def group(self):
        return self.tr('MangoSystem')
        
    def groupId(self):
        return 'mangoscripts'
        
    def shortHelpString(self):
        return self.tr('Transforms the input raster into a 0 to 1 scale, indicating the strength of a membership in a set, based on a specified fuzzification algorithm.')
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT, self.tr('Input Raster Layer')))
        self.addParameter(QgsProcessingParameterBand(self.BAND, self.tr('Band Number'), 1, self.INPUT))
        self.addParameter(QgsProcessingParameterNumber(self.SCALE, self.tr('Degree Of Membership'), defaultValue=100, 
                                                       minValue=0, type=QgsProcessingParameterNumber.Integer, 
                                                       optional=True))
        self.addParameter(QgsProcessingParameterEnum(self.FUNCTION, self.tr('Function Type'), 
                                                     self.FUNCTIONS, defaultValue=0, optional=True))
        self.addParameter(QgsProcessingParameterBoolean(self.ISDECREASE, self.tr('IsDecrease'), 
                                                        defaultValue=True, optional=True))
        
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, self.tr('Output raster')))
        
        
    # =============================================================================
    # min max calculation function
    # =============================================================================
    def calculate_min_max(self, band, feedback):
        feedback.setProgress(0)
        nodata = band.GetNoDataValue()
        minvalue = sys.float_info.max
        maxvalue = sys.float_info.min
        datatype = self.TYPES[gdal.GetDataTypeName(band.DataType)]
        for y in range(band.YSize):
            feedback.setProgress(int(y / float(band.YSize) * 100))
            scanline = band.ReadRaster(0, y, band.XSize, 1, band.XSize, 1, band.DataType)
            values = struct.unpack(datatype * band.XSize, scanline)
            for value in values:
                if value == nodata:
                    continue
                minvalue = min(value, minvalue)
                maxvalue = max(value, maxvalue)
        return minvalue, maxvalue
        
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        band = self.parameterAsInt(parameters, self.BAND, context)
        is_decrease = self.parameterAsBool(parameters, self.ISDECREASE, context)
        function = self.parameterAsEnum(parameters, self.FUNCTION, context)
        feedback.pushInfo('Selected function type is {}'.format(self.FUNCTIONS[function]))
        
        scale = self.parameterAsInt(parameters, self.SCALE, context)
        if scale <= 0:
            scale = 1
            feedback.pushInfo('Degree Of Membership value must be greater than 1! Replaced the default value with 1.')
        
        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        
        inputDs = gdal.Open(unicode(source.source()), GA_ReadOnly)
        inputBand = inputDs.GetRasterBand(band)
        nodata = inputBand.GetNoDataValue()

        # =============================================================================
        # calculate min, max value
        # =============================================================================
        minvalue, maxvalue = self.calculate_min_max(inputBand, feedback)

        # calculate min, max value from qgs interface
        #rasterInterface = source.dataProvider().clone()
        #bandStat = rasterInterface.bandStatistics(1, QgsRasterBandStats.All, source.extent(), 0)
        #minvalue = bandStat.minimumValue
        #maxvalue = bandStat.maximumValue

        # =============================================================================
        # create output raster : always gdal.GDT_Float32
        # =============================================================================
        driver = gdal.GetDriverByName('GTiff')
        outputDs = driver.Create(output_raster, inputDs.RasterXSize, inputDs.RasterYSize, 1, gdal.GDT_Float32)
        outputDs.SetProjection(inputDs.GetProjection())
        outputDs.SetGeoTransform(inputDs.GetGeoTransform())
        outputBand = outputDs.GetRasterBand(1)
        outputBand.SetNoDataValue(nodata)

        # =============================================================================
        # calculate fuzzy membership function
        # =============================================================================
        input_data_type  = self.TYPES[gdal.GetDataTypeName(inputBand.DataType)]
        output_data_type = self.TYPES[gdal.GetDataTypeName(gdal.GDT_Float32)]
        feedback.setProgress(0)
        for y in range(inputBand.YSize):
            if feedback.isCanceled():
                break
            feedback.setProgress(int(y / float(inputBand.YSize) * 100))
            
            scanline = inputBand.ReadRaster(0, y, inputBand.XSize, 1, inputBand.XSize, 1, inputBand.DataType)
            values = struct.unpack(input_data_type * inputBand.XSize, scanline)
            
            output = ''.encode()
            for value in values:
                fuzzy = value
                if value == nodata:
                    fuzzy = nodata
                else:
                    dx = float(value - minvalue)
                    dw = float(maxvalue - minvalue)
                    if dw == 0:
                        fuzzy = 0.0
                    else:
                        if function == 1:   # JSHAPED
                            fuzzy = 1.0 / (1.0 + math.pow((dw - dx) / dw, 2.0))
                        elif function == 2: # SIGMOIDAL
                            fuzzy = math.pow(math.sin((dx / dw) * (math.pi / 2.0)), 2.0)
                        else:                   # LINEAR
                            fuzzy = dx / dw;
                    if is_decrease :
                      fuzzy = 1.0 - fuzzy
                      
                fuzzy = scale * fuzzy
                output = output + struct.pack(output_data_type, fuzzy)
                    
            # write line
            outputBand.WriteRaster(0, y, inputBand.XSize, 1, output, buf_xsize=inputBand.XSize, buf_ysize=1, buf_type=gdal.GDT_Float32)
            del output

        outputDs.FlushCache()
        outputDs = None
        inputDs = None

        return {self.OUTPUT: output_raster}