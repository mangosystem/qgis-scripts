"""
/***************************************************************************
Name                 : Merge Vector Layers
Description          : Merge Vector Layers
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
##Merge Vector Layers=name
##Select_Vector_Layers=multiple vector
##Template_Layer=vector 
##Output_Merge_Layer=output vector

from qgis.core import *
from processing.tools.vector import VectorWriter

# ignore upper, lower case
def find_field(fields, field_name):
    field_index = -1
    index = 0
    for field in fields:
        if (field.name().lower() == field_name.lower()):
            field_index = index
            break
        index += 1
    return field_index

# main
template_layer = processing.getObject(Template_Layer)
template_provider = template_layer.dataProvider()
template_fields = template_provider.fields()
template_geometry_type = template_layer.geometryType()

writer = VectorWriter(Output_Merge_Layer, None, template_fields, 
            template_provider.geometryType(), template_layer.crs())

selected_layers = Select_Vector_Layers.split(';')
for selected in selected_layers:
    layer = processing.getObject(selected)    
    if layer.geometryType() == template_geometry_type:
        idx_fields = []
        fields = layer.dataProvider().fields()
        for field in template_fields:
            idx_fields.append(find_field(fields, field.name()))
            
        features = processing.features(layer)
        for feature in features:
            new_attributes = []
            for idx in idx_fields:
                val = None if idx == -1 else feature.attributes()[idx]
                new_attributes.append(val)

            new_feature = QgsFeature(template_fields)
            new_feature.setGeometry(feature.geometry())
            new_feature.setAttributes(new_attributes)
            writer.addFeature(new_feature)
            
del writer