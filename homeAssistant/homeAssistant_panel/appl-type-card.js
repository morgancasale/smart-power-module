import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { generalStyles } from "./general_styles.js";

class ApplianceTypeCard extends LitElement {
    static get properties() {
        return {
            hass: { type: Object },
            narrow: { type: Boolean },
            route: { type: Object },
            panel: { type: Object },
            socket_num: { type : String },
            HPMode: { type: Boolean },
            appliances: { type: Array }
        };
    }

    catalogAddress = "127.0.0.1";
    catalogPort = 8099;
    
    constructor(){
        super();
        this.appliances = ["None", "Oven", "Microwave", "Fridge", "Washing Machine", "Dryer"];
    }

    sendEvent(event_name, event_msg){
        let Event = new CustomEvent(event_name, {
            detail: { message: event_msg },
            bubbles: true,
            composed: true 
        });
        this.dispatchEvent(Event);
    }

    SetApplType(){
        this.data = this.shadowRoot.getElementById("type_sel").value;
        if(this.data != "None"){
            this.sendEvent("appl_type_set", this.data);
        }
    }

    _onScheduleSelected(ev) {
        this.data = ev.target.value;
    }

    save(){
        return {applianceType : this.data}
    }

    setData(data){
        this.data = data;
        this.shadowRoot.getElementById("type_sel").value = data;
        if(this.HPMode){
            this.SetApplType();
        }
        this.getAppliances();
    }
    
    resetData(){
        this.setData("None");
    }

    async getAppliances(){
        var url = "http://" + this.catalogAddress + ":" + String(this.catalogPort) + "/getInfo?";
        var params = {
            table : "AppliancesInfo",
            keyName : "applianceType",
            keyValue : "*"
        };
        params = new URLSearchParams(params);

        fetch(url + params)
        .then((response) => response.json())
        .then((data) => {
            this.data = data;
            this.appliances = [];
            this.data.map((appl) => this.appliances.push(appl[0].applianceType));
        })
        .catch(error => {
            console.error(error); // if there's an error, it will be logged to the console
        });
        await this.requestUpdate();
    }

    render() {
        this.data = "None"

        return html`
            <ha-card class="Appl-Type-Card">
                <div class="SingleEntry">
                    <div class="description" id="descr"> Appliance Type : </div>
                    <ha-select class="type_sel" id="type_sel" label="Choose type" @selected=${this._onScheduleSelected}>+
                        ${this.appliances.map((item) => html`<mwc-list-item .value=${item}>${item}</mwc-list-item>`)}
                    </ha-select>
                    <mwc-button class="type_btn" label="Set" @click="${this.SetApplType}"></mwc-button>
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
            .type_btn{
                display: flex;
                margin-left: 5px;
                flex-wrap: wrap;
                align-content: center;
            }
        `
    ]

    static get styles() {
        return this.style;
    }
}
customElements.define("appl-type-card", ApplianceTypeCard);