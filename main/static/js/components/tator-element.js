const svgNamespace = "http://www.w3.org/2000/svg";

class TatorElement extends HTMLElement {
  constructor() {
    super();
    this._shadow = this.attachShadow({mode: "open"});
    
    const css = document.createElement("link");
    css.setAttribute("rel", "stylesheet");
    css.setAttribute("href", "/static/css/tator/tator.min.css");
    this._shadow.appendChild(css);

    css.addEventListener("load", evt => {
      this.style.visibility = "visible";
    });
  }

  connectedCallback() {
    this.style.visibility = "hidden";
  }
}
