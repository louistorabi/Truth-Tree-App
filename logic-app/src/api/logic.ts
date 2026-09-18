import { api } from "./client";
import { TruthTableResponseSchema, TruthTableResponse } from "./types";

export async function getTruthTable(
  formula: string
): Promise<TruthTableResponse> {
  const res = await api.post("/truth-table", { formula });
  return TruthTableResponseSchema.parse(res.data);
}

