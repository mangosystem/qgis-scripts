"""
/***************************************************************************
Name                 : Raster Euclidean Distance Analysis
Description          : Raster Euclidean Distance Analysis
Date                 : 10/March/2015
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
##[GEEPS]=group
##Raster Euclidean Distance Analysis=name
##Vector_Layer=vector
##Max_Distance=number -1.0
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

nodata = -9999
srs = osr.SpatialReference()
srs.ImportFromWkt(vector_layer.crs().toWkt())
transform = [extent.xMinimum(), cell_size, 0.0, extent.yMaximum(), 0.0, -cell_size]
raster_width = int(math.ceil(abs(extent.xMaximum() - extent.xMinimum()) / cell_size))
raster_height = int(math.ceil(abs(extent.yMaximum() - extent.yMinimum()) / cell_size))

# =============================================================================
# 3. rasterize temporary raterdataset from vector layer, extent, cellsize
# =============================================================================
temporary_path = getTempFilename('tif')
driver = gdal.GetDriverByName('GTiff')
rasterizedDS = driver.Create(temporary_path, raster_width, raster_height, 1, gdal.GDT_Byte)
rasterizedDS.GetRasterBand(1).SetNoDataValue(nodata)
rasterizedDS.SetGeoTransform(transform)
rasterizedDS.SetProjection(srs.ExportToWkt())
rasterizedDS.GetRasterBand(1).Fill(nodata)
gdal.RasterizeLayer(rasterizedDS, [1], ogr_vector_layer, burn_values=[1])

# =============================================================================
# 4. compute proximity from rasterized dataset
# =============================================================================
options = []
if Max_Distance > 0:
  options.append('MAXDIST=' + str(Max_Distance))

proximityDs = driver.Create(Output, raster_width, raster_height, 1, gdal.GetDataTypeByName(TYPES[Raster_Type]))
proximityDs.GetRasterBand(1).SetNoDataValue(nodata)
proximityDs.SetGeoTransform(transform)
proximityDs.SetProjection(srs.ExportToWkt())
proximityDs.GetRasterBand(1).Fill(nodata)
gdal.ComputeProximity(rasterizedDS.GetRasterBand(1), proximityDs.GetRasterBand(1), options, callback = None)

# =============================================================================
# 5. cleanup
# =============================================================================
rasterizedDS = None
proximityDs  = None
ogr_vector_datasource   = None

