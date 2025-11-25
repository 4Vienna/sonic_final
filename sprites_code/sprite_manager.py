import csv
csv_file = "resources\\sprites_numbers.csv" 

sprites_data = {}
with open(csv_file, newline='') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header row
    for row in reader:
        sprite_name = f'{row[0]}_{row[1]}'
        x = int(row[2])
        y = int(row[3])
        width = int(row[4])
        height = int(row[5])
        sprites_data[sprite_name] = (x, y, width, height)

def get_sprite_data(sprite_name):
    return sprites_data.get(sprite_name, None)

def get_all_sprites_of_type(sprite_name, sprite_type):
    result = []
    for sprite in sprites_data.keys():
        print(sprite)
        if sprite.startswith(sprite_name) and sprite_type in sprite:
            sprite = sprite.replace(f"{sprite_name}_", "")
            result.append(sprite)
    return result