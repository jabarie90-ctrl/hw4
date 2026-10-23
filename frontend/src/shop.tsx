import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { ProductCard } from './api'

type ShopContextValue = {
  spotlight: ProductCard[]
  setSpotlight: (items: ProductCard[]) => void
  recentIds: string[]
  pushRecent: (productId: string) => void
}

const ShopContext = createContext<ShopContextValue | null>(null)
const RECENT_KEY = 'campus_customs_recent'

function loadRecent(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

export function ShopProvider({ children }: { children: ReactNode }) {
  const [spotlight, setSpotlight] = useState<ProductCard[]>([])
  const [recentIds, setRecentIds] = useState<string[]>(() => loadRecent())

  const pushRecent = (productId: string) => {
    setRecentIds((prev) => {
      const next = [productId, ...prev.filter((id) => id !== productId)].slice(0, 6)
      localStorage.setItem(RECENT_KEY, JSON.stringify(next))
      return next
    })
  }

  const value = useMemo(
    () => ({ spotlight, setSpotlight, recentIds, pushRecent }),
    [spotlight, recentIds],
  )

  return <ShopContext.Provider value={value}>{children}</ShopContext.Provider>
}

export function useShop(): ShopContextValue {
  const ctx = useContext(ShopContext)
  if (!ctx) throw new Error('useShop must be used inside ShopProvider')
  return ctx
}
