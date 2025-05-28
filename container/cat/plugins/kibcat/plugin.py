from cat.mad_hatter.decorators import tool, hook


@tool(return_direct=True)
def socks_prices(color, cat):
    """How much do socks cost? Input is the sock color."""
    prices = {
        "black": 5,
        "white": 10,
        "pink": 50,
    }
    if color not in prices.keys():
        return f"No {color} socks"
    else:
        return f"{prices[color]} €"
