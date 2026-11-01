"use strict";
function normalizeBridgeScreenshot(native) {
  if (!native || native.ok !== true || typeof native.session_id !== "string" || !Number.isSafeInteger(native.sequence) || native.sequence < 0) throw Error("Invalid native result envelope");
  const image = native.result;
  if (!image || !["image/png", "image/jpeg"].includes(image.mime)) throw Error("Unsupported screenshot MIME");
  const hasPreview = Object.hasOwn(image, "preview_width") || Object.hasOwn(image, "preview_height");
  const width = hasPreview ? image.preview_width : image.width;
  const height = hasPreview ? image.preview_height : image.height;
  if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height) || width < 1 || height < 1 || width > 1280 || height > 800) throw Error("Invalid screenshot preview dimensions");
  if (!Number.isSafeInteger(image.width) || !Number.isSafeInteger(image.height) || image.width < 1 || image.height < 1 || image.width * image.height > 33554432 || width > image.width || height > image.height) throw Error("Invalid screenshot source dimensions");
  const base64 = image.data_base64;
  if (typeof base64 !== "string" || !base64.length || base64.length > 819200 || base64.length % 4 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(base64)) throw Error("Invalid screenshot base64");
  const binary = atob(base64);
  if (btoa(binary) !== base64 || binary.length > 614400) throw Error("Screenshot preview size or encoding invalid");
  const png = binary.startsWith("\x89PNG\r\n\x1a\n");
  const jpeg = binary.length >= 4 && binary.charCodeAt(0) === 255 && binary.charCodeAt(1) === 216 && binary.charCodeAt(2) === 255 && binary.charCodeAt(binary.length - 2) === 255 && binary.charCodeAt(binary.length - 1) === 217;
  if (!(image.mime === "image/png" ? png : jpeg)) throw Error("Screenshot MIME/signature mismatch");
  return {kind:"image", mime:image.mime, width, height, bytes:binary.length, data_url:"data:" + image.mime + ";base64," + base64};
}
if (typeof module !== "undefined" && module.exports) module.exports = {normalizeBridgeScreenshot};
else globalThis.normalizeBridgeScreenshot = normalizeBridgeScreenshot;
