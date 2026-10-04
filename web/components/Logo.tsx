/** Brand mark (header and footer). Inline SVG so it scales with `size` and needs no extra request.
 *  The clip-path from the source SVG is dropped: it was a full-size rect (a no-op), and a fixed id
 *  would be duplicated because this component renders twice per page (header and footer). */
export default function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg className="mark-glyph" width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true" focusable="false">
      <path d="M26 0H6C2.68629 0 0 2.68629 0 6V26C0 29.3137 2.68629 32 6 32H26C29.3137 32 32 29.3137 32 26V6C32 2.68629 29.3137 0 26 0Z" fill="#14191E" />
      <path opacity="0.45" d="M16 28C18.7614 28 21 22.6274 21 16C21 9.37258 18.7614 4 16 4C13.2386 4 11 9.37258 11 16C11 22.6274 13.2386 28 16 28Z" stroke="#EEEFEA" strokeWidth="1.4" />
      <path d="M6.80835 12.343L25.3177 19.6477" stroke="#C2717F" strokeWidth="2" strokeLinecap="round" />
      <path d="M16 22.4C22.6274 22.4 28 19.5346 28 16C28 12.4654 22.6274 9.60001 16 9.60001C9.37258 9.60001 4 12.4654 4 16C4 19.5346 9.37258 22.4 16 22.4Z" stroke="#EEEFEA" strokeWidth="1.4" />
    </svg>
  )
}
