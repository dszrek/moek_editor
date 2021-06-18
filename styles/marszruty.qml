<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyLocal="1" version="3.10.11-A Coruña" maxScale="0" labelsEnabled="1" simplifyDrawingTol="1" styleCategories="AllStyleCategories" simplifyAlgorithm="0" minScale="25000" simplifyDrawingHints="1" readOnly="0" hasScaleBasedVisibilityFlag="1" simplifyMaxScale="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="singleSymbol" symbollevels="0" forceraster="0" enableorderby="0">
    <symbols>
      <symbol force_rhr="0" name="0" type="line" alpha="1" clip_to_extent="1">
        <layer pass="0" enabled="1" locked="0" class="GeometryGenerator">
          <prop k="SymbolType" v="Line"/>
          <prop k="geometryModifier" v="difference(&#xd;&#xa;  difference(&#xd;&#xa;&#x9;$geometry,&#xd;&#xa;&#x9;buffer( start_point( $geometry ), 0.0008*@map_scale)&#xd;&#xa;  ),&#xd;&#xa;buffer( end_point( $geometry ), 0.0008*@map_scale)&#xd;&#xa;)"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
          <symbol force_rhr="0" name="@0@0" type="line" alpha="1" clip_to_extent="1">
            <layer pass="0" enabled="1" locked="0" class="SimpleLine">
              <prop k="capstyle" v="flat"/>
              <prop k="customdash" v="5;2"/>
              <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="customdash_unit" v="MM"/>
              <prop k="draw_inside_polygon" v="0"/>
              <prop k="joinstyle" v="round"/>
              <prop k="line_color" v="255,255,255,255"/>
              <prop k="line_style" v="solid"/>
              <prop k="line_width" v="1.2"/>
              <prop k="line_width_unit" v="MM"/>
              <prop k="offset" v="0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="ring_filter" v="0"/>
              <prop k="use_custom_dash" v="0"/>
              <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
            <layer pass="0" enabled="1" locked="0" class="SimpleLine">
              <prop k="capstyle" v="flat"/>
              <prop k="customdash" v="5;2"/>
              <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="customdash_unit" v="MM"/>
              <prop k="draw_inside_polygon" v="0"/>
              <prop k="joinstyle" v="round"/>
              <prop k="line_color" v="0,50,125,255"/>
              <prop k="line_style" v="solid"/>
              <prop k="line_width" v="0.8"/>
              <prop k="line_width_unit" v="MM"/>
              <prop k="offset" v="0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="ring_filter" v="0"/>
              <prop k="use_custom_dash" v="0"/>
              <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer pass="0" enabled="1" locked="0" class="GeometryGenerator">
          <prop k="SymbolType" v="Marker"/>
          <prop k="geometryModifier" v="end_point($geometry )&#xd;&#xa;"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
          <symbol force_rhr="0" name="@0@1" type="marker" alpha="1" clip_to_extent="1">
            <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="255,255,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="round"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="255,255,255,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.4"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="1.8"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
            <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,50,125,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="round"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,50,125,0"/>
              <prop k="outline_style" v="no"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="1.8"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer pass="0" enabled="1" locked="0" class="GeometryGenerator">
          <prop k="SymbolType" v="Marker"/>
          <prop k="geometryModifier" v="start_point($geometry )&#xd;&#xa;"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
          <symbol force_rhr="0" name="@0@2" type="marker" alpha="1" clip_to_extent="1">
            <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="255,255,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="round"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="255,255,255,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.4"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="1.8"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
            <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,50,125,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="round"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,50,125,0"/>
              <prop k="outline_style" v="no"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="1.8"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style isExpression="1" fontSize="9" fontSizeUnit="Point" fieldName="CASE&#xd;&#xa;&#x9;WHEN &quot;marsz_m&quot; &lt; 1000 AND &quot;marsz_t&quot; &lt; 60&#xd;&#xa;&#x9;THEN ' ' + to_string(marsz_m) + ' m – ' + to_string(marsz_t) + ' sek '&#xd;&#xa;&#x9;WHEN &quot;marsz_m&quot; &lt; 1000 AND &quot;marsz_t&quot; >= 60&#xd;&#xa;&#x9;THEN ' ' + to_string(marsz_m) + ' m – ' + to_string(round(marsz_t/60,0)) + ' min '&#xd;&#xa;&#x9;WHEN &quot;marsz_m&quot; >= 1000 AND &quot;marsz_t&quot; &lt; 60&#xd;&#xa;&#x9;THEN ' ' + to_string(round(marsz_m/1000,1)) + ' km – ' + to_string(marsz_t) + ' sek '&#xd;&#xa;&#x9;WHEN &quot;marsz_m&quot; >= 1000 AND &quot;marsz_t&quot; >= 60&#xd;&#xa;&#x9;THEN ' ' + to_string(round(marsz_m/1000,1)) + ' km – ' + to_string(round(marsz_t/60,0)) + ' min '&#xd;&#xa;END" namedStyle="Normal" fontCapitals="0" fontUnderline="0" blendMode="0" textColor="255,255,255,255" fontWordSpacing="0" multilineHeight="1" useSubstitutions="0" fontItalic="0" previewBkgrdColor="255,255,255,255" textOrientation="horizontal" fontFamily="MS Shell Dlg 2" fontWeight="50" fontLetterSpacing="0" fontKerning="1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontStrikeout="0" textOpacity="1">
        <text-buffer bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSizeUnits="MM" bufferColor="255,255,255,255" bufferJoinStyle="128" bufferSize="0.6" bufferNoFill="0" bufferDraw="0" bufferBlendMode="0" bufferOpacity="1"/>
        <background shapeOffsetY="0" shapeSizeType="0" shapeOffsetX="0" shapeSizeUnit="MM" shapeBorderColor="0,50,125,255" shapeType="0" shapeRotationType="0" shapeRadiiX="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiY="0" shapeSizeY="1.2" shapeRadiiUnit="MM" shapeJoinStyle="128" shapeSVGFile="" shapeSizeX="1.2" shapeOpacity="0.8" shapeFillColor="0,50,125,255" shapeBorderWidth="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRotation="0" shapeBlendMode="0" shapeDraw="1" shapeOffsetUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthUnit="MM">
          <effect type="effectStack" enabled="0">
            <effect type="dropShadow">
              <prop k="blend_mode" v="13"/>
              <prop k="blur_level" v="2.645"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="0,0,0,255"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="0"/>
              <prop k="offset_angle" v="135"/>
              <prop k="offset_distance" v="2"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="opacity" v="1"/>
            </effect>
            <effect type="outerGlow">
              <prop k="blend_mode" v="0"/>
              <prop k="blur_level" v="0"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color1" v="0,0,255,255"/>
              <prop k="color2" v="0,255,0,255"/>
              <prop k="color_type" v="0"/>
              <prop k="discrete" v="0"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="1"/>
              <prop k="opacity" v="0.5"/>
              <prop k="rampType" v="gradient"/>
              <prop k="single_color" v="255,255,255,255"/>
              <prop k="spread" v="2"/>
              <prop k="spread_unit" v="MM"/>
              <prop k="spread_unit_scale" v="3x:0,0,0,0,0,0"/>
            </effect>
            <effect type="drawSource">
              <prop k="blend_mode" v="0"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="1"/>
              <prop k="opacity" v="1"/>
            </effect>
            <effect type="innerShadow">
              <prop k="blend_mode" v="13"/>
              <prop k="blur_level" v="2.645"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="0,0,0,255"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="0"/>
              <prop k="offset_angle" v="135"/>
              <prop k="offset_distance" v="2"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="opacity" v="1"/>
            </effect>
            <effect type="innerGlow">
              <prop k="blend_mode" v="0"/>
              <prop k="blur_level" v="2.645"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color1" v="0,0,255,255"/>
              <prop k="color2" v="0,255,0,255"/>
              <prop k="color_type" v="0"/>
              <prop k="discrete" v="0"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="0"/>
              <prop k="opacity" v="0.5"/>
              <prop k="rampType" v="gradient"/>
              <prop k="single_color" v="255,255,255,255"/>
              <prop k="spread" v="2"/>
              <prop k="spread_unit" v="MM"/>
              <prop k="spread_unit_scale" v="3x:0,0,0,0,0,0"/>
            </effect>
          </effect>
          <symbol force_rhr="0" name="markerSymbol" type="marker" alpha="1" clip_to_extent="1">
            <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="232,113,141,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowOffsetDist="1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowDraw="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetGlobal="1" shadowRadiusUnit="MM" shadowScale="100" shadowRadiusAlphaOnly="0" shadowOffsetAngle="135" shadowBlendMode="6" shadowUnder="0" shadowRadius="1.5" shadowOffsetUnit="MM" shadowOpacity="0.7" shadowColor="0,0,0,255"/>
        <dd_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format wrapChar="" addDirectionSymbol="0" leftDirectionSymbol="&lt;" rightDirectionSymbol=">" multilineAlign="0" autoWrapLength="0" useMaxLineLengthForAutoWrap="1" formatNumbers="0" decimals="3" reverseDirectionSymbol="0" placeDirectionSymbol="0" plussign="0"/>
      <placement offsetType="0" dist="10" centroidWhole="0" maxCurvedCharAngleOut="-25" overrunDistanceUnit="MM" geometryGeneratorEnabled="1" centroidInside="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" repeatDistance="0" xOffset="0" distUnits="MM" maxCurvedCharAngleIn="25" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" yOffset="0" rotationAngle="0" distMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" overrunDistance="0" offsetUnits="MM" placementFlags="10" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" priority="5" fitInPolygonOnly="0" repeatDistanceUnits="MM" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" layerType="LineGeometry" placement="6" geometryGenerator="line_interpolate_point($geometry,$length/2)" geometryGeneratorType="PointGeometry" preserveRotation="0"/>
      <rendering scaleVisibility="1" upsidedownLabels="0" maxNumLabels="2000" zIndex="0" minFeatureSize="0" mergeLines="0" labelPerPart="0" fontLimitPixelSize="0" limitNumLabels="0" obstacle="1" scaleMax="25000" scaleMin="0" obstacleType="0" fontMaxPixelSize="10000" fontMinPixelSize="3" drawLabels="1" obstacleFactor="1" displayAll="0"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties" type="Map">
            <Option name="LabelRotation" type="Map">
              <Option name="active" type="bool" value="false"/>
              <Option name="type" type="int" value="1"/>
              <Option name="val" type="QString" value=""/>
            </Option>
            <Option name="OffsetQuad" type="Map">
              <Option name="active" type="bool" value="false"/>
              <Option name="type" type="int" value="1"/>
              <Option name="val" type="QString" value=""/>
            </Option>
          </Option>
          <Option name="type" type="QString" value="collection"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option name="anchorPoint" type="QString" value="pole_of_inaccessibility"/>
          <Option name="ddProperties" type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
          <Option name="drawToAllParts" type="bool" value="false"/>
          <Option name="enabled" type="QString" value="1"/>
          <Option name="lineSymbol" type="QString" value="&lt;symbol force_rhr=&quot;0&quot; name=&quot;symbol&quot; type=&quot;line&quot; alpha=&quot;0.8&quot; clip_to_extent=&quot;1&quot;>&lt;layer pass=&quot;0&quot; enabled=&quot;1&quot; locked=&quot;0&quot; class=&quot;SimpleLine&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;round&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;round&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;0,50,125,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.6&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
          <Option name="minLength" type="double" value="0"/>
          <Option name="minLengthMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="minLengthUnit" type="QString" value="MM"/>
          <Option name="offsetFromAnchor" type="double" value="0.5"/>
          <Option name="offsetFromAnchorMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="offsetFromAnchorUnit" type="QString" value="MM"/>
          <Option name="offsetFromLabel" type="double" value="1.5"/>
          <Option name="offsetFromLabelMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="offsetFromLabelUnit" type="QString" value="MM"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>5</featureBlendMode>
  <layerOpacity>0.75</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory penColor="#000000" lineSizeType="MM" penAlpha="255" width="15" minimumSize="0" rotationOffset="270" sizeScale="3x:0,0,0,0,0,0" enabled="0" minScaleDenominator="0" opacity="1" penWidth="0" maxScaleDenominator="1e+08" barWidth="5" height="15" scaleBasedVisibility="0" diagramOrientation="Up" labelPlacementMethod="XHeight" sizeType="MM" backgroundColor="#ffffff" lineSizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" scaleDependency="Area">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute color="#000000" field="" label=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings priority="0" dist="0" zIndex="0" showAll="1" placement="2" obstacle="0" linePlacementFlags="18">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="marsz_id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="user_id">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="marsz_m">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="marsz_t">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" field="marsz_id" index="0"/>
    <alias name="" field="user_id" index="1"/>
    <alias name="" field="marsz_m" index="2"/>
    <alias name="" field="marsz_t" index="3"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" applyOnUpdate="0" field="marsz_id"/>
    <default expression="" applyOnUpdate="0" field="user_id"/>
    <default expression="" applyOnUpdate="0" field="marsz_m"/>
    <default expression="" applyOnUpdate="0" field="marsz_t"/>
  </defaults>
  <constraints>
    <constraint constraints="3" exp_strength="0" unique_strength="1" field="marsz_id" notnull_strength="1"/>
    <constraint constraints="1" exp_strength="0" unique_strength="0" field="user_id" notnull_strength="1"/>
    <constraint constraints="1" exp_strength="0" unique_strength="0" field="marsz_m" notnull_strength="1"/>
    <constraint constraints="1" exp_strength="0" unique_strength="0" field="marsz_t" notnull_strength="1"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" field="marsz_id" desc=""/>
    <constraint exp="" field="user_id" desc=""/>
    <constraint exp="" field="marsz_m" desc=""/>
    <constraint exp="" field="marsz_t" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column name="marsz_id" type="field" width="-1" hidden="0"/>
      <column name="user_id" type="field" width="-1" hidden="0"/>
      <column name="marsz_m" type="field" width="-1" hidden="0"/>
      <column name="marsz_t" type="field" width="-1" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
Formularze QGIS mogą zawierać funkcje Pythona, które będą wywołane przy otwieraniu
 formularza.

Można z nich skorzystać, aby rozbudować formularz.

Wpisz nazwę funkcji w polu
"Python Init function".
Przykład:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="marsz_id"/>
    <field editable="1" name="marsz_m"/>
    <field editable="1" name="marsz_t"/>
    <field editable="1" name="user_id"/>
  </editable>
  <labelOnTop>
    <field name="marsz_id" labelOnTop="0"/>
    <field name="marsz_m" labelOnTop="0"/>
    <field name="marsz_t" labelOnTop="0"/>
    <field name="user_id" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>"marsz_id"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
