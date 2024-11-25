const urlParams = location.search.slice(1).split("&").reduce((a, c) => {a[c.split("=")[0]] = c.split("=")[1];return a;}, {});



const toLocaleTimeString = function(datetime) {
	return datetime.toLocaleTimeString("en-US", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

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

const asyncPost = async function(url, data={}) {
	const response = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"X-CSRFToken": document.querySelector("input[name=csrfmiddlewaretoken]")?.value,
		},
		body: JSON.stringify(data),
	});
	return await response.json();
}

const api = async function(url="/api/") {
	const response = await fetch(url);
	return await response.json();
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

	const sorted = [...tbody.querySelectorAll(`[field="${field}"]`)].sort(function(a, b) {
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
			<label class="form-check-label" for="only-vuln-${pen_code}">Vulnerabilities</label>
		</div>
		<div id="payload-table-${pen_code}" class="table-responsive mt-2 modal-scroll modal-scroll-target">
			<table class="table table-sm table-bordered table-hover m-0 position-relative text-nowrap" style="border-width: 2px">
				<thead class="sticky-top z-1">
					<tr>
						<th scope="col" class="text-center minimum sorted" sort="num">#</th>
						<th scope="col" class="text-center minimum" sort="url">URL</th>
						<th scope="col" class="text-center minimum" sort="attack">Attack Type</th>
						<th scope="col" class="text-center minimum" sort="method">Method</th>
						<th scope="col" sort="payload">Payload</th>
					</tr>
				</thead>
				<tbody class="table-group-divider"></tbody>
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
	if (!data) return;

	const num = table.querySelectorAll("& > tbody > tr:not(.details)")?.length + 1;
	const origin = new URL(url);
	const isVuln = data.observations == "exploit_successful";
	const tr = document.createElement("tr");
	tr.classList.toggle("table-danger", isVuln);
	tr.role = "button";
	tr.onclick = displayPayloadDetails;
	tr.innerHTML = `
		<th field="num" class="text-end" scope="row">${num}</th>
		<td field="url"><a href="${url}" target="_blank" data-bs-toggle="tooltip" data-bs-title="${origin.host}" onclick="event.stopPropagation()">${origin.pathname}</a></td>
		<td field="attack" class="text-center">${data.attack_name}</td>
		<td field="method" class="text-center">${data.method}</td>
		<td field="payload" class="text-truncate" style="max-width: 0px;"></td>
	`;
	tr.querySelector("[field=payload]").setAttribute("payload", data.payload);
	tr.querySelector("[field=payload]").innerText = data.payload;
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
		<th colspan="1" class="shadow-none border-start-0 text-end" scope="row">
			<label role="button" class="link-${isVuln ? "danger" : "secondary"}" data-bs-toggle="tooltip" data-bs-title="Hide">
				<i class="fa-solid fa-close fa-xl"></i>
				<button type="button" onclick="this.closest('tr').classList.remove('show')" hidden></button>
			</label>
		</th>
		<td colspan="999" class="p-0"></td>
	`;
	details.querySelector("td:last-child").append(createSubTable(data));

	const target = details.querySelector("[key=reasoning]");
	const vuln = target.cloneNode(true);
	vuln.setAttribute("key", "vulnerability");
	vuln.querySelector(".text-capitalize").innerHTML = "Vulnerability";
	if (!isVuln) {
		vuln.querySelector(".align-middle > div").innerHTML = "No";
	} else {
		vuln.querySelector(".align-middle > div").innerHTML = `Yes (<label role="button" class="link-success">View Patch Suggestions<button type="button" onclick="openPatch(this)" hidden></button></label>)`;
	}
	target.before(vuln);
	tr.after(details);
}

const createSubTable = function(data, {border=true, index=true, isMarkdown=true, elem=true}={}) {
	if (typeof data === "string") {
		return isMarkdown ? mdToHTML(data) : data;
	}

	const disabled = ["step", "payload", "attack_name", "method", "observations", "timestamp", "url", "file_path", "vulnerable_file_code"];
	const keys = {
		reasoning: "Reason for Above",
		html_differences: `Changed before/after Attack`,
	}
	const table = document.createElement("table");
	table.className = `sub table table-sm table-hover table-border${border ? "ed" : "less"} m-0 h-100 position-relative text-wrap`;
	table.innerHTML = "<tbody></tbody>";
	for (let key in data) {
		if (disabled.includes(key)) continue;
		const isInt = parseInt(key) == key;
		const tr = document.createElement("tr");
		table.querySelector("tbody").append(tr);
		tr.setAttribute("key", key);
		tr.innerHTML = `
			<th class="text-end text-capitalize minimum" scope="row"${index === false && isInt ? " hidden" : ""}>${isInt && key*1+1 || keys[key] || key.replace(/_/g, " ")}</th>
			<td class="p-0 align-middle"></td>
		`;
		if (typeof data[key] !== "object") {
			tr.querySelector("td:last-child").innerHTML = `<div class="px-2 py-1"></div>`;
			tr.querySelector("td:last-child div").innerText = isMarkdown ? mdToHTML(data[key]) : data[key];
		} else {
			tr.querySelector("td:last-child").append(createSubTable(data[key], {border: false}));
		}
	}
	return elem ? table : table.outerHTML;
}

const displayPayloadDetails = function(e) {
	const details = this.nextElementSibling;
	if (details.classList.contains("details")) details.classList.toggle("show");
}

const openPatch = function(btn) {
	// btn.closest("[pen_code]").querySelector("#pen-patches-tab").click();
	const modal = document.querySelector("#penInfoModal");
	if (!modal?.classList.contains("show")) {
		document.querySelector(`[data-bs-target="#penInfoModal"]`)?.click();
	}
	modal?.querySelector("#pen-patches-tab")?.click();
}

const createPatchTable = function(pen_code, {style}={}) {
	const table = document.createElement("div");
	table.innerHTML = `
		<div class="form-check">
			<input class="form-check-input" type="checkbox" id="best-suggestion-${pen_code}" onclick="this.parentNode.classList.toggle('best-suggestion', this.checked)">
			<label class="form-check-label" for="best-suggestion-${pen_code}">Best Suggestion</label>
		</div>
		<div id="patch-table-${pen_code}" class="table-responsive mt-2 modal-scroll modal-scroll-target">
			<table class="table table-sm table-bordered table-hover m-0 position-relative text-nowrap" style="border-width: 2px">
				<thead class="sticky-top z-1">
					<tr>
						<th scope="col" class="text-center minimum">#</th>
						<th scope="col" class="text-center minimum">File</th>
						<th scope="col">Suggestion</th>
					</tr>
				</thead>
				<tbody class="table-group-divider"></tbody>
			</table>
		</div>
	`;

	if (style) {
		for (let key in style) {
			table.querySelector(`#patch-table-${pen_code}`).style.setProperty(key, style[key]);
		}
	}
	return table;
}

const insertPatchTable = function(table, {best, data, reverse=false}) {
	if (!data) return;

	const box = document.createElement("div");
	const num = table.querySelectorAll("th[field=num]")?.length + 1;

	const length = Object.keys(data).length;
	for (let idx in data) {
		const x = data[reverse ? length-1-idx : idx];
		const tr = document.createElement("tr");
		const bestHTML = Object.values(best).map(x => `${mdToHTML(x)}`).join("");
		if (bestHTML) tr.className = "best table-success";
		tr.innerHTML += `
			${reverse && idx == length-1 || !reverse && idx == 0 ? '<th field="num" class="text-end minimum" scope="row" rowspan="' + data.length + '">' + num + '</th>' : ""}
			<td field="file" class="text-start minimum"><label role="button" class="link-success" data-bs-toggle="tooltip" data-bs-title="${x.file_path}">
				${x.file_path.split("/").reverse()[0]}
				<button type="button" onclick="displayCodeViewer('${x.file_path}')" hidden></button>
			</label></td>
			<td field="suggestion" class="text-wrap">
				${bestHTML}${bestHTML ? "<hr class='m-0'/>" : ""}
				${createSubTable(x.patch_instructions, {border: false, elem: false})}
			</td>
		`;
		box.append(tr);

		if (!document.querySelector(`#vulnerable_files [value="${x.file_path}"]`)) {
			const box = document.createElement("div");
			box.innerHTML = `
				<option value="${x.file_path}">${x.file_path}</option>
				<div file="${x.file_path}">${mdToHTML(x.vulnerable_file_code)}</div>
			`;
			const isFirst = document.querySelector("#codes-container").innerHTML == "";
			box.querySelector("option").selected = isFirst;
			box.querySelector("div[file]").classList.toggle("d-none", !isFirst);
			document.querySelector("#vulnerable_files").append(box.querySelector("option"));
			document.querySelector("#codes-container").append(box.querySelector("div[file]"));
			document.querySelector("#codes-container > div:last-child pre").className = "border border-top-0 p-2 modal-scroll";
		}
	}

	for (let x of box.querySelectorAll("[data-bs-toggle=tooltip]")) new bootstrap.Tooltip(x);

	while (box.firstChild) {
		if (reverse) {
			table.querySelector("tbody")?.prepend(box.firstChild);
		} else {
			table.querySelector("tbody")?.append(box.firstChild);
		}
	}
}

const displayCodeViewer = function(file) {
	const codeViewerClick = function() {
		for (let x of document.querySelectorAll(`#pen-vulnFiles [file]`)) {
			x.classList.toggle('d-none', x.getAttribute('file') != file);
		}
		document.querySelector(`#vulnerable_files [value="${file}"]`).selected = true;
		document.querySelector("#penInfoModal").removeEventListener("shown.bs.modal", codeViewerClick);
	}

	if (document.querySelector("#penInfoModal").classList.contains("show")) {
		document.querySelector("#penInfoModal #pen-vulnFiles-tab").click();
		codeViewerClick();
	} else {
		document.querySelector(`[data-bs-target="#penInfoModal"]`).click()
		document.querySelector("#penInfoModal #pen-vulnFiles-tab").click();
		document.querySelector("#penInfoModal").addEventListener("shown.bs.modal", codeViewerClick);
	}
}

const mdToHTML = function(text) {
	return new DOMParser().parseFromString(marked.parse(text), "text/html").querySelector("body").innerHTML;
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

const insertURLTable = function(table, {url, data, reverse=false}) {
	if (data) {
		const tr = document.createElement("tr");
		tr.innerHTML = `
			<th field="num" class="text-end" scope="row">${table.querySelectorAll("tbody tr").length + 1}</th>
			<td field="url"><a href="${url}" target="_blank">${url}</a></td>
			<td field="payloads" class="text-center">${data.payloads || "-"}</td>
			<td field="vulnerabilities" class="text-center">${data.vulnerabilities || "-"}</td>
			<td field="patch_suggestion" class="text-center">${data.patches || "-"}</td>
			<td field="best_suggestion" class="text-center">${data.best || "-"}</td>
		`;

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



console.log(`%cTeam Persona`, `font-size: 2em; color: ${getComputedStyle(document.documentElement).getPropertyValue("--bs-success")};`);
