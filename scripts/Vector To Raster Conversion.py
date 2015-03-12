"""
/***************************************************************************
Name                 : Vector To Raster Conversion
Description          : Vector To Raster Conversion
Date                 : 12/March/2015
copyright            : (C) 2015 by Minpa Lee, Mango System inc.
email                : mapplus@gmail.com
reference:
 ***************************************************************************/

/***************************************************************************
 * Reference
   - https://github.com/Ambrosys/gdal/blob/master/autotest/alg/proximity.py
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
##Vector To Raster Conversion=name
##Vector_Layer=vector
##Attribute_Field=field Vector_Layer
##Extent=extent
##Cell_Size=number 0.0
##Raster_Type=selection Float32;Float64;Int32
##Output=output raster

import math
from osgeo import gdal, ogr, osr
from osgeo.gdalconst import *
from qgis.core import *
from processing.tools.system import *

TYPES = ['Float32','Float64','Int32']

# =============================================================================
# 1. open ogr vector layer from qgs map layer
# =============================================================================
vector_layer = processing.getObject(Vector_Layer)
ogr_vector_datasource = ogr.Open(unicode(vector_layer.source()))
ogr_vector_layer = ogr_vector_datasource.GetLayer()

# =============================================================================
# 2. prepare variables
# =============================================================================
extent = vector_layer.extent()
if Extent:
    # ParameterExtent(xmin, xmax, ymin, ymax)
    tokens = Extent.split(',')
    # QgsRectangle(xmin=0, ymin=0, xmax=0, ymax=0)
    extent = QgsRectangle(float(tokens[0]), float(tokens[2]), float(tokens[1]), float(tokens[3]))

cell_size = Cell_Size
if cell_size <= 0:
    cell_size = int(min(extent.width(), extent.height()) / 250.0)

options = []
if Attribute_Field:
  options.append('ATTRIBUTE=' + unicode(Attribute_Field))
  
# =============================================================================
# 3. create single band raster dataset
# =============================================================================
nodata = -9999
srs = osr.SpatialReference()
srs.ImportFromWkt(vector_layer.crs().toWkt())
transform = [extent.xMinimum(), cell_size, 0.0, extent.yMaximum(), 0.0, -cell_size]
raster_width = int(math.ceil(abs(extent.xMaximum() - extent.xMinimum()) / cell_size))
raster_height = int(math.ceil(abs(extent.yMaximum() - extent.yMinimum()) / cell_size))

driver = gdal.GetDriverByName('GTiff')
rasterizedDS = driver.Create(Output, raster_width, raster_height, 1, gdal.GetDataTypeByName(TYPES[Raster_Type]))
rasterizedDS.GetRasterBand(1).SetNoDataValue(nodata)
rasterizedDS.SetGeoTransform(transform)
rasterizedDS.SetProjection(srs.ExportToWkt())
rasterizedDS.GetRasterBand(1).Fill(nodata)

# =============================================================================
# 4. rasterize from vector layer
# =============================================================================
if len(options) > 0:
  gdal.RasterizeLayer(rasterizedDS, [1], ogr_vector_layer, options=options)
else:
  gdal.RasterizeLayer(rasterizedDS, [1], ogr_vector_layer, burn_values=[1])

# =============================================================================
# 4. cleanup
# =============================================================================
rasterizedDS = None
ogr_vector_datasource   = None

