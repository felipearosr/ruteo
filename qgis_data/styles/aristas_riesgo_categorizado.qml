<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.28" styleCategories="Symbology|Labeling">
  <renderer-v2 type="categorizedSymbol" attr="categoria_riesgo" symbollevels="0" enableorderby="0">
    <categories>
      <category symbol="0" value="bajo" label="Bajo (< 0.1)" render="true"/>
      <category symbol="1" value="medio" label="Medio (0.1 - 0.3)" render="true"/>
      <category symbol="2" value="alto" label="Alto (0.3 - 0.5)" render="true"/>
      <category symbol="3" value="muy_alto" label="Muy Alto (> 0.5)" render="true"/>
    </categories>
    <symbols>
      <symbol type="line" name="0" alpha="1">
        <layer class="SimpleLine" enabled="1">
          <prop k="line_color" v="46,204,113,255"/>
          <prop k="line_width" v="0.5"/>
          <prop k="capstyle" v="round"/>
        </layer>
      </symbol>
      <symbol type="line" name="1" alpha="1">
        <layer class="SimpleLine" enabled="1">
          <prop k="line_color" v="241,196,15,255"/>
          <prop k="line_width" v="0.8"/>
          <prop k="capstyle" v="round"/>
        </layer>
      </symbol>
      <symbol type="line" name="2" alpha="1">
        <layer class="SimpleLine" enabled="1">
          <prop k="line_color" v="230,126,34,255"/>
          <prop k="line_width" v="1.2"/>
          <prop k="capstyle" v="round"/>
        </layer>
      </symbol>
      <symbol type="line" name="3" alpha="1">
        <layer class="SimpleLine" enabled="1">
          <prop k="line_color" v="231,76,60,255"/>
          <prop k="line_width" v="2.0"/>
          <prop k="capstyle" v="round"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
