# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Create Ring Maps
Description          : Create Ring Maps
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
                       QgsGeometry,
                       QgsPointXY,
                       QgsRectangle,
                       QgsWkbTypes,
                       QgsSpatialIndex,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSink)
import processing
import math


class CreateRingMapsAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    FIELDS_OR_RINGS = 'FIELDS_OR_RINGS'
    RING_VALUE_FIELD = 'RING_VALUE_FIELD'
    RING_GAP = 'RING_GAP'
    
    OUTPUT_RING = 'OUTPUT_RING'
    OUTPUT_ANCHOR = 'OUTPUT_ANCHOR'
    
    DEFAULT_SEGS = 10
    GAPS = 1
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return CreateRingMapsAlgorithm()
        
    def name(self):
        return 'CreateRingMaps'.lower()
        
    def displayName(self):
        return self.tr('Create Ring Maps')
        
    def group(self):
        return self.tr('MangoSystem')
        
    def groupId(self):
        return 'mangoscripts'
        
    def shortHelpString(self):
        return self.tr('Create Ring Maps.')
        
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Input VEctor Layer'), [QgsProcessing.TypeVector]))
        
        self.addParameter(QgsProcessingParameterString(self.FIELDS_OR_RINGS, self.tr('Comma Seperated Distance Fields or Ring Count'),
                                                    defaultValue='a3_2000, a3_2001, a3_2002, a3_2003, a3_2004, a3_2005', multiLine=False))
                                                    
        self.addParameter(QgsProcessingParameterString(self.RING_VALUE_FIELD, self.tr('Comma Seperated Distance Fields or Ring Count'),
                                                    defaultValue='ring_val', multiLine=False))
                                                    
        self.addParameter(QgsProcessingParameterNumber(self.RING_GAP, self.tr('Gap'), defaultValue=1, 
                                                       minValue=0, maxValue=10, type=QgsProcessingParameterNumber.Integer, 
                                                       optional=True))
        
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_RING, self.tr('Rings'), QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_ANCHOR, self.tr('Anchors'), QgsProcessing.TypeVectorLine))
        
    # is_number
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    # calculate_layer_extent
    def calculate_layer_extent(self, layer):
        extent = QgsRectangle()
        
        features = layer.getFeatures()
        for feature in features:
            geometry = feature.geometry()
            if extent.isEmpty() :
                extent = geometry.boundingBox()
            else:
                extent.combineExtentWith(geometry.boundingBox())
                
        if extent.isEmpty() :
            extent = layer.extent()
            
        return extent

    # create_point
    def create_point(self, centroid, radian, radius):
        dx = math.cos(radian) * radius
        dy = math.sin(radian) * radius
        
        return QgsPointXY(centroid.x() + dx, centroid.y() + dy)

    # create_ring_cell
    def create_ring_cell(self, centroid, from_deg, to_deg, from_radius, to_radius):
        step = abs(to_deg - from_deg) / self.DEFAULT_SEGS
        radian = 0.0
        
        outer_ring = []
        
        # first interior
        for index in range(self.DEFAULT_SEGS  + 1 - self.GAPS):
            radian = math.radians(from_deg + (index * step))
            outer_ring.append(self.create_point(centroid, radian, from_radius))
        
        # second outer
        for index in range(self.DEFAULT_SEGS - self.GAPS, -1, -1):
            radian = math.radians(from_deg + (index * step))
            outer_ring.append(self.create_point(centroid, radian, to_radius))
            
        return QgsGeometry.fromPolygonXY([outer_ring])

    # create_spatial_index
    def create_spatial_index(self, layer):
        spatial_index = QgsSpatialIndex()
        
        # features dictionary
        centroid_features = {}
        
        features = layer.getFeatures()
        for feature in features:
            # convert to point feature
            point_feature = QgsFeature(layer.fields())
            point_feature.setId(feature.id())
            point_feature.setAttributes(feature.attributes())
            point_feature.setGeometry(feature.geometry().centroid())
            centroid_features[point_feature.id()] = point_feature
            
            spatial_index.insertFeature(point_feature)
        
        return (spatial_index, centroid_features)

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        use_ring_count = False;
        fields_or_rings = self.parameterAsString(parameters, self.FIELDS_OR_RINGS, context)
        if (self.is_number(fields_or_rings)):
            ring_num = int(fields_or_rings)
            use_ring_count = True
        else:
            input_fields = fields_or_rings.strip().split(',')
            ring_num = len(input_fields)
            for idx in range(ring_num):
                input_fields[idx] = input_fields[idx].strip()
        if (ring_num == 0):
            raise QgsProcessingException('The count of Rings must be greater than zero')

        ring_value_field = self.parameterAsString(parameters, self.RING_VALUE_FIELD, context)

        self.GAPS = self.parameterAsInt(parameters, self.RING_GAP, context)
        if self.GAPS < 0 or self.GAPS > 10:
            raise QgsProcessingException('The Gap value must be between 0 and 10.')
        
        # calculate layer's extent & feature count
        feature_count = source.featureCount()
        extent = self.calculate_layer_extent(source)

        # create spatial index & convert to points
        (spatial_index, centroid_features) = self.create_spatial_index(source)

        center_point = extent.center(); # QgsPoint

        minx = extent.xMinimum()
        miny = extent.yMinimum()
        maxx = extent.xMaximum()
        maxy = extent.yMaximum()

        radius = (((maxx - minx)**2 + (maxy - miny)**2) **0.5) / 2.0
        radius_interval = radius / ring_num

        ring_fields = source.fields()
        ring_fields.append(QgsField("ring_num", QVariant.Int))
        ring_fields.append(QgsField(ring_value_field, QVariant.Double))
        
        idx_fields = []
        for idx in range(ring_num):
            if (use_ring_count):
                idx_fields.append(-1)
            else:
                idx_fields.append(ring_fields.lookupField(input_fields[idx]))

        (sink_ring, ring_id) = self.parameterAsSink(parameters, self.OUTPUT_RING, context,
                          ring_fields, QgsWkbTypes.Polygon, source.sourceCrs())
        (sink_anchor, anchor_id) = self.parameterAsSink(parameters, self.OUTPUT_ANCHOR, context,
                          source.fields(), QgsWkbTypes.LineString, source.sourceCrs())
                          
        if sink_ring is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_RING))
        if sink_anchor is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_ANCHOR))
            
        step_angle = 360.0 / feature_count
        half_step = step_angle / 2.0
        total = 100.0 / feature_count if feature_count else 0

        for idx_side in range(feature_count):
            if feedback.isCanceled():
                break
                
            from_deg = half_step + (idx_side * step_angle)
            to_deg = half_step + ((idx_side + 1) * step_angle)
            default_radius = radius
            
            for idx_radius in range(ring_num):
                cell = self.create_ring_cell(center_point, from_deg, to_deg, default_radius,  default_radius + radius_interval)
                cell_centroid_point = cell.centroid().asPoint()
                
                # find nearest feature & create anchor line
                if (idx_radius == 0):
                    fids = spatial_index.nearestNeighbor(cell_centroid_point, 1)
                    for fid in fids:
                        nearest_feature = centroid_features[fid]
                        nearest_point = nearest_feature.geometry().asPoint()
                        
                        anchor_feature = QgsFeature()
                        anchor_feature.setGeometry(QgsGeometry.fromPolylineXY([nearest_point, cell_centroid_point]))
                        anchor_feature.setAttributes(nearest_feature.attributes())
                        
                        # Add a new feature in the sink
                        sink_anchor.addFeature(anchor_feature, QgsFeatureSink.FastInsert)
                        
                        spatial_index.deleteFeature(nearest_feature)
                
                # create and write ring feature
                ring_feature = QgsFeature(ring_fields)
                ring_feature.setGeometry(cell)
                
                ring_attributes = nearest_feature.attributes()
                ring_attributes.append(idx_radius + 1) # ring_num
                if (idx_fields[idx_radius] == -1):
                    ring_attributes.append(0)  # default value = 0
                else:
                    ring_attributes.append(ring_attributes[idx_fields[idx_radius]]) # ring_val
                ring_feature.setAttributes(ring_attributes)
                
                # Add a new feature in the sink
                sink_ring.addFeature(ring_feature, QgsFeatureSink.FastInsert)
                
                default_radius += radius_interval
            
            # Update the progress bar
            feedback.setProgress(int(idx_side * total))

        # cleanup
        del centroid_features
        
        return {self.OUTPUT_RING: ring_id, self.OUTPUT_ANCHOR: anchor_id}
