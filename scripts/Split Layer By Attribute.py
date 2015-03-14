"""
/***************************************************************************
Name                 : Split Layer By Attribute
Description          : Split Layer By Attribute
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
##Split Layer By Attribute=name
##Input_Layer=vector
##Unique_Value_Field=field Input_Layer
##Output_Folder=folder
##Pefix_Name=String Output
##number=output number

import os
from qgis.core import *
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

input_layer = processing.getObject(Input_Layer)
provider = input_layer.dataProvider()

field_index = input_layer.fieldNameIndex(Unique_Value_Field)
if field_index == -1:
    raise GeoAlgorithmExecutionException(Unique_Value_Field + ' does not exist.')

writers = {}
step = 0

features = processing.features(input_layer)
feature_count = input_layer.featureCount()
for feature in features:
    progress.setPercentage(int(100 * step / feature_count))
    step += 1

    uv_value = feature.attributes()[field_index]
    if uv_value not in writers:
        # error = out_file contains unicode text
        out_file = os.path.join(Output_Folder, Pefix_Name + '_' + str(uv_value) + '.shp')
        writers[uv_value] = VectorWriter(out_file, None, provider.fields(),
                                      provider.geometryType(), input_layer.crs())
    writers[uv_value].addFeature(feature)

number = len(writers)
for writer in writers.values():
    del writer
