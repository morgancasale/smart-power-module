import "https://unpkg.com/wired-card@2.1.0/lib/wired-card.js?module";
import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

class SocketButton extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      route: { type: Object },
      panel: { type: Object },
    };
  }

  render() {
    return html`
        <div class="name">Presa 0 </div>
    `;
  }

  static get styles() {
    return css`
        :host{
            width: 100px;
            height: 100px;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-content: center;
        }
        
        :host{
            box-sizing: border-box;
            background-color: var(--btn-back-color);
            border-radius: 12px;
            border-width: 0.1px;
            border-style: solid;
            border-color: var(white);
            position: relative;
            width: 90%;
            aspect-ratio: 1;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-content: center;
            margin-block-end: 0px;
        }
    `;
  }
}
customElements.define("socket-button", SocketButton);