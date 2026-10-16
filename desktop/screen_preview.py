"""Bounded in-memory previews for the native channel; no screen capture here."""
import io

MAX_PREVIEW = 600 * 1024
MAX_SOURCE = 16 * 1024 * 1024
MAX_PIXELS = 33554432


def compact_screenshot(result):
    data = result["data"]
    if not isinstance(data, bytes):
        raise ValueError("screenshot must be bytes")
    if len(data) > MAX_SOURCE:
        raise ValueError("source screenshot size limit")
    if (len(data) <= MAX_PREVIEW and type(result.get("width", 0)) is int
            and type(result.get("height", 0)) is int
            and 0 <= result.get("width", 0) <= 1280
            and 0 <= result.get("height", 0) <= 800):
        return dict(result)
    from PIL import Image
    with Image.open(io.BytesIO(data)) as source:
        if source.width * source.height > MAX_PIXELS:
            raise ValueError("source screenshot pixel limit")
        if source.size != (result.get("width"), result.get("height")):
            raise ValueError("source screenshot dimensions mismatch")
        original_size = source.size
        image = source.convert("RGB")
    image.thumbnail((1280, 800))
    for quality in (80, 60, 40):
        stream = io.BytesIO()
        image.save(stream, format="JPEG", quality=quality, optimize=True)
        preview = stream.getvalue()
        if len(preview) <= MAX_PREVIEW:
            result = dict(result)
            result.update(data=preview, mime="image/jpeg", width=original_size[0],
                          height=original_size[1], preview_width=image.width,
                          preview_height=image.height, coordinate_space="source-image-pixels")
            return result
    raise ValueError("screenshot preview could not fit native channel")
