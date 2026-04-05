#!/usr/bin/env python3
"""
Minimal GPS EXIF JPEG builder.
Creates a JPEG with proper GPS EXIF tags readable by ExifTool on SIFT.
"""

import struct, io, math, random
from PIL import Image, ImageDraw


def make_rational(numerator, denominator=1):
    """Pack a rational number as TIFF rational (two 32-bit uints)"""
    return struct.pack("<II", int(numerator), int(denominator))


def dms_to_exif_rationals(degrees, minutes, seconds):
    """Convert DMS to three EXIF rational values"""
    r1 = make_rational(int(degrees), 1)
    r2 = make_rational(int(minutes), 1)
    # Seconds as fraction with 1000 denominator for precision
    r3 = make_rational(int(round(seconds * 1000)), 1000)
    return r1 + r2 + r3


def build_gps_ifd(lat_d, lat_m, lat_s, lat_ref, lon_d, lon_m, lon_s, lon_ref, altitude=85):
    """
    Build a GPS IFD compatible with standard EXIF.
    Returns (ifd_bytes, data_bytes, data_offset_from_ifd_start)

    GPS IFD tags we'll write:
    Tag 1 (GPSLatitudeRef):  ASCII "N\0" or "S\0"
    Tag 2 (GPSLatitude):     3 RATIONALs
    Tag 3 (GPSLongitudeRef): ASCII "E\0" or "W\0"
    Tag 4 (GPSLongitude):    3 RATIONALs
    Tag 5 (GPSAltitudeRef):  BYTE 0
    Tag 6 (GPSAltitude):     1 RATIONAL
    """
    # TIFF type codes
    BYTE      = 1
    ASCII     = 2
    RATIONAL  = 5  # unsigned rational

    num_entries = 6

    # Each IFD entry: 2+2+4+4 = 12 bytes
    # IFD header: 2 bytes (count)
    # IFD footer: 4 bytes (next IFD offset = 0)
    ifd_size = 2 + (num_entries * 12) + 4

    # Data area starts right after IFD
    data_area = bytearray()

    # We need to know the absolute offset of data relative to TIFF header start
    # The GPS IFD offset from TIFF header will be provided by caller
    # For now, calculate data offsets relative to start of IFD data area
    # data_base will be ifd_start + ifd_size (to be calculated by caller)

    entries = []

    def add_data(b):
        offset = len(data_area)
        data_area.extend(b)
        # Pad to 2-byte boundary
        if len(b) % 2 != 0:
            data_area.extend(b'\x00')
        return offset

    # Tag 1: GPSLatitudeRef - ASCII 2 bytes "N\0"
    lat_ref_bytes = lat_ref.encode('ascii') + b'\x00'
    lat_ref_offset = add_data(lat_ref_bytes)
    entries.append((1, ASCII, 2, lat_ref_offset))

    # Tag 2: GPSLatitude - 3 RATIONALs (24 bytes)
    lat_data = dms_to_exif_rationals(lat_d, lat_m, lat_s)
    lat_offset = add_data(lat_data)
    entries.append((2, RATIONAL, 3, lat_offset))

    # Tag 3: GPSLongitudeRef - ASCII 2 bytes
    lon_ref_bytes = lon_ref.encode('ascii') + b'\x00'
    lon_ref_offset = add_data(lon_ref_bytes)
    entries.append((3, ASCII, 2, lon_ref_offset))

    # Tag 4: GPSLongitude - 3 RATIONALs
    lon_data = dms_to_exif_rationals(lon_d, lon_m, lon_s)
    lon_offset = add_data(lon_data)
    entries.append((4, RATIONAL, 3, lon_offset))

    # Tag 5: GPSAltitudeRef - BYTE 1 value (0 = above sea level)
    alt_ref_bytes = struct.pack('<B', 0)
    alt_ref_offset = add_data(alt_ref_bytes)
    entries.append((5, BYTE, 1, alt_ref_offset))

    # Tag 6: GPSAltitude - 1 RATIONAL
    alt_data = make_rational(altitude, 1)
    alt_offset = add_data(alt_data)
    entries.append((6, RATIONAL, 1, alt_offset))

    return entries, bytes(data_area), ifd_size


def build_exif_app1(lat_d, lat_m, lat_s, lat_ref, lon_d, lon_m, lon_s, lon_ref):
    """
    Build a complete EXIF APP1 segment with GPS IFD.
    Returns raw bytes to insert after JPEG SOI marker.
    """
    # TIFF header (little-endian)
    TIFF_HEADER = b'II'  # little-endian
    TIFF_MAGIC = struct.pack('<H', 42)

    # We'll build:
    # TIFF header (8 bytes) -> IFD0 (main image IFD) -> GPS IFD
    # IFD0 will point to GPS IFD via tag 0x8825

    # First, figure out GPS IFD entries and data
    gps_entries, gps_data, gps_ifd_size = build_gps_ifd(
        lat_d, lat_m, lat_s, lat_ref,
        lon_d, lon_m, lon_s, lon_ref
    )

    # IFD0 entries we'll write:
    # 0x0132 (DateTime): "2024:03:07 14:23:18\0" - 20 bytes ASCII
    # 0x010E (ImageDescription): short string
    # 0x010F (Make): "Apple\0" - 6 bytes
    # 0x0110 (Model): "iPhone 15 Pro\0" - 14 bytes
    # 0x8825 (GPSInfoIFDPointer): offset to GPS IFD

    ifd0_num_entries = 5

    # Layout:
    # [0]     TIFF header: 8 bytes
    # [8]     IFD0 offset pointer in TIFF header -> 8
    # [8]     IFD0: 2 + 5*12 + 4 = 66 bytes
    # [74]    IFD0 data area
    # [74+d0] GPS IFD
    # [74+d0+gps_ifd_size] GPS data area

    tiff_header_size = 8  # II + 42 + offset_to_IFD0

    ifd0_size = 2 + ifd0_num_entries * 12 + 4
    ifd0_start = tiff_header_size  # = 8

    # Build IFD0 data area first to know its size
    ifd0_data = bytearray()

    def ifd0_add(b):
        offset = len(ifd0_data)
        ifd0_data.extend(b)
        if len(b) % 2:
            ifd0_data.extend(b'\x00')
        return offset

    dt_bytes = b'2024:03:07 14:23:18\x00'
    dt_off = ifd0_add(dt_bytes)

    make_bytes = b'Apple\x00'
    make_off = ifd0_add(make_bytes)

    model_bytes = b'iPhone 15 Pro\x00'
    model_off = ifd0_add(model_bytes)

    # desc_bytes not added (will use inline value for short strings)

    ifd0_data_start = ifd0_start + ifd0_size  # absolute offset of IFD0 data
    gps_ifd_start = ifd0_data_start + len(ifd0_data)  # absolute offset of GPS IFD
    gps_data_start = gps_ifd_start + gps_ifd_size     # absolute offset of GPS data area

    def ifd0_abs(rel_off):
        return ifd0_data_start + rel_off

    def gps_abs(rel_off):
        return gps_data_start + rel_off

    # Build IFD0
    ifd0 = bytearray()
    ifd0.extend(struct.pack('<H', ifd0_num_entries))

    def write_entry(tag, typ, count, value_or_offset):
        return struct.pack('<HHI', tag, typ, count) + struct.pack('<I', value_or_offset)

    LONG = 4
    ASCII = 2

    ifd0.extend(write_entry(0x010F, ASCII, len(make_bytes), ifd0_abs(make_off)))   # Make
    ifd0.extend(write_entry(0x0110, ASCII, len(model_bytes), ifd0_abs(model_off))) # Model
    ifd0.extend(write_entry(0x0132, ASCII, len(dt_bytes), ifd0_abs(dt_off)))        # DateTime
    ifd0.extend(write_entry(0x8825, LONG, 1, gps_ifd_start))                       # GPS IFD offset
    # Orientation (short value fits inline)
    ifd0.extend(struct.pack('<HHI', 0x0112, 3, 1))  # tag=Orientation, type=SHORT, count=1
    ifd0.extend(struct.pack('<HH', 1, 0))            # value=1 (normal), padding
    # Next IFD = 0
    ifd0.extend(struct.pack('<I', 0))

    # Build GPS IFD
    gps_num = len(gps_entries)
    gps_ifd_bytes = bytearray()
    gps_ifd_bytes.extend(struct.pack('<H', gps_num))
    for (tag, typ, count, rel_off) in gps_entries:
        gps_ifd_bytes.extend(struct.pack('<HHI', tag, typ, count))
        gps_ifd_bytes.extend(struct.pack('<I', gps_abs(rel_off)))
    gps_ifd_bytes.extend(struct.pack('<I', 0))  # next IFD = 0

    # Assemble TIFF data
    tiff_data = bytearray()
    tiff_data.extend(b'II')                          # Byte order: little-endian
    tiff_data.extend(struct.pack('<H', 42))           # TIFF magic
    tiff_data.extend(struct.pack('<I', ifd0_start))   # Offset to IFD0 (=8)
    tiff_data.extend(bytes(ifd0))
    tiff_data.extend(bytes(ifd0_data))
    tiff_data.extend(bytes(gps_ifd_bytes))
    tiff_data.extend(gps_data)

    # Wrap in EXIF APP1 segment
    exif_header = b'Exif\x00\x00'
    app1_payload = exif_header + bytes(tiff_data)
    app1_length = len(app1_payload) + 2  # +2 for the length field itself
    app1_segment = struct.pack('>H', 0xFFE1) + struct.pack('>H', app1_length) + app1_payload

    return app1_segment


def create_jpeg_with_gps(output_path, variant_key, suspect_name,
                          lat_d, lat_m, lat_s, lat_ref,
                          lon_d, lon_m, lon_s, lon_ref,
                          seed=42):
    """
    Create a realistic-looking JPEG with embedded GPS EXIF data.
    The GPS will be readable by ExifTool on SIFT.
    """
    random.seed(seed)
    width, height = 1280, 960
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    # Generate a realistic gradient (looks like an indoor/outdoor photo)
    base_r = random.randint(80, 150)
    base_g = random.randint(80, 150)
    base_b = random.randint(90, 160)

    for y in range(height):
        for x in range(width):
            noise = random.randint(-10, 10)
            r = max(0, min(255, base_r + int((y / height) * 50) - int((x / width) * 20) + noise))
            g = max(0, min(255, base_g + int((y / height) * 40) - int((x / width) * 15) + noise))
            b = max(0, min(255, base_b + int((y / height) * 35) - int((x / width) * 10) + noise))
            pixels[x, y] = (r, g, b)

    draw = ImageDraw.Draw(img)
    # Simulate architectural elements
    for i in range(0, width, random.randint(60, 100)):
        shade = random.randint(20, 60)
        draw.line([(i, 0), (i, height)],
                  fill=(max(0, base_r - shade), max(0, base_g - shade), max(0, base_b - shade)),
                  width=random.randint(1, 3))
    for j in range(0, height, random.randint(80, 140)):
        shade = random.randint(10, 40)
        draw.rectangle(
            [(0, j), (width, j + random.randint(1, 4))],
            fill=(max(0, base_r - shade), max(0, base_g - shade), max(0, base_b - shade))
        )

    # Save to buffer (no EXIF)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    jpeg_bytes = buf.getvalue()

    # Build our GPS EXIF APP1 segment
    app1 = build_exif_app1(lat_d, lat_m, lat_s, lat_ref, lon_d, lon_m, lon_s, lon_ref)

    # Inject APP1 right after SOI (0xFFD8)
    soi = jpeg_bytes[:2]  # FF D8
    rest = jpeg_bytes[2:]  # Everything after SOI

    # Remove any existing APP0 (JFIF) marker to avoid conflicts
    if rest[:2] == b'\xff\xe0':
        # Skip APP0
        app0_len = struct.unpack('>H', rest[2:4])[0]
        rest = rest[2 + app0_len:]

    final_jpeg = soi + app1 + rest

    with open(output_path, 'wb') as f:
        f.write(final_jpeg)


if __name__ == "__main__":
    # Quick test
    create_jpeg_with_gps(
        "/tmp/test_gps.jpg", "test", "Test Suspect",
        37, 13, 46.56, "N",
        80, 24, 50.04, "W",
        seed=12345
    )
    print("Test JPEG created at /tmp/test_gps.jpg")
    print("File size:", len(open('/tmp/test_gps.jpg','rb').read()), "bytes")
