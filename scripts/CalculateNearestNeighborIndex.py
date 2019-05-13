# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Calculate Nearest Neighbor Index
Description          : Calculate Nearest Neighbor Index
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
                       QgsFeatureRequest,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)
import processing
import sys, math


class NearestNeighborIndexAlgorithm(QgsProcessingAlgorithm):
    POLYGON = 'POLYGON'
    POINT = 'POINT'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return NearestNeighborIndexAlgorithm()
        
    def name(self):
        return 'NearestNeighborIndex'.lower()
        
    def displayName(self):
        return self.tr('Nearest Neighbor Index')
        
    def group(self):
        return self.tr('MangoSystem')
        
    def groupId(self):
        return 'mangoscripts'
        
    def shortHelpString(self):
        return self.tr('Calculates Nearest Neighbor Index(NNI)')
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.POLYGON, self.tr('Polygon Layer'), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINT, self.tr('Point Layer'), [QgsProcessing.TypeVectorPoint]))
        
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Output NNI'), QgsProcessing.TypeVectorPolygon))
        
    # =============================================================================
    # get minimum distance from point features
    # =============================================================================
    def get_minimum_distance(self, point_features, source):
        min_distance = sys.float_info.max
        for dest in point_features:
            if source.id() == dest.id():
                continue
            min_distance = min(min_distance, source.geometry().distance(dest.geometry()))
            if min_distance == 0:
                return min_distance
        return min_distance
        
    def processAlgorithm(self, parameters, context, feedback):
        polygon_layer = self.parameterAsSource(parameters, self.POLYGON, context)
        if polygon_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.POLYGON))
            
        point_layer = self.parameterAsSource(parameters, self.POINT, context)
        if point_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.POINT))
            
        output_fields = polygon_layer.fields()
        output_fields.append(QgsField('point_cnt', QVariant.Int))
        output_fields.append(QgsField('area', QVariant.Double))
        output_fields.append(QgsField('obsavgdist', QVariant.Double))
        output_fields.append(QgsField('expavgdist', QVariant.Double))
        output_fields.append(QgsField('nni', QVariant.Double))
        output_fields.append(QgsField('zscore', QVariant.Double))
        output_fields.append(QgsField('stderr', QVariant.Double))
            
        feedback.pushInfo('CRS is {}'.format(polygon_layer.sourceCrs().authid()))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                          output_fields, polygon_layer.wkbType(), polygon_layer.sourceCrs())
                          
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
            
        total = 100.0 / polygon_layer.featureCount() if polygon_layer.featureCount() else 0
        features = polygon_layer.getFeatures()

        for current, polygon_feature in enumerate(features):
            if feedback.isCanceled():
                break
                
            polygon_geom = polygon_feature.geometry()
            
            # search intersected point features
            intersects_points = []
            request = QgsFeatureRequest().setFilterRect(polygon_geom.boundingBox())
            point_features = point_layer.getFeatures(request)
            for point_feature in point_features:
                if polygon_geom.intersects(point_feature.geometry()):
                    intersects_points.append(point_feature)
            
            # calculate nearest distance & nearest neighbor index
            sum_nearest_dist = 0.0;
            for point_feature in intersects_points:
                min_distance = self.get_minimum_distance(intersects_points, point_feature)
                sum_nearest_dist += min_distance;
                
            area = polygon_geom.area()
            N = len(intersects_points)
            if N < 3:
                observed_mean_dist = None;
                expected_mean_dist = None;
                nearest_neighbor_index = None;
                standard_error = None;
                z_score = None;
            else:
                observed_mean_dist = sum_nearest_dist / float(N);
                expected_mean_dist = 0.5 * math.sqrt(area / float(N));
                nearest_neighbor_index = observed_mean_dist / expected_mean_dist;
                standard_error = math.sqrt(((4.0 - math.pi) * area) / (4.0 * math.pi * N * N));
                z_score = (observed_mean_dist - expected_mean_dist) / standard_error;
            del intersects_points
                
            # create feature
            new_feature = QgsFeature(output_fields)
            new_feature.setGeometry(polygon_geom)
            for idx, val in enumerate(polygon_feature.attributes()):
                new_feature.setAttribute(idx, val)
            
            # set attributes
            new_feature.setAttribute('point_cnt', N)
            new_feature.setAttribute('area', area)
            new_feature.setAttribute('obsavgdist', observed_mean_dist)
            new_feature.setAttribute('expavgdist', expected_mean_dist)
            new_feature.setAttribute('nni', nearest_neighbor_index)
            new_feature.setAttribute('zscore', z_score)
            new_feature.setAttribute('stderr', standard_error)

            # Add a new feature in the sink
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))
            
        return {self.OUTPUT: dest_id}
