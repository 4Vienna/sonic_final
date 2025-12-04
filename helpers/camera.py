class Camera:
    def __init__(self, position=(0, 0), fov=90):
        self.position = position
        self.fov = fov

    def move(self, delta):
        """Move the camera by a delta vector."""
        self.position = (
            self.position[0] + delta[0],
            self.position[1] + delta[1],
        )

    def set_fov(self, fov):
        """Set the camera's field of view."""
        self.fov = fov