# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : WKT to Vector Layer
Description          : WKT to Vector Layer
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
from qgis.utils import (iface)
from qgis.core import (QgsProcessing,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsGeometry,
                       QgsPoint,
                       QgsWkbTypes,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSink)
import processing


class WKTToVectorAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return WKTToVectorAlgorithm()
        
    def name(self):
        return 'WKTToVector'.lower()
        
    def displayName(self):
        return self.tr('WKT to Vector Layer')
        
    def group(self):
        return self.tr('MangoSystem')
        
    def groupId(self):
        return 'mangoscripts'
        
    def shortHelpString(self):
        return self.tr('Converts WKT(Well Known Text) text to features')
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString(self.INPUT, self.tr('WKT Geometry'), multiLine=True))
        
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Output'), QgsProcessing.TypeVector))
        
    def processAlgorithm(self, parameters, context, feedback):
        WKT = self.parameterAsString(parameters, self.INPUT, context).replace('\n', '')
        
        # import from WKT geometry
        try:
            geometry = QgsGeometry.fromWkt(WKT)
        except Exception as detail:
            raise QgsProcessingException('Invalid WKT Geometry: %s' % detail)
        
        # get CRS
        crs = iface.mapCanvas().mapSettings().destinationCrs()
        
        # create vector layer
        fields = QgsFields()
        fields.append(QgsField('id', QVariant.Int))
        fields.append(QgsField('type', QVariant.String))

        feedback.pushInfo('CRS is {}'.format(crs.authid()))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                          fields, geometry.wkbType(), crs)
                          
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
            
        # create new feature
        new_feature = QgsFeature(fields)
        new_feature.setGeometry(geometry)
        new_feature.setAttribute('id', 1)
        new_feature.setAttribute('type', geometry.wkbType())
        
        # Add a new feature in the sink
        sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
        
        return {self.OUTPUT: dest_id}
