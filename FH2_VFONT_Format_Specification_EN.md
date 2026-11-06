# Forza Horizon 2 `.vfont` Format
## Technical Specification, Version 1.0

**Status:** Reverse-engineered format; the main sections have been validated against original FH2 font files.  
**Scope:** Individual `.vfont` files from `Mount\media\ui\Fonts.zip` in Forza Horizon 2.  
**Endianness:** Little-endian.  
**Date:** 6 November 2026.

---

## 1. Overview

The Forza Horizon 2 `.vfont` file is a binary vector-font container. In the files examined, it contains:

1. a font name and a service/header area;
2. a glyph metrics table;
3. a pair-kerning table;
4. a list of glyph geometry records;
5. for each geometry record, vertices stored as four IEEE-754 binary16 (half-float) values and an array of 16-bit indices.

This is not a TTF/OTF or OpenType file and must not be parsed as a conventional OpenType font. The `.vfont` extension is used by multiple Forza titles, but this document describes the validated FH2 layout only. Do not assume that offsets or rules documented here apply to FH3, FH4, FH5, or FH6.

### 1.1 Confidence levels

- **Confirmed on FH2 samples:** the structure was checked against binary files; sections reach EOF exactly and internal counters agree.
- **Empirically established:** behavior was confirmed by modifying a file and testing it in-game, but the full semantics may still be incomplete.
- **Unknown:** the field exists, but its purpose has not been established. Preserve it unchanged.

---

## 2. Verified samples

The structure was checked against the following original files from the FH2 `Fonts.zip` archive:

| File | Size | GlyphCount | KernCount | GeometryCount | EOF validation |
|---|---:|---:|---:|---:|---|
| `Anthem_A.vfont` | 357,080 | 248 | 1,094 | 248 | exact |
| `Anthem_B.vfont` | 351,338 | 248 | 1,101 | 248 | exact |
| `Anthem_C.vfont` | 367,740 | 248 | 1,118 | 248 | exact |
| `Anthem_D.vfont` | 306,676 | 248 | 718 | 248 | exact |
| `verdana.vfont` | 392,582 | 298 | 498 | 298 | exact |

Across all five samples:

- the glyph table contains unique Unicode code points;
- the number of geometry records equals `GlyphCount`;
- every glyph in the metrics table has a matching geometry record, and vice versa;
- `vertex_count` and `index_count` in the glyph table match the corresponding geometry record;
- `index_count` is divisible by three;
- every index is less than `vertex_count`;
- geometry records occupy the file consecutively up to the final byte, with no unexplained trailing or missing data;
- all kerning pairs refer to code points present in the glyph table.

These results apply to the listed samples. They do not prove that every file with a `.vfont` extension from another game uses this layout.

---

## 3. File layout

All offsets below are absolute offsets from the beginning of the file.

| Offset | Size | Type | Description |
|---:|---:|---|---|
| `0x00` | 8 | byte[8] | Font name, ASCII, usually NUL-terminated |
| `0x08` | 120 | byte[120] | Unknown/service area; preserve unchanged |
| `0x80` | 64 | header structure | Counts and font parameters |
| `0xC0` | `GlyphCount × 28` | GlyphRecord[] | Glyph table |
| after glyph table | `KernCount × 12` | KerningRecord[] | Pair-kerning table |
| after kerning table | 4 | uint32 | `GeometryCount` |
| after count | variable | GeometryRecord[] | Glyph geometry |
| end of file | — | — | Exactly matches the end of the last geometry record in verified samples |

Kerning table offset:

```text
KERN_OFFSET = 0xC0 + GlyphCount * 28
```

Geometry count offset:

```text
GEOMETRY_COUNT_OFFSET = 0xC0 + GlyphCount * 28 + KernCount * 12
```

First geometry record offset:

```text
GEOMETRY_OFFSET = GEOMETRY_COUNT_OFFSET + 4
```

---

## 4. Header

### 4.1. Font name and initial area

Bytes `0x00–0x07` contain the font name, for example:

- `Verdana\0`
- `Anthem_A\0`

The area `0x08–0x7F` has not been fully decoded. It may contain data required by the game. **Do not zero, rebuild, or normalize this area.** A safe editor should preserve it byte-for-byte.

### 4.2. Fields beginning at `0x80`

| Offset | Type | Specification name | Status |
|---:|---|---|---|
| `0x80` | uint32 | `GlyphCount` | confirmed |
| `0x84` | uint32 | `HeaderUnknown0` | unknown |
| `0x88` | uint32 | `HeaderUnknown1` | unknown |
| `0x8C` | uint32 | `KernCount` | confirmed |
| `0x90` | float32 | `HeaderFloat0` | type confirmed; meaning unknown |
| `0x94` | float32 | `HeaderFloat1` | type confirmed; meaning unknown |
| `0x98` | float32 | `HeaderFloat2` | type confirmed; meaning unknown |
| `0x9C` | uint32 | `HeaderUnknown2` | unknown |
| `0xA0` | uint32 | `HeaderUnknown3` | unknown |
| `0xA4` | uint32 | `HeaderUnknown4` | unknown |
| `0xA8` | uint32 | `HeaderUnknown5` | unknown |
| `0xAC` | uint32 | `HeaderUnknown6` | unknown |
| `0xB0` | uint32 | `HeaderUnknown7` | unknown |
| `0xB4` | uint32 | `HeaderUnknown8` | unknown |
| `0xB8` | uint32 | `HeaderUnknown9` | unknown |
| `0xBC` | uint32 | `HeaderUnknown10` | unknown |

The `0x90–0x98` fields are consistent with float32 values. This does **not** establish that they represent scale, line height, ascent, or descent. Their semantics are unknown. Do not modify unknown header fields without a dedicated experiment.

`GlyphCount` and `KernCount` are record counts, not byte sizes.

---

## 5. Glyph table

Start offset: `0xC0`  
Record size: **28 bytes** (`0x1C`)  
Number of records: `GlyphCount`

Record layout:

| Record offset | Type | Field | Description |
|---:|---|---|---|
| `+0x00` | uint32 | `codepoint` | Unicode scalar value |
| `+0x04` | float32 | `advance` | Horizontal glyph advance |
| `+0x08` | uint32 | `vertex_count` | Number of geometry vertices |
| `+0x0C` | uint32 | `index_count` | Number of 16-bit indices |
| `+0x10` | uint32 | `reserved0` | Zero in verified samples |
| `+0x14` | uint32 | `reserved1` | Zero in verified samples |
| `+0x18` | uint32 | `reserved2` | Zero in verified samples |

`codepoint` is stored as a little-endian 32-bit integer. It is not UTF-8 and is not a NUL-terminated string. In Python, convert it to a character with `chr(codepoint)` after validating the Unicode range.

`advance` is a 32-bit floating-point metric. It represents horizontal pen movement, not necessarily the visible outline width. It is not a pixel value. Conversion to screen pixels depends on the scale used by the game and the rendering context.

`vertex_count` and `index_count` are duplicated in the corresponding geometry record. In all verified samples, they match for each Unicode code point.

The final three `uint32` fields are zero in the five examined files. They should be treated as reserved/unknown, not assumed to be universally reserved for every version of the format.

### 5.1. Advance versus kerning

`advance` is a per-glyph metric. The kerning table stores separate adjustments for specific character pairs. Therefore, the final distance between two adjacent characters may depend on both the first glyph's `advance` and the `(left, right)` pair adjustment.

An editor that changes only `advance` does not edit the kerning table.

---

## 6. Pair-kerning table

Offset:

```text
KERN_OFFSET = 0xC0 + GlyphCount * 28
```

Record size: **12 bytes** (`0x0C`)  
Number of records: `KernCount`

Record layout:

| Record offset | Type | Field |
|---:|---|---|
| `+0x00` | uint32 | `left_codepoint` |
| `+0x04` | uint32 | `right_codepoint` |
| `+0x08` | float32 | `adjustment` |

`adjustment` is a signed pair-specific spacing correction. A negative value reduces the distance; a positive value increases it. This interpretation is consistent with the observed values and the role of the table.

Example from `verdana.vfont`:

```text
left_codepoint  = 33       # U+0021 EXCLAMATION MARK
right_codepoint = 8221     # U+201D RIGHT DOUBLE QUOTATION MARK
adjustment      ≈ -0.04480287
```

The verified FH2 files contain non-empty kerning tables: for example, `verdana.vfont` has 498 entries and `Anthem_A.vfont` has 1,094. Therefore, the claim that FH2 VFONT has no pair kerning is incorrect for the examined files.

Do not confuse `KernCount` with the glyph count. Kerning is a separate table of pairs, and one code point may participate in many pairs.

---

## 7. Glyph geometry

### 7.1. Geometry record count

Offset:

```text
GEOMETRY_COUNT_OFFSET = 0xC0 + GlyphCount * 28 + KernCount * 12
```

Type: `uint32`  
Expected value in verified files: `GeometryCount == GlyphCount`.

The geometry record array begins immediately after this four-byte count.

### 7.2. Geometry record header

Header size: 12 bytes.

| Record offset | Type | Field |
|---:|---|---|
| `+0x00` | uint32 | `codepoint` |
| `+0x04` | uint32 | `vertex_count` |
| `+0x08` | uint32 | `index_count` |

Use `codepoint` to match geometry with the glyph metrics table. Match by Unicode code point and also validate the counts. Do not rely only on record order.

### 7.3. Vertices

Immediately after the 12-byte header are `vertex_count` vertices.

Vertex size: **8 bytes**.

Each vertex contains four little-endian IEEE-754 binary16 (half-float) values:

| Offset | Type | Working name | Notes |
|---:|---|---|---|
| `+0` | float16 | `x` | X coordinate |
| `+2` | float16 | `y` | Y coordinate |
| `+4` | float16 | `z` | Third coordinate/geometry parameter; exact meaning unknown |
| `+6` | float16 | `w` | Additional component; empirically affects visible intensity/opacity |

Python reader:

```python
x, y, z, w = struct.unpack_from("<eeee", data, vertex_offset)
```

Do not unconditionally interpret `z` and `w` as conventional 3D depth and alpha for every font. The fourth component `w` affects the rendered visual intensity in the tested experiments, but the complete shader/renderer contract has not been recovered.

### 7.4. Indices

After the vertex array comes the index array:

- type: `uint16`;
- endianness: little-endian;
- number of elements: `index_count`;
- size: `index_count * 2` bytes.

In the verified FH2 files, `index_count` is always divisible by three. Each consecutive group of three indices forms a triangle:

```text
(i0, i1, i2), (i3, i4, i5), ...
```

Every index must satisfy:

```text
0 <= index < vertex_count
```

Do not interpret `index_count` as the number of triangles. The triangle count is `index_count // 3`.

All indices in the examined samples are within the vertex range, and all index arrays have lengths divisible by three. This supports a conventional indexed triangle list for the examined FH2 fonts.

### 7.5. Geometry record size

```text
geometry_record_size = 12 + vertex_count * 8 + index_count * 2
```

The next record begins immediately after the final index of the current glyph. No extra per-record alignment is required in the verified files.

An empty glyph (for example, a space) may have `vertex_count == 0` and `index_count == 0`. Its 12-byte geometry header is still present.

---

## 8. Complete section-offset calculation

Let:

```text
G = uint32(0x80)  # GlyphCount
K = uint32(0x8C)  # KernCount
```

Then:

```text
glyph_table_start = 0xC0
glyph_table_size  = G * 28
kern_table_start  = glyph_table_start + glyph_table_size
kern_table_size   = K * 12
geometry_count_offset = kern_table_start + kern_table_size
geometry_count    = uint32(geometry_count_offset)
geometry_records_start = geometry_count_offset + 4
```

Repeat `geometry_count` times:

```text
read codepoint:    uint32
read vertex_count: uint32
read index_count:  uint32

vertex_bytes = vertex_count * 8
index_bytes  = index_count * 2

read vertex_bytes
read index_bytes
```

At the end:

```text
cursor == file_size
```

This equality holds exactly for the verified samples.

---

## 9. Recommended parser validation

A robust parser should validate the data before displaying or modifying it:

1. File size is large enough for the header.
2. `GlyphCount` and `KernCount` are within reasonable limits, and computed offsets do not exceed the file.
3. The glyph table contains no duplicate or invalid Unicode scalar values.
4. `advance` is a finite float32. Do not impose an unnecessarily narrow range without evidence; different fonts may use different metrics.
5. `vertex_count` and `index_count` in the glyph table match the geometry record for the same `codepoint`.
6. `GeometryCount == GlyphCount` for the verified FH2 family.
7. Geometry records contain no duplicate code points.
8. `index_count % 3 == 0`.
9. Every index is less than `vertex_count`.
10. All bounds are checked before reading, including integer overflow and EOF.
11. The cursor after the last geometry record equals the file size.
12. When saving, unchanged sections should remain byte-identical.

Do not reject a file merely because unknown header fields differ from `Verdana`; their purpose has not been established.

---

## 10. Minimal independent Python parser

The following standalone example reads the sections and validates their relationships. It does not reuse code from the earlier FH2 Viewer or Metric Editor. It is intended for inspection and structural validation, not full rendering.

```python
import math
import struct
from pathlib import Path

HEADER_GLYPH_COUNT = 0x80
HEADER_KERN_COUNT = 0x8C
GLYPH_TABLE_OFFSET = 0xC0
GLYPH_RECORD_SIZE = 28
KERN_RECORD_SIZE = 12
GEOMETRY_HEADER_SIZE = 12
VERTEX_SIZE = 8

def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]

def parse_fh2_vfont(path):
    data = Path(path).read_bytes()
    size = len(data)

    if size < 0xC0:
        raise ValueError("File is smaller than the minimum header")

    name = data[:8].split(b"\\0", 1)[0].decode("ascii", "replace")
    glyph_count = u32(data, HEADER_GLYPH_COUNT)
    kern_count = u32(data, HEADER_KERN_COUNT)

    glyph_start = GLYPH_TABLE_OFFSET
    kern_start = glyph_start + glyph_count * GLYPH_RECORD_SIZE
    geometry_count_offset = kern_start + kern_count * KERN_RECORD_SIZE

    if kern_start > size or geometry_count_offset + 4 > size:
        raise ValueError("Table sections exceed file bounds")

    glyphs = {}
    for i in range(glyph_count):
        off = glyph_start + i * GLYPH_RECORD_SIZE
        cp, advance, vc, ic, r0, r1, r2 = struct.unpack_from(
            "<IfIIIII", data, off
        )
        if cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
            raise ValueError(f"Invalid Unicode code point U+{cp:04X}")
        if cp in glyphs:
            raise ValueError(f"Duplicate glyph U+{cp:04X}")
        if not math.isfinite(advance):
            raise ValueError(f"Invalid advance for U+{cp:04X}")
        glyphs[cp] = {
            "advance": advance,
            "vertex_count": vc,
            "index_count": ic,
            "record_offset": off,
            "reserved": (r0, r1, r2),
        }

    kernings = []
    for i in range(kern_count):
        off = kern_start + i * KERN_RECORD_SIZE
        left, right, adjustment = struct.unpack_from("<IIf", data, off)
        if not math.isfinite(adjustment):
            raise ValueError("Invalid kerning adjustment")
        kernings.append((left, right, adjustment))

    geometry_count = u32(data, geometry_count_offset)
    cursor = geometry_count_offset + 4
    geometries = {}

    for i in range(geometry_count):
        if cursor + GEOMETRY_HEADER_SIZE > size:
            raise ValueError("Truncated geometry header")

        cp, vc, ic = struct.unpack_from("<III", data, cursor)
        record_offset = cursor
        cursor += GEOMETRY_HEADER_SIZE

        vertex_bytes = vc * VERTEX_SIZE
        index_bytes = ic * 2
        end = cursor + vertex_bytes + index_bytes

        if end > size:
            raise ValueError(f"Geometry U+{cp:04X} exceeds EOF")
        if ic % 3:
            raise ValueError(f"index_count is not divisible by 3 for U+{cp:04X}")

        vertices = [
            struct.unpack_from("<eeee", data, cursor + j * VERTEX_SIZE)
            for j in range(vc)
        ]
        index_offset = cursor + vertex_bytes
        indices = struct.unpack_from("<" + "H" * ic, data, index_offset) if ic else ()

        if indices and max(indices) >= vc:
            raise ValueError(f"Index out of vertex range for U+{cp:04X}")
        if cp in geometries:
            raise ValueError(f"Duplicate geometry U+{cp:04X}")

        geometries[cp] = {
            "vertex_count": vc,
            "index_count": ic,
            "vertices": vertices,
            "indices": indices,
            "record_offset": record_offset,
        }
        cursor = end

    if cursor != size:
        raise ValueError(
            f"{size - cursor} unexplained bytes remain after the last geometry record"
        )

    if geometry_count != glyph_count:
        raise ValueError("GeometryCount differs from GlyphCount")

    if set(glyphs) != set(geometries):
        raise ValueError("Metrics and geometry code-point sets do not match")

    for cp, glyph in glyphs.items():
        geom = geometries[cp]
        if (glyph["vertex_count"], glyph["index_count"]) != (
            geom["vertex_count"], geom["index_count"]
        ):
            raise ValueError(f"Geometry counts do not match for U+{cp:04X}")

    for left, right, _ in kernings:
        if left not in glyphs or right not in glyphs:
            raise ValueError("Kerning entry references a missing glyph")

    return {
        "name": name,
        "glyph_count": glyph_count,
        "kern_count": kern_count,
        "glyphs": glyphs,
        "kernings": kernings,
        "geometries": geometries,
        "file_size": size,
    }
```

Usage:

```python
font = parse_fh2_vfont("verdana.vfont")
print(font["name"], font["glyph_count"], font["kern_count"])
print(font["glyphs"][ord("A")])
print(font["geometries"][ord("A")]["vertex_count"])
```

---

## 11. Safe editing

### 11.1. Editing Advance

To edit the Advance of glyph `cp`:

```text
record_offset = 0xC0 + glyph_index * 28
advance_offset = record_offset + 4
```

Write the new value as a little-endian float32:

```python
struct.pack_into("<f", mutable_data, advance_offset, new_advance)
```

This changes only the four metric bytes. Geometry, indices, kerning, and all other data remain untouched.

### 11.2. Editing geometry

When changing vertices, preserve:

- the original `vertex_count`;
- the original `index_count`;
- the geometry record byte size;
- valid index ranges;
- section order and exact file length.

If only vertex values are changed and the number of vertices remains the same, file size does not change. If counts or the number of vertices/indices change, subsequent records must be rebuilt and all related structures validated; an in-place overwrite is no longer safe.

### 11.3. Recommendations

- Never overwrite the original on the first save.
- Keep the original file and create a separate patched copy.
- Prefer targeted float32 edits for metrics.
- Do not change `GlyphCount`, `KernCount`, or `GeometryCount` without a specific reason.
- Do not add new code points by simply appending a record: multiple sections and the game loader must be updated and tested.
- Do not transfer geometry between different Forza generations without separately analyzing their format and rendering paths.
- Re-open the saved file with an independent parser and test it in-game.

---

## 12. Limitations and open questions

This specification does not claim to fully describe the FH2 rendering engine. The following are still unknown:

1. exact semantics of fields `0x08–0x7F`;
2. purpose of all header fields `0x84–0xBC`;
3. complete mathematical interpretation of vertex `z` and `w`;
4. exact conversion of coordinates and metrics to screen pixels at every UI scale;
5. fallback behavior when a glyph is missing;
6. loader behavior for unknown or duplicate Unicode code points;
7. compatibility with VFONT files from FH3 and later titles.

Do not fill these gaps with guesses. New conclusions should be accompanied by a concrete test file, binary offsets, and a reproducible result.

---

## 13. Common parser mistakes

- **Skipping the kerning table.** The geometry count is not immediately after the glyph table; it follows `KernCount × 12` bytes.
- **Using the wrong kerning record size.** Each record is 12 bytes, not 8.
- **Misreading indices.** `index_count` is the number of uint16 indices, not the number of triangles.
- **Reading vertices as float32.** Vertex components are half-floats, two bytes each.
- **Ignoring duplicated counters.** Vertex and index counts occur in both the glyph table and geometry header; compare them.
- **Searching for geometry by signature or filename.** Compute its location from the counters and sizes of preceding sections.
- **Treating Advance as pixel width.** It is a font metric, not a screen-space value.
- **Applying the FH2 schema to FH3/FH4/FH5/FH6.** Similar file extensions do not guarantee identical binary layouts.

---

## 14. Validation checklist for a new file

Before treating an unknown `.vfont` as compatible with this specification, verify:

- [ ] name can be read from the first 8 bytes;
- [ ] `GlyphCount` at `0x80` is reasonable;
- [ ] glyph table ends at `0xC0 + GlyphCount × 28`;
- [ ] `KernCount` at `0x8C` yields a valid table of 12-byte records;
- [ ] `GeometryCount` is read at the computed offset;
- [ ] geometry records parse without crossing EOF;
- [ ] `GeometryCount == GlyphCount`;
- [ ] metrics and geometry Unicode code-point sets match;
- [ ] vertex/index counts match between both sections;
- [ ] `index_count` is divisible by three;
- [ ] every index is less than `vertex_count`;
- [ ] the final geometry record ends exactly at EOF.

If any check fails, do not use the FH2 editor on the file without further analysis.

---

## 15. References and provenance

- Original test samples: `Fonts.zip` from Forza Horizon 2, files `Anthem_A.vfont`, `Anthem_B.vfont`, `Anthem_C.vfont`, `Anthem_D.vfont`, and `verdana.vfont`.
- Independent public note with a preliminary 010 Editor template for FH2 VFONT: [ResHax — Forza Horizon 2 vfont](https://reshax.com/topic/19657-forza-horizon-2-vfont/). This specification refines section sizes and offsets by checking the original files. Unknown fields are deliberately left unnamed until supported by evidence.

**Recommended rule for future researchers:** first achieve a successful full read/round-trip of an original file, with exact EOF alignment and validation of all internal references and counters. Add visualization and editing features only after that.
