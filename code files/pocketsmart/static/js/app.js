function money(n) {
  return "₹" + Number(n).toLocaleString("en-IN");
}

function renderResults(data) {
  const el = document.getElementById("results");
  if (!el) return;
  if (data.error) {
    el.innerHTML = `<div class="alert err" id="error-box">${data.error}</div>`;
    return;
  }
  const warn = data.message
    ? `<div class="alert warn" id="fallback-box">${data.message}</div>`
    : "";
  const analysis = data.outfit_analysis
    ? `<p><strong>Outfit analysis:</strong> ${data.outfit_analysis}</p>`
    : "";
  const split = data.split
    ? `<p>Budget split: ${Object.entries(data.split)
        .map(([k, v]) => k + " " + money(v))
        .join(" · ")}</p>`
    : "";
  const items = (data.items || [])
    .map(
      (i) => `<article class="item">
        <div>
          <strong>${i.name}</strong>
          <div>${i.platform} · ${i.category || ""} · qty ${i.qty}</div>
          <div>${i.reason || ""}</div>
        </div>
        <span class="tag">sample data</span>
        <div>${money(i.price * i.qty)}</div>
      </article>`
    )
    .join("");
  el.innerHTML = `${warn}${analysis}
    <p class="totals" id="budget-totals">Budget ${money(data.budget)} · Used ${money(data.total)} · Left ${money(data.remaining)}</p>
    <p>${data.summary || ""} ${split}</p>
    ${items}`;
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw Object.assign(new Error(data.error || "Request failed"), { data });
  return data;
}

document.getElementById("home-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const rooms = [...e.target.querySelectorAll("input[name=rooms]:checked")].map((i) => i.value);
  try {
    const data = await postJSON("/generate-home", {
      budget: Number(fd.get("budget")),
      rooms,
      quantities: {
        lights: Number(fd.get("lights") || 0),
        fans: Number(fd.get("fans") || 0),
        dining_tables: Number(fd.get("dining_tables") || 0),
        sofa: Number(fd.get("sofa") || 0),
        bed: Number(fd.get("bed") || 0),
        storage: Number(fd.get("storage") || 0),
      },
    });
    renderResults(data);
  } catch (err) {
    renderResults(err.data || { error: err.message });
  }
});

document.getElementById("party-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const data = await postJSON("/generate-party", {
      budget: Number(fd.get("budget")),
      guests: Number(fd.get("guests")),
      event_type: fd.get("event_type"),
      venue: fd.get("venue"),
    });
    renderResults(data);
  } catch (err) {
    renderResults(err.data || { error: err.message });
  }
});

document.getElementById("jewelry-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const res = await fetch("/generate-jewelry", { method: "POST", body: fd, credentials: "include" });
    const data = await res.json();
    if (!res.ok) throw Object.assign(new Error(data.error), { data });
    renderResults(data);
  } catch (err) {
    renderResults(err.data || { error: err.message });
  }
});

document.getElementById("login-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = await postJSON("/auth/login", { email: fd.get("email"), password: fd.get("password") });
  document.getElementById("auth-msg").textContent = "Signed in as " + data.user.email;
  location.href = "/dashboard";
});

document.getElementById("register-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = await postJSON("/auth/register", {
    name: fd.get("name"),
    email: fd.get("email"),
    password: fd.get("password"),
  });
  document.getElementById("auth-msg").textContent = "Registered " + data.user.name;
  location.href = "/dashboard";
});

async function fillHistory(targetId) {
  const el = document.getElementById(targetId);
  if (!el) return;
  const res = await fetch("/api/history", { credentials: "include" });
  const data = await res.json();
  if (!data.history?.length) {
    el.innerHTML = "<p>No plans yet.</p>";
    return;
  }
  el.innerHTML = data.history
    .map(
      (h) =>
        `<article class="card"><strong>${h.planner}</strong><p>Budget ${money(h.budget)} · used ${money(h.total)} · ${h.item_count} items</p><p>${h.summary || ""}</p></article>`
    )
    .join("");
}
fillHistory("hist-list");
fillHistory("dash-history");
