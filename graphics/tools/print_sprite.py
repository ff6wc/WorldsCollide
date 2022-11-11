
def print_sprite(sprite_id, palette_id, pose_id):
    from graphics.sprites.sprites import get_path as get_sprite_path
    from graphics.palettes.palettes import  get_path as get_palette_path

    print(str(get_rgb_bytes(get_sprite_path(sprite_id), get_palette_path(palette_id), pose_id)))

def get_rgb_bytes(sprite_path, palette_path, pose_id):
    from graphics.palette_file import PaletteFile
    from graphics.sprite_file import SpriteFile
    from graphics.poses import CHARACTER
    palette = PaletteFile(palette_path)

    sprite = SpriteFile(sprite_path, palette)

    return sprite.rgb_data(CHARACTER[pose_id]) + palette.alpha_rgb_data()

if __name__ == "__main__":
    import os, sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("sprite_id", type = int, help = "Id of the sprite to print")
    parser.add_argument("palette_id", type = int, help = "Id of the palette for the sprite")
    parser.add_argument("pose_id", type = int, help = "Id of the pose for the sprite", required=False, default=1)

    args = parser.parse_args()

    print_sprite(args.sprite_id, args.palette_id, args.pose_id)
