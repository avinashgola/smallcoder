"""Static data for the demo applications."""

USERS = [
    {"id": 1, "login": "ada", "roles": ["admin", "editor"], "active": True},
    {"id": 2, "login": "grace", "roles": ["editor"], "active": True},
    {"id": 3, "login": "linus", "roles": ["viewer"], "active": False},
]

ITEMS = [
    {"sku": "A-100", "name": "Desk lamp", "price": 39.0, "stock": 12},
    {"sku": "A-101", "name": "Office chair", "price": 149.5, "stock": 3},
    {"sku": "B-200", "name": "Standing desk", "price": 480.0, "stock": 0},
]

PAGES = {
    "index": "Welcome to the handbook.",
    "mounting": "Applications can be served under a path prefix.",
    "routing": "Templates are matched from the first character.",
}


def user_by_id(user_id):
    for user in USERS:
        if user["id"] == user_id:
            return dict(user)
    return None


def item_by_sku(sku):
    for item in ITEMS:
        if item["sku"] == sku:
            return dict(item)
    return None


def users_with_role(role):
    return [dict(user) for user in USERS if role in user["roles"]]
