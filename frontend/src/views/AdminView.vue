<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { Bell, Collection, Delete, Edit, Plus, PriceTag, Refresh, Tickets } from '@element-plus/icons-vue'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import {
    createAnnouncement,
    createProblem,
    createTag,
    createTestCase,
    deleteAnnouncement,
    deleteProblem,
    deleteTag,
    deleteTestCase,
    getAdminAnnouncements,
    getAdminProblem,
    getAdminProblems,
    getAdminTags,
    getAdminTestCases,
    updateAnnouncement,
    updateProblem,
    updateTag,
    updateTestCase,
  } from '../api/admin'
  import type {
    AdminAnnouncement,
    AnnouncementWriteRequest,
    ProblemListItem,
    ProblemWriteRequest,
    Tag,
    TestCase,
    TestCaseWriteRequest,
  } from '../types/api'
  import { getDifficultyClass, getDifficultyText } from '../utils/problem'
  import { formatDateTime } from '../utils/time'

  type AdminTab = 'problems'|'tags'|'test-cases'|'announcements'

  const activeTab = ref<AdminTab>('problems')
  const loading = ref(false)
  const saving = ref(false)

  const problems = ref<ProblemListItem[]>([])
  const problemOptions = ref<ProblemListItem[]>([])
  const problemPage = ref(1)
  const problemCount = ref(0)
  const problemHasNext = ref(false)
  const problemHasPrevious = ref(false)
  const problemSearch = ref('')

  const tags = ref<Tag[]>([])
  const tagOptions = ref<Tag[]>([])
  const tagPage = ref(1)
  const tagCount = ref(0)
  const tagHasNext = ref(false)
  const tagHasPrevious = ref(false)

  const testCases = ref<TestCase[]>([])
  const selectedProblem = ref<number|''>('')
  const testCasePage = ref(1)
  const testCaseCount = ref(0)
  const testCaseHasNext = ref(false)
  const testCaseHasPrevious = ref(false)

  const announcements = ref<AdminAnnouncement[]>([])
  const announcementPage = ref(1)
  const announcementCount = ref(0)
  const announcementHasNext = ref(false)
  const announcementHasPrevious = ref(false)

  const problemDialogVisible = ref(false)
  const editingProblemId = ref<number|null>(null)

  function createEmptyProblem(): ProblemWriteRequest
  {
    return {
      title: '',
      description: '',
      input_description: '',
      output_description: '',
      difficulty: 'easy',
      time_limit: 2000,
      memory_limit: 128,
      is_public: true,
      tag_ids: [],
    }
  }

  const problemForm = ref<ProblemWriteRequest>(createEmptyProblem())

  const tagDialogVisible = ref(false)
  const editingTagId = ref<number|null>(null)
  const tagName = ref('')

  const testCaseDialogVisible = ref(false)
  const editingTestCaseId = ref<number|null>(null)

  function createEmptyTestCase(problem: number): TestCaseWriteRequest
  {
    return {
      problem,
      input_data: '',
      output_data: '',
      is_sample: false,
      score: 0,
      order: 0,
    }
  }

  const testCaseForm = ref<TestCaseWriteRequest>(createEmptyTestCase(0))

  const announcementDialogVisible = ref(false)
  const editingAnnouncementId = ref<number|null>(null)

  function createEmptyAnnouncement(): AnnouncementWriteRequest
  {
    return {
      title: '',
      content: '',
      is_active: true,
      is_pinned: false,
    }
  }

  const announcementForm = ref<AnnouncementWriteRequest>(createEmptyAnnouncement())

  async function loadProblems(page = problemPage.value)
  {
    loading.value = true
    try
    {
      const response = await getAdminProblems({
        page,
        search: problemSearch.value || undefined,
      })
      problems.value = response.data.results
      problemCount.value = response.data.count
      problemHasNext.value = Boolean(response.data.next)
      problemHasPrevious.value = Boolean(response.data.previous)
      problemPage.value = page
    }
    catch
    {
      ElMessage.error('题目列表加载失败')
    }
    finally
    {
      loading.value = false
    }
  }

  async function loadProblemOptions()
  {
    const result: ProblemListItem[] = []
    let page = 1

    while (true)
    {
      const response = await getAdminProblems({page})
      result.push(...response.data.results)
      if (!response.data.next)
      {
        break
      }
      page += 1
    }

    problemOptions.value = result
  }

  async function loadTags(page = tagPage.value)
  {
    loading.value = true
    try
    {
      const response = await getAdminTags({page})
      tags.value = response.data.results
      tagCount.value = response.data.count
      tagHasNext.value = Boolean(response.data.next)
      tagHasPrevious.value = Boolean(response.data.previous)
      tagPage.value = page
    }
    catch
    {
      ElMessage.error('标签列表加载失败')
    }
    finally
    {
      loading.value = false
    }
  }

  async function loadTagOptions()
  {
    const result: Tag[] = []
    let page = 1

    while (true)
    {
      const response = await getAdminTags({page})
      result.push(...response.data.results)
      if (!response.data.next)
      {
        break
      }
      page += 1
    }

    tagOptions.value = result
  }

  async function loadTestCases(page = testCasePage.value)
  {
    if (selectedProblem.value === '')
    {
      testCases.value = []
      testCaseCount.value = 0
      return
    }

    loading.value = true
    try
    {
      const response = await getAdminTestCases({
        page,
        problem: selectedProblem.value,
      })
      testCases.value = response.data.results
      testCaseCount.value = response.data.count
      testCaseHasNext.value = Boolean(response.data.next)
      testCaseHasPrevious.value = Boolean(response.data.previous)
      testCasePage.value = page
    }
    catch
    {
      ElMessage.error('测试点列表加载失败')
    }
    finally
    {
      loading.value = false
    }
  }

  async function loadAnnouncements(page = announcementPage.value)
  {
    loading.value = true
    try
    {
      const response = await getAdminAnnouncements({page})
      announcements.value = response.data.results
      announcementCount.value = response.data.count
      announcementHasNext.value = Boolean(response.data.next)
      announcementHasPrevious.value = Boolean(response.data.previous)
      announcementPage.value = page
    }
    catch
    {
      ElMessage.error('公告列表加载失败')
    }
    finally
    {
      loading.value = false
    }
  }

  function openCreateProblem()
  {
    editingProblemId.value = null
    problemForm.value = createEmptyProblem()
    problemDialogVisible.value = true
  }

  async function openEditProblem(id: number)
  {
    try
    {
      const response = await getAdminProblem(id)
      const problem = response.data
      editingProblemId.value = id
      problemForm.value = {
        title: problem.title,
        description: problem.description,
        input_description: problem.input_description,
        output_description: problem.output_description,
        difficulty: problem.difficulty,
        time_limit: problem.time_limit,
        memory_limit: problem.memory_limit,
        is_public: problem.is_public,
        tag_ids: problem.tags.map((tag)=>tag.id),
      }
      problemDialogVisible.value = true
    }
    catch
    {
      ElMessage.error('题目详情加载失败')
    }
  }

  async function saveProblem()
  {
    if (!problemForm.value.title.trim() || !problemForm.value.description.trim())
    {
      ElMessage.warning('请填写题目标题和描述')
      return
    }

    saving.value = true
    try
    {
      if (editingProblemId.value === null)
      {
        await createProblem(problemForm.value)
        ElMessage.success('题目创建成功')
      }
      else
      {
        await updateProblem(editingProblemId.value, problemForm.value)
        ElMessage.success('题目更新成功')
      }
      problemDialogVisible.value = false
      await Promise.all([loadProblems(), loadProblemOptions()])
    }
    catch
    {
      ElMessage.error('题目保存失败，请检查字段内容')
    }
    finally
    {
      saving.value = false
    }
  }

  async function removeProblem(problem: ProblemListItem)
  {
    const confirmed = await confirmDelete(
      `删除题目“${problem.title}”会同时删除相关测试点、提交和题解。`,
    )
    if (!confirmed)
    {
      return
    }

    try
    {
      await deleteProblem(problem.id)
      ElMessage.success('题目已删除')
      await Promise.all([loadProblems(1), loadProblemOptions()])
    }
    catch
    {
      ElMessage.error('题目删除失败')
    }
  }

  function openCreateTag()
  {
    editingTagId.value = null
    tagName.value = ''
    tagDialogVisible.value = true
  }

  function openEditTag(tag: Tag)
  {
    editingTagId.value = tag.id
    tagName.value = tag.name
    tagDialogVisible.value = true
  }

  async function saveTag()
  {
    const name = tagName.value.trim()
    if (!name)
    {
      ElMessage.warning('请输入标签名称')
      return
    }

    saving.value = true
    try
    {
      if (editingTagId.value === null)
      {
        await createTag({name})
        ElMessage.success('标签创建成功')
      }
      else
      {
        await updateTag(editingTagId.value, {name})
        ElMessage.success('标签更新成功')
      }
      tagDialogVisible.value = false
      await Promise.all([loadTags(), loadTagOptions()])
    }
    catch
    {
      ElMessage.error('标签保存失败，名称可能已经存在')
    }
    finally
    {
      saving.value = false
    }
  }

  async function removeTag(tag: Tag)
  {
    const confirmed = await confirmDelete(`确定删除标签“${tag.name}”吗？`)
    if (!confirmed)
    {
      return
    }

    try
    {
      await deleteTag(tag.id)
      ElMessage.success('标签已删除')
      await Promise.all([loadTags(1), loadTagOptions()])
    }
    catch
    {
      ElMessage.error('标签删除失败')
    }
  }

  function openCreateTestCase()
  {
    if (selectedProblem.value === '')
    {
      ElMessage.warning('请先选择题目')
      return
    }
    editingTestCaseId.value = null
    testCaseForm.value = createEmptyTestCase(selectedProblem.value)
    testCaseDialogVisible.value = true
  }

  function openEditTestCase(testCase: TestCase)
  {
    editingTestCaseId.value = testCase.id
    testCaseForm.value = {
      problem: testCase.problem,
      input_data: testCase.input_data,
      output_data: testCase.output_data,
      is_sample: testCase.is_sample,
      score: testCase.score,
      order: testCase.order,
    }
    testCaseDialogVisible.value = true
  }

  async function saveTestCase()
  {
    saving.value = true
    try
    {
      if (editingTestCaseId.value === null)
      {
        await createTestCase(testCaseForm.value)
        ElMessage.success('测试点创建成功')
      }
      else
      {
        await updateTestCase(editingTestCaseId.value, testCaseForm.value)
        ElMessage.success('测试点更新成功')
      }
      testCaseDialogVisible.value = false
      await loadTestCases()
    }
    catch
    {
      ElMessage.error('测试点保存失败')
    }
    finally
    {
      saving.value = false
    }
  }

  async function removeTestCase(testCase: TestCase)
  {
    const confirmed = await confirmDelete(`确定删除测试点 #${testCase.id} 吗？`)
    if (!confirmed)
    {
      return
    }

    try
    {
      await deleteTestCase(testCase.id)
      ElMessage.success('测试点已删除')
      await loadTestCases(1)
    }
    catch
    {
      ElMessage.error('测试点删除失败')
    }
  }

  function openCreateAnnouncement()
  {
    editingAnnouncementId.value = null
    announcementForm.value = createEmptyAnnouncement()
    announcementDialogVisible.value = true
  }

  function openEditAnnouncement(announcement: AdminAnnouncement)
  {
    editingAnnouncementId.value = announcement.id
    announcementForm.value = {
      title: announcement.title,
      content: announcement.content,
      is_active: announcement.is_active,
      is_pinned: announcement.is_pinned,
    }
    announcementDialogVisible.value = true
  }

  async function saveAnnouncement()
  {
    if (!announcementForm.value.title.trim() || !announcementForm.value.content.trim())
    {
      ElMessage.warning('请填写公告标题和内容')
      return
    }

    saving.value = true
    try
    {
      if (editingAnnouncementId.value === null)
      {
        await createAnnouncement(announcementForm.value)
        ElMessage.success('公告创建成功')
      }
      else
      {
        await updateAnnouncement(editingAnnouncementId.value, announcementForm.value)
        ElMessage.success('公告更新成功')
      }
      announcementDialogVisible.value = false
      await loadAnnouncements()
    }
    catch
    {
      ElMessage.error('公告保存失败')
    }
    finally
    {
      saving.value = false
    }
  }

  async function removeAnnouncement(announcement: AdminAnnouncement)
  {
    const confirmed = await confirmDelete(`确定删除公告“${announcement.title}”吗？`)
    if (!confirmed)
    {
      return
    }

    try
    {
      await deleteAnnouncement(announcement.id)
      ElMessage.success('公告已删除')
      await loadAnnouncements(1)
    }
    catch
    {
      ElMessage.error('公告删除失败')
    }
  }

  async function confirmDelete(message: string)
  {
    try
    {
      await ElMessageBox.confirm(message, '确认删除', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      })
      return true
    }
    catch
    {
      return false
    }
  }

  async function initialize()
  {
    await Promise.all([
      loadProblems(),
      loadTags(),
      loadProblemOptions(),
      loadTagOptions(),
      loadAnnouncements(),
    ])

    if (problemOptions.value.length > 0)
    {
      selectedProblem.value = problemOptions.value[0].id
      await loadTestCases(1)
    }
  }

  onMounted(()=>
  {
    initialize()
  })
</script>

<template>
  <main class="admin-page">
    <header class="admin-header">
      <div>
        <p class="eyebrow">Administration</p>
        <h1>内容管理</h1>
      </div>

      <button class="icon-button" type="button" title="刷新当前列表" @click="
        activeTab === 'problems' ? loadProblems() :
        activeTab === 'tags' ? loadTags() :
        activeTab === 'test-cases' ? loadTestCases() :
        loadAnnouncements()
      ">
        <el-icon><Refresh /></el-icon>
      </button>
    </header>

    <nav class="admin-tabs" aria-label="管理模块">
      <button :class="{active: activeTab === 'problems'}" type="button" @click="activeTab = 'problems'">
        <el-icon><Collection /></el-icon>
        题目
      </button>
      <button :class="{active: activeTab === 'tags'}" type="button" @click="activeTab = 'tags'">
        <el-icon><PriceTag /></el-icon>
        标签
      </button>
      <button :class="{active: activeTab === 'test-cases'}" type="button" @click="activeTab = 'test-cases'">
        <el-icon><Tickets /></el-icon>
        测试点
      </button>
      <button :class="{active: activeTab === 'announcements'}" type="button" @click="activeTab = 'announcements'">
        <el-icon><Bell /></el-icon>
        公告
      </button>
    </nav>

    <section v-if="activeTab === 'problems'" class="admin-panel">
      <div class="panel-toolbar">
        <form class="search-form" @submit.prevent="loadProblems(1)">
          <input v-model="problemSearch" placeholder="搜索题目" />
          <button type="submit">搜索</button>
        </form>
        <button class="primary-button" type="button" @click="openCreateProblem">
          <el-icon><Plus /></el-icon>
          新建题目
        </button>
      </div>

      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>题目</th>
              <th>难度</th>
              <th>限制</th>
              <th>标签</th>
              <th class="action-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="problem in problems" :key="problem.id">
              <td>#{{ problem.id }}</td>
              <td>{{ problem.title }}</td>
              <td>
                <span :class="getDifficultyClass(problem.difficulty)">
                  {{ getDifficultyText(problem.difficulty) }}
                </span>
              </td>
              <td>{{ problem.time_limit }} ms / {{ problem.memory_limit }} MB</td>
              <td>
                <div class="tag-list">
                  <span v-for="tag in problem.tags" :key="tag.id" class="tag">{{ tag.name }}</span>
                </div>
              </td>
              <td>
                <div class="row-actions">
                  <button type="button" @click="openEditProblem(problem.id)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </button>
                  <button class="danger-button" type="button" @click="removeProblem(problem)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && problems.length === 0">
              <td colspan="6" class="empty-cell">暂无题目</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <span>共 {{ problemCount }} 条</span>
        <button type="button" :disabled="!problemHasPrevious" @click="loadProblems(problemPage - 1)">上一页</button>
        <span>第 {{ problemPage }} 页</span>
        <button type="button" :disabled="!problemHasNext" @click="loadProblems(problemPage + 1)">下一页</button>
      </div>
    </section>

    <section v-else-if="activeTab === 'tags'" class="admin-panel">
      <div class="panel-toolbar">
        <span>共 {{ tagCount }} 个标签</span>
        <button class="primary-button" type="button" @click="openCreateTag">
          <el-icon><Plus /></el-icon>
          新建标签
        </button>
      </div>

      <div class="tag-admin-list">
        <div v-for="tag in tags" :key="tag.id" class="tag-admin-row">
          <span class="tag">{{ tag.name }}</span>
          <div class="row-actions">
            <button type="button" title="编辑标签" @click="openEditTag(tag)">
              <el-icon><Edit /></el-icon>
            </button>
            <button class="danger-button" type="button" title="删除标签" @click="removeTag(tag)">
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
      </div>

      <div class="pagination">
        <button type="button" :disabled="!tagHasPrevious" @click="loadTags(tagPage - 1)">上一页</button>
        <span>第 {{ tagPage }} 页</span>
        <button type="button" :disabled="!tagHasNext" @click="loadTags(tagPage + 1)">下一页</button>
      </div>
    </section>

    <section v-else-if="activeTab === 'test-cases'" class="admin-panel">
      <div class="panel-toolbar">
        <label class="problem-select">
          <span>题目</span>
          <select v-model="selectedProblem" @change="loadTestCases(1)">
            <option value="" disabled>选择题目</option>
            <option v-for="problem in problemOptions" :key="problem.id" :value="problem.id">
              #{{ problem.id }} {{ problem.title }}
            </option>
          </select>
        </label>
        <button class="primary-button" type="button" :disabled="selectedProblem === ''" @click="openCreateTestCase">
          <el-icon><Plus /></el-icon>
          新建测试点
        </button>
      </div>

      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>顺序</th>
              <th>类型</th>
              <th>分值</th>
              <th>输入</th>
              <th>输出</th>
              <th class="action-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="testCase in testCases" :key="testCase.id">
              <td>#{{ testCase.id }}</td>
              <td>{{ testCase.order }}</td>
              <td>{{ testCase.is_sample ? '公开样例' : '隐藏测试' }}</td>
              <td>{{ testCase.score }}</td>
              <td><pre class="case-preview">{{ testCase.input_data }}</pre></td>
              <td><pre class="case-preview">{{ testCase.output_data }}</pre></td>
              <td>
                <div class="row-actions">
                  <button type="button" @click="openEditTestCase(testCase)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </button>
                  <button class="danger-button" type="button" @click="removeTestCase(testCase)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && testCases.length === 0">
              <td colspan="7" class="empty-cell">暂无测试点</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <span>共 {{ testCaseCount }} 条</span>
        <button type="button" :disabled="!testCaseHasPrevious" @click="loadTestCases(testCasePage - 1)">上一页</button>
        <span>第 {{ testCasePage }} 页</span>
        <button type="button" :disabled="!testCaseHasNext" @click="loadTestCases(testCasePage + 1)">下一页</button>
      </div>
    </section>

    <section v-else class="admin-panel">
      <div class="panel-toolbar">
        <span>共 {{ announcementCount }} 条公告</span>
        <button class="primary-button" type="button" @click="openCreateAnnouncement">
          <el-icon><Plus /></el-icon>
          新建公告
        </button>
      </div>

      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>状态</th>
              <th>置顶</th>
              <th>创建时间</th>
              <th class="action-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="announcement in announcements" :key="announcement.id">
              <td>#{{ announcement.id }}</td>
              <td>
                <strong>{{ announcement.title }}</strong>
                <p class="announcement-content">{{ announcement.content }}</p>
              </td>
              <td>
                <span :class="announcement.is_active ? 'status-active' : 'status-inactive'">
                  {{ announcement.is_active ? '已发布' : '未发布' }}
                </span>
              </td>
              <td>{{ announcement.is_pinned ? '是' : '否' }}</td>
              <td>{{ formatDateTime(announcement.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <button type="button" @click="openEditAnnouncement(announcement)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </button>
                  <button class="danger-button" type="button" @click="removeAnnouncement(announcement)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && announcements.length === 0">
              <td colspan="6" class="empty-cell">暂无公告</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <button type="button" :disabled="!announcementHasPrevious" @click="loadAnnouncements(announcementPage - 1)">上一页</button>
        <span>第 {{ announcementPage }} 页</span>
        <button type="button" :disabled="!announcementHasNext" @click="loadAnnouncements(announcementPage + 1)">下一页</button>
      </div>
    </section>

    <el-dialog v-model="problemDialogVisible" :title="editingProblemId === null ? '新建题目' : '编辑题目'" width="min(760px, 92vw)">
      <form class="admin-form" @submit.prevent="saveProblem">
        <label class="full-field">
          <span>标题</span>
          <input v-model="problemForm.title" maxlength="120" required />
        </label>
        <label class="full-field">
          <span>题目描述</span>
          <textarea v-model="problemForm.description" rows="6" required></textarea>
        </label>
        <label>
          <span>输入说明</span>
          <textarea v-model="problemForm.input_description" rows="4"></textarea>
        </label>
        <label>
          <span>输出说明</span>
          <textarea v-model="problemForm.output_description" rows="4"></textarea>
        </label>
        <label>
          <span>难度</span>
          <select v-model="problemForm.difficulty">
            <option value="easy">简单</option>
            <option value="medium">中等</option>
            <option value="hard">困难</option>
          </select>
        </label>
        <label>
          <span>标签</span>
          <select v-model="problemForm.tag_ids" multiple class="multiple-select">
            <option v-for="tag in tagOptions" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
          </select>
        </label>
        <label>
          <span>时间限制（ms）</span>
          <input v-model.number="problemForm.time_limit" type="number" min="1" required />
        </label>
        <label>
          <span>内存限制（MB）</span>
          <input v-model.number="problemForm.memory_limit" type="number" min="1" required />
        </label>
        <label class="checkbox-field full-field">
          <input v-model="problemForm.is_public" type="checkbox" />
          <span>公开题目</span>
        </label>
        <div class="dialog-actions full-field">
          <button type="button" @click="problemDialogVisible = false">取消</button>
          <button class="primary-button" type="submit" :disabled="saving">保存</button>
        </div>
      </form>
    </el-dialog>

    <el-dialog v-model="tagDialogVisible" :title="editingTagId === null ? '新建标签' : '编辑标签'" width="min(420px, 92vw)">
      <form class="admin-form single-column" @submit.prevent="saveTag">
        <label>
          <span>标签名称</span>
          <input v-model="tagName" maxlength="40" required />
        </label>
        <div class="dialog-actions">
          <button type="button" @click="tagDialogVisible = false">取消</button>
          <button class="primary-button" type="submit" :disabled="saving">保存</button>
        </div>
      </form>
    </el-dialog>

    <el-dialog v-model="testCaseDialogVisible" :title="editingTestCaseId === null ? '新建测试点' : '编辑测试点'" width="min(680px, 92vw)">
      <form class="admin-form" @submit.prevent="saveTestCase">
        <label class="full-field">
          <span>所属题目</span>
          <select v-model="testCaseForm.problem" required>
            <option v-for="problem in problemOptions" :key="problem.id" :value="problem.id">
              #{{ problem.id }} {{ problem.title }}
            </option>
          </select>
        </label>
        <label>
          <span>输入</span>
          <textarea v-model="testCaseForm.input_data" rows="8"></textarea>
        </label>
        <label>
          <span>期望输出</span>
          <textarea v-model="testCaseForm.output_data" rows="8"></textarea>
        </label>
        <label>
          <span>顺序</span>
          <input v-model.number="testCaseForm.order" type="number" min="0" required />
        </label>
        <label>
          <span>分值</span>
          <input v-model.number="testCaseForm.score" type="number" min="0" required />
        </label>
        <label class="checkbox-field full-field">
          <input v-model="testCaseForm.is_sample" type="checkbox" />
          <span>公开样例</span>
        </label>
        <div class="dialog-actions full-field">
          <button type="button" @click="testCaseDialogVisible = false">取消</button>
          <button class="primary-button" type="submit" :disabled="saving">保存</button>
        </div>
      </form>
    </el-dialog>

    <el-dialog v-model="announcementDialogVisible" :title="editingAnnouncementId === null ? '新建公告' : '编辑公告'" width="min(600px, 92vw)">
      <form class="admin-form single-column" @submit.prevent="saveAnnouncement">
        <label>
          <span>标题</span>
          <input v-model="announcementForm.title" maxlength="100" required />
        </label>
        <label>
          <span>内容</span>
          <textarea v-model="announcementForm.content" maxlength="200" rows="6" required></textarea>
        </label>
        <div class="checkbox-row">
          <label class="checkbox-field">
            <input v-model="announcementForm.is_active" type="checkbox" />
            <span>发布</span>
          </label>
          <label class="checkbox-field">
            <input v-model="announcementForm.is_pinned" type="checkbox" />
            <span>置顶</span>
          </label>
        </div>
        <div class="dialog-actions">
          <button type="button" @click="announcementDialogVisible = false">取消</button>
          <button class="primary-button" type="submit" :disabled="saving">保存</button>
        </div>
      </form>
    </el-dialog>
  </main>
</template>

<style scoped>
  .admin-page
  {
    display: grid;
    gap: 16px;
  }

  .admin-header
  {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
  }

  .eyebrow
  {
    margin: 0 0 6px;
    color: var(--primary);
    font-size: 13px;
    font-weight: 600;
  }

  .icon-button
  {
    width: 38px;
    height: 38px;
    display: inline-grid;
    place-items: center;
    padding: 0;
  }

  .admin-tabs
  {
    display: flex;
    gap: 4px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
  }

  .admin-tabs button,
  .row-actions button,
  .primary-button
  {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    white-space: nowrap;
  }

  .admin-tabs button
  {
    border-color: transparent;
    background: transparent;
  }

  .admin-tabs button.active
  {
    color: white;
    border-color: var(--primary);
    background: var(--primary);
  }

  .admin-panel
  {
    margin-top: 0;
  }

  .panel-toolbar
  {
    min-height: 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 16px;
  }

  .search-form,
  .problem-select,
  .row-actions,
  .checkbox-row
  {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .primary-button
  {
    color: white;
    border-color: var(--primary);
    background: var(--primary);
  }

  .primary-button:hover
  {
    color: white;
    border-color: var(--primary-hover);
    background: var(--primary-hover);
  }

  .danger-button
  {
    color: var(--danger);
  }

  .danger-button:hover
  {
    color: white;
    border-color: var(--danger);
    background: var(--danger);
  }

  .table-scroll
  {
    overflow-x: auto;
  }

  .action-column
  {
    width: 190px;
  }

  .tag-list
  {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .tag
  {
    display: inline-flex;
    padding: 3px 8px;
    color: var(--text-muted);
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--surface-muted);
    font-size: 13px;
  }

  .tag-admin-list
  {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
  }

  .tag-admin-row
  {
    min-height: 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 8px 10px;
    border-bottom: 1px solid var(--border);
  }

  .tag-admin-row .row-actions button
  {
    width: 32px;
    height: 32px;
    padding: 0;
  }

  .case-preview
  {
    max-width: 220px;
    max-height: 90px;
    padding: 8px;
    font-size: 12px;
  }

  .announcement-content
  {
    max-width: 430px;
    margin: 4px 0 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .status-active
  {
    color: var(--success);
  }

  .status-inactive
  {
    color: var(--text-muted);
  }

  .empty-cell
  {
    padding: 36px;
    color: var(--text-muted);
    text-align: center;
  }

  .pagination
  {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 16px;
  }

  .admin-form
  {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  .admin-form.single-column
  {
    grid-template-columns: 1fr;
  }

  .admin-form label
  {
    display: grid;
    gap: 6px;
  }

  .admin-form label > span
  {
    font-size: 14px;
    font-weight: 600;
  }

  .admin-form input,
  .admin-form select,
  .admin-form textarea
  {
    width: 100%;
  }

  .multiple-select
  {
    min-height: 108px;
  }

  .full-field
  {
    grid-column: 1 / -1;
  }

  .checkbox-field
  {
    display: flex !important;
    grid-template-columns: none;
    align-items: center;
    gap: 8px !important;
  }

  .checkbox-field input
  {
    width: auto;
  }

  .dialog-actions
  {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding-top: 4px;
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

  @media (max-width: 760px)
  {
    .panel-toolbar,
    .problem-select
    {
      align-items: stretch;
      flex-direction: column;
    }

    .search-form
    {
      width: 100%;
    }

    .search-form input
    {
      min-width: 0;
      flex: 1;
    }

    .tag-admin-list,
    .admin-form
    {
      grid-template-columns: 1fr;
    }

    .full-field
    {
      grid-column: auto;
    }

    .pagination
    {
      justify-content: flex-start;
      flex-wrap: wrap;
    }
  }
</style>
