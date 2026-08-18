import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # bán kính Trái Đất (km)

    lat1, lon1, lat2, lon2 = map(math.radians, [
        lat1, lon1, lat2, lon2
    ])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.asin(math.sqrt(a))
    return round(R * c, 2)  # km, làm tròn 2 số
