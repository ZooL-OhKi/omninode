"use strict";
function omniIsCompleted(partition) {
  return Boolean(partition && typeof partition.querySelector === "function" && partition.querySelector('div[title="Completato"]'));
}
function omniExtractResponseText(partition) {
  if (!partition || typeof partition.querySelector !== "function") return "";
  const prose = partition.querySelector(".prose");
  return prose ? (prose.textContent || "").trim() : "";
}
function omniParseCommand(text, policy) {
  if (typeof text !== "string") return null;
  const match = text.match(/```json\s*([\s\S]*?)```/i);
  if (!match) return null;
  let parsed;
  try { parsed = JSON.parse(match[1]); } catch { return null; }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
  if (parsed.action !== "screenshot") return null;
  if (!parsed.args || typeof parsed.args !== "object" || Array.isArray(parsed.args) || Object.keys(parsed.args).length) return null;
  const id = parsed.request_id;
  if (typeof id !== "string" || !policy || typeof policy.id !== "function" || !policy.id(id)) return null;
  return parsed;
}
function omniBuildResultMessage(command, result) {
  const image = result && result.result && result.result.result ? result.result.result : null;
  const dimensions = image && Number.isSafeInteger(image.width) && Number.isSafeInteger(image.height) ? ` (${image.width}x${image.height})` : "";
  return `OmniNode ${command.request_id}: screenshot acquisito${dimensions}.`;
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = { omniIsCompleted, omniExtractResponseText, omniParseCommand, omniBuildResultMessage };
} else {
  Object.assign(globalThis, { omniIsCompleted, omniExtractResponseText, omniParseCommand, omniBuildResultMessage });
}
