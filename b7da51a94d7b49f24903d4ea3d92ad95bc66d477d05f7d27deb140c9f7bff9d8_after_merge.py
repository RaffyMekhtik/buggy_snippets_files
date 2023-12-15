    def initialize_items(self):
        """ Get all player inventory items and add them to menu

        :return:
        """
        for name, properties in self.game.player1.inventory.items():
            obj = properties['item']
            image = self.shadow_text(obj.name, bg=(128, 128, 128))
            yield MenuItem(image, obj.name, obj.description, obj)