const {test} = require("node:test");
const assert = require("node:assert/strict");
const {normalizeBridgeScreenshot} = require("./bridge_result.js");
const png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=";
function fixture(image = {}, envelope = {}) {
  return {ok:true, session_id:"native-session", sequence:0, result:{mime:"image/png", width:1, height:1, data_base64:png, ...image}, ...envelope};
}
test("normalizes actual nested native screenshot envelope", () => {
  const value = normalizeBridgeScreenshot(fixture());
  assert.equal(value.kind, "image"); assert.equal(value.width, 1); assert.equal(value.height, 1);
  assert.equal(value.bytes, Buffer.from(png, "base64").length);
  assert.equal(value.data_url, "data:image/png;base64," + png);
});
test("uses preview dimensions rather than original desktop dimensions", () => {
  const value = normalizeBridgeScreenshot(fixture({width:1920,height:1080,preview_width:1280,preview_height:720}));
  assert.equal(value.width,1280); assert.equal(value.height,720);
});
for (const image of [
  {mime:"image/svg+xml"}, {mime:"image/jpeg"}, {width:0}, {height:-1}, {width:1281},
  {width:1.5}, {preview_width:1}, {preview_width:2,preview_height:1},
  {data_base64:""}, {data_base64:"!!!!"}, {data_base64:"AAAA="}, {data_base64:"AB=="},
  {data_base64:"A".repeat(819204)}, {width:33554433,height:1,preview_width:1,preview_height:1}
]) test("rejects invalid image " + JSON.stringify(image).slice(0,120), () => assert.throws(() => normalizeBridgeScreenshot(fixture(image))));
for (const envelope of [{ok:false}, {session_id:null}, {sequence:-1}, {sequence:0.5}, {result:null}]) test("rejects invalid envelope " + JSON.stringify(envelope), () => assert.throws(() => normalizeBridgeScreenshot(fixture({}, envelope))));
test("rejects missing native envelope", () => assert.throws(() => normalizeBridgeScreenshot(null)));
