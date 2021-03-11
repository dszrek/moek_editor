<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="1" simplifyMaxScale="1" maxScale="0" labelsEnabled="0" simplifyDrawingHints="0" readOnly="0" simplifyLocal="1" version="3.10.11-A Coruña" simplifyAlgorithm="0" simplifyDrawingTol="1" styleCategories="AllStyleCategories" minScale="500000">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 toleranceUnitScale="3x:0,0,0,0,0,0" type="pointCluster" tolerance="6" enableorderby="0" forceraster="0" toleranceUnit="MM">
    <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
      <symbols>
        <symbol clip_to_extent="1" name="0" type="marker" alpha="1" force_rhr="0">
          <layer enabled="1" pass="0" class="SimpleMarker" locked="0">
            <prop k="angle" v="0"/>
            <prop k="color" v="0,0,0,153"/>
            <prop k="horizontal_anchor_point" v="1"/>
            <prop k="joinstyle" v="bevel"/>
            <prop k="name" v="circle"/>
            <prop k="offset" v="0,0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="outline_color" v="255,255,255,255"/>
            <prop k="outline_style" v="solid"/>
            <prop k="outline_width" v="0.2"/>
            <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="outline_width_unit" v="MM"/>
            <prop k="scale_method" v="diameter"/>
            <prop k="size" v="11"/>
            <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="size_unit" v="MM"/>
            <prop k="vertical_anchor_point" v="1"/>
            <effect enabled="1" type="effectStack">
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
                <prop k="blur_level" v="2.116"/>
                <prop k="blur_unit" v="MM"/>
                <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
                <prop k="color1" v="0,0,255,255"/>
                <prop k="color2" v="0,255,0,255"/>
                <prop k="color_type" v="0"/>
                <prop k="discrete" v="0"/>
                <prop k="draw_mode" v="2"/>
                <prop k="enabled" v="1"/>
                <prop k="opacity" v="0.7"/>
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
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties" type="Map">
                  <Option name="enabled" type="Map">
                    <Option name="active" type="bool" value="true"/>
                    <Option name="expression" type="QString" value="if( to_int( @flag_sel ) = id and @flag_hidden IS NULL, 1, 0)"/>
                    <Option name="type" type="int" value="3"/>
                  </Option>
                  <Option name="fillColor" type="Map">
                    <Option name="active" type="bool" value="false"/>
                    <Option name="type" type="int" value="1"/>
                    <Option name="val" type="QString" value=""/>
                  </Option>
                  <Option name="outlineStyle" type="Map">
                    <Option name="active" type="bool" value="false"/>
                    <Option name="type" type="int" value="1"/>
                    <Option name="val" type="QString" value=""/>
                  </Option>
                </Option>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
          </layer>
          <layer enabled="1" pass="0" class="RasterMarker" locked="0">
            <prop k="alpha" v="1"/>
            <prop k="angle" v="0"/>
            <prop k="fixedAspectRatio" v="0"/>
            <prop k="horizontal_anchor_point" v="1"/>
            <prop k="imageFile" v="base64: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"/>
            <prop k="offset" v="0,0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="scale_method" v="diameter"/>
            <prop k="size" v="50"/>
            <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="size_unit" v="Pixel"/>
            <prop k="vertical_anchor_point" v="1"/>
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties" type="Map">
                  <Option name="alpha" type="Map">
                    <Option name="active" type="bool" value="true"/>
                    <Option name="expression" type="QString" value="if( to_int( @flag_hidden ) = id, 40.0, 100.0)"/>
                    <Option name="type" type="int" value="3"/>
                  </Option>
                  <Option name="enabled" type="Map">
                    <Option name="active" type="bool" value="false"/>
                    <Option name="type" type="int" value="1"/>
                    <Option name="val" type="QString" value=""/>
                  </Option>
                </Option>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
          </layer>
          <layer enabled="1" pass="0" class="RasterMarker" locked="0">
            <prop k="alpha" v="1"/>
            <prop k="angle" v="0"/>
            <prop k="fixedAspectRatio" v="0"/>
            <prop k="horizontal_anchor_point" v="1"/>
            <prop k="imageFile" v="base64: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"/>
            <prop k="offset" v="0,0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="scale_method" v="diameter"/>
            <prop k="size" v="50"/>
            <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="size_unit" v="Pixel"/>
            <prop k="vertical_anchor_point" v="1"/>
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties" type="Map">
                  <Option name="enabled" type="Map">
                    <Option name="active" type="bool" value="true"/>
                    <Option name="expression" type="QString" value="if( @flag_hidden IS NULL and (length( t_notatki )  > 0 ), 1, 0)"/>
                    <Option name="type" type="int" value="3"/>
                  </Option>
                </Option>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </symbols>
      <rotation/>
      <sizescale/>
    </renderer-v2>
    <symbol clip_to_extent="1" name="centerSymbol" type="marker" alpha="1" force_rhr="0">
      <layer enabled="1" pass="0" class="RasterMarker" locked="0">
        <prop k="alpha" v="1"/>
        <prop k="angle" v="0"/>
        <prop k="fixedAspectRatio" v="0"/>
        <prop k="horizontal_anchor_point" v="1"/>
        <prop k="imageFile" v="base64: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"/>
        <prop k="offset" v="0,0"/>
        <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="offset_unit" v="MM"/>
        <prop k="scale_method" v="diameter"/>
        <prop k="size" v="26"/>
        <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="size_unit" v="Pixel"/>
        <prop k="vertical_anchor_point" v="1"/>
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
      </layer>
      <layer enabled="1" pass="0" class="FontMarker" locked="0">
        <prop k="angle" v="0"/>
        <prop k="chr" v="A"/>
        <prop k="color" v="255,127,0,255"/>
        <prop k="font" v="MS Shell Dlg 2"/>
        <prop k="horizontal_anchor_point" v="1"/>
        <prop k="joinstyle" v="miter"/>
        <prop k="offset" v="0,-0.40000000000000002"/>
        <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="offset_unit" v="MM"/>
        <prop k="outline_color" v="255,127,0,255"/>
        <prop k="outline_width" v="0.2"/>
        <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="outline_width_unit" v="MM"/>
        <prop k="size" v="2.6"/>
        <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="size_unit" v="MM"/>
        <prop k="vertical_anchor_point" v="1"/>
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties" type="Map">
              <Option name="char" type="Map">
                <Option name="active" type="bool" value="true"/>
                <Option name="expression" type="QString" value="@cluster_size"/>
                <Option name="type" type="int" value="3"/>
              </Option>
              <Option name="fillColor" type="Map">
                <Option name="active" type="bool" value="false"/>
                <Option name="type" type="int" value="1"/>
                <Option name="val" type="QString" value=""/>
              </Option>
              <Option name="outlineColor" type="Map">
                <Option name="active" type="bool" value="false"/>
                <Option name="type" type="int" value="1"/>
                <Option name="val" type="QString" value=""/>
              </Option>
            </Option>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
      </layer>
    </symbol>
  </renderer-v2>
  <customproperties>
    <property key="dualview/previewExpressions" value="&quot;id&quot;"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory penAlpha="255" sizeType="MM" height="15" lineSizeType="MM" rotationOffset="270" labelPlacementMethod="XHeight" minimumSize="0" enabled="0" barWidth="5" backgroundColor="#ffffff" lineSizeScale="3x:0,0,0,0,0,0" width="15" opacity="1" penWidth="0" backgroundAlpha="255" sizeScale="3x:0,0,0,0,0,0" minScaleDenominator="0" scaleDependency="Area" penColor="#000000" scaleBasedVisibility="0" maxScaleDenominator="1e+08" diagramOrientation="Up">
      <fontProperties style="" description="MS Shell Dlg 2,9.75,-1,5,50,0,0,0,0,0"/>
      <attribute label="" field="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="18" showAll="1" priority="0" zIndex="0" obstacle="0" placement="0" dist="0">
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
    <field name="id">
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
    <field name="pow_grp">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="b_fieldcheck">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="t_notatki">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="id" index="0" name=""/>
    <alias field="user_id" index="1" name=""/>
    <alias field="pow_grp" index="2" name=""/>
    <alias field="b_fieldcheck" index="3" name=""/>
    <alias field="t_notatki" index="4" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="id" applyOnUpdate="0" expression=""/>
    <default field="user_id" applyOnUpdate="0" expression=""/>
    <default field="pow_grp" applyOnUpdate="0" expression=""/>
    <default field="b_fieldcheck" applyOnUpdate="0" expression=""/>
    <default field="t_notatki" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" field="id" unique_strength="1" constraints="3" notnull_strength="1"/>
    <constraint exp_strength="0" field="user_id" unique_strength="0" constraints="1" notnull_strength="1"/>
    <constraint exp_strength="0" field="pow_grp" unique_strength="0" constraints="1" notnull_strength="1"/>
    <constraint exp_strength="0" field="b_fieldcheck" unique_strength="0" constraints="1" notnull_strength="1"/>
    <constraint exp_strength="0" field="t_notatki" unique_strength="0" constraints="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="id" desc="" exp=""/>
    <constraint field="user_id" desc="" exp=""/>
    <constraint field="pow_grp" desc="" exp=""/>
    <constraint field="b_fieldcheck" desc="" exp=""/>
    <constraint field="t_notatki" desc="" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="&quot;id&quot;" sortOrder="0">
    <columns>
      <column hidden="0" width="-1" name="id" type="field"/>
      <column hidden="0" width="-1" name="user_id" type="field"/>
      <column hidden="0" width="-1" name="b_fieldcheck" type="field"/>
      <column hidden="1" width="-1" type="actions"/>
      <column hidden="0" width="-1" name="pow_grp" type="field"/>
      <column hidden="0" width="-1" name="t_notatki" type="field"/>
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
    <field name="b_fieldcheck" editable="1"/>
    <field name="id" editable="1"/>
    <field name="pow_grp" editable="1"/>
    <field name="t_notatki" editable="1"/>
    <field name="user_id" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="b_fieldcheck" labelOnTop="0"/>
    <field name="id" labelOnTop="0"/>
    <field name="pow_grp" labelOnTop="0"/>
    <field name="t_notatki" labelOnTop="0"/>
    <field name="user_id" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>"id"</previewExpression>
  <mapTip>[% flag_chg1() %]</mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
