"""
/***************************************************************************
Name                 : Load Shapefiles from DXF file
Description          : Load Shapefiles from DXF file
Date                 : 12/Feb/2014
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
##Input_DXF_file=file
##Source_CRS=crs EPSG:32652 
##Points_Shapefile=output vector
##LineString_Shapefile=output vector
##warning=output string

import os, subprocess
from osgeo import gdal, ogr, osr
from qgis.core import *
from processing.core.ProcessingLog import ProcessingLog
from processing.tools.vector import VectorWriter

# =================================================================
# http://www.gdal.org/ogr/drv_dxf.html
# ogr2ogr -f "ESRI Shapefile" h_point.shp -a_srs EPSG:32652 -overwrite dc2111_201312.dxf -where "OGR_GEOMETRY='POINT'"
# ogr2ogr -f "ESRI Shapefile" h_linestring.shp -a_srs EPSG:32652 -overwrite H3529100252013.dxf -where "OGR_GEOMETRY='LINESTRING'"

#  os.environ['DXF_ENCODING'] = 'EUC-KR'

os.environ['DXF_ENCODING'] = ''

cmd  = 'ogr2ogr -f "ESRI Shapefile" ' + LineString_Shapefile
cmd += ' -overwrite ' + Input_DXF_file
cmd += ' -a_srs ' + Source_CRS
cmd += ''' -where "OGR_GEOMETRY='LINESTRING'"'''

line_process = subprocess.Popen(cmd, shell=True)
(output, err) = line_process.communicate()
p_status = line_process.wait()
progress.setText(err)

cmd  = 'ogr2ogr -f "ESRI Shapefile" ' + Points_Shapefile
cmd += ' -overwrite ' + Input_DXF_file
cmd += ' -a_srs ' + Source_CRS
cmd += ''' -where "OGR_GEOMETRY='POINT'"'''

point_process = subprocess.Popen(cmd, shell=True)
(output, err) = point_process.communicate()
p_status = point_process.wait()
progress.setText(err)
