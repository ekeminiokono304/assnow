// Everything business-specific lives here. Edit this file to change copy, areas or reviews.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WA_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "2348061380762";
export const PHONE_DISPLAY = "+234 806 138 0762";

export function waLink(message: string): string {
  return `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(message)}`;
}

export const BOOK_MESSAGE = "Hi As Snow! I'd like to book a cleaning / pest control service.";

export const SERVICES = [
  { key: "home_cleaning", title: "Home Cleaning", blurb: "Deep or routine cleans for flats, bungalows and duplexes: kitchens, bathrooms, floors and windows.", icon: "home" },
  { key: "office_cleaning", title: "Office Cleaning", blurb: "Spotless desks, floors and restrooms. Daily, weekly or after-hours service for offices and shops.", icon: "building" },
  { key: "pest_control", title: "Pest Control", blurb: "Targeted treatment for cockroaches, ants, rodents and mosquitoes, safe for family and pets.", icon: "bug" },
  { key: "fumigation", title: "Fumigation", blurb: "Full-property fumigation for stubborn infestations, with follow-up visits to keep pests away.", icon: "shield" },
] as const;

export const PROPERTY_SIZES = [
  { key: "small", label: "Small (studio / 1-bed / small shop)" },
  { key: "medium", label: "Medium (2-3 bed / small office)" },
  { key: "large", label: "Large (4+ bed / duplex / big office)" },
];

export const FREQUENCIES = [
  { key: "once", label: "One-time", note: "" },
  { key: "weekly", label: "Weekly", note: "save 15%" },
  { key: "biweekly", label: "Every 2 weeks", note: "save 10%" },
  { key: "monthly", label: "Monthly", note: "save 5%" },
];

// Placeholder areas: replace with the areas As Snow actually serves.
export const AREAS = ["Gbagada", "Yaba", "Surulere", "Ikeja", "Maryland", "Ojota", "Anthony", "Lekki", "Victoria Island", "Ikoyi", "Ajah", "Magodo"];

export const RATING = { score: "5.0", count: 170 };
export const GOOGLE_REVIEWS_URL = "https://www.google.com/maps/search/?api=1&query=As+Snow+Cleaning+%26+Pest+Control+Lagos";

// Add REAL customer testimonials here (copy them from Google reviews, with permission).
// Nothing is shown until you add some, so the site never displays invented reviews.
export const TESTIMONIALS: { quote: string; name: string; area?: string }[] = [];
