const DRAFT_PREFIX = 'oj_draft_'

export interface DraftImage {
  id: number
  url: string
}

export interface DraftData {
  language?: string
  code?: string
  choiceSelected?: string
  fillBlanks?: string[]
  proofText?: string
  proofImages?: DraftImage[]
}

function draftKey(problemId: number): string {
  return `${DRAFT_PREFIX}${problemId}`
}

export function loadDraft(problemId: number): DraftData {
  try {
    const raw = localStorage.getItem(draftKey(problemId))
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object') return parsed as DraftData
    return {}
  } catch {
    return {}
  }
}

export function saveDraft(problemId: number, data: Partial<DraftData>): void {
  try {
    const existing = loadDraft(problemId)
    const merged: DraftData = { ...existing, ...data }
    localStorage.setItem(draftKey(problemId), JSON.stringify(merged))
  } catch {
    // 忽略 localStorage 异常
  }
}

export function clearDraft(problemId: number): void {
  try {
    localStorage.removeItem(draftKey(problemId))
  } catch {
    // 忽略
  }
}