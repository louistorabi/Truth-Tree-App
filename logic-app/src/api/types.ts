import { z } from "zod";

export const TruthTableResponseSchema = z.object({
  variables: z.array(z.string()),
  rows: z.array(
    z.object({
      assignment: z.record(z.string(), z.boolean()),
      value: z.boolean(),
    })
  ),
});

export type TruthTableResponse = z.infer<
  typeof TruthTableResponseSchema
>;
