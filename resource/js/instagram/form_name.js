const form_name = (function (elm) {
    elm.onsubmit = (function () {
        let v = document.getElementsByName("chatname")[0].value;
        while (v.includes(" ")) {
            v = v.replace(" ", "");
        }
        this.setAttribute("action", "/ig/" + v);
    });
});