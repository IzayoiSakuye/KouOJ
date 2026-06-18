<script setup lang="ts">
  import { onMounted, onUnmounted, ref } from 'vue'
  import { RouterLink, useRoute } from 'vue-router'
  import { getProblem } from '../api/problems'
  import { createSubmission, getSubmission } from '../api/submission'
  import type { Language, ProblemDetail, Submission } from '../types/api'
  import { getDifficultyClass, getDifficultyText } from '../utils/problem'
  import { getStatusClass, getStatusText } from '../utils/status'

  // ide高亮
  import { computed } from 'vue'
  import Codemirror from 'vue-codemirror6'
  import { python } from '@codemirror/lang-python'
  import { cpp } from '@codemirror/lang-cpp'
  import { oneDark } from '@codemirror/theme-one-dark'

  const route = useRoute()

  // 题目信息
  const problem = ref<ProblemDetail | null>(null)
  const loading = ref(false)
  const errorMessage = ref('')

  // 提交代码相关
  const submitLanguage = ref<Language>('cpp')
  const code = ref('')
  const submitting = ref(false)
  const submission = ref<Submission | null>(null)
  const submitError = ref('')
  //可拖动布局
  const leftWidth = ref(55)
  const isResizing = ref(false)
  // 轮询定时器
  let pollingTimer: number | null = null

  // 清除轮询
  function clearPolling()
  {
    if (pollingTimer)
    {
      window.clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  // 加载题目详情
  async function loadProblem()
  {
    loading.value = true
    errorMessage.value = ''

    try
    {
      const response = await getProblem(route.params.id as string)
      problem.value = response.data
    }
    catch (error)
    {
      errorMessage.value = '加载失败'
    }
    finally
    {
      loading.value = false
    }
  }

  // 轮询提交结果
  async function pollSubmission(id: number)
  {
    clearPolling()

    async function fetchSubmission()
    {
      const response = await getSubmission(id)
      submission.value = response.data

      if (!['PENDING', 'JUDGING'].includes(response.data.status))
      {
        clearPolling()
      }
    }

    await fetchSubmission()
    pollingTimer = window.setInterval(fetchSubmission, 1000)
  }

  // 提交代码
  async function handleSubmit()
  {
    if (!problem.value)
    {
      return
    }

    submitting.value = true
    submitError.value = ''
    submission.value = null

    try
    {
      const response = await createSubmission(
        {
          problem: problem.value.id,
          language: submitLanguage.value,
          code: code.value,
        }
      )

      await pollSubmission(response.data.id)
    }
    catch (error)
    {
      submitError.value = '提交失败'
    }
    finally
    {
      submitting.value = false
    }
  }

  // 拖动改变两侧宽度
  function startResize()
  {
    isResizing.value = true
    window.addEventListener('mousemove', handleResize)
    window.addEventListener('mouseup', stopResize)
  }

  function handleResize(event: MouseEvent)
  {
    if (!isResizing.value)
    {
      return
    }

    const windowWidth = window.innerWidth
    const nextWidth = (event.clientX / windowWidth) * 100

    if (nextWidth < 35 || nextWidth > 70)
    {
      return
    }

    leftWidth.value = nextWidth
  }

  function stopResize()
  {
    isResizing.value = false
    window.removeEventListener('mousemove', handleResize)
    window.removeEventListener('mouseup', stopResize)
  }

  // 根据语言切换高亮
  const editorExtensions = computed(()=>
  {
    if (submitLanguage.value==='python3')
    {
      return [python(), oneDark]
    }
    else if (submitLanguage.value==='c' || submitLanguage.value==='cpp')
    {
      return [cpp(), oneDark]
    }
  })

  onMounted(() =>
  {
    loadProblem()
  })

  onUnmounted(() =>
  {
    clearPolling()
  })
</script>

<template>
  <main class="problem-detail">
    <p v-if="loading">加载中...</p>
    <p v-else-if="errorMessage">{{ errorMessage }}</p>
    <article
        v-else-if="problem"
        class="ide-layout"
        :style="{ gridTemplateColumns: `${leftWidth}% 6px 1fr` }"
      >
      <div class="problem-pane">
        <section class="problem-hero">
          <div>
            <h1>#{{ problem.id }} {{ problem.title }}</h1>

            <div class="problem-meta">
              <span :class="getDifficultyClass(problem.difficulty)">
                {{ getDifficultyText(problem.difficulty) }}
              </span>
              <span>{{ problem.time_limit }} ms</span>
              <span>{{ problem.memory_limit }} MB</span>
            </div>
          </div>

          <div class="problem-actions">
            <RouterLink class="secondary-button" :to="`/submissions?problem=${problem.id}`">
              提交记录
            </RouterLink>

            <RouterLink class="secondary-button" :to="`/problems/${problem.id}/solutions`">
              查看题解
            </RouterLink>
          </div>
        </section>

      <section>
        <h2>标签</h2>
        <div class="tag-list">
          <span v-for="tag in problem.tags" :key="tag.id" class="tag">
            {{ tag.name }}
          </span>
        </div>
      </section>

      <section>
        <h2>题目描述</h2>
        <p>{{ problem.description }}</p>
      </section>

      <section>
        <h2>输入描述</h2>
        <p>{{ problem.input_description }}</p>
      </section>

      <section>
        <h2>输出描述</h2>
        <p>{{ problem.output_description }}</p>
      </section>

      <section>
        <h2>样例</h2>
        <div v-if="problem.sample_cases.length === 0">暂无样例</div>

        <div v-for="sample in problem.sample_cases" :key="sample.id" class="sample-case">
          <p>输入</p>
          <pre>{{ sample.input_data }}</pre>
          <p>输出</p>
          <pre>{{ sample.output_data }}</pre>
        </div>
      </section>
      </div>

      <div class="resize-handle" @mousedown="startResize"></div>

      <div class="editor-pane">
        <div class="editor-toolbar">
          <h2>提交代码</h2>

          <select v-model="submitLanguage">
            <option value="python3">Python3</option>
            <option value="c">C</option>
            <option value="cpp">C++</option>
          </select>

          <button class="primary-button" type="button" :disabled="submitting" @click="handleSubmit">
            {{ submitting ? '提交中...' : '提交' }}
          </button>
        </div>
        
        <Codemirror v-model="code" class="ide-editor" :extensions="editorExtensions" force-linting/>
        
        <p v-if="submitError">{{ submitError }}</p>

        <div v-if="submission" class="judge-result">
          <h3>判题结果</h3>
          <p>
            状态：
            <span :class="getStatusClass(submission.status)">
              {{ getStatusText(submission.status) }}
            </span>
          </p>
          <p>得分：{{ submission.score }}</p>
          <p>耗时：{{ submission.time_used }} ms</p>
          <p v-if="submission.error_message">错误信息：{{ submission.error_message }}</p>

          <div v-if="submission.results.length > 0">
            <h4>测试点结果</h4>
            <ul>
              <li v-for="result in submission.results" :key="result.id">
                #{{ result.testcase }} -
                <span :class="getStatusClass(result.status)">
                  {{ getStatusText(result.status) }}
                </span>
                - {{ result.time_used }} ms
              </li>
            </ul>
          </div>
        </div>
      </div> 
    </article>
  </main>
</template>

<style scoped>
.status-pd,
.status-jg {
  color: #b42335;
}

.status-ac {
  color: #2e7d32;
  font-weight: 600;
}

.status-wa,
.status-se {
  color: #c62828;
  font-weight: 600;
}

.status-re {
  color: #8a2be2;
  font-weight: 600;
}

.status-tle {
  color: #ef6c00;
  font-weight: 600;
}

.difficulty-easy {
  color: #2e7d32;
}

.difficulty-medium {
  color: #ef6c00;
}

.difficulty-hard {
  color: #c62828;
}

.problem-layout {
  display: grid;
  gap: 20px;
}

.problem-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.problem-hero h1 {
  margin-bottom: 10px;
}

.problem-meta,
.problem-actions,
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.problem-meta span,
.tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  font-size: 14px;
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

.secondary-button {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px 14px;
  background: var(--surface);
  white-space: nowrap;
}

.submit-panel select,
.submit-panel textarea {
  width: 100%;
  margin-bottom: 12px;
}

.code-editor {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.sample-case {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.judge-result {
  margin-top: 18px;
}

.problem-detail {
  width: min(1440px, calc(100% - 24px));
}

.ide-layout {
  display: grid;
  gap: 0;
  min-height: calc(100vh - 120px);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--surface);
}

.problem-pane,
.editor-pane {
  min-width: 0;
  overflow: auto;
  padding: 20px;
}

.problem-pane {
  background: var(--surface);
}

.editor-pane {
  display: flex;
  flex-direction: column;
  background: #2a1116;
  color: #fff1f2;
}

.resize-handle {
  width: 6px;
  cursor: col-resize;
  background: var(--border);
}

.resize-handle:hover {
  background: var(--primary);
}

.editor-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.ide-editor {
  flex: 1;
  min-height: 360px;
  border: 1px solid #71313b;
  overflow: hidden;
}

.ide-editor :deep(.cm-editor) {
  height: 100%;
  min-height: 360px;
  font-size: 14px;
}

.ide-editor :deep(.cm-scroller) {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.editor-toolbar h2 {
  margin: 0;
  margin-right: auto;
}

.editor-toolbar select {
  width: auto;
}

@media (max-width: 900px) {
  .ide-layout {
    display: block;
  }

  .resize-handle {
    display: none;
  }

  .problem-pane,
  .editor-pane {
    max-height: none;
  }
}
</style>
