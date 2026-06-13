# Sprite, Portrait, and Palette File Formats

Reference for creating custom character sprites, portraits, and palettes
(the files in `graphics/sprites/custom/`, `graphics/portraits/custom/`, and
`graphics/palettes/custom/`). The implementation lives in `graphics/bgr15.py`,
`graphics/sprite_tile.py`, `graphics/sprite.py`, and `graphics/palette.py`.

The PNG conversion tools in `graphics/tools/` (`png_sprite.py`,
`png_portrait.py`) produce these formats from images (they require Pillow).

## Palette files (`.pal`)

A `.pal` file is a sequence of SNES BGR15 colors, 2 bytes per color,
little-endian. Character palettes are 16 colors = 32 bytes.

BGR15 bit layout (15 bits used of 16):

```
0bbbbbgg gggrrrrr   (msb ... lsb of the 16-bit little-endian word)
```

Each component is 5 bits (0-31). The randomizer converts to 8-bit RGB by
multiplying by 8, and back by integer-dividing by 8 — so RGB values are
effectively quantized to multiples of 8.

Color index 0 is transparent in-game.

## Sprite and portrait files (`.bin`)

A `.bin` file is a sequence of SNES 4bpp 8x8 tiles, 32 bytes per tile, with
no header. Each pixel is a 4-bit index into the 16-color palette.

Tile bit-packing (the SNES planar format): each 8-pixel row is built from
4 bytes that each contribute one bit per pixel. For row `r` (0-7) of a tile,
the four bytes are at offsets:

```
plane 0 (bit 0): 2*r
plane 1 (bit 1): 2*r + 1
plane 2 (bit 2): 16 + 2*r
plane 3 (bit 3): 16 + 2*r + 1
```

Within each byte, bit 7 is the leftmost pixel. A worked example is in the
comments at the top of `graphics/sprite_tile.py`.

## Expected sizes

| File | Size | Content |
|---|---|---|
| Character/portrait palette `.pal` | 32 bytes | 16 BGR15 colors |
| Portrait `.bin` | 800 bytes | 25 tiles (5x5 tiles = 40x40 pixels) |
| Character sprite `.bin` | tile multiple | poses as listed in `graphics/poses.py` |

Character sprite files shorter than the slot they replace are padded with
zeros (the missing poses render invisible in-game); longer files are
truncated. Portraits and palettes must match the expected size exactly or
seed generation raises a `ValueError` naming the file.

## Adding a custom sprite to the randomizer

1. Place the `.bin`/`.pal` files in the matching `graphics/*/custom/`
   directory. The filename convention is `Name-Author-Source.bin`.
2. Register the file in the id tables used by `graphics/sprites/sprites.py`,
   `graphics/portraits/portraits.py`, or `graphics/palettes/palettes.py`.
3. Verify with a build: `python3 wc.py -i ff3.smc -o tests/out.smc -cspr ...`
   (see `args/graphics.py` for the flag formats), or render to an image with
   `Sprite.write_ppm`.
