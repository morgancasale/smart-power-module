import {
    LitElement,
    html,
    css
} from "https://cdn.skypack.dev/lit-element@2.4.0/lit-element.js";

//import { unsafeHTML } from 'https://cdn.skypack.dev/lit@2.4.0/directives/unsafe-html.js';
import "https://ajax.googleapis.com/ajax/libs/jquery/3.6.3/jquery.min.js";

import "./socket-settings.js";
import "./house-settings.js";

class MainPage extends LitElement {
    static get properties() {
        return {
            hass: { type: Object, attribute: false },
            narrow: { type: Boolean },
            route: { type: Object },
            panel: { type: Object },
            devicesData: { type: Object },
            houseData: { type: Object },
            loadSocketSettings: { type: Boolean }
        };
    }
    
    constructor(){
        super();
        window.location.hash = "";
        this.devicesData = {};
        this.houseData = {};
        this.errState = false;
        this.baseState = window.location.pathname + window.location.search;
    }

    catalogPort = 8099;

    onHashChange(){
        var main_page = window.document.querySelector("body");
        main_page = main_page.querySelector("home-assistant").shadowRoot
        main_page = main_page.querySelector("home-assistant-main").shadowRoot.querySelector("main-page");

        if(window.location.hash == ""){
            window.removeEventListener('hashchange', main_page.onHashChange);
            main_page.hide_settings();
        }
    }

    async hide_settings(){        
        //history.pushState("", document.title, window.location.pathname + window.location.search);
        //window.history.replaceState([this.baseState], "miao");

        this.fetchData();
        this.shadowRoot.getElementById("container").style.justifyContent = "";
        
        var house_el = this.shadowRoot.getElementById("house-settings");
        if(house_el != null){
            house_el.style.display = "none";
        }
        var socket_el = this.shadowRoot.getElementById("socket-settings");
        if(socket_el != null){
            socket_el.style.display = "none";
        }

        this.shadowRoot.getElementById("btn_cont").style.display = "none";
        this.shadowRoot.getElementById("offline_text").style.display = "none";

        this.shadowRoot.getElementById("main-page").style.display = "flex";

        this.loadSocketSettings = false;
        this.loadHouseSettings = false;

        this.shadowRoot.getElementById("gen_settings_button").style.display = "block";

        if(socket_el != null){ this.resetDelState(); }
        this.resetSavedState();

        this.reRender();
        await this.requestUpdate();
    }

    async reRender(){
        await this.render();
        await this.requestUpdate();
        await new Promise(r => setTimeout(r, 1));
    }

    getSocketData(socket_name){
        return this.devicesData.find(el => el["deviceName"] == socket_name);
    }

    async show_socket_settings(socket) {
        window.location.hash = "#settings";
        this.setMobileTheme();

        this.socketData = this.getSocketData(socket.deviceName);
        this.extDeviceData = this.socketData;
        this.loadSocketSettings = true;
        await this.reRender();

        this.shadowRoot.getElementById("socket-settings").setData(this.socketData);
        this.shadowRoot.getElementById("main-page").style.display = "none";
        this.shadowRoot.getElementById("gen_settings_button").style.display = "none";

        this.shadowRoot.getElementById("container").style.justifyContent = "center";
        this.shadowRoot.getElementById("socket-settings").style.display = "flex";
        this.shadowRoot.getElementById("btn_cont").style.display = "flex";

        if(!socket.online){
            this.shadowRoot.getElementById("offline_text").style.display = "flex"; 
        }
        
        window.addEventListener('hashchange', this.onHashChange);
    }

    async show_house_settings(){
        window.location.hash = "#settings";
        this.setMobileTheme();

        this.loadHouseSettings = true;
        await this.requestUpdate();

        //this.shadowRoot.getElementById("house-settings").setData(this.houseData);
        this.shadowRoot.getElementById("main-page").style.display = "none";
        this.shadowRoot.getElementById("gen_settings_button").style.display = "none";

        this.shadowRoot.getElementById("container").style.justifyContent = "center";
        this.shadowRoot.getElementById("house-settings").style.display = "flex";
        this.shadowRoot.getElementById("btn_cont").style.display = "flex";

        
        window.addEventListener('hashchange', this.onHashChange);
    }

    setMobileTheme() {
        //var window = document.querySelectorAll("home-assistant")[0].shadowRoot.querySelectorAll("home-assistant-main")[0].shadowRoot.querySelectorAll("app-drawer-layout")[0].shadowRoot.querySelector("#contentContainer");
        var content = this.parentElement.parentElement.parentElement;
        var width = parseFloat(getComputedStyle(content).getPropertyValue('width'));

        var cont = this.shadowRoot.querySelector("#container");

        cont.style.setProperty("--btn-cont-width", String(width));

        if(width < 584){
            var zoom = width/584-0.01;
            content.style.setProperty("--content-zoom", String(zoom));
            cont.style.setProperty("--ha-card-border-radius", "0px");
            cont.style.setProperty("--pd-top", "0px");
            cont.style.setProperty("--card-width", "100%");
            cont.style.setProperty("--side-bd", "none");
            
            cont.style.setProperty("--btn-zoom", "1.5");
        } else {
            content.style.setProperty("--content-zoom", String(1));
            cont.style.setProperty("--ha-card-border-radius", "");
            cont.style.setProperty("--pd-top", "56px");            
            cont.style.setProperty("--card-width", "584px");
            cont.style.setProperty("--side-bd", "");

            cont.style.setProperty("--btn-zoom", "1");
        }
    }

    async loadHACards() {
        const helpers = await window.loadCardHelpers();
        helpers.createRowElement({ type: "input-datetime-entity" });
        helpers.createRowElement({ type: "input-button-entity" });
        helpers.importMoreInfoControl("light");

        //this.shadowRoot.getElementById("socket-settings").setData();
    }

    errorHandler(ev){
        ev.preventDefault();
        this.errState = ev.detail.message;
    }

    sendNotification(msg, title="Smart Sockets"){
        this.hass.callService("notify", "persistent_notification", {message: msg, title: title});
    }

    SavedState(success){
        if(success){
            var tick = this.shadowRoot.getElementById("okTick");
            tick.style.display = "block";
            tick.icon = "mdi:check";
            tick.style.color = "";

            var text = this.shadowRoot.getElementById("save_btn_text");
            text.innerText = "Saved";
            text.style.color = "";
        } else {
            var tick = this.shadowRoot.getElementById("okTick");
            tick.style.display = "block";
            tick.icon = "mdi:window-close";
            tick.style.color = "red";

            var text = this.shadowRoot.getElementById("save_btn_text");
            text.style.color = "red";
            text.innerText = "Error";
        }
    }

    resetDelState(){
        var settings = this.shadowRoot.getElementById("socket-settings");
        [0, 1, 2].map((i) =>{
            var scheduling = settings.shadowRoot.getElementById("sched" + (i+1).toString());
            ["OFF", "ON"].map((mode) =>{
                var scheduler = scheduling.shadowRoot.getElementById("sch_"+mode+"_card");
                scheduler.resetDelState();
            });
        });
    }

    resetSavedState(){
        var tick = this.shadowRoot.getElementById("okTick");
        tick.style.display = "none";
        tick.icon = "mdi:check";
        tick.style.color = "";

        var text = this.shadowRoot.getElementById("save_btn_text");
        text.innerText = "Save";
        text.style.color = "";
    }

    getBodyResult(data){
        return data.split("<p>")[1].split("</p>")[0];
    }

    save_socket_settings(){
        this.socketData = this.shadowRoot.getElementById("socket-settings").save();
        this.socketData.deviceID = this.extDeviceData.deviceID;

        var cond = (this.socketData.deviceName != this.extDeviceData.deviceName) | (this.socketData.deviceName == null);
        this.socketData.deviceName = (cond) ? this.socketData.deviceName : this.extDeviceData.deviceName;

        this.extDeviceData.deviceName = this.socketData.deviceName;

        var url = "http://" + this.catalogAddress + ":" + String(this.catalogPort) + "/setDeviceSettings";
        var request = {
            method: "PUT", // *GET, POST, PUT, DELETE, etc.
            mode: "cors", // no-cors, *cors, same-origin
            cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
            credentials: "same-origin", // include, *same-origin, omit
            headers: {
                "Content-Type": "application/json",
                // 'Content-Type': 'application/x-www-form-urlencoded',
            }, // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
            body: JSON.stringify([this.socketData])
        };
        
        if(!this.errState){
            fetch(url, request)
            .then((response) => {
                this.SavedState((this.response=response).ok);
                return response.text();
            })
            .then((txt) => {
                if(!this.response.ok){
                    throw new Error(this.getBodyResult(txt));
                }
            })
            .catch(error => {
                var msg = "An error occured while saving Sockets settings: \n\t" + error.message;
                this.sendNotification(msg);
                throw new Error(msg);
            });
        }
    }

    save_house_settings(){
        var newHouseData = this.shadowRoot.getElementById("house-settings").save();
        Object.assign(newHouseData, { houseID : this.houseData.houseID })

        var url = "http://" + this.catalogAddress + ":" + String(this.catalogPort) + "/setHouseSettings";
        var request = {
            method: "PUT", // *GET, POST, PUT, DELETE, etc.
            mode: "cors", // no-cors, *cors, same-origin
            cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
            credentials: "same-origin", // include, *same-origin, omit
            headers: {
                "Content-Type": "application/json",
                // 'Content-Type': 'application/x-www-form-urlencoded',
            }, // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
            body: JSON.stringify([newHouseData])
        };
        
        if(!this.errState){
            fetch(url, request)
            .then((response) => {
                this.SavedState((this.response=response).ok);
                return response.text();
            })
            .then((txt) => {
                if(!this.response.ok){
                    throw new Error(this.getBodyResult(txt));
                }
            })
            .catch(error => {
                var msg = error.message;
                this.sendNotification(msg);
                throw new Error("An error occured while saving House settings:\n\t" + error.message);
            });
        }
    }

    save(){
        try{
            if(this.loadHouseSettings){
                this.save_house_settings();
            } else if(this.loadSocketSettings){
                this.save_socket_settings();
            }
        } catch(e){
            var msg = "An error occured while saving settings: \n\t" + e.message
            this.sendNotification(msg);
        }
    }

    fetchSocketSettings(){
        var hassStates = this.hass.states;
        this.catalogAddress = hassStates["sensor.local_ip"]["state"];

        var url = "http://" + this.catalogAddress + ":" + String(this.catalogPort) + "/getInfo?";
        var params = {
            table : "DeviceSettings",
            keyName : "deviceID",
            keyValue : "*"
        };
        params = new URLSearchParams(params);

        fetch(url + params)
        .then((response) => {
            if(response.ok){
                return (this.response=response).json();
            } else {
                return (this.response=response).text();
            }
        })
        .then((result) => {
            if(!(typeof result === 'string' || result instanceof String)){
                this.devicesData = result;
                this.sockets = [];
                this.devicesData.map((socket) => 
                    this.sockets.push({deviceName : socket["deviceName"], online : socket["Online"]})
                );
            } else {
                throw new Error(this.getBodyResult(result));
            }
        })
        .catch(error => {
            var msg = "An error occured while retriving Socket Settings: \n\t" + error.message;
            this.sendNotification(msg);
            throw new Error(msg);
        });
    }

    fetchHouseSettings(){
        var url = "http://" + this.catalogAddress + ":" + String(this.catalogPort) + "/getInfo?";
        var params = {
            table : "HouseSettings",
            keyName : "houseID",
            keyValue : "H1"
        };
        params = new URLSearchParams(params);

        try{
            fetch(url + params)
            .then((response) => {
                if(response.ok){
                    return (this.response=response).json();
                } else {
                    return (this.response=response).text();
                }
            })
            .then((result) => {
                if(!(typeof result === 'string' || result instanceof String)){
                    this.houseData = result[0];
                } else {
                    throw new Error(this.getBodyResult(result));
                }
            })
            .catch(error => {
                var msg = "An error occured while retriving House settings: \n\t" + error.message;
                this.sendNotification(msg);
                throw new Error(msg);
            });
        } catch(e){
            throw e;
        }
    }

    fetchData(){ // Fetch sockets settings
        try{
            this.fetchSocketSettings();
            this.fetchHouseSettings();
        } catch(e){
            var msg = "An error occurred while fetching settings: \n\t" + e.message;
            this.sendNotification(msg);
            alert(msg);
        }
    }

    connectedCallback() {
        super.connectedCallback();
        this.devicesData = false;
        this.houseData = false;
        this.loadSocketSettings = false;
        this.loadHouseSettings = false;
        this.fetchData();
    }

    render() {
        if(!this.devicesData | !this.houseData){
            return html`
                <div> Loading... </div>
            `;
        } else {
            //this.setMobileTheme();
            return html`
                <div id="main-page" class="main-page" @click=${this.loadHACards} @hide_settings=${this.hide_settings}>
                    ${this.sockets.map((item) => {
                        var color = "color: " + (item.online ? "" : "red");
                        return html`
                            <div class="child">
                            <ha-card outlined class="socket_button" @click="${() => this.show_socket_settings(item)}">
                                <div name="button_text" class="button_text" style=${color}>${item.deviceName}</div>
                            </ha-card>
                            </div>
                        `
                    })}
                </div>
                
                <div class="container" id="container" @err_occ=${this.errorHandler} @click=${this.resetSavedState}>
                    ${this.loadSocketSettings ? html`<socket-settings id="socket-settings" class="settings" .hass=${this.hass} .extData=${this.extDeviceData}></socket-settings>` : ""}
                    
                    ${this.loadHouseSettings ? html`<house-settings id="house-settings" class="settings" .hass=${this.hass} .extData=${this.houseData}></house-settings>` : ""}

                    <div class="btn btn_cont" id="btn_cont">
                        <mwc-button class="back_btn" id="back_btn" @click=${this.hide_settings}>
                            <ha-icon class="arrowLeft" id="arrowLeft" icon="mdi:arrow-left"></ha-icon>
                        </mwc-button>
                        <div id="offline_cont" class="offline_cont">
                            <div id="offline_text" class="offline_text">OFFLINE</div>
                        </div>
                        <mwc-button class="save_btn" id="save_btn" @click=${this.save}>
                            <ha-icon class="okTick" id="okTick" icon="mdi:check"></ha-icon>
                            <div id="save_btn_text">Save</div>
                        </mwc-button>
                    </div>                    
                </div>                

                <div class="gen_settings_button" id="gen_settings_button" @click=${this.show_house_settings}>
                    <div class="icon_dot" id="icon_dot">
                        <ha-icon class="cog" id="cog" icon="mdi:cog"></ha-icon> 
                    </div>
                </div>
            `;
        }
    }

    static get styles() {
        return css`
            .container{                                
                zoom: var(--content-zoom);
                display: flex;
                flex-flow: column wrap;
                align-content: center;
            }
            
            .main-page{
                display: flex;
                margin-top: 20px;
                flex-wrap: wrap;
                justify-content: center;   
            }

            .child{
                width: 100px;
                height: 100px;
                color: white;
                display: flex;
                flex-wrap: wrap;
                align-content: center;
                justify-content: center;
            }

            .socket_button{
                width: 90%;
                aspect-ratio: 1;
                display: flex;
                flex-wrap: wrap;
                align-content: center;
                justify-content: center;
            }

            .settings{
                display: none;
                padding-top: var(--pd-top);
            }

            .btn{
                zoom: var(--btn-zoom);
            }

            .btn_cont{
                margin-top: 10px;
                display: none;
                width: var(--btn-cont-width);
            }

            .button_text{
                text-align: center;
            }

            .offline_cont{
                margin: auto;
            }
            
            .offline_text{
                display: none;
                color: #f04c41;
            }

            .okTick{
                display: none;
                padding-right: 5px;
            }

            .gen_settings_button{
                zoom: 1.2;
                position: fixed;
                bottom: 20px;
                right: 20px;
            }

            .icon_dot{
                background-color: var(--primary-color);
                aspect-ratio: 1;
                width: 40px;
                border-radius: 50%;
                display: flex;
                flex-wrap: wrap;
                align-content: center;
                justify-content: center;
            }
        `;
    }
}

customElements.define("main-page", MainPage);