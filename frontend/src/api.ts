export type User = {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
}

export type AuthResponse = {
  user: User
  message: string
}

export type ProductCard = {
  product_id: string
  name: string
  price: number
  garment_type: string
  short_description?: string
  description?: string
  image_file_path: string
  colors?: string
}

export type PageContext = {
  path?: string
  product_id?: string | null
  product_name?: string | null
}

export type ChatResponse = {
  reply: string
  products: ProductCard[]
  suggestions: string[]
  tool_events: { name: string; detail?: string }[]
}

export type ChatHistoryItem = {
  role: string
  content: string
  products: ProductCard[]
  created_at?: string
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json()
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? 'Invalid input').join(' ')
    }
  } catch {
    /* ignore */
  }
  return res.statusText || 'Request failed'
}

export async function signup(payload: {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}): Promise<AuthResponse> {
  const res = await fetch('/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function login(payload: {
  email: string
  password: string
}): Promise<AuthResponse> {
  const res = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function sendChat(payload: {
  message: string
  user_id?: number | null
  page?: PageContext
}): Promise<ChatResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function loadChatHistory(userId: number): Promise<ChatHistoryItem[]> {
  const res = await fetch(`/api/chat/history?user_id=${userId}`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchProducts(params?: {
  q?: string
  garment?: string
}): Promise<ProductCard[]> {
  const sp = new URLSearchParams()
  if (params?.q) sp.set('q', params.q)
  if (params?.garment) sp.set('garment', params.garment)
  const qs = sp.toString()
  const res = await fetch(`/api/products${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function fetchGarmentTypes(): Promise<string[]> {
  const res = await fetch('/api/garment-types')
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
