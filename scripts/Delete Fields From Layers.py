"""
/***************************************************************************
Name                 : Delete Fields From Layers
Description          : Delete Fields From Layers
Date                 : 31/Dec/2013
copyright            : (C) 2013 by Minpa Lee
email                : mapplus@gmail.com
reference:
    http://gis.stackexchange.com/questions/6682/how-to-implement-ringmaps-in-arcgis
    http://www.esri.com/esri-news/arcuser/fall-2013/looking-at-temporal-changes
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
##Delete Fields From Layers=name
##Select_Vector_Layers=multiple vector
##Comma_Seperated_Fields_Names_for_Delete=String
##number=output number

from qgis.core import *
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

# ignore upper, lower case
def find_field(fields, field_name):
    field_index = -1
    for field in fields:
        field_index += 1
        if (field.name().lower() == field_name.lower()):
            return field_index
    return field_index

# main
selected_layers = Select_Vector_Layers.split(';')
delete_fields_list = Comma_Seperated_Fields_Names_for_Delete.strip().split(',')
if len(delete_fields_list) == 0:
    raise GeoAlgorithmExecutionException('Comma seperated field names required!')

number = 0
for selected in selected_layers:
    layer = processing.getObject(selected)
    provider = layer.dataProvider()    
    if provider.capabilities() & QgsVectorDataProvider.DeleteAttributes:
        fields_for_delete = []
        for field_name in delete_fields_list:
            field_index = find_field( provider.fields(), field_name.strip())
            if field_index >= 0:
                fields_for_delete.append(field_index)
        
        if len(fields_for_delete) > 0:
            layer.startEditing()
            res = provider.deleteAttributes( fields_for_delete )
            layer.updateFields()
            layer.commitChanges()
            number += 1
    else:
        print "cannot delete fields"
     