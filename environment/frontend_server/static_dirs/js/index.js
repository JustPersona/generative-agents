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

	const sorted = [...tbody.querySelectorAll(`[field=${field}]`)].sort(function(a, b) {
		if (reverse) [a, b] = [b, a];
		[a, b] = [a.innerText.trim().toLowerCase(), b.innerText.trim().toLowerCase()];
		return parseFloat(a) == a ? parseFloat(a) - parseFloat(b) : a.localeCompare(b);
	});
	for (let x of sorted) {
		const tr = x.closest("tr");
		const details = tr.nextElementSibling;
		tbody.append(tr);
		if (details?.classList.contains("details")) tr.after(details);
	}
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

const createPayloadTable = function(pen_code, {style}={}) {
	const table = document.createElement("div");
	table.innerHTML = `
		<div class="form-check">
			<input class="form-check-input" type="checkbox" id="only-vuln-${pen_code}" onclick="this.parentNode.classList.toggle('only-vuln', this.checked)">
			<label class="form-check-label" for="only-vuln-${pen_code}">Only Show Vulnerabilities</label>
		</div>
		<div id="payload-table-${pen_code}" class="table-responsive mt-2" style="max-height: 500px">
			<table class="table table-sm table-bordered table-hover m-0 position-relative text-nowrap" style="border-width: 2px">
				<thead class="sticky-top z-1">
					<tr>
						<th scope="col" class="text-center minimum" sort="num">#</th>
						<th scope="col" class="text-center minimum">Method</th>
						<th scope="col" class="text-center minimum">URL</th>
						<th scope="col">Payload</th>
					</tr>
				</thead>
				<tbody></tbody>
			</table>
		</div>
	`;

	if (style) {
		for (let key in style) {
			table.querySelector(`#payload-table-${pen_code}`).style.setProperty(key, style[key]);
		}
	}
	return table;
}

const insertPayloadTable = function(table, {url, data, reverse=false}) {
	if (data) {
		const num = table.querySelectorAll("& > tbody > tr:not(.details)")?.length + 1;
		const origin = new URL(url);
		const isVuln = data.observations == "exploit_successful";
		const tr = document.createElement("tr");
		tr.classList.toggle("table-danger", isVuln);
		tr.role = "button";
		tr.onclick = displayPayloadDetails;
		tr.innerHTML = `
			<td field="num" class="text-end">${num}</td>
			<td field="method" class="text-center">${data.method}</td>
			<td field="url"><a href="${url}" target="_blank" data-bs-toggle="tooltip" data-bs-title="${origin.host}">${origin.pathname}</a></td>
			<td field="payload" class="text-truncate" style="max-width: 0px;">${data.payload}</td>
		`;
		new bootstrap.Tooltip(tr.querySelector("td[field=url] a"));

		if (reverse) {
			table.querySelector("tbody")?.prepend(tr);
		} else {
			table.querySelector("tbody")?.append(tr);
		}

		const details = document.createElement("tr");
		details.className = "details";
		details.setAttribute("for", num);
		details.innerHTML = `
			<td colspan="1" class="shadow-none border-start-0 text-end">
				<label role="button" class="link-${isVuln ? "danger" : "secondary"}" data-bs-toggle="tooltip" data-bs-title="Hide">
					<i class="fa-solid fa-close fa-xl"></i>
					<button type="button" onclick="this.closest('tr').classList.remove('show')" hidden></button>
				</label>
			</td>
			<td colspan="999" class="p-0"></td>
		`;
		details.querySelector("td:last-child").append(createPayloadSubTable(data));

		const target = details.querySelector("[key=reasoning]");
		const vuln = target.cloneNode(true);
		vuln.setAttribute("key", "vulnerability");
		vuln.querySelector(".text-capitalize").innerHTML = "Vulnerability";
		vuln.querySelector(".align-middle > div").innerHTML = isVuln ? "Yes" : "No";
		target.before(vuln);
		tr.after(details);
	}
}

const createPayloadSubTable = function(data, border=true) {
	const disabled = ["step", "payload", "attack_name", "method", "observations", "timestamp"];
	const keys = {
		reasoning: "reason for above",
		html_differences: `Changed before/after Attack`,
	}
	const table = document.createElement("table");
	table.className = `sub table table-sm table-hover table-border${border ? "ed" : "less"} m-0 position-relative text-wrap`;
	table.innerHTML = "<tbody></tbody>";
	for (let key in data) {
		if (disabled.includes(key)) continue;
		const tr = document.createElement("tr");
		table.querySelector("tbody").append(tr);
		tr.setAttribute("key", key);
		tr.innerHTML = `
			<td class="text-end text-capitalize minimum">${(keys?.[key] || key).replace(/_/g, " ")}</td>
			<td class="p-0 align-middle"></td>
		`;
		if (typeof data[key] !== "object") {
			tr.querySelector("td:last-child").innerHTML = `<div class="px-2 py-1">${mdToHTML(data[key])}</div>`;
		} else {
			tr.querySelector("td:last-child").append(createPayloadSubTable(data[key], false));
		}
	}
	return table;
}

const mdToHTML = function(text) {
	return marked.parse(text);
}

const jsonToUl = function(json, elem="ul") {
	const container = document.createElement("div")
	container.className = "container";
	for (let key in json) {
		container.innerHTML = `
			<div class="row">
				<div class="col-1">${key}</div>
				<div class="col">${json[key]}</div>
			</div>
		`;
	}
	return container;
}

const jsonToUlOld = function(json, elem="ul") {
	const ul = document.createElement(elem);
	ul.className = "m-0 ps-3";
	for (let key in json) {
		const value = json[key];
		const li = document.createElement("li");
		li.innerHTML = `<span class="d-block ps-3" style="text-indent: -1rem">${parseInt(key) == key ? key*1+1 : key}: </span>`;
		li.className = "pb-0 text-wrap";
		if (typeof value === "object") {
			li.append(jsonToUlOld(value));
		} else {
			li.querySelector("span").innerHTML += value;
		}
		ul.append(li);
	}
	return ul;
}

const displayPayloadDetails = function(e) {
	const target = e.target;
	if (target.tagName == "A") return;

	const box = this.nextElementSibling;
	box.classList.toggle("show");
}

const insertURLTable = function(table, {url, data, reverse=false}) {
	if (data) {
		const origin = new URL(url);
		const tr = document.createElement("tr");
		tr.innerHTML = `
			<th field="num" class="text-end">${table.querySelectorAll("tbody tr").length + 1}</th>
			<td field="url"><a href="${url}" target="_blank" data-bs-toggle="tooltip" data-bs-title="${origin.host}">${origin.pathname}</a></td>
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
