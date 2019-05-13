# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Raster Euclidean Distance Analysis
Description          : Calculates, for each cell, the Euclidean distance to the closest source.
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
                       QgsProcessingUtils,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterRasterDestination,
                       QgsVectorFileWriter,
                       QgsProviderRegistry)
from processing.algs.gdal.GdalUtils import GdalUtils
from osgeo import (gdal, ogr, osr)
from osgeo.gdalconst import *

import processing
import math, os, uuid


class RasterEuclideanDistanceAnalysisAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    MAX_DISTANCE = 'MAX_DISTANCE'
    
    EXTENT = 'EXTENT'
    CELL_SIZE = 'CELL_SIZE'
    RASTER_TYPE = 'RASTER_TYPE'
    
    OUTPUT = 'OUTPUT'
    
    RASTER_TYPES = ['Float32', 'Float64', 'Int32']
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return RasterEuclideanDistanceAnalysisAlgorithm()
        
    def name(self):
        return 'RasterEuclideanDistanceAnalysis'.lower()
        
    def displayName(self):
        return self.tr('Raster Euclidean Distance Analysis')
        
    def group(self):
        return self.tr('MangoSystem')
        
    def groupId(self):
        return 'mangoscripts'
        
    def shortHelpString(self):
        return self.tr('Calculates, for each cell, the Euclidean distance to the closest source.')
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, self.tr('Input Vector Layer'), 
                                                           [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterNumber(self.MAX_DISTANCE, self.tr('Maximum Distance'), defaultValue=-1.0, 
                                                       minValue=-1.0, type=QgsProcessingParameterNumber.Double, 
                                                       optional=True))
        
        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, description=self.tr('Extent'), optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.CELL_SIZE, self.tr('Cell Size'), defaultValue=0.0, 
                                                       minValue=0.0, type=QgsProcessingParameterNumber.Double, 
                                                       optional=True))
        self.addParameter(QgsProcessingParameterEnum(self.RASTER_TYPE, self.tr('Raster Type'), 
                                                     self.RASTER_TYPES, 0, optional=True))
        
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, self.tr('Distance raster')))
        
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        max_distance = self.parameterAsDouble(parameters, self.MAX_DISTANCE, context)
        raster_type = self.RASTER_TYPES[self.parameterAsEnum(parameters, self.RASTER_TYPE, context)]
        
        extent = self.parameterAsExtent(parameters, self.EXTENT, context, source.sourceCrs())
        if extent is None or extent.width() == 0 or extent.height() == 0:
            extent = source.sourceExtent()
        
        cell_size = self.parameterAsDouble(parameters, self.CELL_SIZE, context)
        if cell_size <= 0:
            cell_size = int(min(extent.width(), extent.height()) / 250.0)
          
        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        
        # open ogr vector layer from qgs map layer
        ogrLayer, layerName = self.getOgrCompatibleSource(self.INPUT, parameters, context, feedback, True)
        if ogrLayer is None:
            raise QgsProcessingException('Cannot connect OGR driver!')
            
        ogr_vector_datasource = ogr.Open(ogrLayer)
        ogr_vector_layer = ogr_vector_datasource.GetLayer(layerName)
        
        feedback.pushInfo('Raster Type = {0}'.format(raster_type))
        feedback.pushInfo('Cell Size = {0}'.format(cell_size))
        feedback.pushInfo('Extent = {0}'.format(extent))

        nodata = -9999
        srs = osr.SpatialReference()
        srs.ImportFromWkt(source.crs().toWkt())
        transform = [extent.xMinimum(), cell_size, 0.0, extent.yMaximum(), 0.0, -cell_size]
        raster_width = int(math.ceil(abs(extent.xMaximum() - extent.xMinimum()) / cell_size))
        raster_height = int(math.ceil(abs(extent.yMaximum() - extent.yMinimum()) / cell_size))

       # rasterize temporary raterdataset from vector layer, extent, cellsize
        temporary_path = os.path.join(QgsProcessingUtils.tempFolder(), 
                                      'euc_distance_{}.tif'.format(uuid.uuid4().hex))
        feedback.pushInfo('Temporary path = {0}'.format(temporary_path))
        
        driver = gdal.GetDriverByName('GTiff')
        rasterizedDS = driver.Create(temporary_path, raster_width, raster_height, 1, gdal.GDT_Byte)
        rasterizedDS.GetRasterBand(1).SetNoDataValue(nodata)
        rasterizedDS.SetGeoTransform(transform)
        rasterizedDS.SetProjection(srs.ExportToWkt())
        rasterizedDS.GetRasterBand(1).Fill(nodata)
        gdal.RasterizeLayer(rasterizedDS, [1], ogr_vector_layer, burn_values=[1])

        # compute proximity from rasterized dataset
        options = ['DISTUNITS=GEO']
        if max_distance > 0:
          options.append('MAXDIST=' + str(max_distance))

        proximityDs = driver.Create(output_raster, raster_width, raster_height, 1, gdal.GetDataTypeByName(raster_type))
        proximityDs.GetRasterBand(1).SetNoDataValue(nodata)
        proximityDs.SetGeoTransform(transform)
        proximityDs.SetProjection(srs.ExportToWkt())
        proximityDs.GetRasterBand(1).Fill(nodata)
        gdal.ComputeProximity(rasterizedDS.GetRasterBand(1), proximityDs.GetRasterBand(1), options, callback = None)

        # cleanup
        rasterizedDS = None
        proximityDs  = None
        ogr_vector_datasource   = None
            
        return {self.OUTPUT: output_raster}

    # source from GdalAlgorithm.py
    def getOgrCompatibleSource(self, parameter_name, parameters, context, feedback, executing):
        """
        Interprets a parameter as an OGR compatible source and layer name
        :param executing:
        """
        if not executing and parameter_name in parameters and isinstance(parameters[parameter_name], QgsProcessingFeatureSourceDefinition):
            # if not executing, then we throw away all 'selected features only' settings
            # since these have no meaning for command line gdal use, and we don't want to force
            # an export of selected features only to a temporary file just to show the command!
            parameters = {parameter_name: parameters[parameter_name].source}

        input_layer = self.parameterAsVectorLayer(parameters, parameter_name, context)
        ogr_data_path = None
        ogr_layer_name = None
        if input_layer is None or input_layer.dataProvider().name() == 'memory':
            if executing:
                # parameter is not a vector layer - try to convert to a source compatible with OGR
                # and extract selection if required
                ogr_data_path = self.parameterAsCompatibleSourceLayerPath(parameters, parameter_name, context,
                                                                          QgsVectorFileWriter.supportedFormatExtensions(),
                                                                          feedback=feedback)
                ogr_layer_name = GdalUtils.ogrLayerName(ogr_data_path)
            else:
                #not executing - don't waste time converting incompatible sources, just return dummy strings
                #for the command preview (since the source isn't compatible with OGR, it has no meaning anyway and can't
                #be run directly in the command line)
                ogr_data_path = 'path_to_data_file'
                ogr_layer_name = 'layer_name'
        elif input_layer.dataProvider().name() == 'ogr':
            if executing:
                # parameter is a vector layer, with OGR data provider
                # so extract selection if required
                ogr_data_path = self.parameterAsCompatibleSourceLayerPath(parameters, parameter_name, context,
                                                                          QgsVectorFileWriter.supportedFormatExtensions(),
                                                                          feedback=feedback)
                parts = QgsProviderRegistry.instance().decodeUri('ogr', ogr_data_path)
                ogr_data_path = parts['path']
                if 'layerName' in parts and parts['layerName']:
                    ogr_layer_name = parts['layerName']
                else:
                    ogr_layer_name = GdalUtils.ogrLayerName(ogr_data_path)
            else:
                #not executing - don't worry about 'selected features only' handling. It has no meaning
                #for the command line preview since it has no meaning outside of a QGIS session!
                ogr_data_path = GdalUtils.ogrConnectionStringAndFormatFromLayer(input_layer)[0]
                ogr_layer_name = GdalUtils.ogrLayerName(input_layer.dataProvider().dataSourceUri())
        else:
            # vector layer, but not OGR - get OGR compatible path
            # TODO - handle "selected features only" mode!!
            ogr_data_path = GdalUtils.ogrConnectionStringFromLayer(input_layer)
            ogr_layer_name = GdalUtils.ogrLayerName(input_layer.dataProvider().dataSourceUri())
        return ogr_data_path, ogr_layer_name
