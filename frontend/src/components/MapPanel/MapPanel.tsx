import React from 'react';
import { APIProvider, Map as GoogleMap } from '@vis.gl/react-google-maps';
import useStore from '@store/store';
import { Plan } from '@type/plan';

// 3-1 で作ったフロント用のキー。ビルド成果物に埋め込まれる前提で、
// Google Cloud 側でリファラと Maps JavaScript API のみに制限している
const mapsApiKey: string | undefined = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

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

// 出発地を中心に地図を出す。ピン（3-3）と表示範囲の自動調整（3-4）はまだ
const RouteMap = ({ plan }: { plan: Plan }) => {
  const { lat, lng } = plan.origin.place;

  return (
    <div className='h-1/2 flex-none border-b border-gray-200 dark:border-gray-600'>
      {mapsApiKey ? (
        <APIProvider apiKey={mapsApiKey}>
          <GoogleMap
            // defaultCenter は最初の表示にしか効かないので、出発地が変わったら作り直す
            key={`${lat},${lng}`}
            defaultCenter={{ lat, lng }}
            defaultZoom={15}
            gestureHandling='greedy'
            disableDefaultUI
          />
        </APIProvider>
      ) : (
        <div className='flex h-full items-center justify-center text-sm text-gray-500 dark:text-gray-400'>
          地図のキー（VITE_GOOGLE_MAPS_API_KEY）が設定されていません
        </div>
      )}
    </div>
  );
};

const formatKm = (distance_m: number) => `${(distance_m / 1000).toFixed(1)} km`;

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
