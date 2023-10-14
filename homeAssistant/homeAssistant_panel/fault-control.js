import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { generalStyles } from "./general_styles.js";

//import "https://unpkg.com/@material/web@1.0.0-pre.4/index.js?module"

//import "../ha-frontend/src/panels/lovelace/entity-rows/hui-input-datetime-entity-row"

class FaultControl extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      route: { type: Object },
      panel: { type: Object }
    };
  }

  FaultControl() {
    var btn = this.shadowRoot.getElementById("fault_ctrl_btn");
    this.data = !btn.checked;
  }

  save(){
    return {faultControl : this.data};
  }

  setData(data){
    this.data = data;
    var btn = this.shadowRoot.getElementById("fault_ctrl_btn");
    if(btn.checked != data){
      btn.click();
    }
  }

  resetData(){
    this.setData(false);
  }

  render() {
    this.data = null;
    return html`
      <ha-card class="Fault-Control">
        <div class="SingleEntry">
          <div class="description" id="btn_descr">Fault Control</div>
          <div class="button_cont">
            <ha-switch id="fault_ctrl_btn" @click="${this.FaultControl}"></ha-switch>
          </div>
        </div>
      </ha-card>
    `;
  }

  static style = [
    generalStyles,
    css`
      .button_cont{
        margin-left: auto;
        display: flex;
        flex-wrap: wrap;
        align-content: center;
      }
    `
  ]

  static get styles() {
    return this.style;
  }
}
customElements.define("fault-control", FaultControl);