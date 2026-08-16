import { z } from "zod";

export const ruleSchema = z.object({
  code: z.string(),
  title: z.string(),
  summary: z.string(),
  market: z.string(),
  model_applicability: z.string(),
  source_url: z.url(),
  retrieved_date: z.iso.date(),
});

export const quoteSchema = z.object({
  id: z.string(),
  shop_id: z.string(),
  plan_id: z.string(),
  received_at: z.iso.date(),
  out_the_door_cents: z.number().int().positive(),
  warranty_score: z.number().min(0).max(1),
  travel_minutes: z.number().int().nonnegative(),
  completeness_score: z.number().min(0).max(1),
  honda_hybrid_experience: z.number().min(0).max(1),
  comparable_scope: z.boolean(),
  written: z.boolean(),
});

export const decisionPacketSchema = z.object({
  schema_version: z.literal(1),
  exported_at: z.iso.datetime(),
  vehicle_label: z.string(),
  plan: z.object({
    id: z.string(),
    service_codes: z.array(z.string()),
    odometer_miles: z.number().int().nonnegative(),
  }),
  catalog: z.array(ruleSchema),
  quotes: z.array(quoteSchema),
  benchmarks: z.array(z.record(z.string(), z.unknown())).default([]),
  on_site: z.record(z.string(), z.unknown()).optional(),
});

export type DecisionPacket = z.infer<typeof decisionPacketSchema>;

export function parseDecisionPacket(value: unknown): DecisionPacket {
  return decisionPacketSchema.parse(value);
}
