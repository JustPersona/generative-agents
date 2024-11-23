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
		const tr = document.createElement("tr");
		tr.innerHTML = `
			<td field="method">${data.method}</td>
			<td field="vulnerability" class="text-danger text-center">${data.observations == "exploit_successful" ? '<i class="fa-solid fa-check"></i>' : ""}</td>
			<td field="payload">${data.payload}</td>
		`;
		if (reverse) {
			table?.querySelector("tbody")?.prepend(tr);
		} else {
			table?.querySelector("tbody")?.append(tr);
		}
	}
}
