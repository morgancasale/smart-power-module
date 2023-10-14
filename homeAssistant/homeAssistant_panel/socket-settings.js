import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
  LitElement,
  html,
  css
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import {unsafeHTML} from 'https://unpkg.com/lit@2.4.0/directives/unsafe-html.js?module';

import "./scheduling-card.js";

import "./socket-menu-exp.js";

import "./max-power-card.js";

import "./parasitic-control.js";

import "./fault-control.js";

import "./appl-type-card.js";

import "./faulty-behaviour-card.js"

import { generalStyles } from "./general_styles.js";

class SocketSettings extends LitElement {
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

    pageTemplate = (children) =>`
        <div class="container" id="container">
            ${unsafeHTML(children)}
        </div>
    `;

    show_socket_stgs(num, show = true){
        var el = this.shadowRoot.getElementById("socket_stgs" + num);
        if((el.getAttribute("status") == "hidden") && show){
            el.style.display = "flex";
            el.setAttribute("status", "shown");
            this.shadowRoot.getElementById("socket_menu_exp" + num).shadowRoot.getElementById("chevron").setAttribute("icon", "mdi:chevron-up");
        } else{
            el.style.display = "none";
            el.setAttribute("status", "hidden");
            this.shadowRoot.getElementById("socket_menu_exp" + num).shadowRoot.getElementById("chevron").setAttribute("icon", "mdi:chevron-down");
        }
    }

    HideSockets(state){
        if(state){ //HPMode ON
            this.shadowRoot.getElementById("socket1").style.display = "none";
            this.show_socket_stgs(1, false);
            this.shadowRoot.getElementById("socket3").style.display = "none";
            this.show_socket_stgs(3, false);                                   //turning OFF left and right sockets
        } else { //HPMode OFF
            this.shadowRoot.getElementById("socket1").style.display = "block";
            this.shadowRoot.getElementById("socket3").style.display = "block"; //turning ON left and right sockets
        }
    }

    SetHPMode(data){
        var btn = this.shadowRoot.getElementById("HP_button");
        var btn_state = btn.checked;

        if(btn_state != data.HPMode){
            btn.click();
        }
    }

    async HPMode(){
        var btn = this.shadowRoot.getElementById("HP_button");
        
        await new Promise(r => setTimeout(r, 1));
        var state = btn.checked;
        this.HideSockets(state);
        if(state){ //HPMode ON
            this.shadowRoot.getElementById("appl-type-card").style.display = "flex";
            if(this.FaultBehActive){
                this.shadowRoot.getElementById("fault_beh").style.display = "flex";
            }
            this.outData.HPMode = true;
        } else {  //HPMode OFF
            this.shadowRoot.getElementById("appl-type-card").style.display = "none";
            this.shadowRoot.getElementById("fault_beh").style.display = "none";

            var par_ctrl = this.shadowRoot.getElementById("par_ctrl").shadowRoot;
            par_ctrl.querySelector("#mode_sel_cont").style.display = "none";
            par_ctrl.querySelector("#manual_thr").style.marginLeft = "";

            this.outData.HPMode = false;
        }
        this.shadowRoot.getElementById("appl-type-card").HPMode = this.outData.HPMode;
    }

    ShowApplType(){
        var par_ctrl = this.shadowRoot.getElementById("par_ctrl").shadowRoot;
        par_ctrl.querySelector("#mode_sel_cont").style.display = "flex";
        par_ctrl.querySelector("#manual_thr").style.marginLeft = "auto";
    }

    ShowFaultyBehaviour(){
        this.FaultBehActive = true;
        this.shadowRoot.getElementById("fault_beh").style.display = "flex";
    }

    ApplSetHandler(event){
        event.preventDefault();
        this.ShowApplType();
        this.ShowFaultyBehaviour();
    }

    ShowSocketHandler(event){
        event.preventDefault();
        var msg = event.detail.message;
        this.show_socket_stgs(msg.socket, msg.state);
    }

    getSavedData(element){
        var save_data = [];
        for(let i=1; i<4; i++){
            save_data[i-1] = this.shadowRoot.getElementById(element + i).save();
        }
        return save_data;
    }
    
    save(){
        try{
            var deviceName = this.shadowRoot.getElementById("dev_input_field").value;
            if(deviceName == ""){
                var deviceName = this.shadowRoot.getElementById("dev_input_field").label; 
            }
            this.outData.deviceName = (deviceName !="") ? deviceName : this.outData.deviceName;
            
            var sched_data = this.getSavedData("sched");
            if(JSON.stringify(sched_data) === JSON.stringify([null, null, null])){
                this.outData.scheduling = null;
            } else {
                this.outData.scheduling = sched_data;            
            }

            
            var offSocket_data = this.getSavedData("socket_menu_exp");
            Object.assign(this.outData, { enabledSockets : offSocket_data });
            
            Object.assign(this.outData, {"applianceType" : "None"});
            Object.assign(this.outData, {"FBControl" : false, "FBMode" : "Notify"});

            Object.assign(this.outData, this.shadowRoot.getElementById("max-pow").save());
            Object.assign(this.outData, this.shadowRoot.getElementById("fault-ctrl").save());
            Object.assign(this.outData, this.shadowRoot.getElementById("par_ctrl").save());
            if(this.outData.HPMode){
                Object.assign(this.outData, this.shadowRoot.getElementById("appl-type-card").save());
                Object.assign(this.outData, this.shadowRoot.getElementById("fault_beh").save());
            }

            return this.outData;
        } catch(e){
            throw new Error("An error occurred while saving some settings: \n\t" + e.message);
        }
    }

    setData(data){
        this.outData = Object.assign({}, data);
        this.data = data;
        this.SetHPMode(data);

        [0, 1, 2].map((i) =>{
            
            var schedData = [];
            if(this.data.scheduling != null){
                schedData = this.data["scheduling"].filter(el => el["socketID"] == i);
                Object.assign(schedData, {deviceID : this.data.deviceID, socketID : i})
            }
            this.shadowRoot.getElementById("sched" + (i+1).toString()).setData(schedData);

            this.shadowRoot.getElementById("socket_menu_exp" + (i+1).toString()).setData(this.data.enabledSockets[i]);
        });
        
        this.shadowRoot.getElementById("max-pow").setData({
            MPControl : this.data["MPControl"],
            maxPower : this.data["maxPower"],
            MPMode : this.data["MPMode"]
        });

        this.shadowRoot.getElementById("fault-ctrl").setData(this.data["faultControl"]);

        this.shadowRoot.getElementById("par_ctrl").setData({
            parControl : this.data["parControl"],
            parThreshold : this.data["parThreshold"],
            parMode : this.data["parMode"]
        });

        this.shadowRoot.getElementById("appl-type-card").setData(this.data["applianceType"]);

        this.shadowRoot.getElementById("fault_beh").setData({
            FBControl : this.data["FBControl"],
            FBMode : this.data["FBMode"]
        });
    }

    resetData(){
        this.setData(this.defaultData);
    }

    render() {    
        this.defaultData = {
            "deviceID" : null,
            "deviceName" : null,
            "HPMode" : false,
            "scheduling" : []
        }

        this.outData = this.defaultData;

        this.data = this.defaultData;

        return html`
            <ha-card outlined class="card" id="card" @appl_type_set="${this.ApplSetHandler}" @offSocket=${this.ShowSocketHandler}>
                <ha-card>
                    <div class="SingleEntry" id="change_device_name">
                        <div class="description">Change device name:</div>
                        <div class="dev_name_input">
                            <ha-form>
                                <ha-textfield id="dev_input_field" label=${this.extData.deviceName}>Name</ha-textfield>
                            </ha-form>
                        </div>
                    </div>
                </ha-card>
                <ha-card>
                    <div class="SingleEntry" id="HP_btn">
                        <div class="description" id="HP">High Power Mode</div>
                        <div class="button_cont">
                            <ha-switch id="HP_button" @click="${this.HPMode}"></ha-switch>
                        </div>
                    </div>
                </ha-card>

                <max-power-card id="max-pow" ></max-power-card>
                <fault-control id="fault-ctrl"  .HPMode=${this.data.HPMode}></fault-control>
                <parasitic-control id="par_ctrl"  .HPMode=${this.data.HPMode}></parasitic-control> 

                <ha-card>
                    <div class="socket" id="socket1">
                        <div class="SingleEntry" id="socket_menu1" @show_socket_stgs="${this.ShowSocketHandler}">
                            <socket-menu-exp id="socket_menu_exp1" style="width: 100%" .socket=${"1"} .socket_pos=${"Left Socket"}></socket-menu-exp>
                        </div>

                        <div class="socket_stgs" id="socket_stgs1" status="hidden">
                            <scheduling-card id="sched1" .hass=${this.hass} .socketID=${0} .HPMode=${this.data.HPMode}></scheduling-card>                        
                        </div>
                    </div>

                    <div id="socket2">
                        <div class="SingleEntry" id="socket_menu2" @show_socket_stgs="${this.ShowSocketHandler}">
                            <socket-menu-exp id="socket_menu_exp2" style="width: 100%" .socket=${"2"} .socket_pos=${"Center Socket"}></socket-menu-exp>
                        </div>

                        <div class="socket_stgs" id="socket_stgs2" status="hidden">
                            <scheduling-card id="sched2" .hass=${this.hass} .socketID=${1} .HPMode=${false}></scheduling-card>
                            <appl-type-card id="appl-type-card" class="appl-type-card" .hass=${this.hass} .socket_num=${"2"} .HPMode=${this.data.HPMode} .appl_type=${this.extData.applianceType}></appl-type-card>
                            <faulty-behaviour-card id="fault_beh" class="fault_beh" ></faulty-behaviour-card>
                        </div>
                    </div>

                    <div id="socket3" @appl_type_set="${this.ApplSetHandler}">
                        <div class="SingleEntry" id="socket_menu3" @show_socket_stgs="${this.ShowSocketHandler}">
                            <socket-menu-exp id="socket_menu_exp3" style="width: 100%" .socket=${"3"} .socket_pos=${"Right Socket"}></socket-menu-exp>
                        </div>

                        <div class="socket_stgs" id="socket_stgs3" status="hidden">
                            <scheduling-card id="sched3" .hass=${this.hass} .socketID=${2} .HPMode=${this.data.HPMode}></scheduling-card>
                        </div>
                    </div>
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
customElements.define("socket-settings", SocketSettings);