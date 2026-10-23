import Link from "next/link";

/** Uniwise mark (U with a mortarboard), single ink in currentColor, beside the serif wordmark. */
export function Logo() {
  return (
    <Link href="/" className="inline-flex items-center gap-2 rounded text-ink" aria-label="Uniwise – Trang chủ">
      <svg width="28" height="28" viewBox="40 36 140 130" aria-hidden className="shrink-0">
        <path
          d="M 58 55 V 118 C 58 138 72 152 92 152 C 112 152 126 138 126 118 V 88 H 148"
          fill="none"
          stroke="currentColor"
          strokeWidth="14"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M148 46 L168 58 L148 70 L128 58 Z M148 55 A3 3 0 1 0 148 61 A3 3 0 1 0 148 55 Z"
          fill="currentColor"
          fillRule="evenodd"
        />
      </svg>
      <span className="font-serif text-[22px] font-medium leading-none tracking-tight">Uniwise</span>
    </Link>
  );
}
