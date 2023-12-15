    def on_draw(self, event):
        self.framebuffer.activate()
        set_viewport(0, 0, 512, 512)
        clear(color=True, depth=True)
        set_state(depth_test=True)
        self.cube.draw('triangles', self.indices)
        self.framebuffer.deactivate()
        clear(color=True)
        set_state(depth_test=False)
        self.quad.draw('triangle_strip')