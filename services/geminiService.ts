import { GoogleGenAI, Chat } from "@google/genai";

const apiKey = process.env.API_KEY || '';
let ai: GoogleGenAI | null = null;

const getAI = () => {
  if (!ai && apiKey) {
    ai = new GoogleGenAI({ apiKey });
  }
  return ai;
};

// System instruction tailored for the "Phase 0.5" Trust/Audit model
const SYSTEM_INSTRUCTION = `
You are CeramETS, an expert AI Consultant for EU ETS Compliance in the Ceramic & Tomato industries.
Your primary directive is TRUST and ACCURACY. You must act as if you have access to a RAG (Retrieval Augmented Generation) database of EU laws.

CONTEXT:
- The user is a Plant Manager in Portugal.
- They are worried about audits and fines.
- You have "access" to:
  1. Directive 2003/87/EC (EU ETS)
  2. Regulation (EU) 2018/2066 (MRR)
  3. Regulation (EU) 2018/2067 (AVR)
  4. Portuguese Portaria n.º 256/2015

BEHAVIOR RULES:
1. CITATIONS ARE MANDATORY: Whenever you state a rule, you MUST cite the article. 
   Example: "According to MRR Article 27, you must..."
   Example: "Portaria 256/2015 requires submission via SILiAmb by..."
2. ADMIT UNCERTAINTY: If a question is ambiguous, ask for the specific "Permit" or "Monitoring Plan" details.
3. BE CONCISE: Do not write essays. Use bullet points.
4. PHASE 0.5 MODE: You are currently a "Demo" proving that RAG works.

When you answer, try to format your citations clearly so the UI can highlight them.
`;

export const createConsultationChat = (): Chat | null => {
  const client = getAI();
  if (!client) return null;

  return client.chats.create({
    model: 'gemini-3-flash-preview',
    config: {
      systemInstruction: SYSTEM_INSTRUCTION,
      temperature: 0.2, // Lower temperature for more factual/consistent answers
    },
  });
};

export const generateStrategicReport = async (chatHistory: string) => {
  const client = getAI();
  if (!client) return null;

  const prompt = `
    Based on the following consultation history, generate a JSON object representing the strategic outlook.
    History:
    ${chatHistory}

    Return strictly JSON:
    {
      "summary": "Executive summary...",
      "metrics": [{"year": 2023, "verifiedEmissions": 0, "freeAllocation": 0, "carbonPrice": 0}],
      "advice": [{"title": "", "description": "", "impact": "High", "cost": "$$", "timeframe": ""}]
    }
  `;

  try {
    const response = await client.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: {
        responseMimeType: 'application/json'
      }
    });
    return JSON.parse(response.text || '{}');
  } catch (e) {
    console.error("Error generating report", e);
    return null;
  }
};
