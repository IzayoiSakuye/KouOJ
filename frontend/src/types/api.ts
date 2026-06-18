// 标签
export interface Tag
{
  id: number
  name: string
}

// 样例
export interface SampleCase
{
  id: number
  input_data: string
  output_data: string
  order: number
}

// 题目列表元素
export interface ProblemListItem
{
  id: number
  title: string
  difficulty: 'easy'|'medium'|'hard'
  time_limit: number
  memory_limit: number
  tags: Tag[]
}

// 题目详情，继承自题目列表的元素
export interface ProblemDetail extends ProblemListItem
{
  description: string
  input_description: string
  output_description: string
  is_public: boolean
  sample_cases: SampleCase[]
  created_at: string
  updated_at: string
}

// 分页相应
export interface PaginatedResponse<T>
{
  count: number
  next: string|null
  previous: string|null
  results: T[]
}

// 用户信息
export interface User
{
  id: number
  username: string
  email: string
  role: 'user'|'admin'
  solved_count: number
  submit_count: number
  nickname: string
  avatar_url: string
  bio: string
}

// 登录请求与响应
export interface LoginRequest
{
  username: string
  password: string
}

export interface LoginResponse
{
  access: string
  refresh: string
}

// 提交结果状态
export type SubmissionStatus = |'PENDING'|'JUDGING'|'ACCEPTED'|'WRONG_ANSWER'|'TIME_LIMIT_EXCEEDED'|'RUNTIME_ERROR'|'SYSTEM_ERROR'|'COMPILE_ERROR'

// 语言种类
export type Language = 'python3'|'c'|'cpp'

// 创建提交请求
export interface CreateSubmissionRequest
{
  problem: number
  language: Language
  code: string
}

// 创建提交响应
export interface CreateSubmissionResponse
{
  id: number
  problem: number
  language: Language
  code: string
}

// 评测结果
export interface JudgeResult
{
  id: number
  testcase: number
  status: SubmissionStatus
  time_used: number
  memory_used: number
  output:string
  error_message: string
}

// 提交记录
export interface Submission
{
  id: number
  username: string
  problem: number
  problem_title: string
  language: Language
  code: string
  status: SubmissionStatus
  score: number
  time_used: number
  memory_used: number
  error_message: string
  results: JudgeResult[]
  created_at: string
  judged_at: string|null
}
// 注册模块请求
export interface RegisterRequest
{
  username: string
  email: string
  password: string
}
// 注册模块响应
export interface RegisterResponse
{
  id: number
  username: string
  email: string
}

// 热力图
export interface HeatmapItem
{
  date: string
  count: number
}

// 用户数据统计
export interface UserStats
{
  submit_count: number
  accepted_count: number
  solved_count: number
  difficulty:
  {
    easy: number
    medium: number
    hard: number
  }
  heatmap: HeatmapItem[]
}

// 用户数据更新
export interface UpdateProfileRequest 
{
  email: string
  nickname: string
  avatar_url: string
  bio: string
}

// 密码更新
export interface ChangePasswordRequest
{
  old_password: string
  new_password: string
}

// 信息返回
export interface MessageResponse 
{
  detail: string
}

// 主页相关
export interface HomeProblem
{
  id: number
  title: string
  difficulty: 'easy'|'medium'|'hard'
  time_limit: number
  memory_limit: number
  tags: Tag[]
}

export interface Announcement
{
  id: number
  title: string
  content: string
  created_at: string
  is_pinned: boolean
}

export interface HomeData
{
  daily_problem: HomeProblem|null
  announcements: Announcement[]
  unfinished_problems: HomeProblem[]
}

// 题解相关
export interface Solution 
{
  id: number
  problem: number
  author: number
  author_username: string
  title: string
  content: string
  language: string
  is_public: boolean
  created_at: string
  updated_at: string
}

export interface CreateSolutionRequest 
{
  title: string
  content: string
  language: string
  is_public?: boolean
}

// 单次提交复盘 Agent
export type AgentHintLevel = 'direction'|'locate'|'explain'

export type AgentRunStatus = 'RUNNING'|'COMPLETED'|'FAILED'

export interface CreateAgentRunRequest
{
  submission_id: number
  hint_level: AgentHintLevel
}

export interface AgentStep
{
  id: number
  step_type: string
  input_summary: string
  output_summary: string
  success: boolean
  created_at: string
}

export interface AgentRun
{
  id: number
  submission_id: number
  problem_title: string
  hint_level: AgentHintLevel
  status: AgentRunStatus
  selected_solution: number|null
  selected_solution_title: string
  final_message: string
  confidence: number
  steps_count: number
  error_message: string
  steps: AgentStep[]
  created_at: string
  updated_at: string
}
