const tokenInput = document.getElementById("token");
const saveButton = document.getElementById("save");
const status = document.getElementById("status");

chrome.storage.local.get(["bridgeToken"], (items) => {
  if (items.bridgeToken) {
    tokenInput.value = items.bridgeToken;
  }
});

saveButton.addEventListener("click", () => {
  const token = tokenInput.value.trim();
  if (token.length < 32) {
    status.textContent = "Il token deve avere almeno 32 caratteri.";
    status.style.color = "#dc2626";
    return;
  }

  chrome.storage.local.set({ bridgeToken: token }, () => {
    status.textContent = "Token salvato localmente nel browser.";
    status.style.color = "#059669";
  });
});
