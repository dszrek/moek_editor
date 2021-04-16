<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis minScale="500000" maxScale="0" hasScaleBasedVisibilityFlag="1" readOnly="0" styleCategories="AllStyleCategories" simplifyDrawingHints="0" simplifyDrawingTol="1" labelsEnabled="1" simplifyLocal="1" version="3.10.11-A Coruña" simplifyAlgorithm="0" simplifyMaxScale="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="pointCluster" toleranceUnit="MM" forceraster="0" tolerance="8" toleranceUnitScale="3x:0,0,0,0,0,0" enableorderby="0">
    <renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">
      <symbols>
        <symbol force_rhr="0" type="marker" clip_to_extent="1" name="0" alpha="0.75">
          <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
            <prop v="0" k="angle"/>
            <prop v="0,0,0,204" k="color"/>
            <prop v="1" k="horizontal_anchor_point"/>
            <prop v="round" k="joinstyle"/>
            <prop v="equilateral_triangle" k="name"/>
            <prop v="0,0" k="offset"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="255,255,255,255" k="outline_color"/>
            <prop v="solid" k="outline_style"/>
            <prop v="0.2" k="outline_width"/>
            <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
            <prop v="MM" k="outline_width_unit"/>
            <prop v="diameter" k="scale_method"/>
            <prop v="12.2" k="size"/>
            <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
            <prop v="MM" k="size_unit"/>
            <prop v="1" k="vertical_anchor_point"/>
            <effect type="effectStack" enabled="1">
              <effect type="dropShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="outerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="2.116" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="0.7" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="2" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
              <effect type="drawSource">
                <prop v="0" k="blend_mode"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="0.5" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="2" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
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
          <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
            <prop v="0" k="angle"/>
            <prop v="255,255,255,0" k="color"/>
            <prop v="1" k="horizontal_anchor_point"/>
            <prop v="round" k="joinstyle"/>
            <prop v="equilateral_triangle" k="name"/>
            <prop v="0,0" k="offset"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="255,255,255,255" k="outline_color"/>
            <prop v="solid" k="outline_style"/>
            <prop v="1.4" k="outline_width"/>
            <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
            <prop v="MM" k="outline_width_unit"/>
            <prop v="area" k="scale_method"/>
            <prop v="5" k="size"/>
            <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
            <prop v="MM" k="size_unit"/>
            <prop v="1" k="vertical_anchor_point"/>
            <effect type="effectStack" enabled="0">
              <effect type="dropShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="outerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="0.66" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
              <effect type="drawSource">
                <prop v="0" k="blend_mode"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0.7935" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="0.5" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="2" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option type="Map" name="properties">
                  <Option type="Map" name="enabled">
                    <Option type="bool" value="true" name="active"/>
                    <Option type="QString" value="if( &quot;i_pow_cnt&quot; > 1, 1, 0)" name="expression"/>
                    <Option type="int" value="3" name="type"/>
                  </Option>
                </Option>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
          <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
            <prop v="0" k="angle"/>
            <prop v="255,255,255,255" k="color"/>
            <prop v="1" k="horizontal_anchor_point"/>
            <prop v="round" k="joinstyle"/>
            <prop v="equilateral_triangle" k="name"/>
            <prop v="0,0" k="offset"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="255,255,255,255" k="outline_color"/>
            <prop v="solid" k="outline_style"/>
            <prop v="1" k="outline_width"/>
            <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
            <prop v="MM" k="outline_width_unit"/>
            <prop v="area" k="scale_method"/>
            <prop v="5" k="size"/>
            <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
            <prop v="MM" k="size_unit"/>
            <prop v="1" k="vertical_anchor_point"/>
            <effect type="effectStack" enabled="0">
              <effect type="dropShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="outerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="0.66" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
              <effect type="drawSource">
                <prop v="0" k="blend_mode"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0.7935" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="0.5" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="2" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
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
          <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
            <prop v="0" k="angle"/>
            <prop v="223,134,0,255" k="color"/>
            <prop v="1" k="horizontal_anchor_point"/>
            <prop v="round" k="joinstyle"/>
            <prop v="equilateral_triangle" k="name"/>
            <prop v="0,0" k="offset"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="0,0,0,255" k="outline_color"/>
            <prop v="solid" k="outline_style"/>
            <prop v="0.4" k="outline_width"/>
            <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
            <prop v="MM" k="outline_width_unit"/>
            <prop v="area" k="scale_method"/>
            <prop v="5" k="size"/>
            <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
            <prop v="MM" k="size_unit"/>
            <prop v="1" k="vertical_anchor_point"/>
            <effect type="effectStack" enabled="0">
              <effect type="dropShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="outerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="0.66" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
              <effect type="drawSource">
                <prop v="0" k="blend_mode"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0.7935" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="0.5" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="2" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
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
          <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
            <prop v="0" k="angle"/>
            <prop v="255,255,255,0" k="color"/>
            <prop v="1" k="horizontal_anchor_point"/>
            <prop v="round" k="joinstyle"/>
            <prop v="equilateral_triangle" k="name"/>
            <prop v="0,0" k="offset"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="0,0,0,255" k="outline_color"/>
            <prop v="solid" k="outline_style"/>
            <prop v="1" k="outline_width"/>
            <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
            <prop v="MM" k="outline_width_unit"/>
            <prop v="area" k="scale_method"/>
            <prop v="5" k="size"/>
            <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
            <prop v="MM" k="size_unit"/>
            <prop v="1" k="vertical_anchor_point"/>
            <effect type="effectStack" enabled="0">
              <effect type="dropShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="outerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="0.66" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
              <effect type="drawSource">
                <prop v="0" k="blend_mode"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0.7935" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="0.5" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="2" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option type="Map" name="properties">
                  <Option type="Map" name="enabled">
                    <Option type="bool" value="true" name="active"/>
                    <Option type="QString" value="if( &quot;i_pow_cnt&quot; > 1, 1, 0)" name="expression"/>
                    <Option type="int" value="3" name="type"/>
                  </Option>
                </Option>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
          <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
            <prop v="0" k="angle"/>
            <prop v="255,255,255,0" k="color"/>
            <prop v="1" k="horizontal_anchor_point"/>
            <prop v="round" k="joinstyle"/>
            <prop v="equilateral_triangle" k="name"/>
            <prop v="0,0" k="offset"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="217,0,143,255" k="outline_color"/>
            <prop v="solid" k="outline_style"/>
            <prop v="0.5" k="outline_width"/>
            <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
            <prop v="MM" k="outline_width_unit"/>
            <prop v="area" k="scale_method"/>
            <prop v="5" k="size"/>
            <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
            <prop v="MM" k="size_unit"/>
            <prop v="1" k="vertical_anchor_point"/>
            <effect type="effectStack" enabled="0">
              <effect type="dropShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="outerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="0.66" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
              <effect type="drawSource">
                <prop v="0" k="blend_mode"/>
                <prop v="2" k="draw_mode"/>
                <prop v="1" k="enabled"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerShadow">
                <prop v="13" k="blend_mode"/>
                <prop v="2.645" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,0,255" k="color"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="135" k="offset_angle"/>
                <prop v="2" k="offset_distance"/>
                <prop v="MM" k="offset_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
                <prop v="1" k="opacity"/>
              </effect>
              <effect type="innerGlow">
                <prop v="0" k="blend_mode"/>
                <prop v="0.7935" k="blur_level"/>
                <prop v="MM" k="blur_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
                <prop v="0,0,255,255" k="color1"/>
                <prop v="0,255,0,255" k="color2"/>
                <prop v="0" k="color_type"/>
                <prop v="0" k="discrete"/>
                <prop v="2" k="draw_mode"/>
                <prop v="0" k="enabled"/>
                <prop v="0.5" k="opacity"/>
                <prop v="gradient" k="rampType"/>
                <prop v="255,255,255,255" k="single_color"/>
                <prop v="2" k="spread"/>
                <prop v="MM" k="spread_unit"/>
                <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option type="Map" name="properties">
                  <Option type="Map" name="enabled">
                    <Option type="bool" value="true" name="active"/>
                    <Option type="QString" value="if( &quot;i_pow_cnt&quot; > 1, 1, 0)" name="expression"/>
                    <Option type="int" value="3" name="type"/>
                  </Option>
                </Option>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </symbols>
      <rotation/>
      <sizescale/>
    </renderer-v2>
    <symbol force_rhr="0" type="marker" clip_to_extent="1" name="centerSymbol" alpha="0.75">
      <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
        <prop v="0" k="angle"/>
        <prop v="255,255,255,255" k="color"/>
        <prop v="1" k="horizontal_anchor_point"/>
        <prop v="round" k="joinstyle"/>
        <prop v="equilateral_triangle" k="name"/>
        <prop v="0,0" k="offset"/>
        <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
        <prop v="MM" k="offset_unit"/>
        <prop v="255,255,255,255" k="outline_color"/>
        <prop v="solid" k="outline_style"/>
        <prop v="1" k="outline_width"/>
        <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
        <prop v="MM" k="outline_width_unit"/>
        <prop v="area" k="scale_method"/>
        <prop v="5" k="size"/>
        <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
        <prop v="MM" k="size_unit"/>
        <prop v="1" k="vertical_anchor_point"/>
        <effect type="effectStack" enabled="0">
          <effect type="dropShadow">
            <prop v="13" k="blend_mode"/>
            <prop v="2.645" k="blur_level"/>
            <prop v="MM" k="blur_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
            <prop v="0,0,0,255" k="color"/>
            <prop v="2" k="draw_mode"/>
            <prop v="0" k="enabled"/>
            <prop v="135" k="offset_angle"/>
            <prop v="2" k="offset_distance"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
            <prop v="1" k="opacity"/>
          </effect>
          <effect type="outerGlow">
            <prop v="0" k="blend_mode"/>
            <prop v="0" k="blur_level"/>
            <prop v="MM" k="blur_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
            <prop v="0,0,255,255" k="color1"/>
            <prop v="0,255,0,255" k="color2"/>
            <prop v="0" k="color_type"/>
            <prop v="0" k="discrete"/>
            <prop v="2" k="draw_mode"/>
            <prop v="1" k="enabled"/>
            <prop v="1" k="opacity"/>
            <prop v="gradient" k="rampType"/>
            <prop v="255,255,255,255" k="single_color"/>
            <prop v="0.66" k="spread"/>
            <prop v="MM" k="spread_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
          </effect>
          <effect type="drawSource">
            <prop v="0" k="blend_mode"/>
            <prop v="2" k="draw_mode"/>
            <prop v="1" k="enabled"/>
            <prop v="1" k="opacity"/>
          </effect>
          <effect type="innerShadow">
            <prop v="13" k="blend_mode"/>
            <prop v="2.645" k="blur_level"/>
            <prop v="MM" k="blur_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
            <prop v="0,0,0,255" k="color"/>
            <prop v="2" k="draw_mode"/>
            <prop v="0" k="enabled"/>
            <prop v="135" k="offset_angle"/>
            <prop v="2" k="offset_distance"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
            <prop v="1" k="opacity"/>
          </effect>
          <effect type="innerGlow">
            <prop v="0" k="blend_mode"/>
            <prop v="0.7935" k="blur_level"/>
            <prop v="MM" k="blur_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
            <prop v="0,0,255,255" k="color1"/>
            <prop v="0,255,0,255" k="color2"/>
            <prop v="0" k="color_type"/>
            <prop v="0" k="discrete"/>
            <prop v="2" k="draw_mode"/>
            <prop v="0" k="enabled"/>
            <prop v="0.5" k="opacity"/>
            <prop v="gradient" k="rampType"/>
            <prop v="255,255,255,255" k="single_color"/>
            <prop v="2" k="spread"/>
            <prop v="MM" k="spread_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
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
      <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
        <prop v="0" k="angle"/>
        <prop v="223,134,0,255" k="color"/>
        <prop v="1" k="horizontal_anchor_point"/>
        <prop v="round" k="joinstyle"/>
        <prop v="equilateral_triangle" k="name"/>
        <prop v="0,0" k="offset"/>
        <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
        <prop v="MM" k="offset_unit"/>
        <prop v="0,0,0,255" k="outline_color"/>
        <prop v="solid" k="outline_style"/>
        <prop v="0.4" k="outline_width"/>
        <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
        <prop v="MM" k="outline_width_unit"/>
        <prop v="area" k="scale_method"/>
        <prop v="5" k="size"/>
        <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
        <prop v="MM" k="size_unit"/>
        <prop v="1" k="vertical_anchor_point"/>
        <effect type="effectStack" enabled="0">
          <effect type="dropShadow">
            <prop v="13" k="blend_mode"/>
            <prop v="2.645" k="blur_level"/>
            <prop v="MM" k="blur_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
            <prop v="0,0,0,255" k="color"/>
            <prop v="2" k="draw_mode"/>
            <prop v="0" k="enabled"/>
            <prop v="135" k="offset_angle"/>
            <prop v="2" k="offset_distance"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
            <prop v="1" k="opacity"/>
          </effect>
          <effect type="outerGlow">
            <prop v="0" k="blend_mode"/>
            <prop v="0" k="blur_level"/>
            <prop v="MM" k="blur_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
            <prop v="0,0,255,255" k="color1"/>
            <prop v="0,255,0,255" k="color2"/>
            <prop v="0" k="color_type"/>
            <prop v="0" k="discrete"/>
            <prop v="2" k="draw_mode"/>
            <prop v="1" k="enabled"/>
            <prop v="1" k="opacity"/>
            <prop v="gradient" k="rampType"/>
            <prop v="255,255,255,255" k="single_color"/>
            <prop v="0.66" k="spread"/>
            <prop v="MM" k="spread_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
          </effect>
          <effect type="drawSource">
            <prop v="0" k="blend_mode"/>
            <prop v="2" k="draw_mode"/>
            <prop v="1" k="enabled"/>
            <prop v="1" k="opacity"/>
          </effect>
          <effect type="innerShadow">
            <prop v="13" k="blend_mode"/>
            <prop v="2.645" k="blur_level"/>
            <prop v="MM" k="blur_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
            <prop v="0,0,0,255" k="color"/>
            <prop v="2" k="draw_mode"/>
            <prop v="0" k="enabled"/>
            <prop v="135" k="offset_angle"/>
            <prop v="2" k="offset_distance"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_unit_scale"/>
            <prop v="1" k="opacity"/>
          </effect>
          <effect type="innerGlow">
            <prop v="0" k="blend_mode"/>
            <prop v="0.7935" k="blur_level"/>
            <prop v="MM" k="blur_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="blur_unit_scale"/>
            <prop v="0,0,255,255" k="color1"/>
            <prop v="0,255,0,255" k="color2"/>
            <prop v="0" k="color_type"/>
            <prop v="0" k="discrete"/>
            <prop v="2" k="draw_mode"/>
            <prop v="0" k="enabled"/>
            <prop v="0.5" k="opacity"/>
            <prop v="gradient" k="rampType"/>
            <prop v="255,255,255,255" k="single_color"/>
            <prop v="2" k="spread"/>
            <prop v="MM" k="spread_unit"/>
            <prop v="3x:0,0,0,0,0,0" k="spread_unit_scale"/>
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
      <layer class="FontMarker" locked="0" pass="0" enabled="1">
        <prop v="0" k="angle"/>
        <prop v="A" k="chr"/>
        <prop v="0,0,0,255" k="color"/>
        <prop v="Dingbats" k="font"/>
        <prop v="1" k="horizontal_anchor_point"/>
        <prop v="bevel" k="joinstyle"/>
        <prop v="0,-0.5" k="offset"/>
        <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
        <prop v="MM" k="offset_unit"/>
        <prop v="35,35,35,255" k="outline_color"/>
        <prop v="0" k="outline_width"/>
        <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
        <prop v="MM" k="outline_width_unit"/>
        <prop v="2" k="size"/>
        <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
        <prop v="MM" k="size_unit"/>
        <prop v="1" k="vertical_anchor_point"/>
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
      <text-style textOpacity="1" fontWeight="50" multilineHeight="1" textColor="255,156,56,255" fontFamily="MS Shell Dlg 2" fontKerning="1" fieldName="id_arkusz" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontLetterSpacing="0" fontItalic="0" fontSize="10" fontWordSpacing="0" fontCapitals="0" namedStyle="Normal" previewBkgrdColor="255,255,255,255" fontUnderline="0" blendMode="0" textOrientation="horizontal" fontStrikeout="0" isExpression="0" fontSizeUnit="Point" useSubstitutions="0">
        <text-buffer bufferOpacity="1" bufferSizeUnits="MM" bufferSize="0.5" bufferNoFill="1" bufferBlendMode="0" bufferJoinStyle="128" bufferColor="0,0,0,255" bufferDraw="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0"/>
        <background shapeSizeY="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeSizeType="0" shapeRotation="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeDraw="0" shapeOffsetX="0" shapeOffsetY="0" shapeFillColor="255,255,255,255" shapeSizeX="0" shapeBlendMode="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiUnit="MM" shapeBorderWidthUnit="MM" shapeType="1" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidth="0" shapeSizeUnit="MM" shapeJoinStyle="64" shapeSVGFile="" shapeBorderColor="128,128,128,255" shapeRadiiY="0" shapeRotationType="0" shapeOffsetUnit="MM" shapeRadiiX="0">
          <symbol force_rhr="0" type="marker" clip_to_extent="1" name="markerSymbol" alpha="1">
            <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
              <prop v="0" k="angle"/>
              <prop v="125,139,143,255" k="color"/>
              <prop v="1" k="horizontal_anchor_point"/>
              <prop v="bevel" k="joinstyle"/>
              <prop v="circle" k="name"/>
              <prop v="0,0" k="offset"/>
              <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
              <prop v="MM" k="offset_unit"/>
              <prop v="35,35,35,255" k="outline_color"/>
              <prop v="solid" k="outline_style"/>
              <prop v="0" k="outline_width"/>
              <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
              <prop v="MM" k="outline_width_unit"/>
              <prop v="diameter" k="scale_method"/>
              <prop v="2" k="size"/>
              <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
              <prop v="MM" k="size_unit"/>
              <prop v="1" k="vertical_anchor_point"/>
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
        <shadow shadowBlendMode="1" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetAngle="135" shadowScale="100" shadowOffsetUnit="MM" shadowOffsetDist="0" shadowOpacity="1" shadowRadiusUnit="MM" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowColor="255,255,255,255" shadowOffsetGlobal="1" shadowRadius="0.1" shadowRadiusAlphaOnly="0" shadowDraw="0" shadowUnder="0"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format multilineAlign="3" formatNumbers="0" plussign="0" useMaxLineLengthForAutoWrap="1" autoWrapLength="0" leftDirectionSymbol="&lt;" decimals="3" placeDirectionSymbol="0" rightDirectionSymbol=">" wrapChar="" addDirectionSymbol="0" reverseDirectionSymbol="0"/>
      <placement distUnits="MM" fitInPolygonOnly="0" priority="0" geometryGenerator="" yOffset="0" maxCurvedCharAngleIn="25" quadOffset="4" maxCurvedCharAngleOut="-25" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" centroidWhole="0" distMapUnitScale="3x:0,0,0,0,0,0" rotationAngle="0" repeatDistanceUnits="MM" geometryGeneratorType="PointGeometry" dist="6" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" repeatDistance="0" preserveRotation="1" overrunDistance="0" overrunDistanceUnit="MM" placementFlags="10" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" offsetType="0" offsetUnits="MM" geometryGeneratorEnabled="0" layerType="PointGeometry" centroidInside="0" placement="0" xOffset="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering upsidedownLabels="0" scaleVisibility="1" scaleMax="120000" zIndex="0" mergeLines="0" minFeatureSize="0" displayAll="0" fontMinPixelSize="3" obstacle="1" drawLabels="1" limitNumLabels="0" fontLimitPixelSize="0" labelPerPart="0" scaleMin="0" obstacleFactor="2" obstacleType="0" maxNumLabels="2000" fontMaxPixelSize="10000"/>
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
          <Option type="QString" value="&lt;symbol force_rhr=&quot;0&quot; type=&quot;line&quot; clip_to_extent=&quot;1&quot; name=&quot;symbol&quot; alpha=&quot;1&quot;>&lt;layer class=&quot;SimpleLine&quot; locked=&quot;0&quot; pass=&quot;0&quot; enabled=&quot;1&quot;>&lt;prop v=&quot;round&quot; k=&quot;capstyle&quot;/>&lt;prop v=&quot;5;2&quot; k=&quot;customdash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;customdash_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;customdash_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;draw_inside_polygon&quot;/>&lt;prop v=&quot;bevel&quot; k=&quot;joinstyle&quot;/>&lt;prop v=&quot;35,35,35,255&quot; k=&quot;line_color&quot;/>&lt;prop v=&quot;solid&quot; k=&quot;line_style&quot;/>&lt;prop v=&quot;1&quot; k=&quot;line_width&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;line_width_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;ring_filter&quot;/>&lt;prop v=&quot;0&quot; k=&quot;use_custom_dash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;width_map_unit_scale&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;layer class=&quot;SimpleLine&quot; locked=&quot;0&quot; pass=&quot;0&quot; enabled=&quot;1&quot;>&lt;prop v=&quot;round&quot; k=&quot;capstyle&quot;/>&lt;prop v=&quot;5;2&quot; k=&quot;customdash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;customdash_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;customdash_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;draw_inside_polygon&quot;/>&lt;prop v=&quot;round&quot; k=&quot;joinstyle&quot;/>&lt;prop v=&quot;255,127,0,255&quot; k=&quot;line_color&quot;/>&lt;prop v=&quot;solid&quot; k=&quot;line_style&quot;/>&lt;prop v=&quot;0.3&quot; k=&quot;line_width&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;line_width_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;ring_filter&quot;/>&lt;prop v=&quot;0&quot; k=&quot;use_custom_dash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;width_map_unit_scale&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol"/>
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
    <DiagramCategory maxScaleDenominator="1e+08" labelPlacementMethod="XHeight" enabled="0" backgroundAlpha="255" diagramOrientation="Up" rotationOffset="270" sizeScale="3x:0,0,0,0,0,0" minimumSize="0" opacity="1" minScaleDenominator="0" sizeType="MM" barWidth="5" penColor="#000000" scaleDependency="Area" scaleBasedVisibility="0" height="15" penWidth="0" backgroundColor="#ffffff" width="15" penAlpha="255" lineSizeType="MM" lineSizeScale="3x:0,0,0,0,0,0">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute field="" label="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings priority="0" zIndex="0" obstacle="0" dist="0" linePlacementFlags="18" showAll="1" placement="0">
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
    <field name="i_pow_cnt">
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
    <alias field="id_arkusz" index="0" name=""/>
    <alias field="kopalina" index="1" name=""/>
    <alias field="wyrobisko" index="2" name=""/>
    <alias field="zawodn" index="3" name=""/>
    <alias field="wyp_odpady" index="4" name=""/>
    <alias field="nadkl_min" index="5" name=""/>
    <alias field="nadkl_max" index="6" name=""/>
    <alias field="nadkl_sr" index="7" name=""/>
    <alias field="miazsz_min" index="8" name=""/>
    <alias field="miazsz_max" index="9" name=""/>
    <alias field="dlug_max" index="10" name=""/>
    <alias field="szer_max" index="11" name=""/>
    <alias field="wys_min" index="12" name=""/>
    <alias field="wys_max" index="13" name=""/>
    <alias field="data_kontrol" index="14" name=""/>
    <alias field="uwagi" index="15" name=""/>
    <alias field="i_pow_cnt" index="16" name=""/>
    <alias field="t_notatki" index="17" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="id_arkusz" expression="" applyOnUpdate="0"/>
    <default field="kopalina" expression="" applyOnUpdate="0"/>
    <default field="wyrobisko" expression="" applyOnUpdate="0"/>
    <default field="zawodn" expression="" applyOnUpdate="0"/>
    <default field="wyp_odpady" expression="" applyOnUpdate="0"/>
    <default field="nadkl_min" expression="" applyOnUpdate="0"/>
    <default field="nadkl_max" expression="" applyOnUpdate="0"/>
    <default field="nadkl_sr" expression="" applyOnUpdate="0"/>
    <default field="miazsz_min" expression="" applyOnUpdate="0"/>
    <default field="miazsz_max" expression="" applyOnUpdate="0"/>
    <default field="dlug_max" expression="" applyOnUpdate="0"/>
    <default field="szer_max" expression="" applyOnUpdate="0"/>
    <default field="wys_min" expression="" applyOnUpdate="0"/>
    <default field="wys_max" expression="" applyOnUpdate="0"/>
    <default field="data_kontrol" expression="" applyOnUpdate="0"/>
    <default field="uwagi" expression="" applyOnUpdate="0"/>
    <default field="i_pow_cnt" expression="" applyOnUpdate="0"/>
    <default field="t_notatki" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint field="id_arkusz" notnull_strength="1" exp_strength="0" constraints="3" unique_strength="1"/>
    <constraint field="kopalina" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="wyrobisko" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="zawodn" notnull_strength="0" exp_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="wyp_odpady" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="nadkl_min" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="nadkl_max" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="nadkl_sr" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="miazsz_min" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="miazsz_max" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="dlug_max" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="szer_max" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="wys_min" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="wys_max" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="data_kontrol" notnull_strength="1" exp_strength="0" constraints="1" unique_strength="0"/>
    <constraint field="uwagi" notnull_strength="0" exp_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="i_pow_cnt" notnull_strength="1" exp_strength="0" constraints="3" unique_strength="1"/>
    <constraint field="t_notatki" notnull_strength="0" exp_strength="0" constraints="0" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="id_arkusz" desc="" exp=""/>
    <constraint field="kopalina" desc="" exp=""/>
    <constraint field="wyrobisko" desc="" exp=""/>
    <constraint field="zawodn" desc="" exp=""/>
    <constraint field="wyp_odpady" desc="" exp=""/>
    <constraint field="nadkl_min" desc="" exp=""/>
    <constraint field="nadkl_max" desc="" exp=""/>
    <constraint field="nadkl_sr" desc="" exp=""/>
    <constraint field="miazsz_min" desc="" exp=""/>
    <constraint field="miazsz_max" desc="" exp=""/>
    <constraint field="dlug_max" desc="" exp=""/>
    <constraint field="szer_max" desc="" exp=""/>
    <constraint field="wys_min" desc="" exp=""/>
    <constraint field="wys_max" desc="" exp=""/>
    <constraint field="data_kontrol" desc="" exp=""/>
    <constraint field="uwagi" desc="" exp=""/>
    <constraint field="i_pow_cnt" desc="" exp=""/>
    <constraint field="t_notatki" desc="" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{1e658472-5f81-43b5-8878-084196be062a}" key="Canvas"/>
    <actionsetting action="" id="{1e658472-5f81-43b5-8878-084196be062a}" type="0" icon="" capture="0" name="" isEnabledOnlyWhenEditable="0" shortTitle="" notificationMessage="">
      <actionScope id="Canvas"/>
      <actionScope id="Feature"/>
      <actionScope id="Field"/>
    </actionsetting>
  </attributeactions>
  <attributetableconfig sortExpression="&quot;id_arkusz&quot;" actionWidgetStyle="dropDown" sortOrder="0">
    <columns>
      <column width="-1" type="actions" hidden="1"/>
      <column width="-1" type="field" name="id_arkusz" hidden="0"/>
      <column width="-1" type="field" name="kopalina" hidden="0"/>
      <column width="-1" type="field" name="wyrobisko" hidden="0"/>
      <column width="-1" type="field" name="zawodn" hidden="0"/>
      <column width="-1" type="field" name="wyp_odpady" hidden="0"/>
      <column width="-1" type="field" name="nadkl_min" hidden="0"/>
      <column width="-1" type="field" name="nadkl_max" hidden="0"/>
      <column width="-1" type="field" name="nadkl_sr" hidden="0"/>
      <column width="-1" type="field" name="miazsz_min" hidden="0"/>
      <column width="-1" type="field" name="miazsz_max" hidden="0"/>
      <column width="-1" type="field" name="dlug_max" hidden="0"/>
      <column width="-1" type="field" name="szer_max" hidden="0"/>
      <column width="-1" type="field" name="wys_min" hidden="0"/>
      <column width="-1" type="field" name="wys_max" hidden="0"/>
      <column width="-1" type="field" name="data_kontrol" hidden="0"/>
      <column width="-1" type="field" name="uwagi" hidden="0"/>
      <column width="-1" type="field" name="i_pow_cnt" hidden="0"/>
      <column width="-1" type="field" name="t_notatki" hidden="0"/>
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
    <field name="data_kontrol" editable="1"/>
    <field name="dlug_max" editable="1"/>
    <field name="eksploat" editable="1"/>
    <field name="i_pow_cnt" editable="1"/>
    <field name="id" editable="1"/>
    <field name="id1" editable="1"/>
    <field name="id_arkusz" editable="1"/>
    <field name="id_system" editable="1"/>
    <field name="kopalina" editable="1"/>
    <field name="miazsz_max" editable="1"/>
    <field name="miazsz_min" editable="1"/>
    <field name="nadkl_max" editable="1"/>
    <field name="nadkl_min" editable="1"/>
    <field name="nadkl_sr" editable="1"/>
    <field name="szer_max" editable="1"/>
    <field name="t_notatki" editable="1"/>
    <field name="uwagi" editable="1"/>
    <field name="wyp_odpady" editable="1"/>
    <field name="wyrobisko" editable="1"/>
    <field name="wys_max" editable="1"/>
    <field name="wys_min" editable="1"/>
    <field name="zawodn" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="data_kontrol"/>
    <field labelOnTop="0" name="dlug_max"/>
    <field labelOnTop="0" name="eksploat"/>
    <field labelOnTop="0" name="i_pow_cnt"/>
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
    <field labelOnTop="0" name="t_notatki"/>
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
