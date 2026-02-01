const API_BASE =
  (import.meta as any).env?.PUBLIC_API_URL ?? "http://127.0.0.1:5000";

// --- Types ---

export interface Event {
  name: string;
  description: string;
  address: string;
  website: string;
  image: string;
  cost: string;
  category: string;
}

export interface ScoredEvent {
  event: Event;
  score: number;
}

export interface ItineraryEvent {
  event: Event;
  start: string;
  end: string;
  pictures: string[];
}

export interface Itinerary {
  events: ItineraryEvent[];
}

export interface Constraints {
  destination: string;
  date_of_travel: string;
  address: string;
  freeform_text: string;
}

// --- Helpers ---

async function post<T>(endpoint: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json();
}

// --- API Functions ---

export function generateActivities(constraints: Constraints): Promise<Event[]> {
  return post<Event[]>("/generate_activities", constraints);
}

export function generateItinerary(
  constraints: Constraints,
  events: ScoredEvent[],
): Promise<Itinerary> {
  return post<Itinerary>("/generate_itinerary", {
    ...constraints,
    events,
  });
}

export function uploadItinerary(
  email: string,
  itinerary: Itinerary,
): Promise<{ itinerary_id: string }> {
  return post<{ itinerary_id: string }>("/upload_itinerary", {
    email,
    itinerary,
  });
}

export function getItineraries(email: string): Promise<string[]> {
  return post<string[]>("/get_itineraries", { email });
}

export function fetchItinerary(itineraryId: string): Promise<Itinerary> {
  return post<Itinerary>("/fetch_itinerary", { itinerary_id: itineraryId });
}

export function addPhoto(
  itineraryId: string,
  eventIndex: number,
  photo: string,
): Promise<{ status: string; pictures: string[] }> {
  return post<{ status: string; pictures: string[] }>("/add_photo", {
    itinerary_id: itineraryId,
    event_index: eventIndex,
    photo,
  });
}
