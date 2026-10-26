import React from 'react';

// チャットの右に置くパネル。Week 3 で地図が入る。
// スマホ（md 未満）では出さない。
const MapPanel = () => {
  return (
    <aside className='hidden md:flex w-[40%] flex-none flex-col h-full border-l border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100'>
      <h2 className='px-5 pt-4 pb-2 text-base font-semibold'>ルート</h2>
      <div className='flex flex-1 items-center justify-center p-6 text-center text-sm leading-7 text-gray-500 dark:text-gray-400'>
        プランができると、ここに
        <br />
        巡る順番が表示されます
      </div>
    </aside>
  );
};

export default MapPanel;
