import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
    LitElement,
    html,
    css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { generalStyles } from "./general_styles.js";

class FaultyBehaviourCard extends LitElement {
    static get properties() {
        return {
            hass: { type: Object },
            narrow: { type: Boolean },
            route: { type: Object },
            panel: { type: Object },
            HPMode: { type: Boolean }
        };
    }

    FBControl() {
        var btn = this.shadowRoot.getElementById("FB_button");
        this.data.FBControl = !btn.checked;
        if (this.data.FBControl) {
            this.shadowRoot.getElementById("fault_beh").style.display = "flex";
            this.shadowRoot.getElementById("fault_beh_settings").style.display = "flex";
        } else {
            this.shadowRoot.getElementById("fault_beh").style.display = "none";
            this.shadowRoot.getElementById("fault_beh_settings").style.display = "none";
        }
    }

    _onScheduleSelected(ev) {
        this.data.FBMode = ev.target.value;
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
        this.sendEvent("err_occ", true);
    }

    save(){
        if(this.data.FBControl & (this.data.FBMode == null)){
            throw new Error("A Fault Behaviour mode must be selected.");
        }

        return this.data;
    }

    setFBControl(data){
        var btn = this.shadowRoot.getElementById("FB_button");
        if(btn.checked != data.FBControl){
            btn.click();
        }
    }

    setMode(data){
        this.shadowRoot.getElementById("mode_sel").value = data.FBMode;
    }

    setData(data){
        this.data = data;
        this.setFBControl(data);
        this.setMode(data);
    }

    resetData(){
        this.setData(this.defaultData);
    }

    render() {
        this.defaultData = {
            FBControl : false,
            FBMode : ""
        };

        this.data = this.defaultData;

        return html`
        <ha-card class="Faulty-Beh">
            <div class="SingleEntry fault_beh_btn">
                <div class="description" id="btn_descr">Faulty Behaviour Control</div>
                <div class="button_cont">
                    <ha-switch id="FB_button" @click="${this.FBControl}"></ha-switch>
                </div>
            </div>
            <div class="fault_beh_settings SingleEntry" id="fault_beh_settings">
                <div class="fault_beh_mode" id="fault_beh_mode">
                    <div class="description" id="fault_beh_mode_descr"> Mode : </div>
                    <ha-select class="mode_sel" id="mode_sel" label="Choose Mode" @selected=${this._onScheduleSelected}>
                        ${["Notify", "Turn OFF"].map((item) => html`<mwc-list-item .value=${item}>${item}</mwc-list-item>`)}
                    </ha-select>
                </div>
            </div>
        </ha-card>
    `;
    }

    static style = [
        generalStyles,
        css`
            .fault_beh_settings{
                display: none;
            }

            .button_cont{
                margin-left: auto;
                display: flex;
                flex-wrap: wrap;
                align-content: center;
            }

            .fault_beh_mode{
                display: flex;
            }
        `
    ]

    static get styles() {
        return this.style;
    }
}
customElements.define("faulty-behaviour-card", FaultyBehaviourCard);