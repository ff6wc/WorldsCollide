# each tile is 8x8 colors which are each represented by a palette id

from graphics.sprite_tile import SpriteTile

class Sprite:
    def __init__(self, tiles, palette):
        self.palette = palette
        self.tiles = tiles
        self.tile_count = len(tiles)

    @property
    def data(self):
        data = []
        for tile in self.tiles:
            data.extend(tile.data)
        return data

    @data.setter
    def data(self, new_data):
        self.tiles = []
        self.tile_count = len(new_data) // SpriteTile.DATA_SIZE
        for tile_index in range(self.tile_count):
            data_index = tile_index * SpriteTile.DATA_SIZE
            tile_data = new_data[data_index : data_index + SpriteTile.DATA_SIZE]

            tile = SpriteTile(tile_data)
            self.tiles.append(tile)

    def tile_matrix(self, tile_id_matrix):
        # tile_id_matrix is lists of rows, inner lists joined horizontally then outer list joined vertically
        # example formats:
        # [[0, 1], [2, 3]]  returns [[tile 0 + tile 1],
        #                            [tile 2 + tile 3]]
        # [[0, 1]]          returns [[tile 0 + tile 1]] # joined horizontally (one row of tiles)
        # [0, 1]            returns [[tile 0,           # joined vertically (one column of tiles)
        #                             tile 1]]
        result = []
        for tile_row in tile_id_matrix:
                for row_index in range(SpriteTile.ROW_COUNT):
                    result_row = []
                    try:
                        for tile_id in tile_row:
                            try:
                                result_row += self.tiles[tile_id].colors[row_index]
                            except IndexError:
                                result_row += [0] * SpriteTile.COL_COUNT
                    except TypeError as error:
                        tile_id = tile_row # tile_row is not a list of lists, the matrix is one column
                        result_row = self.tiles[tile_id].colors[row_index]
                    result.append(result_row)
        return result

    BITS_PER_VALUE = 8 # rgb component size in ppm output

    def _pose_rgb(self, pose):
        # render a pose (matrix of tile ids) to (width, height, flat rgb values)
        pose_values = self.tile_matrix(pose)

        width = SpriteTile.COL_COUNT * len(pose[0])
        height = SpriteTile.ROW_COUNT * len(pose)

        rgb_values = []
        for row_index in range(height):
            for col_index in range(width):
                color_id = pose_values[row_index][col_index]
                rgb_values.extend(self.palette.colors[color_id].rgb)

        return width, height, rgb_values

    def rgb_data(self, pose):
        return self._pose_rgb(pose)[2]

    def write_ppm(self, output_file, pose):
        width, height, rgb_values = self._pose_rgb(pose)

        from graphics.ppm import write_ppm6
        write_ppm6(width, height, self.BITS_PER_VALUE, rgb_values, output_file)

    def get_ppm(self, pose):
        width, height, rgb_values = self._pose_rgb(pose)

        from graphics.ppm import get_ppm
        return get_ppm(width, height, self.BITS_PER_VALUE, rgb_values)
