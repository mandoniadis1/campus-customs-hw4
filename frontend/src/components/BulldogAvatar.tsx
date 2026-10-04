/** Small Handsome Dan head used as the chat assistant's avatar and launcher icon. */
export default function BulldogAvatar({ size = 32 }: { size?: number }) {
  return (
    <svg className="bulldog-avatar" viewBox="0 0 40 40" width={size} height={size} aria-hidden="true">
      <circle cx="20" cy="20" r="20" fill="#00356b" />
      <path d="M9 12 q-2 -7 5 -5 l1 5 z M31 12 q2 -7 -5 -5 l-1 5 z" fill="#c9a27a" />
      <ellipse cx="20" cy="21" rx="12" ry="11" fill="#e8c9a3" />
      <ellipse cx="20" cy="27" rx="8" ry="5.5" fill="#f6e7d3" />
      <circle cx="15" cy="18" r="1.9" fill="#1b1b1b" />
      <circle cx="25" cy="18" r="1.9" fill="#1b1b1b" />
      <ellipse cx="20" cy="23" rx="3" ry="2" fill="#2a1a12" />
      <path d="M15.5 28 q4.5 3.5 9 0" stroke="#2a1a12" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <path d="M17.5 29 l1 2 l1 -2 M21 29 l1 2 l1 -2" stroke="#fff" strokeWidth="0.9" fill="none" />
    </svg>
  )
}
