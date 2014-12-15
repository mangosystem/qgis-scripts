"""
/***************************************************************************
Name                 : Multiple Ring Buffer
Description          : Multiple Ring Buffer
Date                 : 25/Dec/2014
copyright            : (C) 2014 by Minpa Lee
email                : mapplus@gmail.com
reference:
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
##[My Scripts]=group
##Input_Layer=vector
##Comma_Seperated_Distance_Values=String
##Outside_Only=boolean false
##Output_Layer=output vector

import os
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

# check values
distance_values = Comma_Seperated_Distance_Values.strip().split(',')
if len(distance_values) == 0:
    raise GeoAlgorithmExecutionException('Comma seperated ditance values required!')

# add distance field
input_layer = processing.getObject(Input_Layer)
provider = input_layer.dataProvider()
output_fields = provider.fields()
output_fields.append(QgsField('rind_dist', QVariant.Double))

# write features
writer = VectorWriter(Output_Layer, None, output_fields, QGis.WKBPolygon, input_layer.crs())
features = processing.features(input_layer)
for feature in features:
    geometry = feature.geometry()
    buffered = []
    for index in range(len(distance_values)):
        rind_distance = float(distance_values[index])
        buffered.append(geometry.buffer(rind_distance, 24)) #quadrant segments
        
        new_feature = QgsFeature()
        if Outside_Only == True and index > 0:
            new_feature.setGeometry(buffered[index].difference(buffered[index-1]))
        else:
            new_feature.setGeometry(buffered[index])
        
        new_attributes = feature.attributes()
        new_attributes.append(rind_distance) # ring distance
        new_feature.setAttributes(new_attributes)
        writer.addFeature(new_feature)
    del buffered
del writer
