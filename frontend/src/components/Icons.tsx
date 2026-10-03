const P = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" } as const;

export function Icon({ name, className = "h-7 w-7" }: { name: string; className?: string }) {
  const paths: Record<string, React.ReactElement> = {
    home: <path d="M3 11l9-8 9 8M5 10v10h14V10M10 20v-6h4v6" />,
    building: <path d="M5 21V4h9v17M14 9h5v12M9 8h1M9 12h1M9 16h1M3 21h18" />,
    bug: <path d="M9 9a3 3 0 016 0v7a3 3 0 01-6 0zM12 6V3M9 4l1.5 2M15 4l-1.5 2M5 10l4 1M19 10l-4 1M5 18l4-2M19 18l-4-2M5 14h4M15 14h4" />,
    shield: <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4" />,
    repeat: <path d="M17 2l4 4-4 4M3 11V9a3 3 0 013-3h15M7 22l-4-4 4-4M21 13v2a3 3 0 01-3 3H3" />,
    chat: <path d="M21 12a8 8 0 01-11.6 7.1L4 20l1-4.6A8 8 0 1121 12z" />,
    form: <path d="M6 3h9l4 4v14H6zM14 3v5h5M9 13h7M9 17h5" />,
    check: <path d="M5 12l5 5 9-10" />,
    star: <path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" fill="currentColor" />,
  };
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true" {...P}>
      {paths[name]}
    </svg>
  );
}

export function WhatsAppIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M12 2.5a9.5 9.5 0 00-8.2 14.3L2.5 21.5l4.8-1.2A9.5 9.5 0 1012 2.5z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M9 7.5c.3 2.7 2.6 5.3 6.2 6.6l1.6-1.6-2.1-1.3-1 .9c-1-.4-2-1.4-2.5-2.5l.9-1-1.3-2.1z" fill="currentColor" />
    </svg>
  );
}
