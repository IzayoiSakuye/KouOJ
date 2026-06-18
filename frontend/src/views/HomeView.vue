<script setup lang="ts">
  import { onMounted, ref } from 'vue';
  import { RouterLink } from 'vue-router';
  import { getHomeData } from '../api/home';
  import type { HomeData } from '../types/api';
  import { getDifficultyClass, getDifficultyText } from '../utils/problem';
  import { formatDateTime } from '../utils/time';

  const homeData = ref<HomeData|null>(null)
  const loading = ref(false)
  const errorMessage = ref('')
  async function loadHomeData()
  {
    loading.value = true
    errorMessage.value = ''
    try 
    {
      const response = await getHomeData()
      homeData.value = response.data

    }
    catch (error) 
    {
      errorMessage.value = "首页加载失败"
    }
    finally 
    {
      loading.value = false;
    }
  }

  onMounted(()=>
  {
    loadHomeData()
  })

</script>

<template>
  <main>
    <p v-if="loading">加载中...</p>
    <p v-else-if="errorMessage">{{ errorMessage }}</p>

  <div v-else-if="homeData" class="home-page">
      <!-- 欢迎区域 -->
      <section class="welcome-panel">
        <div>
          <h1>KouOJ</h1>
          <p class="welcome-description">
            Presented by Kouma Industry
          </p>

          <div class="welcome-actions">
            <RouterLink class="primary-link" to="/problems">
              开始刷题
            </RouterLink>

            <RouterLink class="secondary-link" to="/submissions">
              查看提交
            </RouterLink>
          </div>
        </div>
      </section>

      <!-- 每日一题 -->
      <section class="daily-panel">
        <div class="section-header">
          <div>
            <p class="eyebrow">Daily Challenge</p>
            <h2>每日一题</h2>
          </div>

          <RouterLink to="/problems">浏览题库</RouterLink>
        </div>

        <RouterLink v-if="homeData.daily_problem" class="daily-problem" :to="`/problems/${homeData.daily_problem.id}`">
          <div>
            <span class="problem-id">
              #{{ homeData.daily_problem.id }}
            </span>

            <h3>{{ homeData.daily_problem.title }}</h3>

            <div class="tag-list">
              <span v-for="tag in homeData.daily_problem.tags" :key="tag.id" class="tag">
                {{ tag.name }}
              </span>
            </div>
          </div>

          <div class="daily-meta">
            <span class="difficulty-pill" :class="getDifficultyClass(homeData.daily_problem.difficulty)">
              {{ getDifficultyText(homeData.daily_problem.difficulty) }}
            </span>

            <span>{{ homeData.daily_problem.time_limit }} ms</span>
            <span>{{ homeData.daily_problem.memory_limit }} MB</span>
          </div>
        </RouterLink>

        <p v-else>暂无题目</p>
      </section>

      <!-- 快捷入口 -->
      <div class="quick-links">
        <RouterLink to="/problems">
          <strong>题库</strong>
          <span>浏览和筛选全部题目</span>
        </RouterLink>

        <RouterLink to="/submissions">
          <strong>提交记录</strong>
          <span>查看最新判题结果</span>
        </RouterLink>

        <RouterLink to="/profile">
          <strong>个人中心</strong>
          <span>查看刷题统计与热力图</span>
        </RouterLink>
      </div>

      <!-- 下方双栏 -->
      <div class="home-grid">
        <section>
          <div class="section-header">
            <div>
              <p class="eyebrow">Continue Practicing</p>
              <h2>未完成题目</h2>
            </div>

            <RouterLink to="/problems">查看全部</RouterLink>
          </div>

          <div v-if="homeData.unfinished_problems.length > 0" class="problem-list">
            <RouterLink v-for="problem in homeData.unfinished_problems" :key="problem.id" class="problem-row"
              :to="`/problems/${problem.id}`">
              <div>
                <span class="problem-id">#{{ problem.id }}</span>
                <strong>{{ problem.title }}</strong>
              </div>

              <span class="difficulty-pill" :class="getDifficultyClass(problem.difficulty)">
                {{ getDifficultyText(problem.difficulty) }}
              </span>
            </RouterLink>
          </div>

          <p v-else>你已经完成所有题目了。</p>
        </section>

        <section>
          <div class="section-header">
            <div>
              <p class="eyebrow">Announcements</p>
              <h2>系统公告</h2>
            </div>
          </div>

          <div v-if="homeData.announcements.length > 0" class="announcement-list">
            <article v-for="announcement in homeData.announcements" :key="announcement.id" class="announcement-item">
              <div class="announcement-title">
                <span v-if="announcement.is_pinned" class="pinned">
                  置顶
                </span>

                <strong>{{ announcement.title }}</strong>
              </div>

              <p>{{ announcement.content }}</p>
              <time>{{ formatDateTime(announcement.created_at) }}</time>
            </article>
          </div>

          <p v-else>暂无公告</p>
        </section>

      </div>
    </div>

  </main>
</template>

<style scoped>
.home-page
{
  display: grid;
  gap: 20px;
}

.welcome-panel
{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 32px;
  padding: 32px;
  color: white;
  background: #b42335;
}

.welcome-panel h1
{
  margin-bottom: 10px;
  color: white;
  font-size: 36px;
}

.welcome-description
{
  max-width: 560px;
  color: #ffe4e6;
}

.welcome-panel .primary-link
{
  color: #8f1d2c;
  background: white;
}

.welcome-panel .primary-link:hover
{
  color: #6f1622;
  background: #fff1f2;
}

.eyebrow
{
  margin: 0 0 6px;
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
}

.welcome-panel .eyebrow
{
  color: #fecdd3;
}

.welcome-actions,
.language-list,
.tag-list,
.daily-meta
{
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.welcome-actions
{
  margin-top: 22px;
}

.primary-link,
.secondary-link
{
  display: inline-flex;
  padding: 9px 16px;
  border: 1px solid transparent;
  border-radius: var(--radius);
}

.primary-link
{
  color: white;
  background: var(--primary);
}

.secondary-link
{
  color: white;
  border-color: #e9a5ad;
}

.secondary-link:hover
{
  border-color: white;
  color: white;
}

.language-list span
{
  padding: 6px 10px;
  border: 1px solid #c65c68;
  border-radius: 999px;
  color: #fff1f2;
  background: rgba(255, 255, 255, 0.08);
  font-size: 13px;
}

.section-header
{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 16px;
}

.daily-problem
{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface-muted);
}

.daily-problem h3
{
  margin: 5px 0 12px;
  font-size: 21px;
}

.problem-id
{
  color: var(--text-muted);
  font-family: monospace;
  font-size: 13px;
}

.tag,
.difficulty-pill
{
  display: inline-flex;
  padding: 3px 9px;
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: 13px;
}

.quick-links
{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.quick-links a
{
  display: grid;
  gap: 5px;
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
}

.quick-links a:hover
{
  border-color: var(--primary);
}

.quick-links span
{
  color: var(--text-muted);
  font-size: 14px;
}

.home-grid
{
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(300px, 2fr);
  gap: 20px;
  align-items: start;
}

.home-grid > section
{
  min-width: 0;
}

.problem-list,
.announcement-list
{
  min-width: 0;
  display: grid;
}

.problem-row
{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 13px 0;
  border-bottom: 1px solid var(--border);
}

.problem-row div
{
  display: flex;
  align-items: center;
  gap: 10px;
}

.announcement-item
{
  min-width: 0;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.announcement-title
{
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.announcement-title strong
{
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.announcement-item p
{
  max-width: 100%;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.pinned
{
  flex: 0 0 auto;
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--danger);
  background: #fef2f2;
  font-size: 12px;
}

.announcement-item time
{
  color: var(--text-muted);
  font-size: 12px;
}

.difficulty-easy
{
  color: var(--success);
}

.difficulty-medium
{
  color: var(--warning);
}

.difficulty-hard
{
  color: var(--danger);
}

@media (max-width: 800px)
{
  .welcome-panel,
  .daily-problem
  {
    align-items: flex-start;
    flex-direction: column;
  }

  .quick-links,
  .home-grid
  {
    grid-template-columns: 1fr;
  }
}
</style>
