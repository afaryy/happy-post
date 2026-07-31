export type Post = {
  id: string;
  message: string;
  created_at: string;
};

export type CreatePostInput = {
  message: string;
};
