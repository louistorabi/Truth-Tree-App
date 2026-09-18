import { api } from "./client";

// Calls POST /argument-tree with premises + conclusion
export async function getArgumentTree(premises: string[], conclusion: string) {
  const res = await api.post("/argument-tree", { premises, conclusion });
  return res.data;
}
