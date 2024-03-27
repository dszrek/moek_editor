<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="0" simplifyMaxScale="1" simplifyLocal="1" hasScaleBasedVisibilityFlag="0" readOnly="0" styleCategories="AllStyleCategories" version="3.10.11-A Coruña" minScale="1e+08" simplifyDrawingTol="1" simplifyAlgorithm="0" labelsEnabled="0" simplifyDrawingHints="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="nullSymbol"/>
  <customproperties>
    <property value="&quot;wyr_id&quot;" key="dualview/previewExpressions"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory lineSizeScale="3x:0,0,0,0,0,0" scaleDependency="Area" maxScaleDenominator="1e+08" penWidth="0" width="15" penAlpha="255" opacity="1" minimumSize="0" enabled="0" labelPlacementMethod="XHeight" height="15" minScaleDenominator="0" penColor="#000000" sizeType="MM" backgroundColor="#ffffff" scaleBasedVisibility="0" barWidth="5" sizeScale="3x:0,0,0,0,0,0" diagramOrientation="Up" backgroundAlpha="255" rotationOffset="270" lineSizeType="MM">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute label="" field="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="18" zIndex="0" showAll="1" priority="0" dist="0" placement="0" obstacle="0">
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
    <field name="wyr_id">
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
    <field name="order_id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="t_wyr_od">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="t_wyr_do">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="i_area_m2">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="b_wn">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="b_zloze">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="b_new">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="b_confirmed">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="date_ctrl">
      <editWidget type="DateTime">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="time_fchk">
      <editWidget type="DateTime">
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
    <alias index="0" field="wyr_id" name=""/>
    <alias index="1" field="user_id" name=""/>
    <alias index="2" field="order_id" name=""/>
    <alias index="3" field="t_wyr_od" name=""/>
    <alias index="4" field="t_wyr_do" name=""/>
    <alias index="5" field="i_area_m2" name=""/>
    <alias index="6" field="b_wn" name=""/>
    <alias index="7" field="b_zloze" name=""/>
    <alias index="8" field="b_new" name=""/>
    <alias index="9" field="b_confirmed" name=""/>
    <alias index="10" field="date_ctrl" name=""/>
    <alias index="11" field="time_fchk" name=""/>
    <alias index="12" field="t_notatki" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="wyr_id" expression="" applyOnUpdate="0"/>
    <default field="user_id" expression="" applyOnUpdate="0"/>
    <default field="order_id" expression="" applyOnUpdate="0"/>
    <default field="t_wyr_od" expression="" applyOnUpdate="0"/>
    <default field="t_wyr_do" expression="" applyOnUpdate="0"/>
    <default field="i_area_m2" expression="" applyOnUpdate="0"/>
    <default field="b_wn" expression="" applyOnUpdate="0"/>
    <default field="b_zloze" expression="" applyOnUpdate="0"/>
    <default field="b_new" expression="" applyOnUpdate="0"/>
    <default field="b_confirmed" expression="" applyOnUpdate="0"/>
    <default field="date_ctrl" expression="" applyOnUpdate="0"/>
    <default field="time_fchk" expression="" applyOnUpdate="0"/>
    <default field="t_notatki" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint constraints="3" unique_strength="1" notnull_strength="1" field="wyr_id" exp_strength="0"/>
    <constraint constraints="1" unique_strength="0" notnull_strength="1" field="user_id" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="order_id" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="t_wyr_od" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="t_wyr_do" exp_strength="0"/>
    <constraint constraints="1" unique_strength="0" notnull_strength="1" field="i_area_m2" exp_strength="0"/>
    <constraint constraints="1" unique_strength="0" notnull_strength="1" field="b_wn" exp_strength="0"/>
    <constraint constraints="1" unique_strength="0" notnull_strength="1" field="b_zloze" exp_strength="0"/>
    <constraint constraints="1" unique_strength="0" notnull_strength="1" field="b_new" exp_strength="0"/>
    <constraint constraints="1" unique_strength="0" notnull_strength="1" field="b_confirmed" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="date_ctrl" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="time_fchk" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="t_notatki" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="wyr_id" desc="" exp=""/>
    <constraint field="user_id" desc="" exp=""/>
    <constraint field="order_id" desc="" exp=""/>
    <constraint field="t_wyr_od" desc="" exp=""/>
    <constraint field="t_wyr_do" desc="" exp=""/>
    <constraint field="i_area_m2" desc="" exp=""/>
    <constraint field="b_wn" desc="" exp=""/>
    <constraint field="b_zloze" desc="" exp=""/>
    <constraint field="b_new" desc="" exp=""/>
    <constraint field="b_confirmed" desc="" exp=""/>
    <constraint field="date_ctrl" desc="" exp=""/>
    <constraint field="time_fchk" desc="" exp=""/>
    <constraint field="t_notatki" desc="" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column width="-1" type="field" hidden="0" name="wyr_id"/>
      <column width="-1" type="field" hidden="0" name="user_id"/>
      <column width="-1" type="field" hidden="0" name="t_wyr_od"/>
      <column width="-1" type="field" hidden="0" name="t_wyr_do"/>
      <column width="-1" type="field" hidden="0" name="i_area_m2"/>
      <column width="-1" type="field" hidden="0" name="b_wn"/>
      <column width="-1" type="field" hidden="0" name="b_zloze"/>
      <column width="-1" type="field" hidden="0" name="b_new"/>
      <column width="-1" type="field" hidden="0" name="b_confirmed"/>
      <column width="-1" type="field" hidden="0" name="date_ctrl"/>
      <column width="-1" type="field" hidden="0" name="time_fchk"/>
      <column width="-1" type="actions" hidden="1"/>
      <column width="-1" type="field" hidden="0" name="order_id"/>
      <column width="-1" type="field" hidden="0" name="t_notatki"/>
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
    <field editable="1" name="b_new"/>
    <field editable="1" name="b_confirmed"/>
    <field editable="1" name="b_wn"/>
    <field editable="1" name="b_zloze"/>
    <field editable="1" name="date_ctrl"/>
    <field editable="1" name="i_area_m2"/>
    <field editable="1" name="order_id"/>
    <field editable="1" name="t_notatki"/>
    <field editable="1" name="t_wyr_do"/>
    <field editable="1" name="t_wyr_od"/>
    <field editable="1" name="time_fchk"/>
    <field editable="1" name="user_id"/>
    <field editable="1" name="wyr_id"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="b_new"/>
    <field labelOnTop="0" name="b_confirmed"/>
    <field labelOnTop="0" name="b_wn"/>
    <field labelOnTop="0" name="b_zloze"/>
    <field labelOnTop="0" name="date_ctrl"/>
    <field labelOnTop="0" name="i_area_m2"/>
    <field labelOnTop="0" name="order_id"/>
    <field labelOnTop="0" name="t_notatki"/>
    <field labelOnTop="0" name="t_wyr_do"/>
    <field labelOnTop="0" name="t_wyr_od"/>
    <field labelOnTop="0" name="time_fchk"/>
    <field labelOnTop="0" name="user_id"/>
    <field labelOnTop="0" name="wyr_id"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>"wyr_id"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
