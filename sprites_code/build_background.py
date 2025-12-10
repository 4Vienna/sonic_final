import pygame
import csv

class Tile():
    def __init__(self, tile_type, x, y):
        self.tile_type = tile_type
        self.x = x
        self.y = y

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
        x,y = 0,0
        for row in map:
            x=0
            for tile in row:
                if tile != '-1':
                    tiles.append(Tile(int(tile), x, y)) 
                x += self.tile_size
            y += self.tile_size

        self.map_width = x
        self.map_height = y
        return tiles
    