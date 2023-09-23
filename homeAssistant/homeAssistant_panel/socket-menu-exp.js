import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
    LitElement,
    html,
    css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { generalStyles } from "./general_styles.js";

class SocketMenuExp extends LitElement {
    static get properties() {
        return {
            socket_pos: { type: String },
            hass: { type: Object },
            narrow: { type: Boolean },
            route: { type: Object },
            panel: { type: Object },
            socket: { type: String },
            socketState: { type: Boolean }
        };
    }
    constructor(){
        super();
        this.socketState = true;
    }

    sendEvent(event_name, event_msg) {
        let Event = new CustomEvent(event_name, {
            detail: { message: event_msg },
            bubbles: true,
            composed: true
        });
        this.dispatchEvent(Event);
    }

    show_socket_stgs(){
        var msg = {
            socket : this.socket,
            state : true
        }
        if(this.socketState) this.sendEvent("show_socket_stgs", msg);
    }

    async offSocket(){
        var btn = this.shadowRoot.getElementById("off_socket_btn");
        await new Promise(r => setTimeout(r, 1));

        this.socketState = btn.checked;

        if(this.socketState){
            this.shadowRoot.getElementById("chevron").style.display = "flex";
            this.shadowRoot.getElementById("icon_dot").style.backgroundColor = "var(--primary-color)";
        } else {
            var msg = {
                socket : this.socket,
                state : btn.checked
            }
            this.sendEvent("offSocket", msg);

            this.shadowRoot.getElementById("chevron").style.display = "none";
            this.shadowRoot.getElementById("icon_dot").style.backgroundColor = "#747c75";
        }
    }

    setData(data){
        this.data = data;
        var btn = this.shadowRoot.getElementById("off_socket_btn");
        if(btn.checked != data){
            btn.click();
        }
    }

    save(){
        return +this.socketState;
    }

    render() {
        return html`
            <div class="menu_cont">
                <div class="socket_icon" id="socket_icon">
                    <div class="icon_dot" id="icon_dot">
                        <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><title>power-socket-de</title><path d="M4.22 2A2.22 2.22 0 0 0 2 4.22V19.78C2 21 3 22 4.22 22H19.78A2.22 2.22 0 0 0 22 19.78V4.22C22 3 21 2 19.78 2H4.22M11 4.07V6H13V4.07A8 8 0 0 1 20 12A8 8 0 0 1 13 19.93V18H11V19.93A8 8 0 0 1 4 12A8 8 0 0 1 11 4.07M7.5 10.5A1.5 1.5 0 0 0 6 12C6 12.83 6.66 13.5 7.5 13.5A1.5 1.5 0 0 0 9 12A1.5 1.5 0 0 0 7.5 10.5M16.5 10.5A1.5 1.5 0 0 0 15 12A1.5 1.5 0 0 0 16.5 13.5A1.5 1.5 0 0 0 18 12A1.5 1.5 0 0 0 16.5 10.5Z" /></svg>
                    </div>
                </div>
                <div class="description" id="socket_name">${this.socket_pos}</div>
                <div class="button_cont">
                    <ha-switch id="off_socket_btn" @click="${this.offSocket}" checked></ha-switch>
                </div>
                <div class="socket_arrow" id="socket_arrow" @click="${() => this.show_socket_stgs()}">
                    <ha-icon class="arrow" id="chevron" icon="mdi:chevron-down"></ha-icon>              
                </div>
            </div>
        `;
    }

    static style = [
        generalStyles,

        css`
            .menu_cont{
                display: flex;
            }

            .description{
                width: 108px;
            }

            .socket_icon{
                padding-right: 20px;
                display: flex;
                flex-wrap: wrap;
                align-content: center;
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

            .icon{
                width: 75%;
                fill: white;
            }

            .socket_arrow{
                width: 200px;
                display: flex;
                flex-wrap: wrap;
                margin-left: auto;
                place-content: center flex-end;
            }
            
            .arrow{
                color: var(--primary-text-color);
                font-size: 30px;
            }

            .button_cont{
                display: flex;
                flex-wrap: wrap;
                align-content: center;
            }

        `
    ]

    static get styles() {
        return this.style
    }

}
customElements.define("socket-menu-exp", SocketMenuExp);