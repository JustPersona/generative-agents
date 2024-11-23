const post = function(url, data, callback1, callback2) {
	let json = JSON.stringify(data);
	let xhr = new XMLHttpRequest();
	xhr.overrideMimeType("application/json");
	xhr.open('POST', url, true);
	xhr.setRequestHeader("X-CSRFToken", document.querySelector("input[name=csrfmiddlewaretoken]")?.value);
	xhr.addEventListener("load", function() {
		if (this.readyState === 4) {
			if (200 <= xhr.status && xhr.status < 300) {
				if (typeof callback1 === "function") {
					callback1(xhr);
				}
			} else {
				if (typeof callback2 === "function") {
					callback2(xhr);
				}
			}
		}
	});
	xhr.send(json);
}

const setPayload = function(table, data={}, reverse=false) {
	if (data) {
		const active = data.observations == "exploit_successful";
		const tr = document.createElement("tr");
		tr.classList.toggle("table-danger", active);
		tr.innerHTML = `
			<td field="method" class="text-center">${data.method}</td>
			<td field="payload">${data.payload}</td>
		`;
		if (reverse) {
			table?.querySelector("tbody")?.prepend(tr);
		} else {
			table?.querySelector("tbody")?.append(tr);
		}
	}
}

let theme = document.documentElement.getAttribute("data-bs-theme");
if (!["light", "dark"].includes(theme)) {
	document.documentElement.setAttribute("data-bs-theme", window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
}
