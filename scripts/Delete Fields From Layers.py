##[My Scripts]=group 
##Select_Vector_Layers=multiple vector
##Comma_Seperated_Fields_Names_for_Delete=String RDS_MAN_NO,RDS_SIG_CD,MVMN_RESN,MVM_RES_CD,NTFC_DE,OPE_MAN_ID,MNTN_YN,MVMN_DE
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
     