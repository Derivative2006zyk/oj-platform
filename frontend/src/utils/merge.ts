export interface ConflictDetail {
  problem_id: number
  client_version: number
  server_version: number
  server_updated_at: string | null
  server: Record<string, any>
}

export const MERGEABLE_FIELDS = [
  'title',
  'category_id',
  'bank_id',
  'paper_id',
  'difficulty',
  'description',
  'answer',
  'explanation',
  'tags',
  'options',
  'blanks',
] as const

export const FIELD_LABELS: Record<string, string> = {
  title: '标题',
  category_id: '分类',
  bank_id: '归属题库',
  paper_id: '归属试卷',
  difficulty: '难度',
  description: '题目描述',
  answer: '答案',
  explanation: '解析',
  tags: '标签',
  options: '选项',
  blanks: '填空',
}

function sortKeys(obj: Record<string, any>): Record<string, any> {
  return Object.keys(obj)
    .sort()
    .reduce<Record<string, any>>((acc, k) => {
      acc[k] = obj[k]
      return acc
    }, {})
}

export function normalize(value: any): string {
  if (value === null || value === undefined) return ''
  if (Array.isArray(value)) {
    return JSON.stringify(value.map(v => (v && typeof v === 'object' ? sortKeys(v) : v)))
  }
  if (typeof value === 'object') return JSON.stringify(sortKeys(value))
  return String(value)
}

export function isEqual(a: any, b: any): boolean {
  return normalize(a) === normalize(b)
}

export interface MergeResult {
  ok: boolean
  merged?: Record<string, any>
  overlap: string[]
  localChanged: string[]
  serverChanged: string[]
}

/**
 * 以加载时的基线为参照做三路合并。
 * 基线缺失时无法判断改动来源，一律视为冲突。
 */
export function tryMerge(
  local: Record<string, any>,
  base: Record<string, any> | null,
  server: Record<string, any>
): MergeResult {
  if (!base) {
    return {
      ok: false,
      merged: undefined,
      overlap: [...MERGEABLE_FIELDS],
      localChanged: [],
      serverChanged: [],
    }
  }

  const localChanged = MERGEABLE_FIELDS.filter(f => !isEqual(local[f], base[f]))
  const serverChanged = MERGEABLE_FIELDS.filter(f => !isEqual(server[f], base[f]))

  const overlap = localChanged.filter(f => serverChanged.includes(f))
  if (overlap.length > 0) {
    return { ok: false, overlap, localChanged, serverChanged }
  }

  const merged: Record<string, any> = { ...server }
  localChanged.forEach(f => {
    merged[f] = local[f]
  })
  merged.version = server.version

  return { ok: true, merged, overlap: [], localChanged, serverChanged }
}

export function parseConflict(e: any): ConflictDetail | null {
  const detail = e?.response?.data?.detail
  if (!detail || typeof detail !== 'object') return null
  return detail.conflict ?? null
}