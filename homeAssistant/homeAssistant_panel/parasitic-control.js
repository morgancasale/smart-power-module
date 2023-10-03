import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
    LitElement,
    html,
    css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { generalStyles } from "./general_styles.js";

//import "https://unpkg.com/@material/web@1.0.0-pre.4/index.js?module"

//import "../ha-frontend/src/panels/lovelace/entity-rows/hui-input-datetime-entity-row"

class ParasiticControl extends LitElement {
    static get properties() {
        return {
            hass: { type: Object },
            narrow: { type: Boolean },
            route: { type: Object },
            panel: { type: Object },
            HPMode: { type: Boolean }
        };
    }

    constructor(){
        super();
        this.errState = false;
    }

    sendEvent(event_name, event_msg){
        let Event = new CustomEvent(event_name, {
            detail: { message: event_msg },
            bubbles: true,
            composed: true 
        });
        this.dispatchEvent(Event);
    }

    signalError(msg){
        alert(msg);
        this.errState = true;
        this.sendEvent("err_occ", this.errState);
    }

    resetErr(){
        this.errState = false;
        this.sendEvent("err_occ", this.errState);
    }

    ParControl() {
        var state = this.shadowRoot.getElementById("par_ctrl_btn").shadowRoot.getElementById("basic-switch").getAttribute("aria-checked");
        this.data.parControl = (state == "false");
        if (state == "false") {
            this.shadowRoot.getElementById("par_ctrl_settings").style.display = "flex";
        } else {
            this.shadowRoot.getElementById("par_ctrl_settings").style.display = "none";
        }
    }

    _onModeSelected(ev) {
        this.data.parMode = ev.target.value;
        if(this.data.parMode == "Auto"){
            this.shadowRoot.getElementById("par_ctrl_input_field").disabled = true;
        } else {
            this.shadowRoot.getElementById("par_ctrl_input_field").disabled = false;
        }
    }

    resetValid(){
        this.shadowRoot.getElementById("par_ctrl_input_field").invalid = false;
        this.resetErr();
    }

    checkThreshold(){
        if(this.data.parThreshold == null | isNaN(this.data.parThreshold)){
            this.shadowRoot.getElementById("par_ctrl_input_field").invalid = true;
            throw new Error("A value for the power Threshold must be entered.");
        } else {
            if(parseInt(this.data.parThreshold) < 0){                
                this.shadowRoot.getElementById("par_ctrl_input_field").invalid = true;
                throw new Error("The Threshold value must be positive.");
            }
        }
    }

    checkMode(){
        var cond = this.data.parThreshold != null & this.data.parMode == null;
        cond &= (this.shadowRoot.getElementById("mode_sel_cont").style.display == "flex");
        if(cond){
            throw new Error("A mode for the Parasitic control must be selected.")
        } else {
            this.resetErr();
        }
    }

    save(){
        if(this.data.parControl){
            this.data.parThreshold = parseFloat(this.shadowRoot.getElementById("par_ctrl_input_field").value);

            this.checkMode();
            this.checkThreshold();
        }

        return this.data;
    }

    setparControl(data){
        var btn = this.shadowRoot.getElementById("par_ctrl_btn");

        if(btn.checked != data.parControl){
            btn.click();
        }
    }

    setThreshold(data){
        this.shadowRoot.getElementById("par_ctrl_input_field").value = data.parThreshold;
    }

    setMode(data){
        this.shadowRoot.getElementById("mode_sel").value = data.parMode;
    }

    setData(data){
        this.data = data;
        this.setparControl(data);
        this.setThreshold(data);
        this.setMode(data);
    }

    resetData(){
        this.setData(this.defaultData);
    }

    render() {
        this.defaultData = {
            "parControl" : false,
            "parThreshold" : "",
            "parMode" : ""
        };

        this.data = this.defaultData;

        return html`
            <ha-card class="Parasitic-Control">
                <div class="SingleEntry">
                    <div class="description" id="btn_descr">Parasitic Control</div>
                    <div class="button_cont">
                        <ha-switch id="par_ctrl_btn" @click="${this.ParControl}"></ha-switch>
                    </div>
                </div>
                <div class="par_ctrl_settings SingleEntry" id="par_ctrl_settings">
                    <div class="manual_thr" id="manual_thr">
                        <div class="description" id="par_ctrl_descr"> Manual Threshold : </div>
                        <ha-textfield class="par_ctrl_input_field" id="par_ctrl_input_field" @click=${this.resetValid}>Power</ha-textfield>
                        <div class="power_unit description" id="power_unit"> W </div>
                    </div>
                    <div class="mode_sel_cont" id="mode_sel_cont">
                        <div class="description"> Mode: </div>
                        <ha-select class="mode_sel" id="mode_sel" label="Choose mode" @selected=${this._onModeSelected}>
                            ${["Manual", "Auto"].map((item) => html`<mwc-list-item .value=${item}>${item}</mwc-list-item>`)}
                        </ha-select>
                    </div>
                </div>
            </ha-card>
        `;
    }

    static style = [
        generalStyles,
        css`
            .Parasitic-Control{
                padding-bottom: 5px;
            }

            .mode_sel_cont{
                display: none;
                flex-wrap: wrap;
                align-content: center;
            }
            
            .par_ctrl_settings{
                display: none;
                flex-wrap: wrap;
                align-content: center;
            }

            .button_cont{
                margin-left: auto;
                display: flex;
                flex-wrap: wrap;
                align-content: center;
            }

            .manual_thr{
                display: flex;
                flex-wrap: wrap;
                align-content: center;
            }

            .par_ctrl_input_field{
                width: 100px;
            }

            .power_unit{
                margin-left: 10px;
            }
        `
    ]

    static get styles() {
        return this.style;
    }
}
customElements.define("parasitic-control", ParasiticControl);