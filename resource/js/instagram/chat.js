const jump = (function (h) {
    document.getElementById("m" + h).scrollIntoView(true);
});

const chat = (function () {

    let chat = document.getElementById("chat");

    const trigger_onload = (function () {
        let event = new Event("load");
        for (let elm of chat.querySelectorAll(".onload")) {
            elm.dispatchEvent(event);
            elm.classList.remove("onload");
            if (elm.classList.length < 1) {
                elm.removeAttribute("class");
            }
            elm.removeAttribute("onload");
        }
    })

    const msg_request = (function () {

        let active_req = 0;
        let buttons_load = [document.getElementById("btn_prev"), document.getElementById("btn_next")];

        const perfrom_request = (function (val) {
            active_req += val;
            if (active_req > 0) {
                // Disable Buttons
                for (let btn of buttons_load) {
                    btn.setAttribute("disabled", "");
                    btn.innerText = "Loading ...";
                }
            } else {
                // Activate Buttons
                active_req = 0;
                for (let btn of buttons_load) {
                    btn.removeAttribute("disabled");
                    btn.innerText = "Load More";
                }
            }
        });

        const group_request = (function (map, jid) {
            let xhr = new XMLHttpRequest();
            xhr.onload = (function () {
                perfrom_request(-1);
                let c = this.responseXML.body.children;
                let len = c.length;
                for (let index = 0; index < len; index++) {
                    const child = c[0];
                    try {
                        let id = child.getAttribute("id").substring(1);
                        chat.replaceChild(child, map.get(id));
                    } catch (TypeError) {
                        console.error("Failed to Read:", TypeError, child);
                    }
                    if (jid) {
                        jump(jid);
                    }
                }
                trigger_onload();
                external_data.process();
            });
            xhr.onerror = (function () {
                external_data.clear();
                for (const node of map.values()) {
                    chat.removeChild(node);
                }
                perfrom_request(-1);
            })
            let ids = Array.from(map.keys()).join(";");
            xhr.open("GET", "/ig/" + CHAT_NAME + "?msg=1&elm=" + ids);
            xhr.responseType = "document";
            perfrom_request(1);
            xhr.send();
        });

        const single_request = (function (node, id) {
            let map = new Map();
            map.set(id.toString(), node);
            return group_request(map);
        });

        const create_blank = (function (node, id) {
            let elm = document.createElement("div");
            elm.setAttribute("id", "m" + id);
            elm = chat.insertBefore(elm, node);
            return elm;
        });

        const load = (function (node, id) {
            single_request(create_blank(node, id), id);
        });

        const get_current = (function (dir) {
            if (dir) {
                return parseInt(chat.lastElementChild.getAttribute("id").substring(1));
            } else {
                return parseInt(chat.firstElementChild.getAttribute("id").substring(1));
            }
        });

        return {
            load: load,
            reload: (function (id) {
                let node = document.getElementById("m" + id);
                single_request(node, id);
            }),

            next: (function (amount) {
                let current_id = get_current(1);
                let map = new Map();
                for (let index = 0; index < amount; index++) {
                    current_id += 1;
                    map.set(current_id.toString(), create_blank(null, current_id));
                }
                group_request(map);
            }),
            prev: (function (amount) {
                let current_id = get_current(0);
                let map = new Map();
                for (let index = 0; index < amount; index++) {
                    current_id -= 1;
                    map.set(current_id.toString(), create_blank(chat.firstElementChild, current_id));
                }
                group_request(map, current_id + amount);
            }),
        };
    })();

    const msg_format = (function () {
        return {
            "eid": (function (id) {
                let node = document.getElementById("m" + id);
                let user = node.getElementsByClassName("user")[0];
                if (user.getElementsByClassName("eid").length != 0) {
                    return;
                }
                let eid = document.createElement("p");
                eid.setAttribute("class", "eid");
                eid.innerHTML = "[" + id + "]";
                user.appendChild(eid);
            }),
            "shr_more": (function (node, text) {
                node.onclick = null;
                let prt = node.parentElement;
                prt.removeChild(node);
                while (text.includes("\n")) {
                    text = text.replace("\n", "<br>")
                }
                prt.firstElementChild.innerHTML += text;
            }),
        };
    })();

    const external_data = (function () {
        let queue_media = new Map();

        const media_request = (function (queue) {
            if (queue.size < 1) {
                return;
            }
            let xhr = new XMLHttpRequest();
            xhr.onload = (function () {
                let c = this.responseXML.body.children;
                const len = c.length;
                for (let index = 0; index < len; index++) {
                    const child = c[0];
                    try {
                        let old = queue.get(child.getAttribute("id")).node;
                        child.removeAttribute("id");
                        old.replaceWith(child);
                    } catch (TypeError) {
                        console.error("Failed to Read:", TypeError, child);
                    }
                }
            });
            xhr.onerror = (function () {
                for (const elm of queue.values()) {
                    elm.node.classList.replace("igdata", "err");
                    media_error(elm.node, false);
                }
            })
            let args = [];
            queue.forEach((function (value, key) {
                args.push(value.type+key);
            }));
            xhr.open("GET", "/ig/" + CHAT_NAME + "?ig=1&elm=" + args.join(";"));
            xhr.responseType = "document";
            xhr.send();
        });

        const clear = (function () {
            queue_media = new Map();
        });

        const media_error = (function (node, self=true) {
            node.onerror = null;
            const replace = node.getAttribute("alt");
            if (self) {
                node.replaceWith(replace);
            } else {
                node.innerHTML = replace;
            }
        });

        const replace_image = (function (node) {
            node.onerror = null;
            node.setAttribute("src", node.getAttribute("alt"));
        });

        return {
            mda: (function (node, id, type) {
                queue_media.set(id.toString(), {
                    node: node,
                    type: type
                });
            }),
            mda_err: media_error,
            img_err: replace_image,
            process: (function () {
                media_request(queue_media);
                clear();
            }),
            clear: clear,
        };
    })();

    const funcs = {
        load: trigger_onload,
        req: msg_request,
        msg: msg_format,
        ext: external_data,
    };
    return funcs;

})();