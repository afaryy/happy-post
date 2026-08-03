export type DailyEntry = {
  id: string;
  user_id: string;
  entry_date: string;
  happy_items: Array<{
    id: string;
    item_no: number;
    content: string;
    created_at: string;
  }>;
  encouragement_score: number;
  created_at: string;
  updated_at: string;
};

export type CurrentUser = {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
};

export type SaveDailyEntryInput = {
  happy_items: string[];
  encouragement_score: number;
};
