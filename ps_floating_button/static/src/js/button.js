/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class FloatingButton extends Component {
    static template = "ps_floating_button.FloatingButton";

    setup() {
        // User orm service to call ir.config_parameter.get_param
        this.orm = useService("orm");

        // State to store the button url
        this.state = useState({
            buttonUrl: null
        });

        onWillStart(async () => {
            this.state.buttonUrl = await this.orm.call(
                "ir.config_parameter",
                "get_param",
                ["ps_floating_button.button_url"]
            );
        });
    }

    // Function to handle button click
    onClick() {
        if (this.state.buttonUrl) {
            window.open(this.state.buttonUrl, '_blank');
        }
    }
}

registry.category("main_components").add("FloatingButton", {
    Component: FloatingButton,
});
