# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Polygon To Point
Description          : Polygon To Point
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
                       QgsFeature,
                       QgsFeatureSink,
                       QgsWkbTypes,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSink)
import processing


class PolygonToPointAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    POINTONSURFACE = 'POINTONSURFACE'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return PolygonToPointAlgorithm()
        
    def name(self):
        return 'PolygonToPoint'.lower()
        
    def displayName(self):
        return self.tr('Polygon To Point')
        
    def group(self):
        return self.tr('MangoSystem')
        
    def groupId(self):
        return 'mangoscripts'
        
    def shortHelpString(self):
        return self.tr('Converts polygon feature layer to point features')
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Input Polygon Layer'), [QgsProcessing.TypeVectorPolygon]))
        
        self.addParameter(QgsProcessingParameterBoolean(self.POINTONSURFACE, self.tr('Point on Surface'), False, optional=True))
        
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Points'), QgsProcessing.TypeVectorPoint))
        
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        point_on_surface = self.parameterAsBool(parameters, self.POINTONSURFACE, context)
        
        feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                          source.fields(), QgsWkbTypes.Point, source.sourceCrs())
                          
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
            
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break
                
            geometry = feature.geometry()
            point = geometry.centroid()
            if point_on_surface and not geometry.contains(point):
                point = geometry.pointOnSurface()
                
            if point is None:
                raise QgsProcessingException('Error calculating point')
                
            new_feature = QgsFeature()
            new_feature.setGeometry(point)
            new_feature.setAttributes(feature.attributes())

            # Add a new feature in the sink
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))
            
        return {self.OUTPUT: dest_id}
