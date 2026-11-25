// Set NEXT_PUBLIC_API_URL in .env.local (or your hosting settings) when the backend isn't on localhost.
export const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type AnalysisResult = {
  ticketId: string;
  summary: string;
  source: "API" | "Mock";
};

const getMockAnalysis = (ticketId: string): AnalysisResult => ({
  ticketId,
  summary: "Mock analysis: backend unavailable, using demo-safe fallback.",
  source: "Mock",
});

export async function getAnalysis(ticketId: string): Promise<AnalysisResult> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(`${BASE_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        requirement: `Demo requirement for ticket ${ticketId}`,
        code_diff: "+ // demo change",
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      console.warn(`getAnalysis failed with status ${response.status}. Returning Mock object.`);
      return getMockAnalysis(ticketId);
    }

    const data = (await response.json()) as {
      message?: string;
      ticket_id?: string;
    };

    return {
      ticketId: data.ticket_id ?? ticketId,
      summary: data.message ?? "Analysis received from backend.",
      source: "API",
    };
  } catch (error) {
    console.warn("Backend not reachable in getAnalysis. Returning Mock object.", error);
    return getMockAnalysis(ticketId);
  } finally {
    clearTimeout(timeoutId);
  }
}
