# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Raster Extract by Attributes
Description          : Raster Extract by Attributes
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

from PyQt5.QtCore import (QCoreApplication, 
                          QVariant)
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsFeature,
                       QgsFields,
                       QgsField,
                       QgsExpression,
                       QgsExpressionContext,
                       QgsExpressionContextScope,
                       QgsProcessingParameterString,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBand,
                       QgsProcessingParameterRasterDestination)
from osgeo import (gdal)
from osgeo.gdalconst import *

import processing
import sys, struct, math


class RasterExtractByAttributesAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    BAND = 'BAND'
    EXPRESSION = 'EXPRESSION'
    OUTPUT = 'OUTPUT'
    
    RASTER_TYPES ={'Byte':'B','UInt16':'H','Int16':'h','UInt32':'I','Int32':'i','Float32':'f','Float64':'d'}
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return RasterExtractByAttributesAlgorithm()
        
    def name(self):
        return 'RasterExtractByAttributes'.lower()
        
    def displayName(self):
        return self.tr('Raster Extract by Attributes')
        
    def group(self):
        return self.tr('MangoSystem')
        
    def groupId(self):
        return 'mangoscripts'
        
    def shortHelpString(self):
        return self.tr('Raster Extract by Attributes.')
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT, self.tr('Input Raster Layer')))
        self.addParameter(QgsProcessingParameterBand(self.BAND, self.tr('Band Number'), 1, self.INPUT))
        self.addParameter(QgsProcessingParameterString(self.EXPRESSION, self.tr('Expression'), 
                                                    defaultValue='value > 0', multiLine=True))
        
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, self.tr('Output raster')))
        
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        band = self.parameterAsInt(parameters, self.BAND, context)
        expression = self.parameterAsString(parameters, self.EXPRESSION, context).replace('\n', '')
        feedback.pushInfo('Expression = {}'.format(expression))
        if len(expression.strip()) == 0:
            raise QgsProcessingException('Expression values required!')
        
        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        
        # create raster dataset
        inputDs = gdal.Open(unicode(source.source()), GA_ReadOnly)
        inputBand = inputDs.GetRasterBand(band)
        dataType = inputBand.DataType;
        nodata = int(inputBand.GetNoDataValue()) if dataType < 6 else inputBand.GetNoDataValue()
        
        feedback.pushInfo('NoData Value = {0}'.format(nodata))
        feedback.pushInfo('DataType = {0}'.format(dataType))
        feedback.pushInfo('DataType = {0}'.format(self.RASTER_TYPES[gdal.GetDataTypeName(dataType)]))

        driver = gdal.GetDriverByName('GTiff')
        outputDs = driver.Create(output_raster, inputDs.RasterXSize, inputDs.RasterYSize, 1, dataType)
        outputDs.SetProjection(inputDs.GetProjection())
        outputDs.SetGeoTransform(inputDs.GetGeoTransform())
        outputBand = outputDs.GetRasterBand(1)
        outputBand.SetNoDataValue(nodata)

        # prepare feature for expression
        fields = QgsFields()
        fields.append(QgsField('value', QVariant.Double))
        fields.append(QgsField(source.name(), QVariant.Double))

        exp = QgsExpression(expression)
        context = QgsExpressionContext()
        scope = QgsExpressionContextScope()
        context.appendScope(scope)

        feature = QgsFeature(fields)

        # extrace by attributes
        data_type  = self.RASTER_TYPES[gdal.GetDataTypeName(dataType)]
        for y in range(inputBand.YSize):
            if feedback.isCanceled():
                break
            feedback.setProgress(int(y / float(inputBand.YSize) * 100))
            
            scanline = inputBand.ReadRaster(0, y, inputBand.XSize, 1, inputBand.XSize, 1, dataType)
            values = struct.unpack(data_type * inputBand.XSize, scanline)
            
            output = ''.encode()
            for value in values:
                raster_value = nodata
                if value != nodata:
                    feature.setAttribute(0, value)
                    feature.setAttribute(1, value)
                    scope.setFeature(feature)
                    if bool(exp.evaluate(context)):
                      raster_value = value
                    else:
                      raster_value = nodata
                output = output + struct.pack(data_type, raster_value)
                    
            # write line
            outputBand.WriteRaster(0, y, inputBand.XSize, 1, output, buf_xsize=inputBand.XSize, buf_ysize=1, buf_type=dataType)
            del output

        outputDs.FlushCache()
        outputDs = None
        inputDs = None

        return {self.OUTPUT: output_raster}