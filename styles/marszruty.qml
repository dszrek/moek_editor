<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.10.11-A Coruña" readOnly="0" hasScaleBasedVisibilityFlag="1" simplifyAlgorithm="0" simplifyDrawingTol="1" maxScale="0" simplifyLocal="1" minScale="25000" labelsEnabled="1" simplifyMaxScale="1" simplifyDrawingHints="1" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 forceraster="0" symbollevels="0" enableorderby="0" type="singleSymbol">
    <symbols>
      <symbol alpha="1" force_rhr="0" clip_to_extent="1" type="line" name="0">
        <layer enabled="1" locked="0" pass="0" class="GeometryGenerator">
          <prop k="SymbolType" v="Line"/>
          <prop k="geometryModifier" v="difference(&#xd;&#xa;  difference(&#xd;&#xa;&#x9;$geometry,&#xd;&#xa;&#x9;buffer( start_point( $geometry ), 0.0008*@map_scale)&#xd;&#xa;  ),&#xd;&#xa;buffer( end_point( $geometry ), 0.0008*@map_scale)&#xd;&#xa;)"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol alpha="1" force_rhr="0" clip_to_extent="1" type="line" name="@0@0">
            <layer enabled="1" locked="0" pass="0" class="SimpleLine">
              <prop k="capstyle" v="flat"/>
              <prop k="customdash" v="5;2"/>
              <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="customdash_unit" v="MM"/>
              <prop k="draw_inside_polygon" v="0"/>
              <prop k="joinstyle" v="round"/>
              <prop k="line_color" v="59,117,204,255"/>
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" locked="0" pass="0" class="GeometryGenerator">
          <prop k="SymbolType" v="Marker"/>
          <prop k="geometryModifier" v="end_point($geometry )&#xd;&#xa;"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol alpha="1" force_rhr="0" clip_to_extent="1" type="marker" name="@0@1">
            <layer enabled="1" locked="0" pass="0" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="59,117,204,255"/>
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
              <prop k="size" v="2.4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" locked="0" pass="0" class="GeometryGenerator">
          <prop k="SymbolType" v="Marker"/>
          <prop k="geometryModifier" v="start_point($geometry )&#xd;&#xa;"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol alpha="1" force_rhr="0" clip_to_extent="1" type="marker" name="@0@2">
            <layer enabled="1" locked="0" pass="0" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="59,117,204,255"/>
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
              <prop k="size" v="2.4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
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
      <text-style fontStrikeout="0" fontKerning="1" fontSize="9" fontWeight="50" textColor="255,255,255,255" fontItalic="0" multilineHeight="1" useSubstitutions="0" fontFamily="MS Shell Dlg 2" fontUnderline="0" textOrientation="horizontal" blendMode="0" fontCapitals="0" previewBkgrdColor="255,255,255,255" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontSizeUnit="Point" fieldName="CASE&#xd;&#xa;&#x9;WHEN &quot;marsz_m&quot; &lt; 1000 AND &quot;marsz_t&quot; &lt; 60&#xd;&#xa;&#x9;THEN ' ' + to_string(marsz_m) + ' m – ' + to_string(marsz_t) + ' sek '&#xd;&#xa;&#x9;WHEN &quot;marsz_m&quot; &lt; 1000 AND &quot;marsz_t&quot; >= 60&#xd;&#xa;&#x9;THEN ' ' + to_string(marsz_m) + ' m – ' + to_string(round(marsz_t/60,0)) + ' min '&#xd;&#xa;&#x9;WHEN &quot;marsz_m&quot; >= 1000 AND &quot;marsz_t&quot; &lt; 60&#xd;&#xa;&#x9;THEN ' ' + to_string(round(marsz_m/1000,1)) + ' km – ' + to_string(marsz_t) + ' sek '&#xd;&#xa;&#x9;WHEN &quot;marsz_m&quot; >= 1000 AND &quot;marsz_t&quot; >= 60&#xd;&#xa;&#x9;THEN ' ' + to_string(round(marsz_m/1000,1)) + ' km – ' + to_string(round(marsz_t/60,0)) + ' min '&#xd;&#xa;END" fontLetterSpacing="0" namedStyle="Normal" isExpression="1" textOpacity="1" fontWordSpacing="0">
        <text-buffer bufferBlendMode="0" bufferNoFill="0" bufferOpacity="1" bufferJoinStyle="128" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferDraw="0" bufferSize="0.6" bufferColor="255,255,255,255" bufferSizeUnits="MM"/>
        <background shapeDraw="1" shapeBorderColor="255,255,255,255" shapeRadiiUnit="MM" shapeRotationType="0" shapeType="0" shapeRotation="0" shapeOffsetY="0" shapeRadiiX="0" shapeBorderWidthUnit="MM" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSVGFile="" shapeOpacity="0.8" shapeOffsetUnit="MM" shapeSizeType="0" shapeJoinStyle="128" shapeSizeY="1.2" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="97,148,224,255" shapeSizeUnit="MM" shapeBorderWidth="0" shapeSizeX="1.2" shapeBlendMode="0" shapeOffsetX="0" shapeRadiiY="0">
          <effect enabled="0" type="effectStack">
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
          <symbol alpha="1" force_rhr="0" clip_to_extent="1" type="marker" name="markerSymbol">
            <layer enabled="1" locked="0" pass="0" class="SimpleMarker">
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadius="1.5" shadowOffsetUnit="MM" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowColor="0,0,0,255" shadowDraw="0" shadowOffsetDist="1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusAlphaOnly="0" shadowBlendMode="6" shadowRadiusUnit="MM" shadowOffsetAngle="135" shadowScale="100" shadowOffsetGlobal="1" shadowUnder="0" shadowOpacity="0.7"/>
        <dd_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format rightDirectionSymbol=">" decimals="3" autoWrapLength="0" useMaxLineLengthForAutoWrap="1" reverseDirectionSymbol="0" placeDirectionSymbol="0" multilineAlign="0" leftDirectionSymbol="&lt;" formatNumbers="0" wrapChar="" addDirectionSymbol="0" plussign="0"/>
      <placement geometryGeneratorType="PointGeometry" priority="5" repeatDistance="0" overrunDistance="0" maxCurvedCharAngleOut="-25" preserveRotation="0" offsetUnits="MM" distUnits="MM" maxCurvedCharAngleIn="25" repeatDistanceUnits="MM" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" placement="6" fitInPolygonOnly="0" distMapUnitScale="3x:0,0,0,0,0,0" layerType="LineGeometry" geometryGenerator="line_interpolate_point($geometry,$length/2)" quadOffset="4" xOffset="0" offsetType="0" rotationAngle="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" yOffset="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" placementFlags="10" geometryGeneratorEnabled="1" centroidWhole="0" dist="10" centroidInside="0" overrunDistanceUnit="MM" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering scaleMin="0" drawLabels="1" obstacle="1" minFeatureSize="0" limitNumLabels="0" labelPerPart="0" scaleVisibility="1" fontMinPixelSize="3" zIndex="0" obstacleFactor="2" upsidedownLabels="0" obstacleType="0" mergeLines="0" maxNumLabels="2000" scaleMax="25000" fontLimitPixelSize="0" fontMaxPixelSize="10000" displayAll="0"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" type="QString" name="name"/>
          <Option type="Map" name="properties">
            <Option type="Map" name="LabelRotation">
              <Option value="false" type="bool" name="active"/>
              <Option value="1" type="int" name="type"/>
              <Option value="" type="QString" name="val"/>
            </Option>
            <Option type="Map" name="OffsetQuad">
              <Option value="false" type="bool" name="active"/>
              <Option value="1" type="int" name="type"/>
              <Option value="" type="QString" name="val"/>
            </Option>
          </Option>
          <Option value="collection" type="QString" name="type"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option value="pole_of_inaccessibility" type="QString" name="anchorPoint"/>
          <Option type="Map" name="ddProperties">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
          <Option value="false" type="bool" name="drawToAllParts"/>
          <Option value="1" type="QString" name="enabled"/>
          <Option value="&lt;symbol alpha=&quot;1&quot; force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot; type=&quot;line&quot; name=&quot;symbol&quot;>&lt;layer enabled=&quot;1&quot; locked=&quot;0&quot; pass=&quot;0&quot; class=&quot;SimpleLine&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;round&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;round&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;97,148,224,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.4&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; type=&quot;QString&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; type=&quot;QString&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" type="QString" name="lineSymbol"/>
          <Option value="0" type="double" name="minLength"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="minLengthMapUnitScale"/>
          <Option value="MM" type="QString" name="minLengthUnit"/>
          <Option value="0.5" type="double" name="offsetFromAnchor"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="offsetFromAnchorMapUnitScale"/>
          <Option value="MM" type="QString" name="offsetFromAnchorUnit"/>
          <Option value="1.5" type="double" name="offsetFromLabel"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="offsetFromLabelMapUnitScale"/>
          <Option value="MM" type="QString" name="offsetFromLabelUnit"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>5</featureBlendMode>
  <layerOpacity>0.75</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory opacity="1" minimumSize="0" penWidth="0" enabled="0" width="15" lineSizeScale="3x:0,0,0,0,0,0" sizeType="MM" sizeScale="3x:0,0,0,0,0,0" penAlpha="255" rotationOffset="270" barWidth="5" labelPlacementMethod="XHeight" height="15" backgroundAlpha="255" backgroundColor="#ffffff" minScaleDenominator="0" maxScaleDenominator="1e+08" scaleBasedVisibility="0" lineSizeType="MM" penColor="#000000" scaleDependency="Area" diagramOrientation="Up">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute color="#000000" label="" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings showAll="1" obstacle="0" priority="0" dist="0" placement="2" linePlacementFlags="18" zIndex="0">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
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
    <alias field="marsz_id" index="0" name=""/>
    <alias field="user_id" index="1" name=""/>
    <alias field="marsz_m" index="2" name=""/>
    <alias field="marsz_t" index="3" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="marsz_id" expression=""/>
    <default applyOnUpdate="0" field="user_id" expression=""/>
    <default applyOnUpdate="0" field="marsz_m" expression=""/>
    <default applyOnUpdate="0" field="marsz_t" expression=""/>
  </defaults>
  <constraints>
    <constraint field="marsz_id" unique_strength="1" constraints="3" exp_strength="0" notnull_strength="1"/>
    <constraint field="user_id" unique_strength="0" constraints="1" exp_strength="0" notnull_strength="1"/>
    <constraint field="marsz_m" unique_strength="0" constraints="1" exp_strength="0" notnull_strength="1"/>
    <constraint field="marsz_t" unique_strength="0" constraints="1" exp_strength="0" notnull_strength="1"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="marsz_id"/>
    <constraint desc="" exp="" field="user_id"/>
    <constraint desc="" exp="" field="marsz_m"/>
    <constraint desc="" exp="" field="marsz_t"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column width="-1" hidden="0" type="field" name="marsz_id"/>
      <column width="-1" hidden="0" type="field" name="user_id"/>
      <column width="-1" hidden="0" type="field" name="marsz_m"/>
      <column width="-1" hidden="0" type="field" name="marsz_t"/>
      <column width="-1" hidden="1" type="actions"/>
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
    <field labelOnTop="0" name="marsz_id"/>
    <field labelOnTop="0" name="marsz_m"/>
    <field labelOnTop="0" name="marsz_t"/>
    <field labelOnTop="0" name="user_id"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>"marsz_id"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
