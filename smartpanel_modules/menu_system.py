"""
Menu System for Smart Panel
Hierarchical navigation and menu management
"""


class MenuItem:
    """Individual menu item with optional action or submenu"""
    def __init__(self, title, action=None, submenu=None, data=None, enabled=True):
        self.title = title
        self.action = action
        self.submenu = submenu
        self.data = data
        self.enabled = enabled

    def execute(self, context):
        """Execute the menu item's action"""
        if self.action and self.enabled:
            return self.action(context)
        return None


class Menu:
    """Hierarchical menu container with navigation"""
    def __init__(self, title, items=None, parent=None):
        self.title = title
        self.items = items or []
        self.parent = parent
        self.selected_index = 0
        self.scroll_offset = 0
        self.context = {}  # Context for menu actions

    def add_item(self, item):
        """Add an item to the menu"""
        self.items.append(item)

    def get_visible_items(self, max_items=6):
        """Get items visible on screen, handling scrolling"""
        if len(self.items) <= max_items:
            return self.items

        # Ensure selected item is visible
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + max_items:
            self.scroll_offset = self.selected_index - max_items + 1

        return self.items[self.scroll_offset:self.scroll_offset + max_items]

    def navigate(self, direction):
        """Navigate menu: direction = 1 (down) or -1 (up)"""
        if not self.items:
            return

        self.selected_index = max(0, min(len(self.items) - 1, self.selected_index + direction))

        # Handle scrolling
        max_visible = 6
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + max_visible:
            self.scroll_offset = self.selected_index - max_visible + 1

    def select(self, context=None):
        """Select current item"""
        if not self.items or not self.items[self.selected_index].enabled:
            return self

        # Use provided context or menu's stored context
        ctx = context if context else self.context

        item = self.items[self.selected_index]
        if item.submenu:
            return item.submenu
        elif item.action:
            result = item.execute(ctx)
            if result is not None:
                return result
        return self

