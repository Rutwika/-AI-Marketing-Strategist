import type { Segment } from './types'

export interface SegmentInfo {
  name: Segment
  color: string
  description: string
  signal: string
  approach: string
}

export const SEGMENTS: SegmentInfo[] = [
  {
    name: 'Champions',
    color: 'bg-emerald-100 text-emerald-800',
    signal: 'Long relationship, frequent orders, high spend, still buying.',
    description: 'Your most loyal, highest-value customers.',
    approach: 'No discounts - early access, VIP perks, referral asks.',
  },
  {
    name: 'New Potential',
    color: 'bg-sky-100 text-sky-800',
    signal: 'Recent first purchase, only one or two orders so far.',
    description: 'Just joined and freshly engaged.',
    approach: 'Welcome/nurture email, cross-sell an adjacent category.',
  },
  {
    name: 'At-Risk High-Value',
    color: 'bg-amber-100 text-amber-800',
    signal: 'Used to order often and spend a lot - recency and engagement have dropped.',
    description: 'Valuable customers who have gone quiet.',
    approach: 'Priority win-back via SMS or a personal email, strongest allowed offer.',
  },
  {
    name: 'High-Intent Window Shoppers',
    color: 'bg-violet-100 text-violet-800',
    signal: "No purchase yet, but actively browsing or abandoned a cart.",
    description: "Haven't bought, but clearly interested.",
    approach: 'Cart/browse reminder within 24 hours, reviews or social proof.',
  },
  {
    name: 'Bargain Hunters',
    color: 'bg-orange-100 text-orange-800',
    signal: 'Orders often, but almost always with a coupon - low spend per order.',
    description: 'Frequent buyers who need a discount to convert.',
    approach: 'Clearance and overstock promos only - no full-price offers.',
  },
  {
    name: 'Hibernating',
    color: 'bg-slate-200 text-slate-700',
    signal: 'Low recency, frequency and spend across the board.',
    description: 'Effectively inactive.',
    approach: 'One low-cost re-engagement email - no paid channels.',
  },
]

export const SEGMENT_INFO: Partial<Record<string, SegmentInfo>> = Object.fromEntries(
  SEGMENTS.map((s) => [s.name, s]),
)
