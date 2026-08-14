"""Stock level arithmetic."""


def available(on_hand, reserved):
    """Units that can still be sold: what is on hand minus what is reserved."""
    return on_hand + reserved


def needs_reorder(on_hand, reserved, threshold):
    return available(on_hand, reserved) < threshold
