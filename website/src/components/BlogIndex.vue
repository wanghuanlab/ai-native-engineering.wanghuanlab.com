<script setup lang="ts">
import { watchEffect } from "vue";
import { posts } from "../docs";

watchEffect(() => {
  document.title = "工程博客 · AI Native Engineering";
});
</script>

<template>
  <div class="blog-shell container">
    <header class="blog-header">
      <h1>工程博客</h1>
      <p>
        记录基线在真实使用中遇到的问题、背后的设计取舍，以及最终落到仓库里的改动。
      </p>
    </header>
    <ol class="post-list" aria-label="文章列表">
      <li v-for="post in posts" :key="post.id">
        <a :href="`/?blog=${post.id}`" class="post-row">
          <time :datetime="post.date">{{ post.date }}</time>
          <div>
            <h2>{{ post.title }}</h2>
            <p>{{ post.description }}</p>
          </div>
          <span class="post-arrow" aria-hidden="true">↗</span>
        </a>
      </li>
    </ol>
    <p v-if="!posts.length" class="post-empty">还没有文章。</p>
  </div>
</template>

<style scoped>
.blog-shell {
  min-height: 70vh;
  padding-top: 72px;
  padding-bottom: 120px;
}
.blog-header {
  max-width: 760px;
}
.blog-header h1 {
  font-size: clamp(36px, 4.4vw, 60px);
  line-height: 1.2;
  letter-spacing: -0.045em;
  font-weight: 600;
  margin: 0;
}
.blog-header p {
  font-size: 18px;
  line-height: 1.9;
  color: var(--muted);
  margin-top: 24px;
}
.post-list {
  list-style: none;
  padding: 0;
  margin: 64px 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.post-row {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr) 24px;
  gap: 32px;
  align-items: start;
  padding: 36px 32px;
  background: var(--surface);
  color: var(--ink);
  text-decoration: none;
  transition: background 0.2s;
}
.post-row:hover {
  background: #edf2ff;
}
.post-row time {
  font-size: 14px;
  color: var(--muted);
  padding-top: 6px;
}
.post-row h2 {
  font-size: 24px;
  line-height: 1.45;
  letter-spacing: -0.02em;
  font-weight: 600;
  margin: 0;
}
.post-row p {
  font-size: 16px;
  line-height: 1.85;
  color: var(--muted);
  margin: 12px 0 0;
  max-width: 720px;
}
.post-arrow {
  font-size: 22px;
  color: var(--accent);
}
.post-row:hover h2 {
  color: var(--accent);
}
.post-empty {
  color: var(--muted);
  margin-top: 40px;
}
@media (max-width: 800px) {
  .blog-shell {
    padding-top: 48px;
    padding-bottom: 80px;
  }
  .post-row {
    grid-template-columns: minmax(0, 1fr) 20px;
    gap: 12px 16px;
    padding: 26px 20px;
  }
  .post-row time {
    grid-column: 1 / -1;
    padding-top: 0;
  }
  .post-row h2 {
    font-size: 20px;
  }
}
</style>
