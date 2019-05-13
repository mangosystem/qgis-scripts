# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Multiple Ring Buffer
Description          : Creates multiple buffers at specified distances
                       around the input features.
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
                       QgsFeature,
                       QgsFeatureSink,
                       QgsField,
                       QgsWkbTypes,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSink)
import processing


class MultipleRingBufferAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    DISTANCES = 'DISTANCES'
    OUTSIDE = 'OUTSIDE'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MultipleRingBufferAlgorithm()

    def name(self):
        return 'MultipleRingBuffer'.lower()

    def displayName(self):
        return self.tr('Multiple Ring Buffer')

    def group(self):
        return self.tr('MangoSystem')

    def groupId(self):
        return 'mangoscripts'

    def shortHelpString(self):
        return self.tr('Creates multiple buffers at specified distances around the input features.')

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Input Vector Layer'), [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterString(self.DISTANCES, self.tr('Comma Seperated Distance Values'),
                                                    defaultValue='500, 1000, 1500', multiLine=False))
        self.addParameter(QgsProcessingParameterBoolean(self.OUTSIDE, self.tr('Outside Polygons Only'), True, optional=True))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Buffered'), QgsProcessing.TypeVectorPolygon))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        distances = self.parameterAsString(parameters, self.DISTANCES, context)
        distance_values = distances.strip().split(',')
        if len(distance_values) == 0:
            raise QgsProcessingException('Comma seperated ditance values required!')

        outside_only = self.parameterAsBool(parameters, self.OUTSIDE, context)

        feedback.pushInfo('Distances is {}'.format(distances))

        output_fields = source.fields()
        output_fields.append(QgsField('rind_dist', QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                          output_fields, QgsWkbTypes.Polygon, source.sourceCrs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            geometry = feature.geometry()
            buffered = []
            for index in range(len(distance_values)):
                rind_distance = float(distance_values[index])
                buffered.append(geometry.buffer(rind_distance, 24)) #quadrant segments

                new_feature = QgsFeature()
                if outside_only == True and index > 0:
                    new_feature.setGeometry(buffered[index].difference(buffered[index-1]))
                else:
                    new_feature.setGeometry(buffered[index])

                new_attributes = feature.attributes()
                new_attributes.append(rind_distance) # ring distance
                new_feature.setAttributes(new_attributes)

                # Add a new feature in the sink
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            del buffered

            # Update the progress bar
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}
