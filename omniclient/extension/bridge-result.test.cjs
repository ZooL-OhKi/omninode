const {test} = require("node:test");
const assert = require("node:assert/strict");
const {normalizeBridgeScreenshot, screenshotDimensions} = require("./bridge_result.js");
const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=","base64");
function fixture(image = {}, envelope = {}) {
  return {ok:true,session_id:"native-session",sequence:0,result:{mime:"image/png",width:1,height:1,data_base64:png.toString("base64"),...image},...envelope};
}
function pngHeader(width,height) {
  const bytes=Buffer.from(png); bytes.writeUInt32BE(width,16); bytes.writeUInt32BE(height,20); return bytes;
}
// Header-only JPEG fixtures test the bounded parser, not full image decoding.
function jpegHeader(width,height,marker=0xc0) {
  const bytes=Buffer.from([255,216,255,marker,0,11,8,0,0,0,0,1,1,17,0,255,217]);
  bytes.writeUInt16BE(height,7); bytes.writeUInt16BE(width,9); return bytes;
}
test("normalizes nested native PNG envelope",()=>{
  const value=normalizeBridgeScreenshot(fixture());
  assert.equal(value.kind,"image");assert.equal(value.width,1);assert.equal(value.height,1);assert.equal(value.bytes,png.length);
});
test("preview dimensions match binary, not original display dimensions",()=>{
  const value=normalizeBridgeScreenshot(fixture({width:1920,height:1080,preview_width:1,preview_height:1}));
  assert.equal(value.width,1);assert.equal(value.height,1);
});
for(const [width,height] of [[1920,1080],[1281,600],[800,801],[0,600],[800,0]]) {
  test(`reject PNG binary ${width}x${height} with claimed 800x600`,()=>assert.throws(()=>normalizeBridgeScreenshot(fixture({width:800,height:600,data_base64:pngHeader(width,height).toString("base64")}))));
  for(const marker of [0xc0,0xc1,0xc2]) test(`reject JPEG SOF ${marker} binary ${width}x${height}`,()=>assert.throws(()=>normalizeBridgeScreenshot(fixture({mime:"image/jpeg",width:800,height:600,data_base64:jpegHeader(width,height,marker).toString("base64")}))));
}
for(const marker of [0xc0,0xc1,0xc2]) test(`read JPEG SOF ${marker}`,()=>{
  const value=normalizeBridgeScreenshot(fixture({mime:"image/jpeg",width:800,height:600,data_base64:jpegHeader(800,600,marker).toString("base64")}));
  assert.equal(value.width,800);assert.equal(value.height,600);
});
test("reject within-limit dimensions differing from metadata",()=>assert.throws(()=>normalizeBridgeScreenshot(fixture({width:800,height:600}))));
test("reject incorrect IHDR type",()=>{const bytes=Buffer.from(png);bytes.write("IDAT",12);assert.throws(()=>normalizeBridgeScreenshot(fixture({data_base64:bytes.toString("base64")})));});
test("reject incorrect IHDR length",()=>{const bytes=Buffer.from(png);bytes.writeUInt32BE(12,8);assert.throws(()=>normalizeBridgeScreenshot(fixture({data_base64:bytes.toString("base64")})));});
test("reject truncated PNG",()=>assert.throws(()=>screenshotDimensions(png.subarray(0,24).toString("latin1"),"image/png")));
for(const data of [Buffer.from([255,216,255,217]),Buffer.from([255,216,255,224,255,255,255,217]),Buffer.from([255,216,255,218,0,2,255,217]),Buffer.from([255,216,0,0,255,217])]) test("reject malformed JPEG "+data.toString("hex"),()=>assert.throws(()=>screenshotDimensions(data.toString("latin1"),"image/jpeg")));
for(const image of [{mime:"image/svg+xml"},{mime:"image/jpeg"},{width:0},{height:-1},{width:1281},{width:1.5},{preview_width:1},{preview_width:2,preview_height:1},{data_base64:""},{data_base64:"!!!!"},{data_base64:"AAAA="},{data_base64:"AB=="},{data_base64:"A".repeat(819204)},{width:33554433,height:1,preview_width:1,preview_height:1}]) test("reject invalid image "+JSON.stringify(image).slice(0,80),()=>assert.throws(()=>normalizeBridgeScreenshot(fixture(image))));
for(const envelope of [{ok:false},{session_id:null},{session_id:""},{sequence:-1},{sequence:0.5},{result:null}]) test("reject invalid envelope "+JSON.stringify(envelope),()=>assert.throws(()=>normalizeBridgeScreenshot(fixture({},envelope))));
test("reject missing envelope",()=>assert.throws(()=>normalizeBridgeScreenshot(null)));
