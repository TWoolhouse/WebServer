const icycle = (function () {

    let collections = new Map();

    function scan(name="icycle") {
        for (const elm of document.getElementsByClassName("icycle")) {
            if (!collections.has(elm)) {
                let time = elm.getAttribute("ice");
                let func = cycle_next.bind(cycle_next, elm);
                collections.set(elm, setInterval(func, time === null ? 1000 : parseInt(time)));
            }
        }
    }

    function cycle_next(container) {
        let elms = Array.from(container.getElementsByClassName("ice"));
        for (const elm of elms) {
            if (elm.getAttribute("ice") != null) {
                elm.removeAttribute("ice");
                elms[(elms.indexOf(elm)+1) % elms.length].setAttribute("ice", 1);
                break;
            }
        }
    }

    scan();

})();
