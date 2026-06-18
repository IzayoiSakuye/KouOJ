<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { useRouter, useRoute, RouterLink } from 'vue-router';
  import { getSubmissions } from '../api/submission';
  import type { Submission, SubmissionStatus } from '../types/api';
  import { getStatusClass, getStatusText } from '../utils/status';
  import { formatDateTime } from '../utils/time';

  const submissions = ref<Submission[]> ([]);
  const loading = ref(false)
  const errorMessage = ref('')
  
  // 查看某个题目的提交
  const selectedProblem = ref<number|undefined>(undefined)
  // 筛选用
  const selectedStatus = ref<SubmissionStatus|''>('')
  const route = useRoute()
  const router = useRouter()
  // 分页
  const currentPage = ref(1)
  const totalCount = ref(0)
  const hasNext = ref(false)
  const hasPrevious = ref(false)

  // 封装更新url的函数
  function syncQuery(page: number)
  {
    router.replace(
    {
      path:'/submissions',
      query:
      {
        page: String(page),
        problem: selectedProblem.value?String(selectedProblem.value):undefined,
        status: selectedStatus.value||undefined,
      },
    })
  }
  async function loadSubmissions(page = currentPage.value)
  {
    loading.value = true;
    errorMessage.value = ''

    syncQuery(page)

    try
    {
      const response = await getSubmissions({
        page,
        status: selectedStatus.value||undefined,
        problem: selectedProblem.value,
      })
      submissions.value = response.data.results
      totalCount.value = response.data.count
      hasNext.value = Boolean(response.data.next)
      hasPrevious.value = Boolean(response.data.previous)
      currentPage.value = page
    }
    catch(error)
    {
      errorMessage.value = ("提交记录页出现问题")
    }
    finally
    {
      loading.value = false;
    }
  }

  // 跳转到上一页
  function goPreviousPage()
  {
    if (hasPrevious.value&& currentPage.value>1)
    {
      loadSubmissions(currentPage.value-1)
    }
  }

  // 跳转到下一页
  function goNextPage()
  {
    if (hasNext.value)
    {
      loadSubmissions(currentPage.value+1);
    }
  }
  onMounted(()=>
  {
    // 添加查询参数
    const problemQuery = route.query.problem
    const statusQuery = route.query.status
    const pageQuery = route.query.page
    if (typeof problemQuery==='string')
    {
      selectedProblem.value = Number(problemQuery)
    }
    if (typeof statusQuery==='string')
    {
      selectedStatus.value = statusQuery as SubmissionStatus
    }
    const page = typeof pageQuery ==='string'?Number(pageQuery):1
    loadSubmissions(Number.isNaN(page)?1:page)
  })
</script>
<template>
  <main class="submission-list-page">
    <section class="submission-list-header">
      <div>
        <p class="eyebrow">Submissions</p>
        <h1>提交记录</h1>
        <p>查看提交状态、耗时、内存和判题结果。</p>
      </div>
    </section>

    <section class="filter-panel">
      <form class="filter-form" @submit.prevent="loadSubmissions(1)">
        <select v-model="selectedStatus">
          <option value="">全部状态</option>
          <option value="PENDING">Pending</option>
          <option value="JUDGING">Judging</option>
          <option value="ACCEPTED">Accepted</option>
          <option value="WRONG_ANSWER">Wrong Answer</option>
          <option value="TIME_LIMIT_EXCEEDED">Time Limit Exceeded</option>
          <option value="RUNTIME_ERROR">Runtime Error</option>
          <option value="SYSTEM_ERROR">System Error</option>
          <option value="COMPILE_ERROR">Compile Error</option>
        </select>

        <button class="primary-button" type="submit">筛选</button>

        <button
          type="button"
          @click="selectedStatus='';selectedProblem = undefined; loadSubmissions(1)" 
          
        >
          重置
        </button>
      </form>
    </section>

    <section class="table-panel">
      <p v-if="loading">加载中...</p>
      <p v-else-if="errorMessage">{{ errorMessage }}</p>

      <table v-else>
        <thead>
          <tr>
            <th style="width: 90px;">ID</th>
            <th style="width: 120px;">提交用户</th>
            <th>题目</th>
            <th style="width: 110px;">语言</th>
            <th style="width: 170px;">状态</th>
            <th style="width: 90px;">得分</th>
            <th style="width: 110px;">耗时</th>
            <th style="width: 110px;">内存</th>
            <th style="width: 180px;">提交时间</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="submission in submissions" :key="submission.id">
            <td>
              <RouterLink class="submission-id" :to="`/submissions/${submission.id}`">
                #{{ submission.id }}
              </RouterLink>
            </td>
            <td>{{ submission.username }}</td>
            <td>
              <RouterLink :to="`/problems/${submission.problem}`">
                {{ submission.problem_title || submission.problem }}
              </RouterLink>
            </td>

            <td>{{ submission.language }}</td>

            <td>
              <span class="status-pill" :class="getStatusClass(submission.status)">
                {{ getStatusText(submission.status) }}
              </span>
            </td>

            <td>{{ submission.score }}</td>
            <td>{{ submission.time_used }} ms</td>
            <td>{{ submission.memory_used }} KB</td>
            <td>{{ formatDateTime(submission.created_at) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="pagination">
        <button type="button" :disabled="!hasPrevious" @click="goPreviousPage">
          上一页
        </button>

        <span>第 {{ currentPage }} 页</span>
        <span>共 {{ totalCount }} 条</span>

        <button type="button" :disabled="!hasNext" @click="goNextPage">
          下一页
        </button>
      </div>
    </section>
  </main>
</template>
<style scoped>
.submission-list-page {
  display: grid;
  gap: 20px;
}

.submission-list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--primary);
  font-weight: 600;
}

.filter-panel,
.table-panel {
  margin-top: 0;
}

.filter-form {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-form select {
  min-width: 220px;
}

.primary-button {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.primary-button:hover {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
  color: white;
}

.submission-id {
  font-weight: 600;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  font-size: 14px;
}

.status-pd,
.status-jg {
  color: #b42335;
}

.status-ac {
  color: #16a34a;
  font-weight: 600;
}

.status-wa,
.status-se,
.status-ce {
  color: #dc2626;
  font-weight: 600;
}

.status-re {
  color: #7c3aed;
  font-weight: 600;
}

.status-tle {
  color: #d97706;
  font-weight: 600;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

@media (max-width: 900px) {
  table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  .pagination {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
