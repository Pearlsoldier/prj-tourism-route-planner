

def _place(stop) -> dict:
    # placeに意味は目的地という「役割」を持たない。この_place関数は、ただ場所の情報だけを整えて返す関数なので、_placeとする
    name = stop["name"]
    lat = stop["lat"]
    lng = stop["lng"]
    place = {"name": name, "lat":lat, "lng":lng }
    return place


def _travel(leg) -> dict:
    # 入力に２地点区間の情報（現在地点名、移動先名、その区間の移動距離、移動時間)が入ると、その区間の移動距離、移動時間と移動方法がつけて返される。
    distance_m = leg["distance_m"]
    duration_min = leg["duration_min"]
    mode = "walk"
    travel = { "distance_m":distance_m, "duration_min":duration_min, "mode":mode}
    return travel


def _visit(stop, leg) -> dict:
    # stopとlegを受け取り、目的地の名前、緯度経度、移動時間、移動距離、移動方法を返す。
    place = _place(stop)
    travel = _travel(leg)
    arrival_time = stop["arrival_time"]
    stay_minutes = stop["stay_minutes"]
    departure_time = stop["departure_time"]
    visit = {"place":place,
            "arrival_time":arrival_time,
            "stay_minutes":stay_minutes,
            "departure_time":departure_time,     
            "travel":travel
    }
    return visit

def to_plan(guidebook) -> dict | None:
    # フロントエンドに送り地図にするための目的地、移動情報を整える。
    if not guidebook.is_ready():
        return None

    if len(guidebook.selected[1:]) != len(guidebook.legs):
        print(f"★ ガイドブックの件数が合っていません。guidebook.selected[1:]: {len(guidebook.selected[1:])} | guidebook.legs: {len(guidebook.legs)}")
        return None
    place = _place(guidebook.selected[0])
    departure_time = guidebook.selected[0]["departure_time"]
    origin = {"place":place, "departure_time":departure_time}
    visits = []
    zip_a = guidebook.selected[1:]
    zip_b = guidebook.legs
    z = zip(zip_a,zip_b)
    for stop, leg in z:
        visit = _visit(stop, leg)
        visits.append(visit)

    plan = {"origin":origin, "visits":visits}
    return plan

