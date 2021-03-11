<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" simplifyMaxScale="1" maxScale="0" labelsEnabled="0" simplifyDrawingHints="1" readOnly="0" simplifyLocal="1" version="3.10.11-A Coruña" simplifyAlgorithm="0" simplifyDrawingTol="1" styleCategories="AllStyleCategories" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
    <symbols>
      <symbol clip_to_extent="1" name="0" type="fill" alpha="1" force_rhr="0">
        <layer enabled="1" pass="0" class="SimpleFill" locked="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="0,0,0,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="128,128,128,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.1"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
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
  <customproperties>
    <property key="dualview/previewExpressions" value="mv_tv_id"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>2</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory penAlpha="255" sizeType="MM" height="15" lineSizeType="MM" rotationOffset="270" labelPlacementMethod="XHeight" minimumSize="0" enabled="0" barWidth="5" backgroundColor="#ffffff" lineSizeScale="3x:0,0,0,0,0,0" width="15" opacity="1" penWidth="0" backgroundAlpha="255" sizeScale="3x:0,0,0,0,0,0" minScaleDenominator="0" scaleDependency="Area" penColor="#000000" scaleBasedVisibility="0" maxScaleDenominator="1e+08" diagramOrientation="Up">
      <fontProperties style="" description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0"/>
      <attribute label="" field="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="18" showAll="1" priority="0" zIndex="0" obstacle="0" placement="1" dist="0">
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
    <checkConfiguration type="Map">
      <Option name="QgsGeometryGapCheck" type="Map">
        <Option name="allowedGapsBuffer" type="double" value="0"/>
        <Option name="allowedGapsEnabled" type="bool" value="false"/>
        <Option name="allowedGapsLayer" type="QString" value=""/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <fieldConfiguration>
    <field name="tv_id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="vn_id">
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
    <field name="b_sel">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="b_done">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="b_pow">
      <editWidget type="">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="x_row">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="y_row">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="tv_id" index="0" name=""/>
    <alias field="vn_id" index="1" name=""/>
    <alias field="user_id" index="2" name=""/>
    <alias field="b_sel" index="3" name=""/>
    <alias field="b_done" index="4" name=""/>
    <alias field="b_pow" index="5" name=""/>
    <alias field="x_row" index="6" name=""/>
    <alias field="y_row" index="7" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="tv_id" applyOnUpdate="0" expression=""/>
    <default field="vn_id" applyOnUpdate="0" expression=""/>
    <default field="user_id" applyOnUpdate="0" expression=""/>
    <default field="b_sel" applyOnUpdate="0" expression=""/>
    <default field="b_done" applyOnUpdate="0" expression=""/>
    <default field="b_pow" applyOnUpdate="0" expression=""/>
    <default field="x_row" applyOnUpdate="0" expression=""/>
    <default field="y_row" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" field="tv_id" unique_strength="1" constraints="3" notnull_strength="1"/>
    <constraint exp_strength="0" field="vn_id" unique_strength="0" constraints="1" notnull_strength="1"/>
    <constraint exp_strength="0" field="user_id" unique_strength="0" constraints="0" notnull_strength="0"/>
    <constraint exp_strength="0" field="b_sel" unique_strength="0" constraints="1" notnull_strength="1"/>
    <constraint exp_strength="0" field="b_done" unique_strength="0" constraints="1" notnull_strength="1"/>
    <constraint exp_strength="0" field="b_pow" unique_strength="0" constraints="1" notnull_strength="1"/>
    <constraint exp_strength="0" field="x_row" unique_strength="0" constraints="1" notnull_strength="1"/>
    <constraint exp_strength="0" field="y_row" unique_strength="0" constraints="1" notnull_strength="1"/>
  </constraints>
  <constraintExpressions>
    <constraint field="tv_id" desc="" exp=""/>
    <constraint field="vn_id" desc="" exp=""/>
    <constraint field="user_id" desc="" exp=""/>
    <constraint field="b_sel" desc="" exp=""/>
    <constraint field="b_done" desc="" exp=""/>
    <constraint field="b_pow" desc="" exp=""/>
    <constraint field="x_row" desc="" exp=""/>
    <constraint field="y_row" desc="" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column hidden="0" width="-1" name="vn_id" type="field"/>
      <column hidden="0" width="-1" name="user_id" type="field"/>
      <column hidden="1" width="-1" type="actions"/>
      <column hidden="0" width="-1" name="x_row" type="field"/>
      <column hidden="0" width="-1" name="y_row" type="field"/>
      <column hidden="0" width="-1" name="tv_id" type="field"/>
      <column hidden="0" width="-1" name="b_sel" type="field"/>
      <column hidden="0" width="-1" name="b_done" type="field"/>
      <column hidden="0" width="-1" name="b_pow" type="field"/>
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
    <field name="b_done" editable="1"/>
    <field name="b_pow" editable="1"/>
    <field name="b_sel" editable="1"/>
    <field name="mv_tv_id" editable="1"/>
    <field name="team_id" editable="1"/>
    <field name="tv_id" editable="1"/>
    <field name="user_id" editable="1"/>
    <field name="vn_id" editable="1"/>
    <field name="x_row" editable="1"/>
    <field name="y_row" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="b_done" labelOnTop="0"/>
    <field name="b_pow" labelOnTop="0"/>
    <field name="b_sel" labelOnTop="0"/>
    <field name="mv_tv_id" labelOnTop="0"/>
    <field name="team_id" labelOnTop="0"/>
    <field name="tv_id" labelOnTop="0"/>
    <field name="user_id" labelOnTop="0"/>
    <field name="vn_id" labelOnTop="0"/>
    <field name="x_row" labelOnTop="0"/>
    <field name="y_row" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>mv_tv_id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
