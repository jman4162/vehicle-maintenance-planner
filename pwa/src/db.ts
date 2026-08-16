import Dexie, { type EntityTable } from "dexie";
import type { EncryptedEnvelope } from "./crypto";

export interface VaultRecord {
  id: string;
  kind: "decision-packet" | "on-site-decision";
  updatedAt: string;
  envelope: EncryptedEnvelope;
}

export const db = new Dexie("VehicleMaintenancePlanner") as Dexie & {
  vault: EntityTable<VaultRecord, "id">;
};

db.version(1).stores({ vault: "id, kind, updatedAt" });
