const vol = (function () {

    let value = 0;
    const elms = {
        "display": [],
        "target": undefined,
    }

    const update_vol = (function (vol) {
        for (const elm of elms.display) {
            elm.value = elm.innerHTML = vol;
            //  = vol;
        }
    });

    const load = (function () {
        for (const volumes of document.getElementsByClassName("volume")) {
            if (!elms.target) {
                for (const e of volumes.getElementsByClassName("target")) {
                    elms.target = e;
                    break;
                }
            }
        }
        let list = [];
        if (elms.target) { list.push(elms.target); }
        for (const volumes of document.getElementsByClassName("volume")) {
            list = list.concat(Array.from(volumes.getElementsByClassName("display")));
        }
        elms.display = list;
        request("get", 0);
        console.log(elms);
    });

    const request = (function (type, amount) {
        if (amount === undefined) {
            amount = "";
        }
        let xhr = new XMLHttpRequest();
        xhr.onload = function () {
            let data = JSON.parse(this.responseText);
            // console.log(data);
            update_vol(data.volume)
        };
        xhr.open("POST", "/vol/cmd?v=vol");
        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.send("c=" + type + "&amt=" + amount);
    });

    return {
        load: load,
        move: request.bind(request, "scrub"),
        set: (function (val) {
            if (val === undefined) {
                val = elms.target.value;
            }
            request("set", val);
        }),
        sync: (function (val) {
            if (val === undefined) {
                val = elms.target.value;
            }
            request("sync", val);
        }),

        ply: request.bind(request, "media", 0),
        fwd: request.bind(request, "media", 1),
        rev: request.bind(request, "media", 2),
    };
})();