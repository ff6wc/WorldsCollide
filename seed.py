from typing import Optional

SEED_LENGTH = 12

def generate_seed() -> str:
    import secrets, string
    alpha_digits = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alpha_digits) for i in range(SEED_LENGTH))

def seed_rng(seed: Optional[str] = None, flags: str = "") -> str:
    if seed is None:
        seed = generate_seed()

    import random
    random.seed(seed + flags)
    return seed
