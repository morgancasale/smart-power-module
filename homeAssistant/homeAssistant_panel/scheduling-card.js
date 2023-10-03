import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { generalStyles } from "./general_styles.js";

import "./scheduler-card.js";

class SchedulingCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      route: { type: Object },
      panel: { type: Object },
      HPMode: { type: Boolean },
      socketID: { type: Number }
    };
  }

  SchedulingMode(){
    var state = this.shadowRoot.getElementById("sch_mode_switch").checked;

    if(state){
        this.shadowRoot.getElementById("scheduling_title").innerText = "Scheduling OFF state: ";
        this.shadowRoot.getElementById("sch_OFF_card").style.display = "block";
        this.shadowRoot.getElementById("sch_ON_card").style.display = "none";
    } else {
        this.shadowRoot.getElementById("scheduling_title").innerText = "Scheduling ON state: ";
        this.shadowRoot.getElementById("sch_ON_card").style.display = "block";
        this.shadowRoot.getElementById("sch_OFF_card").style.display = "none";
    }
  }

  save(){
    this.data = [];

    try{
      var offScheduling = this.shadowRoot.getElementById("sch_OFF_card").save();
      var onScheduling = this.shadowRoot.getElementById("sch_ON_card").save();

      if(offScheduling["startSchedule"] != ""){
        this.data.push({
          socketID : this.socketID,
          mode : "OFF",
          startSchedule : offScheduling["startSchedule"],
          enableEndSchedule : offScheduling["enableEndSchedule"],
          endSchedule : offScheduling["enableEndSchedule"] ? offScheduling["endSchedule"] : ""
        })
      }

      if(onScheduling["startSchedule"] != ""){
        this.data.push({
          socketID : this.socketID,
          mode : "ON",
          startSchedule : onScheduling["startSchedule"],
          enableEndSchedule : onScheduling["enableEndSchedule"],
          endSchedule : onScheduling["enableEndSchedule"] ? onScheduling["endSchedule"] : ""
        })
      }

      this.data = (this.data.length != 0) ? this.data : null;

      return this.data;
    } catch(e) {
      throw new Error("An error occured while saving schedules: \n\t" + e.message);
    }
  }

  setSchedModeOFF(){
    var btn = this.shadowRoot.getElementById("sch_mode_switch");
    if(btn.checked){
      btn.click();
    }
  }

  setData(data){
    this.setSchedModeOFF();
    this.scheds = {
      "OFF" : [],
      "ON" : []
    };

    ["OFF", "ON"].map((mode) => {
      var sched = (data == []) ? [] : data.filter(el => el["mode"] == mode);
      this.shadowRoot.getElementById("sch_" + mode + "_card").setData(sched);
    });
  }

  resetData(){
    this.setData();
  }

  render() {
    return html`
        <ha-card class="Scheduling">
            <div class="SingleEntry" id="sch_mode_sel">
                <div class="description" id="scheduling_title"> Scheduling OFF state : </div>
                <div class="sch_mode_switch"> <ha-switch id="sch_mode_switch" @click=${this.SchedulingMode}></ha-switch> </div> <!--ha-control-switch-->
            </div>
            <scheduler-card .hass=${this.hass} id="sch_OFF_card" class="sch_OFF_card" .mode=${"OFF"} .HPMode=${this.HPMode}></scheduler-card>
            <scheduler-card .hass=${this.hass} id="sch_ON_card" class="sch_ON_card" .mode=${"ON"} .HPMode=${this.HPMode}></scheduler-card>
        </ha-card>
    `;
  }

  static style = [
    generalStyles,
    css`
      .sch_mode_switch{
        width: 100px;
        margin-left: auto;
      }

      .sch_ON_card{
        display: none;
      }
    `
  ]

  static get styles() {
    return this.style;
  }
}
customElements.define("scheduling-card", SchedulingCard);