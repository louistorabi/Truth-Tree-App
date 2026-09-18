import { api } from "./client";

// Calls the backend endpoint POST /truth-tree
export async function getTruthTree(formula: string) {
  const res = await api.post("/truth-tree", { formula });
  return res.data;
}
