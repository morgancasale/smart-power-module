import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
  LitElement,
  html,
  css
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { generalStyles } from "./general_styles.js";

import "./electric-meter-stgs.js"

class HouseSettings extends LitElement {
    static get properties() {
        return {
            hass : { type : Object },
            narrow : { type : Boolean },
            route : { type : Object },
            panel : { type : Object },
            socket_name : { type : String },
            extData : { type: Object }
        };
    }

    constructor(){
        super();
        this.outData = {
            houseName : "",
            powerLimit : 0
        };
    }
    
    save(){
        try{
            var houseName = this.shadowRoot.getElementById("house_input_field").value;
            houseName = (houseName !="") ? houseName : this.extData.houseName;
            Object.assign(this.outData, { houseName : houseName });

            var powerLimit = this.shadowRoot.getElementById("el_meter_stgs").save();
            Object.assign(this.outData, { powerLimit : powerLimit });

            return this.outData;
        } catch(e){
            throw new Error("An error occurred while saving House settings: \n\t" + e.message);
        }
    }

    render() {
        return html`
            <ha-card outlined class="card" id="card" @offSocket=${this.ShowSocketHandler}>
                <ha-card>
                    <div class="SingleEntry" id="change_house_name">
                        <div class="description">Change house name:</div>
                        <div class="house_name_input">
                            <ha-form>
                                <ha-textfield id="house_input_field" label=${this.extData.houseName}>Name</ha-textfield>
                            </ha-form>
                        </div>
                    </div>
                </ha-card>
                <ha-card>
                    <electric-meter-stgs id="el_meter_stgs" label=${this.extData.powerLimit}></electric-meter-stgs>
                </ha-card>
            </ha-card>
        `;
    }

    static style = [
        generalStyles,

        css`
            .c_card{
                margin-bottom: 5px;
            }

            .SingleEntry{
                width: 542px;
                height: 72px;
                display: flex;
                padding-left: 20px;
                padding-right: 20px;
                align-content: center;
                flex-wrap: wrap;
            }

            .dev_name_input{
                display: flex;
                flex-wrap: wrap;
                align-content: center;
                margin-left: auto;
            }

            .button_cont{
                margin-left: auto;
                display: flex;
                flex-wrap: wrap;
                align-content: center;
            }

            .socket_stgs{
                display: none;
                flex-wrap: wrap;            
            }

            .appl-type-card{
                display: none;
            }

            .fault_beh{
                display: none;
            } 
        `
    ]

    static get styles() {
        return this.style
    }
}
customElements.define("house-settings", HouseSettings);