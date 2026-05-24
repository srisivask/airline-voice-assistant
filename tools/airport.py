import math

# Unique airport records with coordinates for distance calculations
_AIRPORT_RECORDS = [
    {"iata": "LAX", "name": "Los Angeles International Airport",           "city": "Los Angeles",    "lat": 33.9425,  "lng": -118.4081},
    {"iata": "JFK", "name": "John F. Kennedy International Airport",       "city": "New York",       "lat": 40.6413,  "lng": -73.7781},
    {"iata": "EWR", "name": "Newark Liberty International Airport",        "city": "Newark",         "lat": 40.6895,  "lng": -74.1745},
    {"iata": "ORD", "name": "O'Hare International Airport",                "city": "Chicago",        "lat": 41.9742,  "lng": -87.9073},
    {"iata": "SFO", "name": "San Francisco International Airport",         "city": "San Francisco",  "lat": 37.6213,  "lng": -122.3790},
    {"iata": "MIA", "name": "Miami International Airport",                 "city": "Miami",          "lat": 25.7959,  "lng": -80.2870},
    {"iata": "DFW", "name": "Dallas/Fort Worth International Airport",     "city": "Dallas",         "lat": 32.8998,  "lng": -97.0403},
    {"iata": "ATL", "name": "Hartsfield-Jackson Atlanta International",    "city": "Atlanta",        "lat": 33.6407,  "lng": -84.4277},
    {"iata": "SEA", "name": "Seattle-Tacoma International Airport",        "city": "Seattle",        "lat": 47.4502,  "lng": -122.3088},
    {"iata": "BOS", "name": "Logan International Airport",                 "city": "Boston",         "lat": 42.3656,  "lng": -71.0096},
    {"iata": "DEN", "name": "Denver International Airport",                "city": "Denver",         "lat": 39.8561,  "lng": -104.6737},
    {"iata": "LAS", "name": "Harry Reid International Airport",            "city": "Las Vegas",      "lat": 36.0840,  "lng": -115.1537},
    {"iata": "PHX", "name": "Phoenix Sky Harbor International Airport",    "city": "Phoenix",        "lat": 33.4373,  "lng": -112.0078},
    {"iata": "IAH", "name": "George Bush Intercontinental Airport",        "city": "Houston",        "lat": 29.9902,  "lng": -95.3368},
    {"iata": "DCA", "name": "Ronald Reagan Washington National Airport",   "city": "Washington D.C.","lat": 38.8521,  "lng": -77.0377},
    {"iata": "MCO", "name": "Orlando International Airport",               "city": "Orlando",        "lat": 28.4312,  "lng": -81.3081},
    {"iata": "MSP", "name": "Minneapolis-Saint Paul International Airport","city": "Minneapolis",    "lat": 44.8848,  "lng": -93.2223},
    {"iata": "PDX", "name": "Portland International Airport",              "city": "Portland",       "lat": 45.5898,  "lng": -122.5951},
    {"iata": "SAN", "name": "San Diego International Airport",             "city": "San Diego",      "lat": 32.7338,  "lng": -117.1933},
    {"iata": "YYZ", "name": "Toronto Pearson International Airport",       "city": "Toronto",        "lat": 43.6777,  "lng": -79.6248},
    {"iata": "YVR", "name": "Vancouver International Airport",             "city": "Vancouver",      "lat": 49.1967,  "lng": -123.1815},
    {"iata": "YUL", "name": "Montréal-Trudeau International Airport",      "city": "Montreal",       "lat": 45.4706,  "lng": -73.7408},
    {"iata": "YYC", "name": "Calgary International Airport",               "city": "Calgary",        "lat": 51.1315,  "lng": -114.0106},
    {"iata": "LHR", "name": "Heathrow Airport",                            "city": "London",         "lat": 51.4700,  "lng": -0.4543},
    {"iata": "CDG", "name": "Charles de Gaulle Airport",                   "city": "Paris",          "lat": 49.0097,  "lng": 2.5479},
    {"iata": "AMS", "name": "Amsterdam Airport Schiphol",                  "city": "Amsterdam",      "lat": 52.3086,  "lng": 4.7639},
    {"iata": "FRA", "name": "Frankfurt Airport",                           "city": "Frankfurt",      "lat": 50.0379,  "lng": 8.5622},
    {"iata": "MAD", "name": "Adolfo Suárez Madrid–Barajas Airport",       "city": "Madrid",         "lat": 40.4983,  "lng": -3.5676},
    {"iata": "FCO", "name": "Leonardo da Vinci International Airport",     "city": "Rome",           "lat": 41.8003,  "lng": 12.2389},
    {"iata": "AAL", "name": "Aalborg Airport",                             "city": "Aalborg",        "lat": 57.0928,  "lng": 9.8492},
    {"iata": "CPH", "name": "Copenhagen Airport",                          "city": "Copenhagen",     "lat": 55.6181,  "lng": 12.6561},
    {"iata": "NRT", "name": "Narita International Airport",                "city": "Tokyo",          "lat": 35.7720,  "lng": 140.3929},
    {"iata": "SYD", "name": "Kingsford Smith Airport",                     "city": "Sydney",         "lat": -33.9399, "lng": 151.1753},
    {"iata": "SIN", "name": "Singapore Changi Airport",                    "city": "Singapore",      "lat": 1.3644,   "lng": 103.9915},
    {"iata": "HKG", "name": "Hong Kong International Airport",             "city": "Hong Kong",      "lat": 22.3080,  "lng": 113.9185},
    {"iata": "DXB", "name": "Dubai International Airport",                 "city": "Dubai",          "lat": 25.2532,  "lng": 55.3657},
    {"iata": "ICN", "name": "Incheon International Airport",               "city": "Seoul",          "lat": 37.4602,  "lng": 126.4407},
    {"iata": "BKK", "name": "Suvarnabhumi Airport",                        "city": "Bangkok",        "lat": 13.6900,  "lng": 100.7501},
]

# Fast lookup by city name / IATA alias
AIRPORTS: dict[str, dict] = {
    # United States
    "los angeles": {"iata": "LAX", "name": "Los Angeles International Airport", "city": "Los Angeles"},
    "lax":         {"iata": "LAX", "name": "Los Angeles International Airport", "city": "Los Angeles"},
    "new york":    {"iata": "JFK", "name": "John F. Kennedy International Airport", "city": "New York"},
    "jfk":         {"iata": "JFK", "name": "John F. Kennedy International Airport", "city": "New York"},
    "newark":      {"iata": "EWR", "name": "Newark Liberty International Airport", "city": "Newark"},
    "ewr":         {"iata": "EWR", "name": "Newark Liberty International Airport", "city": "Newark"},
    "chicago":     {"iata": "ORD", "name": "O'Hare International Airport", "city": "Chicago"},
    "ord":         {"iata": "ORD", "name": "O'Hare International Airport", "city": "Chicago"},
    "san francisco": {"iata": "SFO", "name": "San Francisco International Airport", "city": "San Francisco"},
    "sfo":         {"iata": "SFO", "name": "San Francisco International Airport", "city": "San Francisco"},
    "miami":       {"iata": "MIA", "name": "Miami International Airport", "city": "Miami"},
    "mia":         {"iata": "MIA", "name": "Miami International Airport", "city": "Miami"},
    "dallas":      {"iata": "DFW", "name": "Dallas/Fort Worth International Airport", "city": "Dallas"},
    "fort worth":  {"iata": "DFW", "name": "Dallas/Fort Worth International Airport", "city": "Dallas"},
    "dfw":         {"iata": "DFW", "name": "Dallas/Fort Worth International Airport", "city": "Dallas"},
    "atlanta":     {"iata": "ATL", "name": "Hartsfield-Jackson Atlanta International Airport", "city": "Atlanta"},
    "atl":         {"iata": "ATL", "name": "Hartsfield-Jackson Atlanta International Airport", "city": "Atlanta"},
    "seattle":     {"iata": "SEA", "name": "Seattle-Tacoma International Airport", "city": "Seattle"},
    "sea":         {"iata": "SEA", "name": "Seattle-Tacoma International Airport", "city": "Seattle"},
    "boston":      {"iata": "BOS", "name": "Logan International Airport", "city": "Boston"},
    "bos":         {"iata": "BOS", "name": "Logan International Airport", "city": "Boston"},
    "denver":      {"iata": "DEN", "name": "Denver International Airport", "city": "Denver"},
    "den":         {"iata": "DEN", "name": "Denver International Airport", "city": "Denver"},
    "las vegas":   {"iata": "LAS", "name": "Harry Reid International Airport", "city": "Las Vegas"},
    "las":         {"iata": "LAS", "name": "Harry Reid International Airport", "city": "Las Vegas"},
    "phoenix":     {"iata": "PHX", "name": "Phoenix Sky Harbor International Airport", "city": "Phoenix"},
    "phx":         {"iata": "PHX", "name": "Phoenix Sky Harbor International Airport", "city": "Phoenix"},
    "houston":     {"iata": "IAH", "name": "George Bush Intercontinental Airport", "city": "Houston"},
    "iah":         {"iata": "IAH", "name": "George Bush Intercontinental Airport", "city": "Houston"},
    "washington":  {"iata": "DCA", "name": "Ronald Reagan Washington National Airport", "city": "Washington D.C."},
    "washington dc": {"iata": "DCA", "name": "Ronald Reagan Washington National Airport", "city": "Washington D.C."},
    "dca":         {"iata": "DCA", "name": "Ronald Reagan Washington National Airport", "city": "Washington D.C."},
    "orlando":     {"iata": "MCO", "name": "Orlando International Airport", "city": "Orlando"},
    "mco":         {"iata": "MCO", "name": "Orlando International Airport", "city": "Orlando"},
    "minneapolis": {"iata": "MSP", "name": "Minneapolis-Saint Paul International Airport", "city": "Minneapolis"},
    "msp":         {"iata": "MSP", "name": "Minneapolis-Saint Paul International Airport", "city": "Minneapolis"},
    "portland":    {"iata": "PDX", "name": "Portland International Airport", "city": "Portland"},
    "pdx":         {"iata": "PDX", "name": "Portland International Airport", "city": "Portland"},
    "san diego":   {"iata": "SAN", "name": "San Diego International Airport", "city": "San Diego"},
    "san":         {"iata": "SAN", "name": "San Diego International Airport", "city": "San Diego"},
    # Canada
    "toronto":     {"iata": "YYZ", "name": "Toronto Pearson International Airport", "city": "Toronto"},
    "yyz":         {"iata": "YYZ", "name": "Toronto Pearson International Airport", "city": "Toronto"},
    "vancouver":   {"iata": "YVR", "name": "Vancouver International Airport", "city": "Vancouver"},
    "yvr":         {"iata": "YVR", "name": "Vancouver International Airport", "city": "Vancouver"},
    "montreal":    {"iata": "YUL", "name": "Montréal-Trudeau International Airport", "city": "Montreal"},
    "yul":         {"iata": "YUL", "name": "Montréal-Trudeau International Airport", "city": "Montreal"},
    "calgary":     {"iata": "YYC", "name": "Calgary International Airport", "city": "Calgary"},
    "yyc":         {"iata": "YYC", "name": "Calgary International Airport", "city": "Calgary"},
    # Europe
    "london":      {"iata": "LHR", "name": "Heathrow Airport", "city": "London"},
    "lhr":         {"iata": "LHR", "name": "Heathrow Airport", "city": "London"},
    "paris":       {"iata": "CDG", "name": "Charles de Gaulle Airport", "city": "Paris"},
    "cdg":         {"iata": "CDG", "name": "Charles de Gaulle Airport", "city": "Paris"},
    "amsterdam":   {"iata": "AMS", "name": "Amsterdam Airport Schiphol", "city": "Amsterdam"},
    "ams":         {"iata": "AMS", "name": "Amsterdam Airport Schiphol", "city": "Amsterdam"},
    "frankfurt":   {"iata": "FRA", "name": "Frankfurt Airport", "city": "Frankfurt"},
    "fra":         {"iata": "FRA", "name": "Frankfurt Airport", "city": "Frankfurt"},
    "madrid":      {"iata": "MAD", "name": "Adolfo Suárez Madrid–Barajas Airport", "city": "Madrid"},
    "mad":         {"iata": "MAD", "name": "Adolfo Suárez Madrid–Barajas Airport", "city": "Madrid"},
    "rome":        {"iata": "FCO", "name": "Leonardo da Vinci International Airport", "city": "Rome"},
    "fco":         {"iata": "FCO", "name": "Leonardo da Vinci International Airport", "city": "Rome"},
    "aalborg":     {"iata": "AAL", "name": "Aalborg Airport", "city": "Aalborg"},
    "aal":         {"iata": "AAL", "name": "Aalborg Airport", "city": "Aalborg"},
    "copenhagen":  {"iata": "CPH", "name": "Copenhagen Airport", "city": "Copenhagen"},
    "cph":         {"iata": "CPH", "name": "Copenhagen Airport", "city": "Copenhagen"},
    # Asia-Pacific
    "tokyo":       {"iata": "NRT", "name": "Narita International Airport", "city": "Tokyo"},
    "nrt":         {"iata": "NRT", "name": "Narita International Airport", "city": "Tokyo"},
    "sydney":      {"iata": "SYD", "name": "Kingsford Smith Airport", "city": "Sydney"},
    "syd":         {"iata": "SYD", "name": "Kingsford Smith Airport", "city": "Sydney"},
    "singapore":   {"iata": "SIN", "name": "Singapore Changi Airport", "city": "Singapore"},
    "sin":         {"iata": "SIN", "name": "Singapore Changi Airport", "city": "Singapore"},
    "hong kong":   {"iata": "HKG", "name": "Hong Kong International Airport", "city": "Hong Kong"},
    "hkg":         {"iata": "HKG", "name": "Hong Kong International Airport", "city": "Hong Kong"},
    "dubai":       {"iata": "DXB", "name": "Dubai International Airport", "city": "Dubai"},
    "dxb":         {"iata": "DXB", "name": "Dubai International Airport", "city": "Dubai"},
    "seoul":       {"iata": "ICN", "name": "Incheon International Airport", "city": "Seoul"},
    "icn":         {"iata": "ICN", "name": "Incheon International Airport", "city": "Seoul"},
    "bangkok":     {"iata": "BKK", "name": "Suvarnabhumi Airport", "city": "Bangkok"},
    "bkk":         {"iata": "BKK", "name": "Suvarnabhumi Airport", "city": "Bangkok"},
}

# Cities without airports mapped to (lat, lng) — used to suggest nearest airports
NEARBY_CITIES: dict[str, tuple] = {
    # Southern California
    "santa monica":   (34.0195, -118.4912),
    "beverly hills":  (34.0736, -118.4004),
    "pasadena":       (34.1478, -118.1445),
    "anaheim":        (33.8366, -117.9143),
    "long beach":     (33.7701, -118.1937),
    "malibu":         (34.0259, -118.7798),
    "irvine":         (33.6846, -117.8265),
    "santa barbara":  (34.4208, -119.6982),
    "palm springs":   (33.8303, -116.5453),
    "glendale ca":    (34.1425, -118.2551),
    "burbank":        (34.1808, -118.3090),
    # Northern California
    "palo alto":      (37.4419, -122.1430),
    "san jose":       (37.3382, -121.8863),
    "berkeley":       (37.8716, -122.2727),
    "santa cruz":     (36.9741, -122.0308),
    "napa":           (38.2975, -122.2869),
    "monterey":       (36.6002, -121.8947),
    "oakland":        (37.8044, -122.2712),
    # New York area
    "brooklyn":       (40.6782,  -73.9442),
    "manhattan":      (40.7831,  -73.9712),
    "the bronx":      (40.8448,  -73.8648),
    "queens":         (40.7282,  -73.7949),
    "hoboken":        (40.7440,  -74.0324),
    "jersey city":    (40.7178,  -74.0431),
    "yonkers":        (40.9312,  -73.8988),
    "stamford":       (41.0534,  -73.5387),
    "white plains":   (41.0340,  -73.7629),
    # Chicago area
    "evanston":       (42.0451,  -87.6877),
    "naperville":     (41.7508,  -88.1535),
    "aurora":         (41.7606,  -88.3201),
    "joliet":         (41.5250,  -88.0817),
    # Dallas area
    "plano":          (33.0198,  -96.6989),
    "irving":         (32.8140,  -96.9489),
    "arlington":      (32.7357,  -97.1081),
    "frisco":         (33.1507,  -96.8236),
    "mckinney":       (33.1972,  -96.6397),
    "garland":        (32.9126,  -96.6389),
    # Phoenix area
    "scottsdale":     (33.4942, -111.9261),
    "tempe":          (33.4255, -111.9400),
    "mesa":           (33.4152, -111.8315),
    "chandler":       (33.3062, -111.8413),
    "glendale az":    (33.5387, -112.1860),
    "gilbert":        (33.3528, -111.7890),
    # Denver area
    "boulder":        (40.0150, -105.2705),
    "fort collins":   (40.5853, -105.0844),
    "colorado springs": (38.8339, -104.8214),
    "aurora co":      (39.7294, -104.8319),
    "lakewood":       (39.7047, -105.0814),
    # Seattle area
    "bellevue":       (47.6101, -122.2015),
    "redmond":        (47.6740, -122.1215),
    "tacoma":         (47.2529, -122.4443),
    "kirkland":       (47.6815, -122.2087),
    "renton":         (47.4829, -122.2171),
    # Miami area
    "fort lauderdale": (26.1224, -80.1373),
    "boca raton":     (26.3683,  -80.1289),
    "west palm beach": (26.7153, -80.0534),
    "coral gables":   (25.7215,  -80.2684),
    "hollywood fl":   (26.0112,  -80.1495),
    # Boston area
    "cambridge":      (42.3736,  -71.1097),
    "somerville":     (42.3876,  -71.0995),
    "providence":     (41.8240,  -71.4128),
    "worcester":      (42.2626,  -71.8023),
    "quincy":         (42.2529,  -71.0023),
    # Las Vegas area
    "henderson":      (36.0397, -114.9819),
    "north las vegas": (36.1989, -115.1175),
    "paradise":       (36.0900, -115.1440),
    # Houston area
    "sugar land":     (29.6197,  -95.6349),
    "the woodlands":  (30.1658,  -95.4613),
    "katy":           (29.7858,  -95.8244),
    "pasadena tx":    (29.6911,  -95.2091),
    # Atlanta area
    "decatur":        (33.7748,  -84.2963),
    "marietta":       (33.9526,  -84.5499),
    "alpharetta":     (34.0754,  -84.2941),
    "sandy springs":  (33.9304,  -84.3733),
    # Portland area
    "beaverton":      (45.4871, -122.8037),
    "hillsboro":      (45.5229, -122.9898),
    "gresham":        (45.5001, -122.4302),
    # San Diego area
    "chula vista":    (32.6401, -117.0842),
    "tijuana":        (32.5149, -117.0382),
    "el cajon":       (32.7948, -116.9625),
    # Washington DC area
    "arlington va":   (38.8816,  -77.0910),
    "alexandria":     (38.8048,  -77.0469),
    "bethesda":       (38.9807,  -77.1007),
    "reston":         (38.9586,  -77.3570),
    "silver spring":  (38.9912,  -77.0262),
    # Minneapolis area
    "saint paul":     (44.9537,  -93.0900),
    "bloomington mn": (44.8408,  -93.3477),
    "edina":          (44.8797,  -93.3497),
    # Canada
    "mississauga":    (43.5890,  -79.6441),
    "markham":        (43.8561,  -79.3370),
    "brampton":       (43.7315,  -79.7624),
    "richmond hill":  (43.8828,  -79.4403),
    "surrey":         (49.1913, -122.8490),
    "burnaby":        (49.2488, -122.9805),
    "richmond bc":    (49.1666, -123.1336),
    "laval":          (45.6066,  -73.7124),
    "longueuil":      (45.5314,  -73.5182),
    # Europe
    "windsor uk":     (51.4816,   -0.6043),
    "slough":         (51.5105,   -0.5950),
    "versailles":     (48.8014,    2.1301),
    "utrecht":        (52.0907,    5.1214),
    "cologne":        (50.9333,    6.9500),
    "düsseldorf":     (51.2217,    6.7762),
    "dusseldorf":     (51.2217,    6.7762),
    "rotterdam":      (51.9244,    4.4777),
    "barcelona":      (41.2974,    2.0833),
    "milan":          (45.4654,    9.1859),
    "munich":         (48.1351,   11.5820),
    "brussels":       (50.8503,    4.3517),
    "zurich":         (47.3769,    8.5417),
    "vienna":         (48.2082,   16.3738),
    # Asia-Pacific
    "kyoto":          (35.0116,  135.7681),
    "osaka":          (34.6937,  135.5023),
    "yokohama":       (35.4437,  139.6380),
    "busan":          (35.1796,  129.0756),
    "chiba":          (35.6074,  140.1065),
    "pattaya":        (12.9236,  100.8825),
    "johor bahru":    (1.4927,   103.7414),
    "shenzhen":       (22.5431,  114.0579),
    "guangzhou":      (23.1291,  113.2644),
    "macau":          (22.1987,  113.5439),
    "gold coast":     (-28.0167, 153.4000),
}


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _nearest_airports(lat: float, lng: float, limit: int = 3) -> list:
    scored = sorted(
        _AIRPORT_RECORDS,
        key=lambda r: _haversine(lat, lng, r["lat"], r["lng"])
    )
    return [(r, _haversine(lat, lng, r["lat"], r["lng"])) for r in scored[:limit]]


def resolve_airport(city_name: str) -> str:
    key = city_name.strip().lower()

    # Exact match
    airport = AIRPORTS.get(key)
    if airport:
        return f"FOUND: {airport['iata']} — {airport['name']} ({airport['city']})"

    # Partial match — skip 3-char IATA codes to avoid spurious substring hits
    for alias, info in AIRPORTS.items():
        if len(alias) > 3 and (key in alias or alias in key):
            return f"FOUND: {info['iata']} — {info['name']} ({info['city']})"

    # Nearby city lookup — suggest closest airports
    coords = NEARBY_CITIES.get(key)
    if coords:
        nearest = _nearest_airports(*coords)
        suggestions = "; ".join(
            f"{r['iata']} — {r['name']} ({r['city']}, ~{int(dist)} km away)"
            for r, dist in nearest
        )
        return (
            f"NEARBY: '{city_name}' doesn't have a direct airport in our system. "
            f"Closest airports we serve: {suggestions}"
        )

    return (
        f"NOT_FOUND: No airport found for '{city_name}'. "
        "Ask the user to clarify or provide the name of a nearby major city."
    )
