<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" simplifyAlgorithm="0" readOnly="0" hasScaleBasedVisibilityFlag="1" maxScale="0" minScale="300000" simplifyMaxScale="1" labelsEnabled="1" simplifyDrawingTol="1" version="3.10.11-A Coruña" simplifyDrawingHints="0" simplifyLocal="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 toleranceUnit="MM" type="pointCluster" enableorderby="0" forceraster="0" tolerance="8" toleranceUnitScale="3x:0,0,0,0,0,0">
    <renderer-v2 type="singleSymbol" enableorderby="0" forceraster="0" symbollevels="0">
      <symbols>
        <symbol force_rhr="0" clip_to_extent="1" type="marker" alpha="0.75" name="0">
          <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
            <prop k="angle" v="0"/>
            <prop k="color" v="0,0,0,204"/>
            <prop k="horizontal_anchor_point" v="1"/>
            <prop k="joinstyle" v="round"/>
            <prop k="name" v="equilateral_triangle"/>
            <prop k="offset" v="0,0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="outline_color" v="255,255,255,255"/>
            <prop k="outline_style" v="solid"/>
            <prop k="outline_width" v="0.2"/>
            <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="outline_width_unit" v="MM"/>
            <prop k="scale_method" v="diameter"/>
            <prop k="size" v="12.2"/>
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
                <Option type="QString" value="" name="name"/>
                <Option type="Map" name="properties">
                  <Option type="Map" name="enabled">
                    <Option type="bool" value="true" name="active"/>
                    <Option type="QString" value="if( to_string( @wn_sel ) = id_arkusz, 1, 0)" name="expression"/>
                    <Option type="int" value="3" name="type"/>
                  </Option>
                </Option>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
          <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
            <prop k="angle" v="0"/>
            <prop k="color" v="255,255,255,255"/>
            <prop k="horizontal_anchor_point" v="1"/>
            <prop k="joinstyle" v="miter"/>
            <prop k="name" v="equilateral_triangle"/>
            <prop k="offset" v="0,0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="outline_color" v="255,255,255,255"/>
            <prop k="outline_style" v="solid"/>
            <prop k="outline_width" v="1"/>
            <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="outline_width_unit" v="MM"/>
            <prop k="scale_method" v="area"/>
            <prop k="size" v="5"/>
            <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="size_unit" v="MM"/>
            <prop k="vertical_anchor_point" v="1"/>
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
                <prop k="opacity" v="1"/>
                <prop k="rampType" v="gradient"/>
                <prop k="single_color" v="255,255,255,255"/>
                <prop k="spread" v="0.66"/>
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
                <prop k="blur_level" v="0.7935"/>
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
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
          <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
            <prop k="angle" v="0"/>
            <prop k="color" v="223,134,0,255"/>
            <prop k="horizontal_anchor_point" v="1"/>
            <prop k="joinstyle" v="miter"/>
            <prop k="name" v="equilateral_triangle"/>
            <prop k="offset" v="0,0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="outline_color" v="0,0,0,255"/>
            <prop k="outline_style" v="solid"/>
            <prop k="outline_width" v="0.4"/>
            <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="outline_width_unit" v="MM"/>
            <prop k="scale_method" v="area"/>
            <prop k="size" v="5"/>
            <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="size_unit" v="MM"/>
            <prop k="vertical_anchor_point" v="1"/>
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
                <prop k="opacity" v="1"/>
                <prop k="rampType" v="gradient"/>
                <prop k="single_color" v="255,255,255,255"/>
                <prop k="spread" v="0.66"/>
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
                <prop k="blur_level" v="0.7935"/>
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
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </symbols>
      <rotation/>
      <sizescale/>
    </renderer-v2>
    <symbol force_rhr="0" clip_to_extent="1" type="marker" alpha="0.75" name="centerSymbol">
      <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
        <prop k="angle" v="0"/>
        <prop k="color" v="255,255,255,255"/>
        <prop k="horizontal_anchor_point" v="1"/>
        <prop k="joinstyle" v="miter"/>
        <prop k="name" v="equilateral_triangle"/>
        <prop k="offset" v="0,0"/>
        <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="offset_unit" v="MM"/>
        <prop k="outline_color" v="255,255,255,255"/>
        <prop k="outline_style" v="solid"/>
        <prop k="outline_width" v="1"/>
        <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="outline_width_unit" v="MM"/>
        <prop k="scale_method" v="area"/>
        <prop k="size" v="5"/>
        <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="size_unit" v="MM"/>
        <prop k="vertical_anchor_point" v="1"/>
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
            <prop k="opacity" v="1"/>
            <prop k="rampType" v="gradient"/>
            <prop k="single_color" v="255,255,255,255"/>
            <prop k="spread" v="0.66"/>
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
            <prop k="blur_level" v="0.7935"/>
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
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
      </layer>
      <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
        <prop k="angle" v="0"/>
        <prop k="color" v="223,134,0,255"/>
        <prop k="horizontal_anchor_point" v="1"/>
        <prop k="joinstyle" v="miter"/>
        <prop k="name" v="equilateral_triangle"/>
        <prop k="offset" v="0,0"/>
        <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="offset_unit" v="MM"/>
        <prop k="outline_color" v="0,0,0,255"/>
        <prop k="outline_style" v="solid"/>
        <prop k="outline_width" v="0.4"/>
        <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="outline_width_unit" v="MM"/>
        <prop k="scale_method" v="area"/>
        <prop k="size" v="5"/>
        <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="size_unit" v="MM"/>
        <prop k="vertical_anchor_point" v="1"/>
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
            <prop k="opacity" v="1"/>
            <prop k="rampType" v="gradient"/>
            <prop k="single_color" v="255,255,255,255"/>
            <prop k="spread" v="0.66"/>
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
            <prop k="blur_level" v="0.7935"/>
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
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
      </layer>
      <layer pass="0" enabled="1" locked="0" class="FontMarker">
        <prop k="angle" v="0"/>
        <prop k="chr" v="A"/>
        <prop k="color" v="0,0,0,255"/>
        <prop k="font" v="Dingbats"/>
        <prop k="horizontal_anchor_point" v="1"/>
        <prop k="joinstyle" v="bevel"/>
        <prop k="offset" v="0,-0.5"/>
        <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="offset_unit" v="MM"/>
        <prop k="outline_color" v="35,35,35,255"/>
        <prop k="outline_width" v="0"/>
        <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="outline_width_unit" v="MM"/>
        <prop k="size" v="2"/>
        <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
        <prop k="size_unit" v="MM"/>
        <prop k="vertical_anchor_point" v="1"/>
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option type="Map" name="properties">
              <Option type="Map" name="char">
                <Option type="bool" value="true" name="active"/>
                <Option type="QString" value="@cluster_size" name="expression"/>
                <Option type="int" value="3" name="type"/>
              </Option>
            </Option>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
      </layer>
    </symbol>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style previewBkgrdColor="255,255,255,255" textOrientation="horizontal" fontWeight="50" fontLetterSpacing="0" blendMode="0" isExpression="0" fontUnderline="0" textColor="255,156,56,255" multilineHeight="1" textOpacity="1" fontFamily="MS Shell Dlg 2" useSubstitutions="0" fontStrikeout="0" fontWordSpacing="0" fieldName="id_arkusz" namedStyle="Normal" fontCapitals="0" fontSize="10" fontSizeUnit="Point" fontItalic="0" fontKerning="1" fontSizeMapUnitScale="3x:0,0,0,0,0,0">
        <text-buffer bufferColor="0,0,0,255" bufferSize="0.5" bufferNoFill="1" bufferBlendMode="0" bufferDraw="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferJoinStyle="128" bufferOpacity="1" bufferSizeUnits="MM"/>
        <background shapeDraw="0" shapeSVGFile="" shapeRadiiY="0" shapeOffsetUnit="MM" shapeType="1" shapeSizeX="0" shapeFillColor="255,255,255,255" shapeSizeUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeBlendMode="0" shapeRotationType="0" shapeRadiiUnit="MM" shapeOffsetY="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64" shapeSizeType="0" shapeBorderWidthUnit="MM" shapeOffsetX="0" shapeRadiiX="0" shapeSizeY="0" shapeBorderWidth="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeBorderColor="128,128,128,255" shapeOpacity="1" shapeRotation="0">
          <symbol force_rhr="0" clip_to_extent="1" type="marker" alpha="1" name="markerSymbol">
            <layer pass="0" enabled="1" locked="0" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="125,139,143,255"/>
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
                  <Option type="QString" value="" name="name"/>
                  <Option name="properties"/>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadiusAlphaOnly="0" shadowRadiusUnit="MM" shadowOpacity="1" shadowOffsetAngle="135" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowOffsetDist="0" shadowOffsetUnit="MM" shadowDraw="0" shadowUnder="0" shadowColor="255,255,255,255" shadowOffsetGlobal="1" shadowRadius="0.1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowBlendMode="1"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format rightDirectionSymbol=">" reverseDirectionSymbol="0" placeDirectionSymbol="0" plussign="0" addDirectionSymbol="0" leftDirectionSymbol="&lt;" formatNumbers="0" autoWrapLength="0" useMaxLineLengthForAutoWrap="1" multilineAlign="3" decimals="3" wrapChar=""/>
      <placement distMapUnitScale="3x:0,0,0,0,0,0" placement="0" distUnits="MM" yOffset="0" geometryGenerator="" rotationAngle="0" offsetType="0" repeatDistanceUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" preserveRotation="1" geometryGeneratorEnabled="0" xOffset="0" placementFlags="10" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" fitInPolygonOnly="0" layerType="PointGeometry" overrunDistanceUnit="MM" centroidInside="0" dist="6" centroidWhole="0" maxCurvedCharAngleIn="25" overrunDistance="0" quadOffset="4" geometryGeneratorType="PointGeometry" offsetUnits="MM" priority="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleOut="-25" repeatDistance="0"/>
      <rendering fontMinPixelSize="3" drawLabels="1" obstacleType="0" minFeatureSize="0" labelPerPart="0" obstacleFactor="2" obstacle="1" maxNumLabels="2000" displayAll="0" upsidedownLabels="0" fontLimitPixelSize="0" scaleMax="120000" scaleVisibility="1" limitNumLabels="0" zIndex="0" scaleMin="0" fontMaxPixelSize="10000" mergeLines="0"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" value="" name="name"/>
          <Option name="properties"/>
          <Option type="QString" value="collection" name="type"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option type="QString" value="pole_of_inaccessibility" name="anchorPoint"/>
          <Option type="Map" name="ddProperties">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
          <Option type="bool" value="false" name="drawToAllParts"/>
          <Option type="QString" value="1" name="enabled"/>
          <Option type="QString" value="&lt;symbol force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot; type=&quot;line&quot; alpha=&quot;1&quot; name=&quot;symbol&quot;>&lt;layer pass=&quot;0&quot; enabled=&quot;1&quot; locked=&quot;0&quot; class=&quot;SimpleLine&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;round&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;35,35,35,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;1&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;layer pass=&quot;0&quot; enabled=&quot;1&quot; locked=&quot;0&quot; class=&quot;SimpleLine&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;round&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;round&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;255,127,0,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol"/>
          <Option type="double" value="0" name="minLength"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="minLengthMapUnitScale"/>
          <Option type="QString" value="MM" name="minLengthUnit"/>
          <Option type="double" value="3" name="offsetFromAnchor"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="offsetFromAnchorMapUnitScale"/>
          <Option type="QString" value="MM" name="offsetFromAnchorUnit"/>
          <Option type="double" value="0" name="offsetFromLabel"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="offsetFromLabelMapUnitScale"/>
          <Option type="QString" value="MM" name="offsetFromLabelUnit"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <customproperties>
    <property value="COALESCE( &quot;ID_ARKUSZ&quot;, '&lt;NULL>' )" key="dualview/previewExpressions"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory enabled="0" width="15" penWidth="0" height="15" scaleDependency="Area" scaleBasedVisibility="0" opacity="1" backgroundAlpha="255" rotationOffset="270" sizeScale="3x:0,0,0,0,0,0" lineSizeScale="3x:0,0,0,0,0,0" diagramOrientation="Up" minScaleDenominator="0" labelPlacementMethod="XHeight" penAlpha="255" sizeType="MM" maxScaleDenominator="1e+08" backgroundColor="#ffffff" penColor="#000000" barWidth="5" minimumSize="0" lineSizeType="MM">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute label="" color="#000000" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings showAll="1" obstacle="0" dist="0" priority="0" zIndex="0" linePlacementFlags="18" placement="0">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
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
    <field name="id_arkusz">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="kopalina">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="wyrobisko">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="zawodn">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="eksploat">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="wyp_odpady">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="nadkl_min">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="nadkl_max">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="nadkl_sr">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="miazsz_min">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="miazsz_max">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="dlug_max">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="szer_max">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="wys_min">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="wys_max">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="data_kontrol">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="uwagi">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="id"/>
    <alias index="1" name="" field="id_arkusz"/>
    <alias index="2" name="" field="kopalina"/>
    <alias index="3" name="" field="wyrobisko"/>
    <alias index="4" name="" field="zawodn"/>
    <alias index="5" name="" field="eksploat"/>
    <alias index="6" name="" field="wyp_odpady"/>
    <alias index="7" name="" field="nadkl_min"/>
    <alias index="8" name="" field="nadkl_max"/>
    <alias index="9" name="" field="nadkl_sr"/>
    <alias index="10" name="" field="miazsz_min"/>
    <alias index="11" name="" field="miazsz_max"/>
    <alias index="12" name="" field="dlug_max"/>
    <alias index="13" name="" field="szer_max"/>
    <alias index="14" name="" field="wys_min"/>
    <alias index="15" name="" field="wys_max"/>
    <alias index="16" name="" field="data_kontrol"/>
    <alias index="17" name="" field="uwagi"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="id" expression=""/>
    <default applyOnUpdate="0" field="id_arkusz" expression=""/>
    <default applyOnUpdate="0" field="kopalina" expression=""/>
    <default applyOnUpdate="0" field="wyrobisko" expression=""/>
    <default applyOnUpdate="0" field="zawodn" expression=""/>
    <default applyOnUpdate="0" field="eksploat" expression=""/>
    <default applyOnUpdate="0" field="wyp_odpady" expression=""/>
    <default applyOnUpdate="0" field="nadkl_min" expression=""/>
    <default applyOnUpdate="0" field="nadkl_max" expression=""/>
    <default applyOnUpdate="0" field="nadkl_sr" expression=""/>
    <default applyOnUpdate="0" field="miazsz_min" expression=""/>
    <default applyOnUpdate="0" field="miazsz_max" expression=""/>
    <default applyOnUpdate="0" field="dlug_max" expression=""/>
    <default applyOnUpdate="0" field="szer_max" expression=""/>
    <default applyOnUpdate="0" field="wys_min" expression=""/>
    <default applyOnUpdate="0" field="wys_max" expression=""/>
    <default applyOnUpdate="0" field="data_kontrol" expression=""/>
    <default applyOnUpdate="0" field="uwagi" expression=""/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" constraints="3" field="id" notnull_strength="1" unique_strength="1"/>
    <constraint exp_strength="0" constraints="1" field="id_arkusz" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="kopalina" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="wyrobisko" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" field="zawodn" notnull_strength="0" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="eksploat" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="wyp_odpady" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="nadkl_min" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="nadkl_max" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="nadkl_sr" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="miazsz_min" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="miazsz_max" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="dlug_max" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="szer_max" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="wys_min" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="wys_max" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="1" field="data_kontrol" notnull_strength="1" unique_strength="0"/>
    <constraint exp_strength="0" constraints="0" field="uwagi" notnull_strength="0" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="id"/>
    <constraint desc="" exp="" field="id_arkusz"/>
    <constraint desc="" exp="" field="kopalina"/>
    <constraint desc="" exp="" field="wyrobisko"/>
    <constraint desc="" exp="" field="zawodn"/>
    <constraint desc="" exp="" field="eksploat"/>
    <constraint desc="" exp="" field="wyp_odpady"/>
    <constraint desc="" exp="" field="nadkl_min"/>
    <constraint desc="" exp="" field="nadkl_max"/>
    <constraint desc="" exp="" field="nadkl_sr"/>
    <constraint desc="" exp="" field="miazsz_min"/>
    <constraint desc="" exp="" field="miazsz_max"/>
    <constraint desc="" exp="" field="dlug_max"/>
    <constraint desc="" exp="" field="szer_max"/>
    <constraint desc="" exp="" field="wys_min"/>
    <constraint desc="" exp="" field="wys_max"/>
    <constraint desc="" exp="" field="data_kontrol"/>
    <constraint desc="" exp="" field="uwagi"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{ba24fa0c-2825-4c91-bb6f-ea38a0492b54}" key="Canvas"/>
    <actionsetting isEnabledOnlyWhenEditable="0" shortTitle="" type="0" id="{ba24fa0c-2825-4c91-bb6f-ea38a0492b54}" icon="" name="" action="" notificationMessage="" capture="0">
      <actionScope id="Feature"/>
      <actionScope id="Canvas"/>
      <actionScope id="Field"/>
    </actionsetting>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="&quot;id_arkusz&quot;" actionWidgetStyle="dropDown">
    <columns>
      <column type="actions" width="-1" hidden="1"/>
      <column type="field" name="id_arkusz" width="-1" hidden="0"/>
      <column type="field" name="kopalina" width="-1" hidden="0"/>
      <column type="field" name="wyrobisko" width="-1" hidden="0"/>
      <column type="field" name="zawodn" width="-1" hidden="0"/>
      <column type="field" name="eksploat" width="-1" hidden="0"/>
      <column type="field" name="wyp_odpady" width="-1" hidden="0"/>
      <column type="field" name="nadkl_min" width="-1" hidden="0"/>
      <column type="field" name="nadkl_max" width="-1" hidden="0"/>
      <column type="field" name="nadkl_sr" width="-1" hidden="0"/>
      <column type="field" name="miazsz_min" width="-1" hidden="0"/>
      <column type="field" name="miazsz_max" width="-1" hidden="0"/>
      <column type="field" name="dlug_max" width="-1" hidden="0"/>
      <column type="field" name="szer_max" width="-1" hidden="0"/>
      <column type="field" name="wys_min" width="-1" hidden="0"/>
      <column type="field" name="wys_max" width="-1" hidden="0"/>
      <column type="field" name="data_kontrol" width="-1" hidden="0"/>
      <column type="field" name="uwagi" width="-1" hidden="0"/>
      <column type="field" name="id" width="-1" hidden="0"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1">C:/qgis</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>C:/qgis</editforminitfilepath>
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
    <field editable="1" name="data_kontrol"/>
    <field editable="1" name="dlug_max"/>
    <field editable="1" name="eksploat"/>
    <field editable="1" name="id"/>
    <field editable="1" name="id1"/>
    <field editable="1" name="id_arkusz"/>
    <field editable="1" name="id_system"/>
    <field editable="1" name="kopalina"/>
    <field editable="1" name="miazsz_max"/>
    <field editable="1" name="miazsz_min"/>
    <field editable="1" name="nadkl_max"/>
    <field editable="1" name="nadkl_min"/>
    <field editable="1" name="nadkl_sr"/>
    <field editable="1" name="szer_max"/>
    <field editable="1" name="uwagi"/>
    <field editable="1" name="wyp_odpady"/>
    <field editable="1" name="wyrobisko"/>
    <field editable="1" name="wys_max"/>
    <field editable="1" name="wys_min"/>
    <field editable="1" name="zawodn"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="data_kontrol"/>
    <field labelOnTop="0" name="dlug_max"/>
    <field labelOnTop="0" name="eksploat"/>
    <field labelOnTop="0" name="id"/>
    <field labelOnTop="0" name="id1"/>
    <field labelOnTop="0" name="id_arkusz"/>
    <field labelOnTop="0" name="id_system"/>
    <field labelOnTop="0" name="kopalina"/>
    <field labelOnTop="0" name="miazsz_max"/>
    <field labelOnTop="0" name="miazsz_min"/>
    <field labelOnTop="0" name="nadkl_max"/>
    <field labelOnTop="0" name="nadkl_min"/>
    <field labelOnTop="0" name="nadkl_sr"/>
    <field labelOnTop="0" name="szer_max"/>
    <field labelOnTop="0" name="uwagi"/>
    <field labelOnTop="0" name="wyp_odpady"/>
    <field labelOnTop="0" name="wyrobisko"/>
    <field labelOnTop="0" name="wys_max"/>
    <field labelOnTop="0" name="wys_min"/>
    <field labelOnTop="0" name="zawodn"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>COALESCE( "ID_ARKUSZ", '&lt;NULL>' )</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
