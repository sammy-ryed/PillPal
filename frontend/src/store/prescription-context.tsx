"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import type { PrescriptionResult, ReminderPlan } from "@/lib/types";

interface PrescriptionState {
  uploadedFile: File | null;
  parsedResult: PrescriptionResult | null;
  reminderPlan: ReminderPlan | null;
  setUploadedFile: (f: File | null) => void;
  setParsedResult: (r: PrescriptionResult | null) => void;
  setReminderPlan: (p: ReminderPlan | null) => void;
  reset: () => void;
}

const PrescriptionContext = createContext<PrescriptionState | null>(null);

export function PrescriptionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [parsedResult, setParsedResult] = useState<PrescriptionResult | null>(null);
  const [reminderPlan, setReminderPlan] = useState<ReminderPlan | null>(null);

  const reset = useCallback(() => {
    setUploadedFile(null);
    setParsedResult(null);
    setReminderPlan(null);
  }, []);

  return (
    <PrescriptionContext.Provider
      value={{
        uploadedFile,
        parsedResult,
        reminderPlan,
        setUploadedFile,
        setParsedResult,
        setReminderPlan,
        reset,
      }}
    >
      {children}
    </PrescriptionContext.Provider>
  );
}

export function usePrescription(): PrescriptionState {
  const ctx = useContext(PrescriptionContext);
  if (!ctx) throw new Error("usePrescription must be used inside PrescriptionProvider");
  return ctx;
}
