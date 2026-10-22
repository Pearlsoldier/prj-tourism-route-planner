// バックエンドの to_plan（backend/functions/plan_payload.py）が返す plan の形。
// 形を変えるときは to_plan と ADR-0001 も合わせて変える。

// _place の戻り値。役割を持たない、ただの場所
export interface Place {
  name: string;
  lat: number;
  lng: number;
}

// _travel の戻り値。直前の地点からこの訪問先までの移動
export interface Travel {
  distance_m: number;
  duration_min: number;
  mode: 'walk';
}

// 出発地。訪問先ではないので到着時刻・滞在時間を持たない
export interface Origin {
  place: Place;
  departure_time: string; // "HH:MM"
}

// _visit の戻り値
export interface Visit {
  place: Place;
  arrival_time: string; // "HH:MM"
  stay_minutes: number;
  departure_time: string; // "HH:MM"
  travel: Travel;
}

export interface Plan {
  origin: Origin;
  visits: Visit[];
}
