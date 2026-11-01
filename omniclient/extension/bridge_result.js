"use strict";
function screenshotDimensions(binary, mime) {
  const n = binary.length;
  const u8 = i => { if (i < 0 || i >= n) throw Error("Truncated image header"); return binary.charCodeAt(i); };
  const u16 = i => u8(i) * 256 + u8(i + 1);
  const u32 = i => u16(i) * 65536 + u16(i + 2);
  if (mime === "image/png") {
    if (n < 33 || !binary.startsWith("\x89PNG\r\n\x1a\n") || u32(8) !== 13 || binary.slice(12,16) !== "IHDR") throw Error("Invalid PNG IHDR");
    return {width:u32(16), height:u32(20)};
  }
  if (mime !== "image/jpeg" || n < 4 || u16(0) !== 0xffd8 || u16(n - 2) !== 0xffd9) throw Error("Invalid JPEG framing");
  let offset = 2;
  while (offset < n - 2) {
    if (u8(offset++) !== 0xff) throw Error("Invalid JPEG marker");
    while (offset < n && u8(offset) === 0xff) offset++;
    const marker = u8(offset++);
    if (marker === 0xda || marker === 0xd9) break;
    if (marker === 0 || marker === 0xd8 || marker === 1 || (marker >= 0xd0 && marker <= 0xd7)) throw Error("Unexpected JPEG marker");
    const length = u16(offset);
    if (length < 2 || offset + length > n - 2) throw Error("Invalid JPEG segment length");
    if ([0xc0,0xc1,0xc2].includes(marker)) {
      if (length < 8) throw Error("Truncated JPEG SOF");
      const components = u8(offset + 7);
      if (components < 1 || components > 4 || length !== 8 + components * 3 || ![8,12].includes(u8(offset + 2))) throw Error("Invalid JPEG SOF");
      return {width:u16(offset + 5), height:u16(offset + 3)};
    }
    offset += length;
  }
  throw Error("Supported JPEG SOF missing before scan");
}
function normalizeBridgeScreenshot(native) {
  if (!native || native.ok !== true || typeof native.session_id !== "string" || !native.session_id || !Number.isSafeInteger(native.sequence) || native.sequence < 0) throw Error("Invalid native result envelope");
  const image = native.result;
  if (!image || !["image/png", "image/jpeg"].includes(image.mime)) throw Error("Unsupported screenshot MIME");
  const preview = Object.hasOwn(image,"preview_width") || Object.hasOwn(image,"preview_height");
  const width = preview ? image.preview_width : image.width;
  const height = preview ? image.preview_height : image.height;
  if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height) || width < 1 || height < 1 || width > 1280 || height > 800) throw Error("Invalid screenshot preview dimensions");
  if (!Number.isSafeInteger(image.width) || !Number.isSafeInteger(image.height) || image.width < 1 || image.height < 1 || image.width * image.height > 33554432 || width > image.width || height > image.height) throw Error("Invalid screenshot source dimensions");
  const base64 = image.data_base64;
  if (typeof base64 !== "string" || !base64.length || base64.length > 819200 || base64.length % 4 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(base64)) throw Error("Invalid screenshot base64");
  const binary = atob(base64);
  if (btoa(binary) !== base64 || binary.length > 614400) throw Error("Screenshot preview size or encoding invalid");
  const actual = screenshotDimensions(binary, image.mime);
  if (actual.width < 1 || actual.height < 1 || actual.width > 1280 || actual.height > 800 || actual.width !== width || actual.height !== height) throw Error("Screenshot binary dimensions exceed limits or mismatch metadata");
  return {kind:"image", mime:image.mime, width:actual.width, height:actual.height, bytes:binary.length, data_url:"data:" + image.mime + ";base64," + base64};
}
if (typeof module !== "undefined" && module.exports) module.exports = {normalizeBridgeScreenshot, screenshotDimensions};
else globalThis.normalizeBridgeScreenshot = normalizeBridgeScreenshot;
