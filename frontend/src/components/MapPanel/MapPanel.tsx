import React, { useEffect } from 'react';
import {
  APIProvider,
  AdvancedMarker,
  ColorScheme,
  Map as GoogleMap,
  Pin,
  useMap,
} from '@vis.gl/react-google-maps';
import useStore from '@store/store';
import { Plan } from '@type/plan';

// 3-1 で作ったフロント用のキー。ビルド成果物に埋め込まれる前提で、
// Google Cloud 側でリファラと Maps JavaScript API のみに制限している
const mapsApiKey: string | undefined = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

// 番号付きのピン（AdvancedMarker）にはマップ ID が要る。
// 未設定なら Google が開発用に用意している DEMO_MAP_ID を使う
const mapId: string =
  import.meta.env.VITE_GOOGLE_MAPS_MAP_ID || 'DEMO_MAP_ID';

// ピンの色。右のリストの印（bg-blue-600 / bg-red-600）と揃える
const ORIGIN_COLOR = { background: '#2563eb', borderColor: '#1e40af' };
const VISIT_COLOR = { background: '#dc2626', borderColor: '#991b1b' };

// チャットの右に置くパネル。Week 3 で地図が入る。
// スマホ（md 未満）では出さない。
const MapPanel = () => {
  const chatId = useStore((state) => state.chats?.[state.currentChatIndex]?.id);
  const plan = useStore((state) => (chatId ? state.plans[chatId] : undefined));

  return (
    <aside className='hidden md:flex w-[40%] flex-none flex-col h-full border-l border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100'>
      {plan && <RouteMap plan={plan} />}
      <h2 className='px-5 pt-4 pb-1 text-base font-semibold'>ルート</h2>
      {plan ? (
        <PlanList plan={plan} />
      ) : (
        <div className='flex flex-1 items-center justify-center p-6 text-center text-sm leading-7 text-gray-500 dark:text-gray-400'>
          プランができると、ここに
          <br />
          巡る順番が表示されます
        </div>
      )}
    </aside>
  );
};

// 出発地を S、訪問先を訪問順の番号でピンにし、全部のピンが収まる範囲で表示する
const RouteMap = ({ plan }: { plan: Plan }) => {
  const theme = useStore((state) => state.theme);
  const { origin, visits } = plan;
  const { lat, lng } = origin.place;

  return (
    <div className='h-1/2 flex-none border-b border-gray-200 dark:border-gray-600'>
      {mapsApiKey ? (
        <APIProvider apiKey={mapsApiKey}>
          <GoogleMap
            // defaultCenter と colorScheme は最初の表示にしか効かないので、
            // 出発地かテーマが変わったら作り直す
            key={`${lat},${lng},${theme}`}
            mapId={mapId}
            colorScheme={theme === 'dark' ? ColorScheme.DARK : ColorScheme.LIGHT}
            defaultCenter={{ lat, lng }}
            defaultZoom={15}
            gestureHandling='greedy'
            disableDefaultUI
          >
            <AdvancedMarker position={{ lat, lng }} title={origin.place.name}>
              <Pin {...ORIGIN_COLOR} glyph='S' glyphColor='#ffffff' />
            </AdvancedMarker>
            {visits.map((visit, i) => (
              <AdvancedMarker
                key={`${i}-${visit.place.name}`}
                position={{ lat: visit.place.lat, lng: visit.place.lng }}
                title={`${i + 1}. ${visit.place.name}`}
              >
                <Pin {...VISIT_COLOR} glyph={String(i + 1)} glyphColor='#ffffff' />
              </AdvancedMarker>
            ))}
            <RouteLine plan={plan} />
            <FitToPlan plan={plan} />
          </GoogleMap>
        </APIProvider>
      ) : (
        <div className='flex h-full items-center justify-center text-sm text-gray-500 dark:text-gray-400'>
          地図のキー（VITE_GOOGLE_MAPS_API_KEY）が設定されていません
        </div>
      )}
    </div>
  );
};

// 地図の表示範囲を、出発地と全訪問先が収まるように合わせる。
// 描画はせず、plan が変わるたびに地図を動かすだけの部品
const FitToPlan = ({ plan }: { plan: Plan }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    const places = [plan.origin.place, ...plan.visits.map((v) => v.place)];
    if (places.length === 1) {
      // 1点だけだと fitBounds は最大まで拡大してしまうので、中心とズームを直接決める
      map.setCenter(places[0]);
      map.setZoom(15);
      return;
    }
    const bounds = new google.maps.LatLngBounds();
    places.forEach(({ lat, lng }) => bounds.extend({ lat, lng }));
    map.fitBounds(bounds, 48); // 48px の余白を残して、端のピンが切れないようにする
  }, [map, plan]);

  return null;
};

// 出発地 → 1 → 2 … を訪問順に直線（点線）で結ぶ。
// 実際に歩く道の形ではない（道の形はバックエンドが取っていないので v1.1.0 で検討）。
// @vis.gl 1.6.1 には線の部品がないので、地図に google.maps.Polyline を直接置く
const RouteLine = ({ plan }: { plan: Plan }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    const path = [plan.origin.place, ...plan.visits.map((v) => v.place)].map(
      ({ lat, lng }) => ({ lat, lng })
    );
    const line = new google.maps.Polyline({
      map,
      path,
      strokeOpacity: 0, // 実線は消し、下の icons で点線を描く
      icons: [
        {
          icon: {
            path: 'M 0,-1 0,1',
            strokeColor: VISIT_COLOR.background,
            strokeOpacity: 0.8,
            scale: 3,
          },
          offset: '0',
          repeat: '12px',
        },
      ],
      zIndex: 0, // ピンより下に描く
    });
    // plan が変わったり地図が作り直されたりしたら、古い線を消す
    return () => line.setMap(null);
  }, [map, plan]);

  return null;
};

const formatKm =(distance_m: number) => `${(distance_m / 1000).toFixed(1)} km`;

const PlanList = ({ plan }: { plan: Plan }) => {
  const { origin, visits } = plan;
  const totalDistance = visits.reduce((sum, v) => sum + v.travel.distance_m, 0);
  const endTime =
    visits.length > 0
      ? visits[visits.length - 1].departure_time
      : origin.departure_time;

  return (
    <>
      <p className='px-5 pb-3 text-xs text-gray-500 dark:text-gray-400'>
        {visits.length}か所・徒歩 {formatKm(totalDistance)}・
        {origin.departure_time}〜{endTime}
      </p>
      <ol className='flex-1 overflow-y-auto px-4 pb-4'>
        <Stop badge='S' name={origin.place.name} isOrigin>
          {origin.departure_time} 出発
        </Stop>
        {visits.map((visit, i) => (
          <React.Fragment key={`${i}-${visit.place.name}`}>
            <li className='ml-[25px] border-l-2 border-dotted border-gray-300 dark:border-gray-600 py-1.5 pl-6 text-xs text-gray-500 dark:text-gray-400'>
              徒歩 {visit.travel.duration_min}分（
              {formatKm(visit.travel.distance_m)}）
            </li>
            <Stop badge={String(i + 1)} name={visit.place.name}>
              {visit.arrival_time} 着 → {visit.stay_minutes}分 →{' '}
              {visit.departure_time} 発
            </Stop>
          </React.Fragment>
        ))}
      </ol>
    </>
  );
};

// 出発地は S、訪問先は訪問順の番号。3-3 の地図のピンと同じ印にする
const Stop = ({
  badge,
  name,
  isOrigin = false,
  children,
}: {
  badge: string;
  name: string;
  isOrigin?: boolean;
  children: React.ReactNode;
}) => (
  <li className='flex items-start gap-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-850 px-3 py-2.5'>
    <span
      className={`grid h-[26px] w-[26px] flex-none place-items-center rounded-full text-xs font-bold text-white ${
        isOrigin ? 'bg-blue-600' : 'bg-red-600'
      }`}
    >
      {badge}
    </span>
    <div className='min-w-0'>
      <div className='truncate text-sm font-semibold'>{name}</div>
      <div className='mt-0.5 text-xs text-gray-500 dark:text-gray-400'>
        {children}
      </div>
    </div>
  </li>
);

export default MapPanel;
