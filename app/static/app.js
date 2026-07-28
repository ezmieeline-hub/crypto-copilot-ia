// ======================================================
// CRYPTO COPILOT IA
// APP.JS — PARTIE 1
// Initialisation, API, connexion et navigation
// ======================================================

// Sélectionne le premier élément correspondant.
const $ = (selector) => document.querySelector(selector);

// Sélectionne tous les éléments correspondants.
const $$ = (selector) => document.querySelectorAll(selector);

// Vérifie qu’un élément existe avant de l’utiliser.
function elementExists(selector) {
  return Boolean($(selector));
}

// Appelle une route de l’API.
async function api(url, options = {}) {
  let response;

  try {
    response = await fetch(url, options);
  } catch (error) {
    throw new Error(
      "Impossible de contacter le serveur. Vérifie ta connexion puis réessaie."
    );
  }

  let data;

  try {
    data = await response.json();
  } catch (error) {
    data = {
      detail: "Le serveur a renvoyé une réponse incorrecte."
    };
  }

  if (!response.ok) {
    throw new Error(data.detail || "Une erreur est survenue.");
  }

  return data;
}

// Formate les nombres en français.
function formatNumber(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return number.toLocaleString("fr-FR", {
    maximumSignificantDigits: 8
  });
}

// Formate les pourcentages.
function formatPercent(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return `${number.toLocaleString("fr-FR", {
    maximumFractionDigits: 2
  })} %`;
}

// Affiche ou masque un élément.
function setHidden(selector, hidden) {
  const element = $(selector);

  if (element) {
    element.hidden = hidden;
  }
}

// Affiche un message dans un élément.
function setText(selector, message) {
  const element = $(selector);

  if (element) {
    element.textContent = message;
  }
}

// Initialisation de l’application.
async function init() {
  try {
    const user = await api("/api/me");

    if (user.authenticated) {
      setHidden("#login", true);
      setHidden("#app", false);

      initializeButtons();
      initializeNavigation();
    } else {
      setHidden("#login", false);
      setHidden("#app", true);
    }
  } catch (error) {
    console.error("Erreur d’initialisation :", error);

    setHidden("#login", false);
    setHidden("#app", true);
    setText(
      "#loginErr",
      "Impossible de vérifier la connexion au serveur."
    );
  }
}

// Connexion.
async function login(event) {
  event.preventDefault();

  const usernameInput = $("#user");
  const passwordInput = $("#pass");
  const errorElement = $("#loginErr");

  if (!usernameInput || !passwordInput) {
    return;
  }

  const username = usernameInput.value.trim();
  const password = passwordInput.value;

  if (!username || !password) {
    if (errorElement) {
      errorElement.textContent =
        "Renseigne ton identifiant et ton mot de passe.";
    }

    return;
  }

  if (errorElement) {
    errorElement.textContent = "Connexion en cours…";
  }

  try {
    await api("/api/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        username,
        password
      })
    });

    window.location.reload();
  } catch (error) {
    if (errorElement) {
      errorElement.textContent = error.message;
    }
  }
}

// Déconnexion.
async function logout() {
  try {
    await api("/api/logout", {
      method: "POST"
    });
  } catch (error) {
    console.error("Erreur de déconnexion :", error);
  } finally {
    window.location.reload();
  }
}

// Active l’onglet demandé.
function activateTab(button) {
  const tabName = button.dataset.tab;

  if (!tabName) {
    return;
  }

  $$("nav button").forEach((navigationButton) => {
    navigationButton.classList.remove("active");
  });

  $$(".tab").forEach((tab) => {
    tab.classList.remove("active");
  });

  button.classList.add("active");

  const selectedTab = $(`#${tabName}`);

  if (selectedTab) {
    selectedTab.classList.add("active");
  }

  if (tabName === "alerts" && typeof loadAlerts === "function") {
    loadAlerts();
  }

  if (tabName === "journal" && typeof loadTrades === "function") {
    loadTrades();
  }
}

// Initialise la navigation.
function initializeNavigation() {
  $$("nav button").forEach((button) => {
    button.addEventListener("click", () => {
      activateTab(button);
    });
  });
}

// Initialise le formulaire de connexion.
const loginForm = $("#loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", login);
}
// ======================================================
// APP.JS — PARTIE 2
// Analyse IA
// ======================================================

// Lance une analyse
async function runAnalysis() {

    const symbol = prompt(
        "Quelle crypto souhaitez-vous analyser ?\n\nExemple : BTC, ETH, SOL, XRP..."
    );

    if (!symbol) {
        return;
    }

    const interval = "15m";

    try {

        const result = await api(
            `/api/analyze/${symbol.trim().toUpperCase()}?interval=${interval}`
        );

        renderAnalysis(result);

    } catch (error) {

        alert(error.message);

    }

}

// Affiche l'analyse
function renderAnalysis(result) {

    let verdictColor = "bad";

    if (result.verdict === "VALIDÉ") {
        verdictColor = "good";
    }

    if (result.verdict === "À SURVEILLER") {
        verdictColor = "wait";
    }

    const html = `

<div class="panel">

<div class="row">

<div>

<h2>${result.symbol} • ${result.interval}</h2>

<span class="badge ${verdictColor}">
${result.verdict}
</span>

</div>

<div>

<small class="muted">
Score IA
</small>

<b style="font-size:34px">

${result.score} %

</b>

</div>

</div>

<div class="grid">

<div class="card metric">
Prix
<b>${formatNumber(result.price)}</b>
</div>

<div class="card metric">
Scénario
<b>${result.side}</b>
</div>

<div class="card metric">
Tendance
<b>${result.trend}</b>
</div>

<div class="card metric">
Confirmation
<b>${result.confirmed ? "Oui" : "Non"}</b>
</div>

</div>

<h3>Plan de Trading</h3>

<div class="plan">

<div class="level">
Entrée
<b>${formatNumber(result.entry)}</b>
</div>

<div class="level">
Stop Loss
<b>${formatNumber(result.stop)}</b>
</div>

<div class="level">
TP1
<b>${formatNumber(result.tp1)}</b>
</div>

<div class="level">
TP2
<b>${formatNumber(result.tp2)}</b>
</div>

<div class="level">
TP3
<b>${formatNumber(result.tp3)}</b>
</div>

</div>

<div class="grid" style="margin-top:20px;">

<div class="card">

<h3>Confirmations</h3>

${result.reasons.map(item=>`

<div class="item">

${item}

</div>

`).join("")}

</div>

<div class="card">

<h3>Risques</h3>

${result.risks.map(item=>`

<div class="item">

${item}

</div>

`).join("")}

</div>

</div>

<br>

<button id="saveTradeBtn">

💾 Ajouter au journal

</button>

</div>

`;

    const cards = document.querySelector(".market-grid");

    if (cards) {

        cards.insertAdjacentHTML(
            "afterend",
            html
        );

    } else {

        alert(
            "Analyse terminée mais impossible d'afficher le résultat."
        );

    }

    const saveButton = document.getElementById("saveTradeBtn");

    if (saveButton) {

        saveButton.onclick = () => {

            saveTrade(result);

        };

    }

}

// Bouton Nouvelle Analyse
function initializeButtons() {

    const analyseButton = document.getElementById("analyseBtn");

    if (analyseButton) {

        analyseButton.onclick = runAnalysis;

    }

}
// ======================================================
// APP.JS — PARTIE 3
// TradingView, journal, alertes et démarrage
// ======================================================

// Enregistre une analyse dans le journal de trading.
async function saveTrade(result) {
  try {
    await api("/api/trades", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(result)
    });

    alert("Analyse ajoutée au journal.");
  } catch (error) {
    alert(`Impossible d’ajouter l’analyse : ${error.message}`);
  }
}

// Importe et analyse une capture TradingView.
async function uploadShot() {
  const imageInput = $("#image");
  const questionInput = $("#question");
  const resultElement = $("#visionResult");

  if (!imageInput || !imageInput.files.length) {
    alert("Sélectionne d’abord une capture TradingView.");
    return;
  }

  const file = imageInput.files[0];
  const formData = new FormData();

  formData.append("file", file);

  if (questionInput) {
    formData.append(
      "question",
      questionInput.value.trim()
    );
  } else {
    formData.append(
      "question",
      "Analyse cette capture TradingView."
    );
  }

  if (resultElement) {
    resultElement.textContent = "Analyse de la capture en cours…";
  }

  try {
    const response = await api("/api/screenshot", {
      method: "POST",
      body: formData
    });

    if (resultElement) {
      resultElement.textContent =
        response.analysis || "Analyse terminée.";
    } else {
      alert(response.analysis || "Analyse terminée.");
    }
  } catch (error) {
    if (resultElement) {
      resultElement.textContent = error.message;
    } else {
      alert(error.message);
    }
  }
}

// Charge les alertes.
async function loadAlerts() {
  const alertsElement = $("#alertsList");

  if (!alertsElement) {
    return;
  }

  alertsElement.innerHTML =
    '<div class="item">Chargement des alertes…</div>';

  try {
    const alerts = await api("/api/alerts");

    if (!Array.isArray(alerts) || alerts.length === 0) {
      alertsElement.innerHTML =
        '<div class="item">Aucune alerte pour le moment.</div>';
      return;
    }

    alertsElement.innerHTML = alerts
      .map((alertItem) => {
        const date = alertItem.created_at
          ? new Date(alertItem.created_at).toLocaleString("fr-FR")
          : "Date indisponible";

        return `
          <div class="item">
            <b>
              ${alertItem.symbol || "Crypto"}
              ${alertItem.interval || ""}
              · ${alertItem.side || "ATTENTE"}
              · ${alertItem.score ?? "—"} %
            </b>

            <br>

            <span class="muted">
              ${date}
            </span>
          </div>
        `;
      })
      .join("");
  } catch (error) {
    alertsElement.innerHTML = `
      <div class="item error">
        ${error.message}
      </div>
    `;
  }
}

// Charge le journal de trading.
async function loadTrades() {
  const tradesElement = $("#tradesList");

  if (!tradesElement) {
    return;
  }

  tradesElement.innerHTML =
    '<div class="item">Chargement du journal…</div>';

  try {
    const trades = await api("/api/trades");

    if (!Array.isArray(trades) || trades.length === 0) {
      tradesElement.innerHTML =
        '<div class="item">Le journal est vide.</div>';
      return;
    }

    tradesElement.innerHTML = trades
      .map((trade) => {
        return `
          <div class="item">
            <b>
              ${trade.symbol || "Crypto"}
              ${trade.interval || ""}
              · ${trade.side || "ATTENTE"}
            </b>

            <br>

            Entrée : ${formatNumber(trade.entry)}
            · Stop : ${formatNumber(trade.stop)}
            · TP1 : ${formatNumber(trade.tp1)}
          </div>
        `;
      })
      .join("");
  } catch (error) {
    tradesElement.innerHTML = `
      <div class="item error">
        ${error.message}
      </div>
    `;
  }
}

// Lance immédiatement une vérification du marché.
async function scanNow() {
  try {
    await api("/api/scan-now", {
      method: "POST"
    });

    await loadAlerts();

    alert("Vérification du marché terminée.");
  } catch (error) {
    alert(`Erreur pendant la vérification : ${error.message}`);
  }
}

// Ouvre le sélecteur de capture TradingView.
function openTradingViewImport() {
  const imageInput = $("#image");

  if (imageInput) {
    imageInput.click();
    return;
  }

  alert(
    "La zone d’import TradingView n’est pas encore présente dans cette page."
  );
}

// Initialise tous les boutons de l’application.
function initializeButtons() {
  const analyseButton = $("#analyseBtn");

  if (analyseButton) {
    analyseButton.onclick = runAnalysis;
  }

  const logoutButton = $("#logoutBtn");

  if (logoutButton) {
    logoutButton.onclick = logout;
  }

  const uploadButton =
    $("#uploadBtn") ||
    $("#analyseImageBtn") ||
    $("#visionBtn");

  if (uploadButton) {
    uploadButton.onclick = uploadShot;
  }

  const tradingViewButton =
    $("#tradingViewBtn") ||
    $("#importBtn");

  if (tradingViewButton) {
    tradingViewButton.onclick = openTradingViewImport;
  }

  const scanButton =
    $("#scanBtn") ||
    $("#scanNowBtn");

  if (scanButton) {
    scanButton.onclick = scanNow;
  }

  const refreshAlertsButton = $("#refreshAlertsBtn");

  if (refreshAlertsButton) {
    refreshAlertsButton.onclick = loadAlerts;
  }

  const refreshTradesButton = $("#refreshTradesBtn");

  if (refreshTradesButton) {
    refreshTradesButton.onclick = loadTrades;
  }
}

// Rend certaines fonctions accessibles aux boutons HTML
// qui utilisent encore l’attribut onclick.
window.logout = logout;
window.runAnalysis = runAnalysis;
window.uploadShot = uploadShot;
window.loadAlerts = loadAlerts;
window.loadTrades = loadTrades;
window.scanNow = scanNow;
window.saveTrade = saveTrade;

// Démarre l’application.
init();

