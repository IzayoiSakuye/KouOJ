import http from './http'
import type {
  AdminAnnouncement,
  AnnouncementWriteRequest,
  PaginatedResponse,
  ProblemDetail,
  ProblemListItem,
  ProblemWriteRequest,
  Tag,
  TestCase,
  TestCaseWriteRequest,
} from '../types/api'

export interface PageQuery
{
  page?: number
  search?: string
}

export interface TestCaseQuery extends PageQuery
{
  problem?: number
  is_sample?: boolean
}

export function getAdminProblems(params?: PageQuery)
{
  return http.get<PaginatedResponse<ProblemListItem>>('/problems/', {params})
}

export function getAdminProblem(id: number)
{
  return http.get<ProblemDetail>(`/problems/${id}/`)
}

export function createProblem(data: ProblemWriteRequest)
{
  return http.post<ProblemDetail>('/problems/', data)
}

export function updateProblem(id: number, data: ProblemWriteRequest)
{
  return http.patch<ProblemDetail>(`/problems/${id}/`, data)
}

export function deleteProblem(id: number)
{
  return http.delete(`/problems/${id}/`)
}

export function getAdminTags(params?: PageQuery)
{
  return http.get<PaginatedResponse<Tag>>('/tags/', {params})
}

export function createTag(data: Pick<Tag, 'name'>)
{
  return http.post<Tag>('/tags/', data)
}

export function updateTag(id: number, data: Pick<Tag, 'name'>)
{
  return http.patch<Tag>(`/tags/${id}/`, data)
}

export function deleteTag(id: number)
{
  return http.delete(`/tags/${id}/`)
}

export function getAdminTestCases(params?: TestCaseQuery)
{
  return http.get<PaginatedResponse<TestCase>>('/test-cases/', {params})
}

export function createTestCase(data: TestCaseWriteRequest)
{
  return http.post<TestCase>('/test-cases/', data)
}

export function updateTestCase(id: number, data: TestCaseWriteRequest)
{
  return http.patch<TestCase>(`/test-cases/${id}/`, data)
}

export function deleteTestCase(id: number)
{
  return http.delete(`/test-cases/${id}/`)
}

export function getAdminAnnouncements(params?: PageQuery)
{
  return http.get<PaginatedResponse<AdminAnnouncement>>('/announcements/', {params})
}

export function createAnnouncement(data: AnnouncementWriteRequest)
{
  return http.post<AdminAnnouncement>('/announcements/', data)
}

export function updateAnnouncement(id: number, data: AnnouncementWriteRequest)
{
  return http.patch<AdminAnnouncement>(`/announcements/${id}/`, data)
}

export function deleteAnnouncement(id: number)
{
  return http.delete(`/announcements/${id}/`)
}
