import math


EARTH_RADIUS_METERS = 6_371_000


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return EARTH_RADIUS_METERS * c


def is_within_radius(
    lat1: float, lon1: float, lat2: float, lon2: float, radius: float
) -> bool:
    return haversine(lat1, lon1, lat2, lon2) <= radius
