<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="1" version="3.10.14-A Coruña" hasScaleBasedVisibilityFlag="0" maxScale="0" simplifyAlgorithm="0" minScale="1e+08" simplifyMaxScale="1" readOnly="0" styleCategories="AllStyleCategories" simplifyDrawingTol="1" simplifyLocal="1" simplifyDrawingHints="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol name="0" type="fill" force_rhr="0" clip_to_extent="1" alpha="1">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="255,255,255,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="217,0,143,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.3"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="no"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="rule-based">
    <rules key="{cbc83ded-37cf-4ff7-aad0-43704165ba99}">
      <rule scalemindenom="25000" key="{f52eb5bf-3343-468c-9447-1b19cf62f2a9}" scalemaxdenom="10000000" description="Far">
        <settings calloutType="simple">
          <text-style multilineHeight="1" previewBkgrdColor="0,0,0,255" textOpacity="1" fontUnderline="0" fontKerning="1" fontSize="8" namedStyle="Normal" fontFamily="MS Shell Dlg 2" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontCapitals="0" fontSizeUnit="Point" fontItalic="0" isExpression="1" fontLetterSpacing="0" fieldName="pow_id  +  '\n'  + t_pow_name" textOrientation="horizontal" fontStrikeout="0" textColor="217,0,143,255" blendMode="0" fontWordSpacing="0" fontWeight="50" useSubstitutions="0">
            <text-buffer bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferBlendMode="0" bufferDraw="0" bufferSize="2" bufferColor="255,255,255,255" bufferOpacity="1" bufferNoFill="1" bufferJoinStyle="128"/>
            <background shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthUnit="MM" shapeSizeY="0" shapeRadiiUnit="MM" shapeSizeType="0" shapeOffsetUnit="MM" shapeRadiiX="0" shapeSizeX="0" shapeBorderColor="255,255,255,255" shapeType="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeRotationType="0" shapeRadiiY="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSVGFile="" shapeRotation="0" shapeSizeUnit="MM" shapeJoinStyle="128" shapeOffsetX="0" shapeBorderWidth="2" shapeDraw="1" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="255,255,255,255" shapeOpacity="1" shapeOffsetY="0" shapeBlendMode="0">
              <effect type="effectStack" enabled="1">
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
                <effect type="drawSource">
                  <prop k="blend_mode" v="0"/>
                  <prop k="draw_mode" v="2"/>
                  <prop k="enabled" v="1"/>
                  <prop k="opacity" v="0.75"/>
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
              <symbol name="markerSymbol" type="marker" force_rhr="0" clip_to_extent="1" alpha="1">
                <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
                  <prop k="angle" v="0"/>
                  <prop k="color" v="183,72,75,255"/>
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
            <shadow shadowRadius="1.5" shadowRadiusAlphaOnly="0" shadowOffsetUnit="MM" shadowOffsetDist="1" shadowBlendMode="6" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowUnder="0" shadowOffsetAngle="135" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusUnit="MM" shadowOffsetGlobal="1" shadowColor="0,0,0,255" shadowDraw="0" shadowOpacity="0.7" shadowScale="100"/>
            <dd_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </dd_properties>
            <substitutions/>
          </text-style>
          <text-format wrapChar="" placeDirectionSymbol="0" addDirectionSymbol="0" leftDirectionSymbol="&lt;" rightDirectionSymbol=">" useMaxLineLengthForAutoWrap="1" multilineAlign="1" decimals="3" autoWrapLength="0" formatNumbers="0" reverseDirectionSymbol="0" plussign="0"/>
          <placement dist="0" rotationAngle="0" distUnits="MM" yOffset="10" maxCurvedCharAngleOut="-25" geometryGeneratorEnabled="0" placement="1" centroidWhole="0" geometryGenerator="" overrunDistance="0" geometryGeneratorType="PointGeometry" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" offsetUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" overrunDistanceUnit="MM" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" placementFlags="10" repeatDistanceUnits="MM" repeatDistance="0" preserveRotation="1" fitInPolygonOnly="0" centroidInside="1" maxCurvedCharAngleIn="25" layerType="PolygonGeometry" priority="5" distMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" offsetType="0" xOffset="10"/>
          <rendering zIndex="0" obstacle="1" scaleVisibility="1" upsidedownLabels="0" fontMaxPixelSize="10000" mergeLines="0" obstacleType="1" maxNumLabels="2000" displayAll="0" minFeatureSize="0" scaleMin="10000" limitNumLabels="0" labelPerPart="0" fontLimitPixelSize="0" scaleMax="1500000" obstacleFactor="1" drawLabels="1" fontMinPixelSize="3"/>
          <dd_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
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
              <Option name="enabled" type="QString" value="0"/>
              <Option name="lineSymbol" type="QString" value="&lt;symbol name=&quot;symbol&quot; type=&quot;line&quot; force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot; alpha=&quot;1&quot;>&lt;layer class=&quot;SimpleLine&quot; enabled=&quot;1&quot; pass=&quot;0&quot; locked=&quot;0&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
              <Option name="minLength" type="double" value="0"/>
              <Option name="minLengthMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="minLengthUnit" type="QString" value="MM"/>
              <Option name="offsetFromAnchor" type="double" value="0"/>
              <Option name="offsetFromAnchorMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="offsetFromAnchorUnit" type="QString" value="MM"/>
              <Option name="offsetFromLabel" type="double" value="0"/>
              <Option name="offsetFromLabelMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="offsetFromLabelUnit" type="QString" value="MM"/>
            </Option>
          </callout>
        </settings>
      </rule>
      <rule scalemindenom="1" key="{25ad63b8-c2ef-437d-aaef-1987365e05ac}" scalemaxdenom="25000" description="Near">
        <settings calloutType="simple">
          <text-style multilineHeight="1" previewBkgrdColor="0,0,0,255" textOpacity="1" fontUnderline="0" fontKerning="1" fontSize="8" namedStyle="Normal" fontFamily="MS Shell Dlg 2" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontCapitals="0" fontSizeUnit="Point" fontItalic="0" isExpression="1" fontLetterSpacing="0" fieldName="pow_id  +  ' - '  + t_pow_name" textOrientation="horizontal" fontStrikeout="0" textColor="217,0,143,255" blendMode="0" fontWordSpacing="0" fontWeight="50" useSubstitutions="0">
            <text-buffer bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferBlendMode="0" bufferDraw="1" bufferSize="0.8" bufferColor="255,255,255,255" bufferOpacity="1" bufferNoFill="1" bufferJoinStyle="128"/>
            <background shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthUnit="MM" shapeSizeY="0" shapeRadiiUnit="MM" shapeSizeType="0" shapeOffsetUnit="MM" shapeRadiiX="0" shapeSizeX="0" shapeBorderColor="255,255,255,255" shapeType="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeRotationType="0" shapeRadiiY="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSVGFile="" shapeRotation="0" shapeSizeUnit="MM" shapeJoinStyle="128" shapeOffsetX="0" shapeBorderWidth="2" shapeDraw="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="255,255,255,255" shapeOpacity="1" shapeOffsetY="0" shapeBlendMode="0">
              <effect type="effectStack" enabled="1">
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
                <effect type="drawSource">
                  <prop k="blend_mode" v="0"/>
                  <prop k="draw_mode" v="2"/>
                  <prop k="enabled" v="1"/>
                  <prop k="opacity" v="0.75"/>
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
              <symbol name="markerSymbol" type="marker" force_rhr="0" clip_to_extent="1" alpha="1">
                <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
                  <prop k="angle" v="0"/>
                  <prop k="color" v="183,72,75,255"/>
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
            <shadow shadowRadius="1.5" shadowRadiusAlphaOnly="0" shadowOffsetUnit="MM" shadowOffsetDist="1" shadowBlendMode="6" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowUnder="0" shadowOffsetAngle="135" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusUnit="MM" shadowOffsetGlobal="1" shadowColor="0,0,0,255" shadowDraw="0" shadowOpacity="0.7" shadowScale="100"/>
            <dd_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </dd_properties>
            <substitutions/>
          </text-style>
          <text-format wrapChar="" placeDirectionSymbol="0" addDirectionSymbol="0" leftDirectionSymbol="&lt;" rightDirectionSymbol=">" useMaxLineLengthForAutoWrap="1" multilineAlign="1" decimals="3" autoWrapLength="0" formatNumbers="0" reverseDirectionSymbol="0" plussign="0"/>
          <placement dist="2" rotationAngle="0" distUnits="MM" yOffset="0" maxCurvedCharAngleOut="-25" geometryGeneratorEnabled="0" placement="7" centroidWhole="0" geometryGenerator="" overrunDistance="0" geometryGeneratorType="PointGeometry" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" offsetUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" overrunDistanceUnit="MM" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" placementFlags="10" repeatDistanceUnits="MM" repeatDistance="0" preserveRotation="1" fitInPolygonOnly="1" centroidInside="1" maxCurvedCharAngleIn="25" layerType="PolygonGeometry" priority="5" distMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" offsetType="0" xOffset="0"/>
          <rendering zIndex="0" obstacle="1" scaleVisibility="0" upsidedownLabels="0" fontMaxPixelSize="10000" mergeLines="0" obstacleType="0" maxNumLabels="2000" displayAll="0" minFeatureSize="0" scaleMin="10000" limitNumLabels="0" labelPerPart="1" fontLimitPixelSize="0" scaleMax="1500000" obstacleFactor="0.76" drawLabels="1" fontMinPixelSize="3"/>
          <dd_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
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
              <Option name="enabled" type="QString" value="0"/>
              <Option name="lineSymbol" type="QString" value="&lt;symbol name=&quot;symbol&quot; type=&quot;line&quot; force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot; alpha=&quot;1&quot;>&lt;layer class=&quot;SimpleLine&quot; enabled=&quot;1&quot; pass=&quot;0&quot; locked=&quot;0&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
              <Option name="minLength" type="double" value="0"/>
              <Option name="minLengthMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="minLengthUnit" type="QString" value="MM"/>
              <Option name="offsetFromAnchor" type="double" value="0"/>
              <Option name="offsetFromAnchorMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="offsetFromAnchorUnit" type="QString" value="MM"/>
              <Option name="offsetFromLabel" type="double" value="0"/>
              <Option name="offsetFromLabelMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="offsetFromLabelUnit" type="QString" value="MM"/>
            </Option>
          </callout>
        </settings>
      </rule>
    </rules>
  </labeling>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory penWidth="0" lineSizeScale="3x:0,0,0,0,0,0" barWidth="5" maxScaleDenominator="1e+08" backgroundAlpha="255" labelPlacementMethod="XHeight" penAlpha="255" scaleBasedVisibility="0" lineSizeType="MM" opacity="1" scaleDependency="Area" width="15" sizeScale="3x:0,0,0,0,0,0" minScaleDenominator="0" sizeType="MM" backgroundColor="#ffffff" penColor="#000000" diagramOrientation="Up" enabled="0" rotationOffset="270" height="15" minimumSize="0">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute color="#000000" field="" label=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings placement="1" showAll="1" zIndex="0" dist="0" linePlacementFlags="18" obstacle="0" priority="0">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration type="Map">
      <Option name="QgsGeometryGapCheck" type="Map">
        <Option name="allowedGapsBuffer" type="double" value="0"/>
        <Option name="allowedGapsEnabled" type="bool" value="false"/>
        <Option name="allowedGapsLayer" type="QString" value=""/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <fieldConfiguration>
    <field name="pow_id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="pow_grp">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="t_pow_name">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" field="pow_id" index="0"/>
    <alias name="" field="pow_grp" index="1"/>
    <alias name="" field="t_pow_name" index="2"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="pow_id" applyOnUpdate="0" expression=""/>
    <default field="pow_grp" applyOnUpdate="0" expression=""/>
    <default field="t_pow_name" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint field="pow_id" notnull_strength="1" unique_strength="1" constraints="3" exp_strength="0"/>
    <constraint field="pow_grp" notnull_strength="1" unique_strength="0" constraints="1" exp_strength="0"/>
    <constraint field="t_pow_name" notnull_strength="1" unique_strength="0" constraints="1" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="pow_id" exp=""/>
    <constraint desc="" field="pow_grp" exp=""/>
    <constraint desc="" field="t_pow_name" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column name="pow_grp" type="field" hidden="0" width="-1"/>
      <column name="pow_id" type="field" hidden="0" width="-1"/>
      <column type="actions" hidden="1" width="-1"/>
      <column name="t_pow_name" type="field" hidden="0" width="-1"/>
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
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="mv_tp_id" editable="1"/>
    <field name="pow_grp" editable="1"/>
    <field name="pow_id" editable="1"/>
    <field name="t_pow_name" editable="1"/>
    <field name="t_team_name" editable="1"/>
    <field name="team_id" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="mv_tp_id" labelOnTop="0"/>
    <field name="pow_grp" labelOnTop="0"/>
    <field name="pow_id" labelOnTop="0"/>
    <field name="t_pow_name" labelOnTop="0"/>
    <field name="t_team_name" labelOnTop="0"/>
    <field name="team_id" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>mv_tp_id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
