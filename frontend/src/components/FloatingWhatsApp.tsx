import { BOOK_MESSAGE, waLink } from "@/lib/site";
import { WhatsAppIcon } from "./Icons";

export default function FloatingWhatsApp() {
  return (
    <a
      href={waLink(BOOK_MESSAGE)}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Book on WhatsApp"
      className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-full bg-wa px-5 py-3.5 font-semibold text-white shadow-lg shadow-black/20 transition hover:bg-wa-dark active:scale-95"
    >
      <WhatsAppIcon />
      <span>Book on WhatsApp</span>
    </a>
  );
}
