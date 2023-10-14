import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
    LitElement,
    html,
    css
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { generalStyles } from "./general_styles.js";

//import "https://unpkg.com/@material/web@1.0.0-pre.4/index.js?module"

//import "../ha-frontend/src/panels/lovelace/entity-rows/hui-input-datetime-entity-row"

class ElectricMeterStgs extends LitElement {
    static get properties() {
        return {
            hass: { type: Object },
            narrow: { type: Boolean },
            route: { type: Object },
            panel: { type: Object },
            label: { type: String }
        };
    }

    resetValid(){
        this.shadowRoot.getElementById("el_meter_input_field").invalid = false;
    }

    checkThreshold(data){
        if(data == null | isNaN(data)){
            this.shadowRoot.getElementById("el_meter_input_field").invalid = true;
            throw new Error("A value for the power limit must be entered.");
        } else if(data < 0){                
            this.shadowRoot.getElementById("el_meter_input_field").invalid = true;
            throw new Error("The power limit value must be positive.");
        }
    }

    save(){        
        var data = this.shadowRoot.getElementById("el_meter_input_field").value;
        data = (data != "") ? data : String(this.powerLimit);
        data = parseFloat(data);

        this.checkThreshold(data);
        
        return data;
    }

    render() {
        this.powerLimit = this.label;
        return html`
            <div class="el_meter_stgs SingleEntry" id="el_meter_stgs">
                <div class="description" id="power_descr"> House Power limit : </div>
                <ha-textfield class="el_meter_input_field" id="el_meter_input_field" @click=${this.resetValid} label=${this.label}>Power</ha-textfield>
                <div class="power_unit description" id="power_unit"> W </div>
            </div>
        `;
    }

    static style = [
        generalStyles,
        css`            
            .el_meter_stgs{
                flex-wrap: wrap;
                align-content: center;
                padding-bottom: 5px;
            }

            .el_meter_input_field{
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
customElements.define("electric-meter-stgs", ElectricMeterStgs);