/** @odoo-module **/
import {Component, onWillStart, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

class FloatingButton extends Component {
    static template = "ps_floating_button.FloatingButton";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            buttonUrl: null,
            x: null,
            y: null,
        });

        onWillStart(async () => {
            try {
                // Get button url
                this.state.buttonUrl = await this.orm.call(
                    "floating.button",
                    "get_button_url",
                    []
                );

                // Get button coordinates
                const coordinates = await this.orm.call(
                    "floating.button",
                    "get_button_coordinates",
                    []
                );

                this.state.x = coordinates.x;
                this.state.y = coordinates.y;
            } catch (error) {
                console.error("Error loading button parameters:", error);
            }
        });
    }

    onClick() {
        if (this.state.buttonUrl) {
            window.open(this.state.buttonUrl, '_blank');
        }
    }
}

registry.category("main_components").add("FloatingButton", {
    Component: FloatingButton,
});
