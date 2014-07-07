"""
/***************************************************************************
Name                 : Export To Shapefiles
Description          : Export To Shapefiles
Date                 : 4/Jun/2014
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
##Select_Vector_Layers=multiple vector
##Include_gid_column=boolean
##Output_Folder=folder
##Ovewrite=boolean True
##output=output number

import os
from qgis.core import *
from processing.core.VectorWriter import VectorWriter

# main
exported = 0
selected_layers = Select_Vector_Layers.split(';')
selected_count = len(selected_layers)
for selected in selected_layers:
    layer = processing.getObject(selected)
    output_path = os.path.join(Output_Folder, layer.name() + '.shp')
    exported += 1
    progress.setPercentage(int(100 * exported / selected_count))
    
    # check exist Ovewrite
    if os.path.isfile(output_path) and Ovewrite == False:
        print "Already exists: " + output_path
        continue
    
    # export to shapefiles
    provider = layer.dataProvider()
    new_fields = provider.fields()
    if Include_gid_column == False:
        new_fields = QgsFields()
        for field in provider.fields():
            if (field.name().lower() <> 'gid'):
                new_fields.append(field)
    
    # remap fields
    idx_fields = []
    for field in new_fields:
        idx_fields.append(layer.fieldNameIndex(field.name()))
    
    writer = VectorWriter(output_path, None, new_fields, provider.geometryType(), layer.crs())
    features = processing.features(layer)
    for feature in features:
        new_feature = QgsFeature()
        new_feature.setGeometry(feature.geometry())
        if Include_gid_column:
            new_feature.setAttributes(feature.attributes())
        else:
            new_attributes = []
            for idx in idx_fields:
                new_attributes.append(feature.attributes()[idx])
            new_feature.setAttributes(new_attributes)
            
        writer.addFeature(new_feature)
    del writer

output = selected_count
