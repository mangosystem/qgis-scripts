# -*- coding: utf-8 -*-
#===================================
# Introduction
#===================================

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from glob import glob
from os import path

from qgis.utils import iface

#===================================
# QGIS Version
#===================================
print QGis.QGIS_VERSION_INT

if QGis.QGIS_VERSION_INT >= 10900:
    print "QGIS 2.0 uses SIP api v2"
else:
    print "QGIS 1.8 uses SIP api v1"

#===================================
# File
#===================================
# 1. python os.path http://docs.python.org/2/library/os.path.html
file = "C:/OpenGeoSuite/data/seoul/admin_emd.shp"
(head, tail) = path.split(file)
(name, ext) = path.splitext(tail)
print name

# 2. QT QFileInfo http://qt-project.org/doc/qt-4.8/qfileinfo.html
file_info = QFileInfo(file)
if file_info.exists():
    layer_name = file_info.completeBaseName()
    print layer_name
else:
    print "file not exist"

#===================================
# Encoding: EUC-KR
#===================================
# system default
settings = QSettings()
encode = settings.value("/UI/encoding")
print encode

# utf-8
settings.setValue("/UI/encoding", "UTF-8")
encode = settings.value("/UI/encoding")
print encode

# for korean
settings.setValue("/UI/encoding", "EUC-KR")

#===================================
# Loading Vector Layers
#===================================
# layer = QgsVectorLayer(data_source, layer_name, provider_name)
vlayer = QgsVectorLayer("C:/OpenGeoSuite/data/seoul/admin_emd.shp", "admin_emd", "ogr")
QgsMapLayerRegistry.instance().addMapLayer(vlayer)

# or

# QgsVectorLayer * 	addVectorLayer (QString vectorLayerPath, QString baseName, QString providerKey)=0
vlayer = iface.addVectorLayer("C:/OpenGeoSuite/data/seoul/admin_emd.shp", "admin_emd_2", "ogr")

#===================================
# iface & canvas
#===================================
canvas = iface.mapCanvas() 

canvas.setCanvasColor(Qt.red)
canvas.refresh()

canvas.setCanvasColor(Qt.white)
canvas.refresh()

# active layer
layer = iface.activeLayer()
layer = canvas.currentLayer()

#===================================
# Loading PostGIS Layer
#===================================
uri = QgsDataSourceURI()
# set hostname, port, database, username and password
uri.setConnection("localhost", "5432", "database", "username", "password")
# set database schema, table name, geometry column and optionaly subset (WHERE clause)
uri.setDataSource("public", "roads", "the_geom", "cityid = 2643")

postgis_layer = QgsVectorLayer(uri.uri(), "roads", "postgres")
QgsMapLayerRegistry.instance().addMapLayer(postgis_layer)

#===================================
# Loading WFS Layer 현재까지 1.0.0만 지원
#===================================
uri = "http://localhost:8080/geoserver/wfs?srsname=EPSG:4326&typename=topp:states&version=1.0.0&request=GetFeature&service=WFS"

wfs_layer = QgsVectorLayer(uri, "WFS Layer", "WFS")
QgsMapLayerRegistry.instance().addMapLayer(wfs_layer)

#===================================
# Loading Raster Layers
#===================================
rlayer = QgsRasterLayer("C:/OpenGeoSuite/data/seoul_raster/dem30.tif", "dem30")
QgsMapLayerRegistry.instance().addMapLayer(rlayer)

# or

rlayer = iface.addRasterLayer("C:/OpenGeoSuite/data/seoul_raster/dem30.tif", "dem30_2")

#===================================
# Query Raster Values
#===================================
point_location = QgsPoint(198326.53051, 447706.97545)
raster_sample = rlayer.dataProvider().identify(point_location, QgsRaster.IdentifyFormatValue).results()
raster_value = float(raster_sample[1])  # band index
print raster_value  # 31.0

#===================================
# Get layers
#===================================
# only visible layers
for layer in iface.mapCanvas().layers():
    print layer.name()

# all layers
allLayers = QgsMapLayerRegistry.instance().mapLayers()
for name,layer in allLayers.iteritems():
    print layer.name()

#===================================
# Selected features
#===================================
vlayer = iface.activeLayer()

features = vlayer.selectedFeatures()
count = vlayer.selectedFeatureCount()
print "selected features = " + str(count)

if count > 0:
    for feature in features:
        print feature.id(), 
else:
    print "not selected"

#==================================
# Feature & Attributes
#==================================
# select vector layers: admin_emd
vlayer = qgis.utils.iface.activeLayer()
provider = vlayer.dataProvider()

# list fields
fields = provider.fields()
for field in fields:
    print field.name(), 

# retrieve every feature with its geometry and attributes
features = vlayer.getFeatures()
for feature in features:
    # fetch geometry
    geometry = feature.geometry()
    
    print "\nFeature ID = %d: " % feature.id(), geometry.centroid().asPoint()
    
    # show all attributes and their values
    for attr in feature.attributes():
        print attr, 

#==================================
# Attribute & Spatial Filter
#==================================
# fid query
vlayer.removeSelection()
request = QgsFeatureRequest().setFilterFid(5)
feature = vlayer.getFeatures(request).next()
vlayer.select(feature.id())

print "Feature ID = %d: " % feature.id()
print feature.id(), feature[4], feature["EMD_NM"], feature.EMD_NM

qgis.utils.iface.mapCanvas().setExtent(feature.geometry().boundingBox())
qgis.utils.iface.mapCanvas().refresh()

# Filter options: NoFlags NoGeometry SubsetOfAttributes ExactIntersect 
vlayer.removeSelection()

request = QgsFeatureRequest().setFilterFid(5)
request.setFlags(QgsFeatureRequest.NoGeometry)
request.setSubsetOfAttributes([0, 1, 2])

feature = vlayer.getFeatures(request).next()
print feature.geometry(), feature[4]

# Rectangle query
vlayer.removeSelection()

map_extent = QgsRectangle()
query_extent = QgsRectangle(194052.547, 447030.808, 197991.199,448635.444)
request = QgsFeatureRequest().setFilterRect(query_extent)
features = vlayer.getFeatures(request)
for feature in features:
    geometry = feature.geometry()
    if map_extent.isEmpty() :
        map_extent = geometry.boundingBox()
    else:
        map_extent.unionRect(geometry.boundingBox())
    
    print "Feature ID = %d: " % feature.id(), geometry.centroid().asPoint()
    vlayer.select(feature.id())

qgis.utils.iface.mapCanvas().setExtent(map_extent)
qgis.utils.iface.mapCanvas().refresh()

vlayer.removeSelection()

# vlayer.setSubsetString( 'Counties = "Norwich"' )

#===================================
# Geometry(QgsGeometry) Handling
#===================================
geom_point = QgsGeometry.fromPoint(QgsPoint(10,10))
geom_line = QgsGeometry.fromPolyline( [ QgsPoint(4,4), QgsPoint(7,7) ] )
geom_polygon = QgsGeometry.fromPolygon( [ [ QgsPoint(1,1), QgsPoint(2,2), QgsPoint(2,1) ] ] )

wkt_geom = QgsGeometry.fromWkt("POINT(3 4)")

geom_point.asPoint()       # QgsPoint
geom_line.asPolyline()     # QgsPolyline
geom_polygon.asPolygon()   # QgsPolygon

# area(), length(), distance()
print geom_line.distance(geom_point)

#===================================
# Transformation
#===================================
crsSrc = QgsCoordinateReferenceSystem(4326)    # WGS84
crsDest = QgsCoordinateReferenceSystem(5174)   # Korean 
xform = QgsCoordinateTransform(crsSrc, crsDest)

# forward transformation: src -> dest
pt1 = xform.transform(QgsPoint(127.0028902777778, 38))
print "transformed point:", pt1

pt1 = xform.transform(QgsPoint(127, 38))
print "transformed point:", pt1

#===================================
# Modifying schema
#===================================
vlayer = qgis.utils.iface.activeLayer()
provider = vlayer.dataProvider()

# QgsField (name=QString, type=QVariant, typeName=QString, int len=0, int prec=0, comment=QString)
# QgsField("ara", QVariant.Double, "real",    19, 9)
# QgsField("num", QVariant.Int,    "integer", 10, 0)
# QgsField("nam", QVariant.String, "string",  20, 0)
stringfield = QgsField("mytext", QVariant.String)
intfield = QgsField("myint", QVariant.Int)
doublefield = QgsField("mydouble", QVariant.Double)

caps = provider.capabilities()

# 1. add fields
if caps & QgsVectorDataProvider.AddAttributes:
    res = vlayer.dataProvider().addAttributes( [ stringfield, intfield, doublefield ] )
    vlayer.updateFields()
else:
    print "cannot add new fields"
    
# 2. delete fields
if caps & QgsVectorDataProvider.DeleteAttributes:
    res = vlayer.dataProvider().deleteAttributes( [ stringfield, intfield, doublefield ] )
    vlayer.updateFields()
else:
    print "cannot delete fields"
    

#===================================
# Memory layer
#===================================
# create memory layer
tlayer = QgsVectorLayer("Polygon?crs=epsg:5174&index=yes", "Point_Buffered", "memory")
provider = tlayer.dataProvider()

# start editing mode
tlayer.startEditing()

# add fields
provider.addAttributes( [QgsField("dx", QVariant.Double), QgsField("dy", QVariant.Double) ] )

# create and add a feature
centroid = QgsPoint(198326.53051, 447706.97545)
buffered_geom = QgsGeometry.fromPoint(centroid).buffer(5000, 8)  # segments = 8

feature = QgsFeature(provider.fields())
feature.setGeometry( buffered_geom )
feature.setAttribute(0, centroid.x())
feature.setAttribute(1, centroid.y())

provider.addFeatures([feature])

# commit changes
tlayer.commitChanges()

# udpate extent
tlayer.updateExtents()

# add layer
QgsMapLayerRegistry.instance().addMapLayer(tlayer)
qgis.utils.iface.mapCanvas().setExtent(tlayer.extent())
qgis.utils.iface.mapCanvas().refresh()

#===================================
# Memory layer 2
#===================================
# create memory layer
tlayer = QgsVectorLayer("Point?crs=epsg:5174&index=yes", "circle_points", "memory")
provider = tlayer.dataProvider()

# start editing mode
tlayer.startEditing()

# add fields
provider.addAttributes( [ 
                QgsField("id",  QVariant.Int),
                QgsField("name", QVariant.String),
                QgsField("angle", QVariant.Double),
                QgsField("dx", QVariant.Double),
                QgsField("dy", QVariant.Double) ] )

fields = provider.fields()

# add a feature
features = []

# create circle
import math
sides = 32
radius = 5000.0
centroid = QgsPoint(198326.53051, 447706.97545)

feature = QgsFeature(fields)
feature.setGeometry( QgsGeometry.fromPoint(centroid) )
feature.setAttribute(0, 0)
feature.setAttribute(1, u"Name_" + str(0))
feature.setAttribute(2, 0)
feature.setAttribute(3, centroid.x())
feature.setAttribute(4, centroid.y())

features.append(feature)

for index in xrange(sides):
    radians = (float(index) / float(sides)) * (math.pi * 2.0)
    degree = radians * (180.0 / math.pi);
    dx = centroid.x() + math.cos(radians) * radius
    dy = centroid.y() + math.sin(radians) * radius
    print degree, radius, dx, dy
    
    feature = QgsFeature(fields)    
    feature.setGeometry( QgsGeometry.fromPoint(QgsPoint(dx, dy)) )
    feature.setAttribute(0, int(index + 1))
    feature.setAttribute(1, u"Name_" + str(index + 1))
    feature.setAttribute(2, degree)
    feature.setAttribute(3, dx)
    feature.setAttribute(4, dy)
    
    features.append(feature)

provider.addFeatures(features)

# commit changes
tlayer.commitChanges()

# udpate extent
tlayer.updateExtents()

# add layer
QgsMapLayerRegistry.instance().addMapLayer(tlayer)
qgis.utils.iface.mapCanvas().setExtent(tlayer.extent())
qgis.utils.iface.mapCanvas().refresh()

# show some stats
print "fields:", len(provider.fields())
print "features:", provider.featureCount()
extent = provider.extent()
print "extent: ", extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()

minimum = provider.minimumValue(2)  # 2 = field index
maximum = provider.maximumValue(2)  # 2 = field index
print minimum, maximum

# write shapefile
outputPath = 'C:/OpenGeoSuite/data/seoul/memory_circle_points.shp'
error = QgsVectorFileWriter.writeAsVectorFormat(tlayer, outputPath, "EUC-KR", crs, "ESRI Shapefile")
if error == QgsVectorFileWriter.NoError:
    print "shapefile exported!"

# write GeoJSON
outputPath = 'C:/OpenGeoSuite/data/seoul/circle_points.json'
error = QgsVectorFileWriter.writeAsVectorFormat(tlayer, outputPath, "utf-8", crs, "GeoJSON")
if error == QgsVectorFileWriter.NoError:
    print "geojson exported!"

#===================================
# Simple calculator 1 : calculate xy coordinate
#===================================
vlayer = QgsVectorLayer("C:/OpenGeoSuite/data/seoul/stores.shp", "stores", "ogr")

xfield = vlayer.fieldNameIndex("xc")
yfield = vlayer.fieldNameIndex("yc")

if xfield == -1:
    res = vlayer.dataProvider().addAttributes( [ QgsField("xc", QVariant.Double) ] )

if yfield == -1:
    res = vlayer.dataProvider().addAttributes( [ QgsField("yc", QVariant.Double) ] )

# reload attributes
vlayer.updateFields()
xfield = vlayer.fieldNameIndex("xc")
yfield = vlayer.fieldNameIndex("yc")

# Loop through each vector feature
features = vlayer.getFeatures()
for feature in features:
    geometry = feature.geometry()
    
    # centroid
    centroid = geometry.centroid().asPoint()
    
    fid = int(feature.id())
    vlayer.startEditing()
    
    # changeAttributeValue(feature id, index of field to be changed, new attribute value)
    vlayer.changeAttributeValue(fid, xfield, centroid.x())
    vlayer.changeAttributeValue(fid, yfield, centroid.y())
    vlayer.commitChanges()


#===================================
# Simple calculator 2 : calculate raster values from point
#===================================
vlayer = QgsVectorLayer("C:/OpenGeoSuite/data/seoul/stores.shp", "stores", "ogr")

rlayer = QgsRasterLayer("C:/OpenGeoSuite/data/seoul_raster/dem30.tif", "dem30")

value_field = "elev"
field_index = vlayer.fieldNameIndex(value_field)

if field_index == -1:
    res = vlayer.dataProvider().addAttributes( [ QgsField(value_field, QVariant.Double) ] )
    
    # reload attributes
    vlayer.updateFields()
    field_index = vlayer.fieldNameIndex(value_field)

# Loop through each vector feature
features = vlayer.getFeatures()
for feature in features:
    geom = feature.geometry()
    
    # get the raster value of the cell under the vector point
    rasterSample = rlayer.dataProvider().identify(geom.asPoint(), QgsRaster.IdentifyFormatValue).results()
    
    # the key is the raster band, and the value is the cell's raster value
    elevation = float(rasterSample[1])  # band index
    
    # changeAttributeValue(feature id, index of field to be changed, new attribute value)
    vlayer.startEditing()
    vlayer.changeAttributeValue(int(feature.id()), field_index, elevation)
    vlayer.commitChanges()

#===================================
# QgsGeometryAnalyzer
# 
# buffer (QgsVectorLayer *layer, const QString &shapefileName, double bufferDistance, bool onlySelectedFeatures=false, bool dissolve=false, int bufferDistanceField=-1, QProgressDialog *p=0)
# centroids (QgsVectorLayer *layer, const QString &shapefileName, bool onlySelectedFeatures=false, QProgressDialog *p=0)
# convexHull (QgsVectorLayer *layer, const QString &shapefileName, bool onlySelectedFeatures=false, int uniqueIdField=-1, QProgressDialog *p=0)
# dissolve (QgsVectorLayer *layer, const QString &shapefileName, bool onlySelectedFeatures=false, int uniqueIdField=-1, QProgressDialog *p=0)
# simplify (QgsVectorLayer *layer, const QString &shapefileName, double tolerance, bool onlySelectedFeatures=false, QProgressDialog *p=0)
#===================================
from qgis.analysis import QgsGeometryAnalyzer 

layer = qgis.utils.iface.mapCanvas().currentLayer()

# or

layer = qgis.utils.iface.activeLayer()

QgsGeometryAnalyzer().buffer(layer, "C:/OpenGeoSuite/data/seoul/buffer_500.shp", 500, False, False, -1)

#===================================
# QgsSpatialIndex
#===================================
# Function to create a spatial index for input QgsVectorDataProvider
def createSpatialIndex(provider):
    spatialIndex = QgsSpatialIndex()
    
    features = provider.getFeatures()
    for feature in features:
        spatialIndex.insertFeature(feature)
    
    return spatialIndex

# admin_sgg 레이어의 fid가 18번인 피처와 교차하는 stores 레이어의 피처 수는?
admin_layer = QgsVectorLayer("C:/OpenGeoSuite/data/seoul/admin_sgg.shp", "admin_sgg", "ogr")
store_layer = QgsVectorLayer("C:/OpenGeoSuite/data/seoul/stores.shp", "stores", "ogr")
spatialIndex = createSpatialIndex(store_layer)

request = QgsFeatureRequest().setFilterFid(18)  # fid
feature = admin_layer.getFeatures(request).next()
admin_geom = feature.geometry()

intersection_count = 0
stores_fids = spatialIndex.intersects(admin_geom.boundingBox())
for fid in stores_fids:
    request = QgsFeatureRequest().setFilterFid(int(fid))
    store_feature = store_layer.getFeatures(request).next()
    
    if admin_geom.intersects(store_feature.geometry()):
        intersection_count += 1
        print "Feature ID = %d: " % store_feature.id(), store_feature.geometry().centroid().asPoint()

print intersection_count


# Return layer from a name
def getLayer(layerName):
    allLayers = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in allLayers.iteritems():
        if layer.name() == layerName:
            if layer.isValid():
                return layer
            else:
                return None
    return None