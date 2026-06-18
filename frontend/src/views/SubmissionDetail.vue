<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { getSubmission } from '../api/submission';
  import { createAgentRun } from '../api/aiAgent';
  import type { AgentHintLevel, AgentRun, Submission } from '../types/api';
  import { getStatusClass, getStatusText } from '../utils/status';
  const route = useRoute()
  const submission = ref<Submission|null>(null)
  const loading = ref(false)
  const errorMessage = ref('')
  const agentRun = ref<AgentRun|null>(null)
  const agentRunCache = ref<Partial<Record<AgentHintLevel, AgentRun>>>({})
  const agentLoading = ref(false)
  const agentError = ref('')
  const selectedHintLevel = ref<AgentHintLevel>('direction')
  const hintLevels: { value: AgentHintLevel; label: string; description: string }[] = [
    {
      value: 'direction',
      label: '方向',
      description: '适合先确认问题类型或复盘整体思路。',
    },
    {
      value: 'locate',
      label: '定位',
      description: '结合提交结果定位可疑代码和边界。',
    },
    {
      value: 'explain',
      label: '详细',
      description: '给出更完整的修正路径和局部写法建议。',
    },
  ]
  // 提交详情代码高亮
  import { computed } from 'vue'
  import CodeMirror from 'vue-codemirror6'
  import { python } from '@codemirror/lang-python'
  import { cpp } from '@codemirror/lang-cpp'
  import { oneDark } from '@codemirror/theme-one-dark'
  
  async function loadSubmission() 
  {
    loading.value = true
    errorMessage.value = ''
    try
    {
      const response = await getSubmission(route.params.id as string)
      submission.value = response.data
    } 
    catch(error)
    {
      errorMessage.value = '提交详情加载错误'
    } 
    finally
    {
      loading.value = false
    }
  }

  // 根据代码显示高亮
  const codeExtensions = computed(() =>
  {
    if (submission.value?.language === 'python3')
    {
      return [python(), oneDark]
    }

    return [cpp(), oneDark]
  })

  const selectedHintDescription = computed(() =>
  {
    return hintLevels.find((item) => item.value === selectedHintLevel.value)?.description || ''
  })

  async function runAgent(level: AgentHintLevel)
  {
    if (!submission.value) return

    selectedHintLevel.value = level
    const cachedRun = agentRunCache.value[level]
    if (cachedRun)
    {
      agentRun.value = cachedRun
      agentError.value = ''
      return
    }

    agentLoading.value = true
    agentError.value = ''
    agentRun.value = null

    try
    {
      const response = await createAgentRun({
        submission_id: submission.value.id,
        hint_level: level,
      })
      agentRun.value = response.data
      agentRunCache.value[level] = response.data
    }
    catch(error)
    {
      agentError.value = '本次提交复盘失败，请稍后再试'
    }
    finally
    {
      agentLoading.value = false
    }
  }

  function getHintLevelText(level: AgentHintLevel)
  {
    const item = hintLevels.find((hintLevel) => hintLevel.value === level)
    return item?.label || level
  }

  onMounted(()=>
  {
    loadSubmission()
  })
</script>
  
<template>
  <main class="submission-detail-page">
    <p v-if="loading">加载中...</p>
    <p v-else-if="errorMessage">{{ errorMessage }}</p>

    <template v-else-if="submission">
      <section class="submission-hero">
        <div>
          <p class="eyebrow">Submission</p>
          <h1>提交 #{{ submission.id }}</h1>

          <p>
            <RouterLink :to="`/problems/${submission.problem}`">
              {{ submission.problem_title || submission.problem }}
            </RouterLink>
            · {{ submission.language }}
            · {{ submission.score }} 分
          </p>
        </div>

        <span class="status-pill" :class="getStatusClass(submission.status)">
          {{ getStatusText(submission.status) }}
        </span>
      </section>

      <section class="submission-main">
        <div class="info-panel">
          <h2>提交信息</h2>

          <dl>
            <div>
              <dt>提交用户</dt>
              <dd>{{ submission.username }}</dd>
            </div>

            <div>
              <dt>题目</dt>
              <dd>
                <RouterLink :to="`/problems/${submission.problem}`">
                  {{ submission.problem_title || submission.problem }}
                </RouterLink>
              </dd>
            </div>

            <div>
              <dt>语言</dt>
              <dd>{{ submission.language }}</dd>
            </div>

            <div>
              <dt>得分</dt>
              <dd>{{ submission.score }}</dd>
            </div>

            <div>
              <dt>耗时</dt>
              <dd>{{ submission.time_used }} ms</dd>
            </div>

            <div>
              <dt>内存</dt>
              <dd>{{ submission.memory_used }} KB</dd>
            </div>

            <div>
              <dt>提交时间</dt>
              <dd>{{ submission.created_at }}</dd>
            </div>

            <div>
              <dt>判题时间</dt>
              <dd>{{ submission.judged_at || '-' }}</dd>
            </div>
          </dl>
        </div>

        <div class="code-panel">
          <h2>提交代码</h2>
          <CodeMirror v-model="submission.code" class="readonly-editor" :extensions="codeExtensions" :readonly="true" :disabled="true"/>
        </div>
      </section>

      <section>
        <h2>测试点结果</h2>

        <p v-if="submission.results.length === 0">暂无测试点结果</p>

        <table v-else>
          <thead>
            <tr>
              <th>测试点</th>
              <th>状态</th>
              <th>耗时</th>
              <th>内存</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="result in submission.results" :key="result.id">
              <td>#{{ result.testcase }}</td>
              <td>
                <span class="status-pill" :class="getStatusClass(result.status)">
                  {{ getStatusText(result.status) }}
                </span>
              </td>
              <td>{{ result.time_used }} ms</td>
              <td>{{ result.memory_used }} KB</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="agent-panel">
        <div class="agent-header">
          <div>
            <p class="eyebrow">Review Agent</p>
            <h2>本次提交复盘</h2>
            <p>{{ selectedHintDescription }}</p>
          </div>
        </div>

        <div class="hint-toolbar">
          <button
            v-for="hintLevel in hintLevels"
            :key="hintLevel.value"
            type="button"
            :class="{ active: selectedHintLevel === hintLevel.value }"
            :disabled="agentLoading"
            @click="runAgent(hintLevel.value)"
          >
            {{ hintLevel.label }}
          </button>
        </div>

        <p v-if="agentLoading" class="agent-state">Agent 正在复盘这次提交...</p>
        <p v-else-if="agentError" class="agent-error">{{ agentError }}</p>

        <article v-else-if="agentRun" class="agent-result">
          <div class="agent-result-meta">
            <span>档位：{{ getHintLevelText(agentRun.hint_level) }}</span>
            <span>置信度：{{ agentRun.confidence }}</span>
            <span>步骤：{{ agentRun.steps_count }}</span>
          </div>

          <pre>{{ agentRun.final_message }}</pre>

          <details v-if="agentRun.steps.length > 0">
            <summary>查看复盘步骤</summary>

            <ol>
              <li v-for="step in agentRun.steps" :key="step.id">
                <strong>{{ step.step_type }}</strong>
                <span :class="step.success ? 'step-ok' : 'step-warn'">
                  {{ step.success ? '成功' : '降级' }}
                </span>
                <p>{{ step.output_summary }}</p>
              </li>
            </ol>
          </details>
        </article>

        <p v-else class="agent-empty">
          选择一个档位开始复盘。
        </p>
      </section>
    </template>
  </main>
</template>
<style scoped>
.submission-detail-page {
  display: grid;
  gap: 20px;
}

.submission-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--primary);
  font-weight: 600;
}

.submission-main {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
}

.info-panel,
.code-panel {
  min-width: 0;
}

dl {
  display: grid;
  gap: 12px;
  margin: 0;
}

dl div {
  display: grid;
  gap: 4px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}

dt {
  color: var(--text-muted);
  font-size: 14px;
}

dd {
  margin: 0;
  color: var(--text);
  font-weight: 600;
}

.code-panel pre {
  min-height: 420px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  font-size: 14px;
  white-space: nowrap;
}

.mini-pre {
  max-width: 260px;
  max-height: 120px;
  overflow: auto;
  font-size: 13px;
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

.readonly-editor {
  min-height: 420px;
  border: 1px solid #71313b;
  border-radius: var(--radius);
  overflow: hidden;
}

.readonly-editor :deep(.cm-editor) {
  height: 420px;
  font-size: 14px;
}

.readonly-editor :deep(.cm-scroller) {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.agent-panel {
  display: grid;
  gap: 16px;
  padding-top: 4px;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.agent-header h2 {
  margin-bottom: 8px;
}

.agent-header p:last-child,
.agent-empty,
.agent-state {
  margin: 0;
  color: var(--text-muted);
}

.hint-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hint-toolbar button {
  min-width: 86px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 14px;
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  font-weight: 600;
}

.hint-toolbar button.active {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--surface-muted);
}

.hint-toolbar button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.agent-error {
  margin: 0;
  color: #dc2626;
  font-weight: 600;
}

.agent-result {
  display: grid;
  gap: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  background: var(--surface);
}

.agent-result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--text-muted);
  font-size: 14px;
}

.agent-result pre {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.75;
  font-family: inherit;
}

.agent-result details {
  border-top: 1px solid var(--border);
  padding-top: 12px;
}

.agent-result summary {
  cursor: pointer;
  font-weight: 700;
}

.agent-result ol {
  display: grid;
  gap: 12px;
  margin: 12px 0 0;
  padding-left: 20px;
}

.agent-result li p {
  margin: 6px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.step-ok,
.step-warn {
  margin-left: 8px;
  font-size: 13px;
  font-weight: 700;
}

.step-ok {
  color: #16a34a;
}

.step-warn {
  color: #d97706;
}

@media (max-width: 900px) {
  .submission-hero {
    flex-direction: column;
  }

  .submission-main {
    grid-template-columns: 1fr;
  }

  .agent-header {
    flex-direction: column;
  }

  table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }
}
</style>
