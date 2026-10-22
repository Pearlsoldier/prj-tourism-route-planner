import { Plan } from '@type/plan';
import { StoreSlice } from './store';

// チャットの id ごとに、バックエンドから届いた最新の plan を持つ。
// currentChatIndex はチャットの並べ替えでずれるのでキーにしない（ADR-0001 決定5）。
// null は「プランがまだ完成していない」応答が届いたことを表す。
// createPartializedState に加えていないので、再読み込みで消える。
export interface PlanSlice {
  plans: Record<string, Plan | null>;
  setPlan: (chatId: string, plan: Plan | null) => void;
}

export const createPlanSlice: StoreSlice<PlanSlice> = (set, get) => ({
  plans: {},
  setPlan: (chatId: string, plan: Plan | null) => {
    set((prev: PlanSlice) => ({
      ...prev,
      plans: { ...prev.plans, [chatId]: plan },
    }));
  },
});
