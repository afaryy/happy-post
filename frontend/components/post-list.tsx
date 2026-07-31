import type { Post } from "@/lib/types";

type PostListProps = {
  posts: Post[];
};

export function PostList({ posts }: PostListProps) {
  if (posts.length === 0) {
    return <p>No posts yet.</p>;
  }

  return (
    <ul>
      {posts.map((post) => (
        <li key={post.id}>{post.message}</li>
      ))}
    </ul>
  );
}
