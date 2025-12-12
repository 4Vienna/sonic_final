import pygame
import csv

class Tile():
    def __init__(self, tile_type, x, y, solid=None):
        # allow tile_type to be stored as int; `solid` can be explicitly set
        try:
            self.tile_type = int(tile_type)
        except Exception:
            # keep original value if it can't be converted
            self.tile_type = tile_type
        self.x = x
        self.y = y
        if solid is None:
            solid_list = [0, 1, 9, 10, 11]  # define which tile types are solid by default
            self.solid = True if self.tile_type in solid_list else False
        else:
            self.solid = bool(solid)

    def draw(self, surface, tileset, tile_size, tiles_per_row):
        # tile_type expected as integer index into the tileset
        idx = int(self.tile_type)
        if idx < 0:
            return
        # compute src rect on tileset
        col = idx % tiles_per_row
        row = idx // tiles_per_row
        src_rect = pygame.Rect(col * tile_size, row * tile_size, tile_size, tile_size)
        surface.blit(tileset, (self.x, self.y), src_rect)

class TileMap():
    def __init__(self, map_csv_filename, tileset_filename=None, tile_size=16, scale=1.0):
        # tile_size: source tileset tile size (pixels)
        # scale: final scale factor to apply to the rendered map surface
        self.tile_size = tile_size
        self.scale = float(scale) if scale is not None else 1.0
        # load tiles from csv
        self.tiles = self.load_tiles(map_csv_filename)

        # load tileset image (if provided try to infer)
        if tileset_filename is None:
            # try to infer tileset filename from csv path
            tileset_filename = map_csv_filename.replace('_map.csv', '_tiles.png')

        try:
            self.tileset = pygame.image.load(tileset_filename).convert_alpha()
        except Exception:
            self.tileset = None

        # compute map surface at source size
        self.map_surface = pygame.Surface((self.map_width, self.map_height), pygame.SRCALPHA)
        if self.tileset is not None:
            self.tileset.set_colorkey((0,0,0))
            self.tiles_per_row = max(1, self.tileset.get_width() // self.tile_size)
        else:
            self.tiles_per_row = 1

        self.load_map()

        # If a scale other than 1.0 is requested, scale the pre-rendered map surface
        if self.scale != 1.0:
            scaled_w = max(1, int(self.map_width * self.scale))
            scaled_h = max(1, int(self.map_height * self.scale))
            # create a scaled version for fast blits
            self.map_surface = pygame.transform.scale(self.map_surface, (scaled_w, scaled_h))
            # update map dimensions to scaled values
            self.map_width = scaled_w
            self.map_height = scaled_h

    def draw_map(self, surface):
        surface.blit(self.map_surface, (0,0))

    
    def load_map(self):
        # draw every tile onto the pre-rendered map surface
        if self.tileset is None:
            # nothing to draw
            return
        for tile in self.tiles:
            tile.draw(self.map_surface, self.tileset, self.tile_size, self.tiles_per_row)

    def read_csv(self, filename):
        map = []
        with open(filename, 'r') as f:
            data = csv.reader(f)
            for row in data:
                map.append(list(row))
        return map
    
    def load_tiles(self, filename):
        tiles = []
        map = self.read_csv(filename)
        # keep a copy of the raw map array (list of rows) for collision queries
        self.map_array = map
        x, y = 0, 0
        # build a grid of Tile objects (or None) matching map_array so we can
        # quickly query per-cell properties like `solid`.
        self.tile_grid = []
        for row in map:
            x = 0
            grid_row = []
            for tile in row:
                if tile != '-1':
                    # support optional `type:solid` syntax in CSV cells, e.g. `5:1` or `3:solid`
                    t = None
                    try:
                        cell = str(tile).strip()
                        if ':' in cell:
                            parts = [p.strip() for p in cell.split(':', 1)]
                            base = int(parts[0])
                            flag = parts[1].lower()
                            solid_flag = flag in ('1', 'true', 'yes', 'y', 'solid', 's')
                            t = Tile(base, x, y, solid=solid_flag)
                        else:
                            t = Tile(int(cell), x, y)
                    except Exception:
                        t = None
                    if t is not None:
                        tiles.append(t)
                        grid_row.append(t)
                else:
                    grid_row.append(None)
                x += self.tile_size
            self.tile_grid.append(grid_row)
            y += self.tile_size

        self.map_width = x
        self.map_height = y
        return tiles

    def get_tile_index_at_world(self, x, y):
        """Return the tile index (int) at world coordinates x,y, or -1 if none/out of bounds.

        World coordinates are expected to be in the same coordinate space as the scaled
        `map_surface` (i.e. after applying `scale`). We therefore convert world coords
        back to source tile indices by dividing by (tile_size * scale).
        """
        if not hasattr(self, 'map_array') or self.map_array is None:
            return -1
        try:
            tile_w = int(self.tile_size * self.scale)
        except Exception:
            tile_w = self.tile_size

        if tile_w <= 0:
            return -1

        # Account for map origin (world coordinates where the map's top-left is placed)
        origin_x = int(getattr(self, 'map_origin_x', 0))
        origin_y = int(getattr(self, 'map_origin_y', 0))

        local_x = int(x) - origin_x
        local_y = int(y) - origin_y

        if local_x < 0 or local_y < 0:
            return -1

        col = int(local_x // tile_w)
        row = int(local_y // tile_w)
        if row < 0 or col < 0:
            return -1
        if row >= len(self.map_array) or col >= len(self.map_array[row]):
            return -1
        try:
            return int(self.map_array[row][col])
        except Exception:
            return -1

    def get_tile_coords_at_world(self, x, y):
        """Return (row, col) of the tile at world coords x,y or (-1,-1) if out-of-bounds."""
        try:
            tile_w = int(self.tile_size * self.scale)
        except Exception:
            tile_w = self.tile_size

        if tile_w <= 0:
            return -1, -1

        origin_x = int(getattr(self, 'map_origin_x', 0))
        origin_y = int(getattr(self, 'map_origin_y', 0))

        local_x = int(x) - origin_x
        local_y = int(y) - origin_y

        if local_x < 0 or local_y < 0:
            return -1, -1

        col = int(local_x // tile_w)
        row = int(local_y // tile_w)
        if row < 0 or col < 0:
            return -1, -1
        if row >= len(self.map_array) or col >= len(self.map_array[row]):
            return -1, -1
        return row, col

    def is_solid_at(self, x, y):
        """Return True if the tile at world coords x,y is solid.

        This checks the Tile object's `solid` attribute if available. Falls
        back to treating tile index 0 as solid for compatibility.
        """
        # prefer tile object grid when available
        if hasattr(self, 'tile_grid'):
            row, col = self.get_tile_coords_at_world(x, y)
            if row == -1:
                return False
            try:
                tile = self.tile_grid[row][col]
                if tile is None:
                    return False
                return bool(getattr(tile, 'solid', False))
            except Exception:
                pass

        # fallback: treat index 0 as solid (legacy behavior)
        idx = self.get_tile_index_at_world(x, y)
        return idx == 0
    