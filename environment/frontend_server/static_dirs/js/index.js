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

const sortBtnClick = function(btn) {
	const tbody = btn.closest("table").querySelector("tbody");
	const th = btn.closest("th");
	const field = th.getAttribute("sort");
	const thead = th.closest("thead");

	const reverse = th.classList.contains("sorted") && !th.classList.contains("reverse");
	th.classList.toggle("reverse", reverse);
	for (let x of thead.querySelectorAll("[sort]")) {
		x.classList.toggle("sorted", x == th);
		x.querySelector("i").classList.toggle("text-secondary", x != th);
	}

	const sorted = Array.from(tbody.querySelectorAll(`[field=${field}`)).sort(function(a, b) {
		if (reverse) [a, b] = [b, a];
		[a, b] = [a.innerText.trim().toLowerCase(), b.innerText.trim().toLowerCase()];
		return parseFloat(a) == a ? parseFloat(a) - parseFloat(b) : a.localeCompare(b);
	});
	tbody.innerHTML = "";
	for (let x of sorted) tbody.append(x.closest("tr"));
}

const sortingTable = function(table) {
	for (let x of table.querySelectorAll("thead [sort]")) {
		x.innerHTML = `<label role="button">
			${x.innerHTML}
			<i class="fa-solid fa-sort-down${x.classList.contains("sorted") ? "" : " text-secondary"}"></i>
			<button type="button" onclick="sortBtnClick(this)" hidden></button>
		</label>`;
	}
}

const insertPayloadTable = function(table, {url, data, reverse=false}) {
	if (data) {
		const origin = new URL(url);
		const active = data.observations == "exploit_successful";
		const tr = document.createElement("tr");
		tr.classList.toggle("table-danger", active);
		tr.innerHTML = `
			<td field="num" class="text-end">${table?.querySelectorAll("tbody tr")?.length + 1}</td>
			<td field="method" class="text-center">${data.method}</td>
			<td field="url"><a href="${url}" data-bs-toggle="tooltip" data-bs-title="${origin.host}">${origin.pathname}</a></td>
			<td field="payload">${data.payload}</td>
		`;
		new bootstrap.Tooltip(tr.querySelector("td[field=url] a"));

		if (reverse) {
			table?.querySelector("tbody")?.prepend(tr);
		} else {
			table?.querySelector("tbody")?.append(tr);
		}

	}
}

const insertURLTable = function(table, {url, data, reverse=false}) {
	if (data) {
		const origin = new URL(url);
		const tr = document.createElement("tr");
		tr.innerHTML = `
			<th field="num" class="text-end">${table.querySelectorAll("tbody tr").length + 1}</th>
			<td field="url"><a href="${url}" data-bs-toggle="tooltip" data-bs-title="${origin.host}">${origin.pathname}</a></td>
			<td field="payloads" class="text-center">${data.payloads || "-"}</td>
			<td field="vulnerabilities" class="text-center">${data.vulnerabilities || "-"}</td>
		`;
		new bootstrap.Tooltip(tr.querySelector("td[field=url] a"));

		if (reverse) {
			table?.querySelector("tbody")?.prepend(tr);
		} else {
			table?.querySelector("tbody")?.append(tr);
		}
	}
}

const getCanvas = function({canvas, config}) {
	return new Chart(canvas.getContext("2d"), config);
}
const addChartData = function(chart, {labels, data}) {
	chart.data.labels.push(...labels);
	chart.data.datasets[0].data.push(...data);
	chart.update();
}
const resetChart = function(chart) {
	chart.data.labels = [];
	chart.data.datasets.forEach((dataset) => {
		dataset.data = [];
	})
	chart.update();
}



let theme = document.documentElement.getAttribute("data-bs-theme");
if (!["light", "dark"].includes(theme)) {
	document.documentElement.setAttribute("data-bs-theme", window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
}

window.addEventListener("DOMContentLoaded", function() {
	for (let table of document.querySelectorAll("table")) sortingTable(table);
})
