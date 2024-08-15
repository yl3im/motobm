ZONE = '''<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<config>
  <category name="Zone">
    <set name="Zone" alias="{zone_alias}" key="NORMAL">
      <collection name="ZoneItems">
        {channels}
      </collection>
      <field name="ZP_ZONEALIAS">{zone_alias}</field>
      <field name="ZP_ZONETYPE" Name="Normal">NORMAL</field>
      <field name="ZP_ZVFNLITEM" Name="None">NONE</field>
      <field name="Comments"></field>
    </set>
  </category>
</config>
'''

CONVENTIONAL_PERSONALITY_RX_TX = '''
<set name="ConventionalPersonality" alias="{ch_alias}" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="2">SLOT2</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_rx}</field>
  <field name="CP_RXFREQ">{ch_tx}</field>
  <field name="CP_EMACKALERTEN">True</field>
  <field name="CP_CNVPERSALIAS">{ch_alias}</field>
  <field name="CP_TXINHXPLEN" Name="Color Code Free">MTCHCLRCD</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_GPSRVRTPERSIT" Name="Selected">SELECTED</field>
  <field name="CP_OVCMDECODEENABLE">True</field>
  <field name="CP_TXCOMPUDPIPHEADEN" Name="DMR Standard">DMR_UDP_HEADER</field>
  <field name="CP_LOCATIONDATADELIVERYMODE" Name="Follow Data Call Confirmed">FOLLOW_CALL_DATA_SETTING</field>
  <field name="CP_MYCALLADCRTR" Name="Follow Admit Criteria">FOLLOW_ADMIT_CRITERIA</field>
  <field name="CP_TEXTMESSAGETYPE" Name="Advantage">TMS</field>
  <field name="CP_TRANSMITINTERRUPTTYPE" Name="Advantage">PROPRIETARY</field>
</set>
'''

CONVENTIONAL_PERSONALITY = '''
<set name="ConventionalPersonality" alias="{ch_alias} TS1" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="1">SLOT1</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_rx}</field>
  <field name="CP_RXFREQ">{ch_tx}</field>
  <field name="CP_EMACKALERTEN">True</field>
  <field name="CP_CNVPERSALIAS">{ch_alias} TS1</field>
  <field name="CP_TXINHXPLEN" Name="Color Code Free">MTCHCLRCD</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_GPSRVRTPERSIT" Name="Selected">SELECTED</field>
  <field name="CP_OVCMDECODEENABLE">True</field>
  <field name="CP_TXCOMPUDPIPHEADEN" Name="DMR Standard">DMR_UDP_HEADER</field>
  <field name="CP_LOCATIONDATADELIVERYMODE" Name="Follow Data Call Confirmed">FOLLOW_CALL_DATA_SETTING</field>
  <field name="CP_MYCALLADCRTR" Name="Follow Admit Criteria">FOLLOW_ADMIT_CRITERIA</field>
  <field name="CP_TEXTMESSAGETYPE" Name="Advantage">TMS</field>
  <field name="CP_TRANSMITINTERRUPTTYPE" Name="Advantage">PROPRIETARY</field>
</set>
<set name="ConventionalPersonality" alias="{ch_alias} TS2" key="DGTLCONV6PT25">
  <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
  <field name="CP_SLTASSGMNT" Name="2">SLOT2</field>
  <field name="CP_COLORCODE">{ch_cc}</field>
  <field name="CP_TXFREQ">{ch_rx}</field>
  <field name="CP_RXFREQ">{ch_tx}</field>
  <field name="CP_EMACKALERTEN">True</field>
  <field name="CP_CNVPERSALIAS">{ch_alias} TS2</field>
  <field name="CP_TXINHXPLEN" Name="Color Code Free">MTCHCLRCD</field>
  <field name="CP_MLTSTPSNLTIND">True</field>
  <field name="CP_GPSRVRTPERSIT" Name="Selected">SELECTED</field>
  <field name="CP_OVCMDECODEENABLE">True</field>
  <field name="CP_TXCOMPUDPIPHEADEN" Name="DMR Standard">DMR_UDP_HEADER</field>
  <field name="CP_LOCATIONDATADELIVERYMODE" Name="Follow Data Call Confirmed">FOLLOW_CALL_DATA_SETTING</field>
  <field name="CP_MYCALLADCRTR" Name="Follow Admit Criteria">FOLLOW_ADMIT_CRITERIA</field>
  <field name="CP_TEXTMESSAGETYPE" Name="Advantage">TMS</field>
  <field name="CP_TRANSMITINTERRUPTTYPE" Name="Advantage">PROPRIETARY</field>
</set>
    '''
